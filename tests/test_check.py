"""Tests for vtc.check: real local HTTP + SQLite fixtures and harness guards. Loopback network only."""

import contextlib
import functools
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import uuid
from dataclasses import asdict
import time
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vtc import http_example  # noqa: E402
from vtc.check import SCENARIOS, Observation, exit_code, main, run_checks, run_scenario, write_reports  # noqa: E402

SECRET = "sk-test-DO-NOT-LEAK-4242"
BY_NAME = {s.name: s for s in SCENARIOS}
ALL_EVENTS = tuple(event for s in SCENARIOS for event in s.required_events)
CREATE_TICKET = http_example.default_client()


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "vtc.check", *args], cwd=ROOT, capture_output=True, text=True, timeout=120
    )


def fresh_key_client(base_url, operation_id):
    """A buggy client: every attempt mints a new key, so retries look like new work."""
    for _ in range(3):
        if CREATE_TICKET(base_url, uuid.uuid4().hex, attempts=1):
            return True
    return False


class FakeAdapter:
    """In-process adapter for harness guard tests; no service behind it."""

    def __init__(self, effects=1, events=ALL_EVENTS, invoked=True, settled=True, observation=None, fail=None, block=None):
        self.effects, self.events, self.invoked, self.settled = effects, events, invoked, settled
        self.observation, self.fail, self.block = observation, fail, block

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        if self.fail == "exit":
            raise RuntimeError(SECRET)

    def invoke(self, operation_id):
        if self.fail == "invoke":
            raise RuntimeError(SECRET)
        if self.block is not None:
            self.block.wait(5)
        return self.invoked

    def restart(self):
        pass

    def settle(self):
        return self.settled

    def observe(self, operation_id):
        if self.observation is not None:
            return self.observation
        return Observation(completed=self.effects > 0, effects=self.effects, events=self.events)


def fake(**options):
    return lambda scenario: FakeAdapter(**options)


def secret_factory(scenario):
    return FakeAdapter(fail="invoke")


def slow_enter_factory(scenario):
    @contextlib.contextmanager
    def manager():
        child = subprocess.Popen([
            sys.executable, "-c",
            "import os,time; from pathlib import Path; time.sleep(2); Path(os.environ['VTC_TEST_MARKER']).write_text('leaked')",
        ])
        try:
            Path(os.environ["VTC_TEST_READY"]).write_text("started")
            time.sleep(20)
            yield FakeAdapter()
        finally:
            child.kill()
            child.wait()
    return manager()


class FixtureEndToEndTests(unittest.TestCase):
    def cli_report(self, profile):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report"
            proc = run_cli("--profile", profile, "--out", str(out))
            self.assertTrue((out / "report.json").exists(), proc.stdout + proc.stderr)
            report = json.loads((out / "report.json").read_text(encoding="utf-8"))
            markdown = (out / "report.md").read_text(encoding="utf-8")
        self.assertEqual([s["scenario"] for s in report["scenarios"]], [s.name for s in SCENARIOS])
        self.assertIn("exactly-once", markdown)
        return proc, report

    def test_broken_profile_duplicates_in_every_fault_scenario(self):
        proc, report = self.cli_report("broken")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(report["exit_code"], 1)
        for s in report["scenarios"]:
            name = s["scenario"]
            self.assertEqual(s["status"], "pass" if name == "clean" else "violation", (name, s["reason"]))
            self.assertEqual(s["effects"], 1 if name == "clean" else 2, name)
            self.assertTrue(s["reported"] and all(s["reported"]), name)
            for event in BY_NAME[name].required_events:
                self.assertIn(event, s["fault_events"])

    def test_durable_profile_passes_every_scenario(self):
        proc, report = self.cli_report("durable")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for s in report["scenarios"]:
            self.assertEqual((s["status"], s["effects"], s["completed"]), ("pass", 1, True), s["scenario"])
            self.assertTrue(all(s["reported"]))

    def test_fault_scenarios_repeat_deterministically(self):
        for profile, status, effects in (("broken", "violation", 2), ("durable", "pass", 1)):
            factory = http_example.fixture_factory(profile)
            for name in ("lost_reply", "late_commit", "concurrent"):
                for _ in range(2):
                    result = run_scenario(factory, BY_NAME[name])
                    self.assertEqual((result.status, result.effects), (status, effects), (profile, name, result.reason))

    def test_durable_replays_same_key_and_rejects_a_different_payload(self):
        with http_example.fixture_factory("durable")(BY_NAME["clean"]) as adapter:
            proc, db = adapter.proc, adapter.db
            self.assertTrue(adapter.base_url.startswith("http://127.0.0.1:"))
            self.assertTrue(adapter.invoke("same-key"))
            self.assertTrue(adapter.invoke("same-key"))
            request = urllib.request.Request(
                adapter.base_url + "/tickets",
                data=json.dumps({"title": "a different ticket"}).encode(),
                headers={"Content-Type": "application/json", "Idempotency-Key": "same-key"},
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request, timeout=5)
            caught.exception.close()
            self.assertEqual(caught.exception.code, 422)
            self.assertTrue(adapter.settle())
            self.assertEqual(adapter.observe("same-key").effects, 1)
        self.assertIsNotNone(proc.poll())
        self.assertFalse(db.exists())

    def test_client_that_never_retries_is_not_a_pass(self):
        client = functools.partial(CREATE_TICKET, attempts=1)
        result = run_scenario(http_example.fixture_factory("durable", client), BY_NAME["late_commit"])
        self.assertEqual(result.status, "inconclusive")
        self.assertEqual(result.reported, [False])
        self.assertEqual((result.completed, result.effects), (True, 1))
        self.assertIn("late_commit:released_at_settle", result.fault_events)
        self.assertEqual(exit_code([result]), 2)

    def test_client_that_changes_key_between_attempts_is_caught(self):
        result = run_scenario(http_example.fixture_factory("durable", fresh_key_client), BY_NAME["lost_reply"])
        self.assertEqual((result.status, result.effects), ("violation", 2))

    def test_wrong_operation_or_payload_cannot_pass(self):
        for client in (
            lambda url, key: CREATE_TICKET(url, "wrong-key"),
            lambda url, key: CREATE_TICKET(url, key, title="wrong payload"),
        ):
            result = run_scenario(http_example.fixture_factory("durable", client), BY_NAME["clean"])
            self.assertEqual((result.status, result.completed, result.effects), ("violation", False, 1))

    def test_server_child_gets_a_minimal_environment(self):
        with mock.patch.dict(os.environ, {"VTC_FAKE_TOKEN": SECRET}):
            env = http_example._child_env()
        self.assertNotIn("VTC_FAKE_TOKEN", env)
        self.assertNotIn(SECRET, env.values())


