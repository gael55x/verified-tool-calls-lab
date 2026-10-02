"""Retry contract check: one logical operation, retried under faults, must leave
exactly one side effect.

    python -m vtc.check --profile broken --out repro-output/retry-broken    # exit 1
    python -m vtc.check --profile durable --out repro-output/retry-durable  # exit 0
    python -m vtc.check --client mymodule:create_ticket   # your client, built-in fixture
    python -m vtc.check --adapter mymodule:factory        # your service, your hooks

Standalone: nothing here uses the vtc simulator. Exit codes: 0 every scenario
passed, 1 a violation was observed, 2 invalid input or an inconclusive run.

Adapter contract. factory(scenario) is called once per scenario and returns a
context manager whose __enter__ returns an object with:

    invoke(operation_id: str) -> bool   one logical call; True if the caller saw success
    restart() -> None                   kill and restart the service, keeping its storage
    settle() -> bool                    release held work and wait; True only once quiet
    observe(operation_id: str) -> Observation   final state, read after settle()

Adapter and client modules are trusted local code imported into this process; they
are not sandboxed. The CLI has a whole-run process deadline and stops its owned
process group on exit. The direct Python API requires bounded adapter I/O; concurrent
calls run on threads and cannot be cancelled in-process. Do not detach child processes.
See docs/RETRY_CHECK.md.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
import signal
import subprocess
import tempfile
import uuid
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_TIMEOUT = 30.0
MAX_EVENTS = 200
SPEC_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*")
EXIT_LABELS = {0: "every scenario passed", 1: "violation observed", 2: "invalid or inconclusive"}
NOTE = (
    "A pass means no duplicate or lost effect was observed in these five deterministic "
    "scenarios against this target. It is not an exactly-once proof."
)


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    parallel: int = 1  # invoke() calls released together through a barrier
    restart: bool = False  # after the first call: restart(), then invoke() the same id again
    required_events: tuple[str, ...] = ()  # observe() must report these to prove the fault ran


SCENARIOS = (
    Scenario("clean", "One call, no fault."),
    Scenario(
        "lost_reply",
        "The service commits, then closes the connection without replying.",
        required_events=("lost_reply:dropped_after_commit",),
    ),
    Scenario(
        "late_commit",
        "The first attempt is held before its write until a retry commits (or settle), then released.",
        required_events=("late_commit:held", "late_commit:released"),
    ),
    Scenario(
        "concurrent",
        "Two calls with the same id start together and overlap inside the service.",
        parallel=2,
        required_events=("concurrent:overlap",),
    ),
    Scenario(
        "restart",
        "One call, a kill and restart of the service process on the same storage, then the same id again.",
        restart=True,
        required_events=("restart:new_process",),
    ),
)


KNOWN_EVENTS = frozenset(event for scenario in SCENARIOS for event in scenario.required_events) | {
    "server:start", "late_commit:hold_timeout", "late_commit:released_at_settle",
    "concurrent:barrier_timeout", "request:received", "effect:committed",
    "effect:replayed", "effect:payload_conflict",
}


@dataclass(frozen=True)
class Observation:
    completed: bool  # the operation's final state exists
    effects: int  # side effects recorded for the operation
    events: tuple[str, ...] = ()  # short lowercase fault labels, e.g. "lost_reply:dropped_after_commit"


@dataclass
class Result:
    scenario: str
    operation_id: str
    status: str = "inconclusive"  # pass | violation | inconclusive
    reason: str = ""
    reported: list[bool] = field(default_factory=list)  # what each invoke() told its caller
    completed: bool | None = None
    effects: int | None = None
    events: list[str] = field(default_factory=list)  # harness steps, in order
    fault_events: list[str] = field(default_factory=list)  # validated labels from observe()
    suggestion: str = ""
    abandoned: bool = False


SUGGEST = {
    "pass": "None for this scenario.",
    "duplicate": (
        "Record the operation id under a UNIQUE constraint in the same transaction as the "
        "side effect, and replay the stored result for repeats."
    ),
    "phantom": "Report success only after the effect is durably committed.",
    "unconfirmed": (
        "The client gave up, so retry handling went untested: retry with the same operation "
        "id, or surface an unknown-outcome error to the caller."
    ),
    "inconclusive": "Fix the adapter, fault hooks or environment and rerun; this scenario proves nothing yet.",
}


class _Abort(Exception):
    """A step failed in a way that leaves the scenario inconclusive."""


class LoadError(Exception):
    pass


def _run(result, step, call):
    """Keep adapter setup, serial calls and cleanup on the owning thread.

    The CLI supervisor enforces the whole-run deadline. Adapter I/O must also
    be bounded when using the Python API directly.
    """
    result.events.append(step)
    try:
        return [call()]
    except Exception as exc:
        raise _Abort(f"{step} raised {type(exc).__name__}") from None


def _parallel(result, step, timeout, calls):
    result.events.append(step)
    boxes = [{} for _ in calls]

    def target(call, box):
        try:
            box["value"] = call()
        except Exception as exc:
            box["error"] = type(exc).__name__

    threads = [threading.Thread(target=target, args=pair, daemon=True)
               for pair in zip(calls, boxes)]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + timeout
    for thread in threads:
        thread.join(max(0, deadline - time.monotonic()))
    if any(thread.is_alive() for thread in threads):
        result.abandoned = True
        raise _Abort("concurrent call was abandoned, not cancelled; stop this process")
    for box in boxes:
        if "error" in box:
            raise _Abort(f"{step} raised {box['error']}")
    return [box["value"] for box in boxes]


def _invoke(result, adapter, operation_id, parallel, timeout):
    first = len(result.reported) + 1
    if parallel == 1:
        values = _run(result, f"invoke:{first}", lambda: adapter.invoke(operation_id))
    else:
        barrier = threading.Barrier(parallel)

        def call():
            barrier.wait(timeout)
            return adapter.invoke(operation_id)

        values = _parallel(result, f"invoke:{first}-{first + parallel - 1}:together", timeout, [call] * parallel)
    for number, value in enumerate(values, first):
        if type(value) is not bool:
            raise _Abort(f"invoke:{number} returned {type(value).__name__}, not bool")
        result.reported.append(value)
        result.events.append(f"invoke:{number}:returned:{str(value).lower()}")


def _judge(result, scenario, observation):
    if (
        not isinstance(observation, Observation)
        or type(observation.completed) is not bool
        or type(observation.effects) is not int
        or observation.effects < 0
    ):
        raise _Abort("observe did not return a valid Observation")
    events = observation.events
    if (
        not isinstance(events, (tuple, list))
        or len(events) > MAX_EVENTS
        or not all(type(e) is str and e in KNOWN_EVENTS for e in events)
    ):
        raise _Abort("observe returned events outside KNOWN_EVENTS")
    result.completed, result.effects, result.fault_events = observation.completed, observation.effects, list(events)
    missing = [e for e in scenario.required_events if e not in events]
    if observation.effects > 1:
        verdict = ("violation", f"{observation.effects} side effects for one operation id", "duplicate")
    elif any(result.reported) and not observation.completed:
        verdict = ("violation", "client reported success but the operation never completed", "phantom")
    elif missing:
        verdict = ("inconclusive", "fault was not exercised; missing events: " + ", ".join(missing), "inconclusive")
    elif not all(result.reported):
        verdict = ("inconclusive", "client reported failure, so retry handling was not confirmed", "unconfirmed")
    elif not observation.completed or observation.effects != 1:
        verdict = ("inconclusive", "completion and effect count disagree", "inconclusive")
    else:
        verdict = ("pass", "one effect and a reported success", "pass")
    result.status, result.reason, result.suggestion = verdict[0], verdict[1], SUGGEST[verdict[2]]


def run_scenario(factory, scenario, timeout=DEFAULT_TIMEOUT):
    """Run one scenario against factory(scenario) and classify what was observed."""
    result = Result(scenario.name, "retry-check-" + scenario.name + "-" + uuid.uuid4().hex)
    operation_id = result.operation_id
    entered = False
    try:
        manager = _run(result, "adapter:create", lambda: factory(scenario))[0]
        adapter = _run(result, "adapter:enter", lambda: manager.__enter__())[0]
        entered = True
        _invoke(result, adapter, operation_id, scenario.parallel, timeout)
        if scenario.restart:
            _run(result, "restart", lambda: adapter.restart())
            _invoke(result, adapter, operation_id, 1, timeout)
        if _run(result, "settle", lambda: adapter.settle())[0] is not True:
            raise _Abort("settle did not confirm that in-flight work finished")
        _judge(result, scenario, _run(result, "observe", lambda: adapter.observe(operation_id))[0])
    except _Abort as exc:
        result.status, result.reason, result.suggestion = "inconclusive", str(exc), SUGGEST["inconclusive"]
    finally:
        if entered and not result.abandoned:
            try:
                _run(result, "adapter:exit", lambda: manager.__exit__(None, None, None))
            except _Abort as exc:
                result.reason = f"cleanup failed: {exc}; {result.reason}"
                result.events.append("adapter:exit:failed")
                if result.status == "pass":
                    result.status = "inconclusive"
                result.suggestion = SUGGEST["inconclusive"]
    return result


def run_checks(factory, timeout=DEFAULT_TIMEOUT):
    """Run every scenario in order; stop starting new ones once a call was abandoned."""
    results = []
    for scenario in SCENARIOS:
        if any(r.abandoned for r in results):
            results.append(
                Result(
                    scenario.name,
                    "retry-check-" + scenario.name,
                    reason="not run: an earlier call was abandoned",
                    suggestion=SUGGEST["inconclusive"],
                )
            )
        else:
            results.append(run_scenario(factory, scenario, timeout))
    return results


def exit_code(results):
    if any(r.status == "violation" for r in results):
        return 1
    return 0 if results and all(r.status == "pass" for r in results) else 2


def load_object(spec):
    """Import trusted local code named MODULE:NAME and return the callable it names."""
    if not SPEC_RE.fullmatch(spec):
        raise LoadError("expected MODULE:NAME, for example mypackage.retry_check:factory")
    module_name, name = spec.split(":")
    try:
        target = getattr(importlib.import_module(module_name), name)
    except Exception as exc:
        raise LoadError(f"could not load {spec} ({type(exc).__name__})") from None
    if not callable(target):
        raise LoadError(f"{spec} is not callable")
    return target


def render_markdown(results, target, code):
    lines = [
        "# Retry contract check",
        "",
        f"Target: {target}",
        "",
        f"Exit code: {code} ({EXIT_LABELS[code]})",
        "",
        "| scenario | status | reported success | final completion | effects | reason |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r.scenario} | {r.status} | {r.reported} | {r.completed} | {r.effects} | {r.reason} |")
    for r in results:
        lines += [
            "",
            f"## {r.scenario}",
            "",
            f"- harness events: {' > '.join(r.events) or 'none'}",
            f"- fault events: {' > '.join(r.fault_events) or 'none'}",
            f"- action: {r.suggestion}",
        ]
    lines += ["", NOTE, ""]
    return "\n".join(lines)


def write_reports(results, out, target, code):
    out = Path(out)
    out.mkdir()  # refuses an existing path
    report = {
        "tool": "vtc.check",
        "target": target,
        "exit_code": code,
        "note": NOTE,
        "scenarios": [asdict(r) for r in results],
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out / "report.md").write_text(render_markdown(results, target, code), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m vtc.check",
        description="Check that retries of one logical operation leave exactly one side effect.",
    )
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument(
        "--adapter", metavar="MODULE:FACTORY", help="your adapter factory (trusted code, run in this process)"
    )
    target_group.add_argument(
        "--client", metavar="MODULE:FUNCTION", help="your function(base_url, operation_id) -> bool, run against the built-in fixture"
    )
    parser.add_argument("--profile", choices=("broken", "durable"), help="built-in fixture behaviour (default: durable)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="whole CLI deadline in seconds; also bounds concurrent joins (default: %(default)s)")
    parser.add_argument("--out", type=Path, help="new directory for report.json and report.md")
    args = parser.parse_args(argv)
    if args.adapter and args.profile:
        parser.error("--profile applies only to the built-in fixture")
    if not 0 < args.timeout <= 600:
        parser.error("--timeout must be in (0, 600]")
    if args.out is not None and (os.path.lexists(args.out) or not args.out.parent.is_dir()):
        print("error: --out must name a new directory inside an existing one", file=sys.stderr)
        return 2
    try:
        if args.adapter:
            factory, target = load_object(args.adapter), f"adapter {args.adapter}"
        else:
            from vtc import http_example

            profile = args.profile or "durable"
            client = load_object(args.client) if args.client else None
            factory = http_example.fixture_factory(profile, client)
            target = f"built-in fixture ({profile}) with client {args.client or 'examples/ticket_client.py:create_ticket'}"
    except LoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    try:
        results = run_checks(factory, args.timeout)
    except Exception as exc:  # a harness bug must not look like a violation (exit 1)
        print(f"error: harness failed ({type(exc).__name__})", file=sys.stderr)
        return 2
    code = exit_code(results)
    for r in results:
        print(f"{r.scenario:<12} {r.status:<13} reported={r.reported} completed={r.completed} effects={r.effects}  {r.reason}")
    print(f"exit {code}: {EXIT_LABELS[code]}")
    if args.out is not None:
        try:
            write_reports(results, args.out, target, code)
        except OSError as exc:
            print(f"error: could not write reports ({type(exc).__name__})", file=sys.stderr)
            return 2
        print(f"reports written to {args.out}")
    return code


def cli(argv=None):
    """POSIX process boundary: kill owned descendants, including on deadline/interrupt.

    Trusted adapters must not detach children into another session. This is
    lifecycle containment, not a security sandbox.
    """
    argv = sys.argv[1:] if argv is None else argv
    bounds = argparse.ArgumentParser(add_help=False)
    bounds.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    args, _ = bounds.parse_known_args(argv)
    if not 0 < args.timeout <= 600:
        print("error: --timeout must be in (0, 600]", file=sys.stderr)
        return 2
    if os.name != "posix":
        print("error: CLI process cleanup currently requires Linux or macOS", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="vtc-check-run-") as tmp:
        env = dict(os.environ, TMPDIR=tmp)
        proc = subprocess.Popen(
            [sys.executable, "-c", "import sys; from vtc.check import main; sys.exit(main())", *argv],
            env=env, start_new_session=True,
        )
        def interrupted(signum, frame):
            raise KeyboardInterrupt

        previous_term = signal.signal(signal.SIGTERM, interrupted)
        try:
            code = proc.wait(timeout=args.timeout)
            return code if code in (0, 1, 2) else 2
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            print("inconclusive: whole-run deadline or interruption; owned process group stopped", file=sys.stderr)
            return 2
        finally:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            signal.signal(signal.SIGTERM, previous_term)


if __name__ == "__main__":
    sys.exit(cli())
