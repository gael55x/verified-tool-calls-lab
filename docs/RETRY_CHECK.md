# Retry contract check (`vtc.check`)

A small, inspectable Python test tool that asks one question of your code: when a
call is retried after a lost reply, a slow first attempt, an overlapping attempt or a
service restart, does the operation still leave exactly one side effect?

It runs five fixed, deterministic scenarios, counts the real effects after all
in-flight work has finished, and exits non-zero when it sees a duplicate. It needs
Python 3.10+ on Linux or macOS and the standard library only. Run it from the repository root; nothing
is installed.

This tool is separate from the `vtc` research simulator. It does not import or change
`model.py`, `wrappers.py`, `evaluate.py`, `audit.py`, `compare.py` or any results.

## Quick start

```sh
mkdir -p repro-output

# Known-bad service: four duplicate effects, exit code 1
python -m vtc.check --profile broken --out repro-output/retry-broken

# Durable service: one effect in every scenario, exit code 0
python -m vtc.check --profile durable --out repro-output/retry-durable
```

`--out` must name a directory that does not exist yet; the tool refuses to touch an
existing path; its parent directory must exist. It validates arguments before it starts anything. Each run writes
`report.json` and `report.md` there. Without `--out` it prints a summary only.

## Scenarios

Every scenario uses one stable operation id (`retry-check-<scenario>-<random suffix>`, fresh for each case), one fixed
payload, and a fresh service with isolated storage.

| scenario | what happens | fault event that must be observed |
|---|---|---|
| `clean` | one call, no fault | none |
| `lost_reply` | the service commits, then closes the connection without a reply; the client should retry | `lost_reply:dropped_after_commit` |
| `late_commit` | the first attempt is held before its write until a retry has committed, then released; if the client never retries, `settle()` releases it | `late_commit:held`, `late_commit:released` |
| `concurrent` | two calls start through a barrier and overlap inside the service | `concurrent:overlap` |
| `restart` | one call, a real kill and restart of the service process on the same storage, then the same id again | `restart:new_process` |

The faults are placed by cooperative, test-only hooks inside the target service, not by
a network proxy. Server-side gates (events and a barrier, not sleeps) decide ordering,
and the service records an audit event when each fault really happened. If the event
is missing, the scenario is inconclusive, never a pass.

After the calls return, the harness calls `settle()` (release anything still held and
wait until no request is in flight) and only then `observe()` the final state.

## Reading results

Each scenario reports **reported success** (what each `invoke()` returned to its caller)
separately from **final completion** and the **effect count** read from storage.

| status | meaning |
|---|---|
| `pass` | every call reported success, the fault event was seen, exactly one effect |
| `violation` | more than one effect, or success was reported but nothing completed |
| `inconclusive` | an adapter error, an invalid observation, a missing fault event, no quiescence, a timeout, a cleanup failure, or the client reported failure so its retry path was never confirmed |

Exit codes: `0` every scenario passed; `1` at least one violation was observed (even if
others were inconclusive); `2` invalid input or anything inconclusive. Errors appear in
reports by exception type only; messages, payloads and headers are never copied.

A client that gives up and returns `False` is reported as inconclusive, not as a pass:
the tool cannot tell "safe" from "untested". This is a deliberate false-negative guard;
expect it with clients that do not retry.

## Run your own client against the built-in fixture

`--client MODULE:FUNCTION` swaps in your function for `examples/ticket_client.py`:

```python
def create_ticket(base_url: str, operation_id: str) -> bool: ...
```

It must send `POST {base_url}/tickets` with header `Idempotency-Key: <operation_id>`
and JSON body `{"title": "printer on fire"}`, bound every attempt with a timeout, return `True`
only on a confirmed 2xx, and return `False` (not raise) when it gives up. Against
`--profile durable` this checks the client side of the contract: a client that mints a
new key per attempt, or never retries, will not pass.

Wrapping an SDK usually takes a few lines:

```python
# mypkg/retry_check_client.py
from mysdk import Client, SdkError

def create_ticket(base_url, operation_id):
    client = Client(base_url=base_url, timeout=2.0, max_retries=2)
    try:
        client.tickets.create(title="printer on fire", idempotency_key=operation_id)
        return True
    except SdkError:
        return False
```

```sh
python -m vtc.check --client mypkg.retry_check_client:create_ticket --profile durable
```

This only works if your client can target the fixture's small protocol. To check your
own service, write an adapter.

## Check your own service: the adapter contract

`--adapter MODULE:FACTORY` imports your factory. It is called once per scenario as
`factory(scenario)` and returns a context manager whose `__enter__` returns an object
with four methods:

| method | contract |
|---|---|
| `invoke(operation_id) -> bool` | make one logical call with your real client code; `True` only if the caller was told it succeeded |
| `restart() -> None` | kill your service process and start a new one on the same storage (only used by `restart`) |
| `settle() -> bool` | release any held request and wait, with a bound, until nothing is in flight; return `True` only if that happened |
| `observe(operation_id) -> Observation` | read the final state from storage: `Observation(completed: bool, effects: int, events: tuple[str, ...])` |