class HarnessGuardTests(unittest.TestCase):
    def test_one_effect_with_fault_events_passes(self):
        results = run_checks(fake())
        self.assertEqual([r.status for r in results], ["pass"] * len(SCENARIOS))
        self.assertEqual(exit_code(results), 0)

    def test_partial_concurrent_false_success_is_violation(self):
        from vtc.check import Result, _judge
        result = Result("concurrent", "operation", reported=[True, False])
        _judge(result, BY_NAME["concurrent"], Observation(False, 0, ALL_EVENTS))
        self.assertEqual(result.status, "violation")

    def test_serial_adapter_lifecycle_is_same_thread(self):
        class ThreadBound(FakeAdapter):
            def __enter__(self):
                self.owner = threading.get_ident()
                return self
            def invoke(self, key):
                if threading.get_ident() != self.owner:
                    raise RuntimeError("wrong thread")
                return True
            def __exit__(self, *args):
                if threading.get_ident() != self.owner:
                    raise RuntimeError("wrong cleanup thread")
        self.assertEqual(run_scenario(lambda s: ThreadBound(), BY_NAME["clean"]).status, "pass")

    def test_duplicate_effects_are_violations(self):
        results = run_checks(fake(effects=2))
        self.assertEqual({r.status for r in results}, {"violation"})
        self.assertEqual(exit_code(results), 1)

    def test_reported_success_without_completion_is_a_violation(self):
        self.assertEqual({r.status for r in run_checks(fake(effects=0))}, {"violation"})

    def test_missing_fault_events_cannot_pass(self):
        results = run_checks(fake(events=()))
        self.assertEqual(results[0].status, "pass")
        for r in results[1:]:
            self.assertEqual(r.status, "inconclusive")
            self.assertIn("missing events", r.reason)
        self.assertEqual(exit_code(results), 2)

    def test_adapter_errors_are_inconclusive_and_not_leaked(self):
        results = run_checks(fake(fail="invoke"))
        for r in results:
            self.assertEqual(r.status, "inconclusive")
            self.assertIn("RuntimeError", r.reason)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            write_reports(results, out, "fake", exit_code(results))
            text = "".join(p.read_text(encoding="utf-8") for p in sorted(out.iterdir()))
        self.assertIn("RuntimeError", text)
        self.assertNotIn(SECRET, text)

    def test_settle_must_return_true(self):
        for settled in (False, "yes", None):
            self.assertEqual({r.status for r in run_checks(fake(settled=settled))}, {"inconclusive"}, settled)

    def test_invalid_observations_are_rejected_without_copying_them(self):
        bad = (
            {"completed": True, "effects": 1},
            Observation(True, True, ALL_EVENTS),
            Observation(True, 1, ({"token": SECRET},)),
            Observation(True, 1, ["Not A Label"]),
            Observation(True, 1, ["sk-lowercase-secret"]),
        )
        for observation in bad:
            results = run_checks(fake(observation=observation))
            self.assertEqual({r.status for r in results}, {"inconclusive"}, observation)
            self.assertNotIn(SECRET, json.dumps([asdict(r) for r in results]))

    def test_non_bool_invoke_is_inconclusive(self):
        results = run_checks(fake(invoked=1))
        self.assertEqual({r.status for r in results}, {"inconclusive"})
        self.assertIn("returned int", results[0].reason)

    def test_factory_must_return_a_context_manager(self):
        results = run_checks(lambda scenario: object())
        self.assertEqual({r.status for r in results}, {"inconclusive"})
        self.assertIn("adapter:enter raised AttributeError", results[0].reason)

    def test_cleanup_failure_cannot_pass(self):
        results = run_checks(fake(fail="exit"))
        for r in results:
            self.assertEqual(r.status, "inconclusive")
            self.assertTrue(r.reason.startswith("cleanup failed"))
            self.assertNotIn(SECRET, r.reason)

    def test_hanging_call_is_abandoned_and_stops_the_run(self):
        release = threading.Event()
        try:
            results = [run_scenario(fake(block=release), BY_NAME["concurrent"], timeout=0.2)]
        finally:
            release.set()
        self.assertTrue(results[0].abandoned)
        self.assertIn("abandoned, not cancelled", results[0].reason)
        self.assertEqual({r.status for r in results}, {"inconclusive"})