`scenario.name` tells your service which fault to arm. `events` must contain only
labels from `vtc.check.KNOWN_EVENTS` (at most 200) and include the required labels
above, emitted when the fault actually happened. Arbitrary strings, payloads, wrong
types or `effects=True` make the scenario inconclusive and are not copied into reports.
A verifier must check the requested operation and expected content, not merely that
some row exists. An adapter is trusted evidence, not a security boundary.

```python
# mypkg/retry_check.py
import contextlib
import tempfile
from pathlib import Path
from vtc.check import Observation
from mypkg.testing import start_service  # your test-only launcher with fault hooks
from mypkg.client import create_ticket   # your existing client code

@contextlib.contextmanager
def factory(scenario):
    with tempfile.TemporaryDirectory() as tmp:
        service = start_service(fault=scenario.name, db=Path(tmp) / "tickets.sqlite3")
        try:
            yield Adapter(service)
        finally:
            service.stop()

class Adapter:
    def __init__(self, service):
        self.service = service

    def invoke(self, operation_id):
        return create_ticket(self.service.url, operation_id)

    def restart(self):
        self.service.kill()
        self.service.start(fault="clean")

    def settle(self):
        return self.service.release_and_wait_idle(timeout=10)

    def observe(self, operation_id):
        count = self.service.count_rows("tickets")
        completed = self.service.has_ticket(operation_id, title="printer on fire")
        return Observation(completed=completed, effects=count, events=tuple(self.service.fault_events()))
```

The `mypkg` and `mysdk` examples are adaptation sketches, not bundled packages.
The fixture in `vtc/http_example.py` is a complete runnable example of these hooks.
Use disposable local test services only. `--adapter` executes your code and does not
restrict where that code can connect. Never point fault hooks at production.

**Trust and time bounds.** Modules are trusted local code, not sandboxed. The CLI
runs the suite in its own process group with a whole-run deadline (`--timeout`,
default 30 seconds), then kills any remaining owned child processes and removes
its temporary workspace. On deadline or interruption it exits 2; a report may not
have been written, so always check the exit code. Adapters must not detach children
into another process session or rely on exception cleanup to undo writes. The CLI
currently supports Linux and macOS.

Setup, serial invocation, observation and cleanup use the same thread. The concurrent
scenario calls `invoke` from two threads, so that method must use thread-safe clients
or per-call connections. The direct Python API has no whole-process deadline; bound
all adapter I/O yourself. A stuck concurrent call is marked abandoned, later cases
are skipped and in-process cleanup is withheld to avoid racing active work. Discard
that test process. Prefer the CLI for third-party adapter experiments.

## CI

```yaml
- name: Retry contract check
  run: |
    mkdir -p repro-output
    python -m vtc.check --adapter mypkg.retry_check:factory --out repro-output/retry-check
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: retry-check
    path: repro-output/retry-check
```

The job fails on exit 1 (duplicate observed) and exit 2 (could not prove anything).

## The built-in fixture

`python -m vtc.http_example --db FILE --profile broken|durable --fault SCENARIO`
starts a test-only ticket service on `127.0.0.1` with an ephemeral port. The checker
launches it as a separate process with a minimal environment (no inherited tokens or
proxy settings), a bounded readiness wait, a temporary SQLite file per scenario, and
kills it and removes the file afterwards, including on errors. `POST /_test/settle`
and the `--fault` hooks are test controls, not a production API.

- `broken` caches replies in memory only after a reply is sent and otherwise ignores
  the key, so a lost reply, a late first attempt, an overlap or a restart each insert a
  second ticket.
- `durable` checks the key inside the same `BEGIN IMMEDIATE` transaction as the
  insert, backed by `UNIQUE(op_key)` in SQLite, so repeats replay the stored ticket even
  after a restart. Reusing a key with a different payload returns `422`; this is covered
  by `tests/test_check.py`, while the five scenarios use one fixed payload.

The effect count is the number of ticket rows in the isolated database, so a client
that changes its key between attempts also shows up as a duplicate. Completion
separately requires the supplied operation ID and exact declared ticket title. A
wrong-key or wrong-payload write cannot pass merely because one row exists.

## Limitations

- Five scenarios and one payload. A pass means no duplicate was observed in those runs;
  it is not an exactly-once proof and does not explore other interleavings.
- Faults need cooperative test-only hooks in the target. There is no network proxy, so
  partitions, partial writes and timeouts inside your dependencies are not simulated.
- Results are only as honest as your adapter's `observe()` and fault events.
- `restart` kills a process (SIGKILL on POSIX); it does not simulate host crashes or
  lost fsyncs.
- The default example client times out after 2 s, so `late_commit` takes about 2 s.
- A hard CLI timeout stops its process group, not remote services or intentionally
  detached children. The Python API alone cannot cancel a hanging adapter.
- No customer adoption, incident reduction or production readiness is established.

## Related projects

Other MIT-licensed tools cover overlapping ground and may suit you better:
[hhw12409/idempotency-tester](https://github.com/hhw12409/idempotency-tester)
(multi-protocol concurrent replay with database checks and CI),
[sangaraju1988/latch](https://github.com/sangaraju1988/latch) (idempotency middleware
and chaos), [yadukpb/verified-tool](https://github.com/yadukpb/verified-tool)
(postcondition verification) and [Shopify/toxiproxy](https://github.com/Shopify/toxiproxy)
(network fault injection). This tool's scope is narrower: a small stdlib contract suite
with deterministic in-service fault gates and a plug-in adapter.