class CliGuardTests(unittest.TestCase):
    def quiet_main(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            try:
                code = main(list(args))
            except SystemExit as exc:
                code = exc.code
        return code, err.getvalue()

    def test_existing_output_directory_is_refused_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "existing"
            out.mkdir()
            (out / "keep.txt").write_text("keep", encoding="utf-8")
            code, _ = self.quiet_main("--profile", "broken", "--out", str(out))
            self.assertEqual(code, 2)
            self.assertEqual(os.listdir(out), ["keep.txt"])
            self.assertEqual((out / "keep.txt").read_text(encoding="utf-8"), "keep")

    def test_invalid_specs_exit_2_without_creating_output(self):
        cases = (
            ("--adapter", "not a spec"),
            ("--adapter", "no_such_module_vtc_xyz:factory"),
            ("--adapter", "os:sep"),
            ("--adapter", "tests.test_check:missing_factory"),
            ("--client", "no_such_module_vtc_xyz:create"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            for flag, spec in cases:
                code, err = self.quiet_main(flag, spec, "--out", str(out))
                self.assertEqual(code, 2, spec)
                self.assertIn("error", err)
                self.assertFalse(out.exists(), spec)

    def test_cli_deadline_stops_children_even_during_adapter_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker, ready = Path(tmp) / "leak", Path(tmp) / "ready"
            env = dict(os.environ, VTC_TEST_MARKER=str(marker), VTC_TEST_READY=str(ready))
            proc = subprocess.run(
                [sys.executable, "-m", "vtc.check", "--adapter", "tests.test_check:slow_enter_factory", "--timeout", "1"],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertTrue(ready.exists(), "probe did not enter the adapter")
            self.assertIn("whole-run deadline", proc.stderr)
            time.sleep(2)
            self.assertFalse(marker.exists(), "child survived the CLI deadline")

    def test_cli_sigterm_stops_its_worker_and_children(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker, ready = Path(tmp) / "leak", Path(tmp) / "ready"
            env = dict(os.environ, VTC_TEST_MARKER=str(marker), VTC_TEST_READY=str(ready))
            proc = subprocess.Popen(
                [sys.executable, "-m", "vtc.check", "--adapter", "tests.test_check:slow_enter_factory"],
                cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            try:
                deadline = time.monotonic() + 5
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(ready.exists(), "probe did not enter the adapter")
                proc.terminate()
                stdout, stderr = proc.communicate(timeout=5)
                self.assertEqual(proc.returncode, 2, stdout + stderr)
                time.sleep(2)
                self.assertFalse(marker.exists(), "child survived SIGTERM")
            finally:
                if proc.poll() is None:
                    proc.kill()
                proc.communicate()

    def test_profile_with_adapter_is_rejected(self):
        code, _ = self.quiet_main("--adapter", "tests.test_check:secret_factory", "--profile", "broken")
        self.assertEqual(code, 2)

    def test_cli_does_not_leak_adapter_exception_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            proc = run_cli("--adapter", "tests.test_check:secret_factory", "--out", str(out))
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            reports = "".join(p.read_text(encoding="utf-8") for p in sorted(out.iterdir()))
        self.assertIn("RuntimeError", reports)
        for text in (proc.stdout, proc.stderr, reports):
            self.assertNotIn(SECRET, text)


if __name__ == "__main__":
    unittest.main()
