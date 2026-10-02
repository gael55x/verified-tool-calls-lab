# Real HTTP retry checks

The practical extension uses real local sockets, an HTTP service in a child process,
and SQLite records. It is separate from the original 2,160-episode simulator study.
The application and failures are controlled test fixtures, not customer traffic.

## Measured reference results

| Scenario | Unsafe service effects | Durable service effects | Expected effects |
| --- | ---: | ---: | ---: |
| Clean control | 1 | 1 | 1 |
| Reply lost after commit | 2 | 1 | 1 |
| First write commits late | 2 | 1 | 1 |
| Concurrent attempts | 2 | 1 | 1 |
| Service process killed and restarted | 2 | 1 | 1 |

The unsafe service exits **1** with four violations. The durable service exits **0**
with five passing checks. Both use the same client and scenarios. The durable fix
stores the operation key under a unique constraint in the same transaction as the
ticket, checks payload identity and replays the existing result. The unsafe version
relies on an in-memory reply cache populated after sending a reply.

These counts are deliberately triggered counterexamples, not incident probabilities,
an estimate of reliability improvement, or proof of exactly-once behavior. They do
not claim that the original paper algorithm was run against this HTTP application.

[Broken service report](../evidence/retry-check-001/broken/report.md) ·
[Durable service report](../evidence/retry-check-001/durable/report.md) ·
[Explicit client adapter report](../evidence/retry-check-001/custom-client/report.md) ·
[Source/environment manifest](../evidence/retry-check-001/manifest.json).

## What the checks establish

- A commit can outlive a lost response or process restart. The checker observes the
  database independently of the HTTP client's success message.
- The late-commit scenario releases pending work before final inspection. Checking
  only at the first successful response would miss the second write.
- Wrong operation IDs, wrong payloads, changed keys across retries, missing fault
  evidence, unavailable observations and mixed false-success responses cannot pass.
- Deadline and SIGTERM tests start a real descendant process during adapter entry
  and check that it cannot finish its delayed write after the CLI is stopped.

## Independent review and limits

Claude Opus 5.5 authored the initial extension. Codex executed it and corrected
review findings. A separate Codex reviewer independently identified and rechecked
wrong-operation completion, mixed false success, lifecycle cleanup and fresh-clone
documentation problems. The final check still trusts adapters to provide honest
observations and fault evidence. It does not discover those facts automatically.

The included client entry point was exercised. An unrelated developer's application
and onboarding experience remain untested. CLI process containment supports Linux
and macOS; it cannot stop remote or deliberately detached services. The direct
Python API requires bounded adapter I/O. Database constraints here protect one
transactional ticket write, not a distributed workflow or a separate email/payment.

The original simulator was rerun and independently audited after the extension.
All five scientific artifacts were byte-identical to `evidence/run-002`. Its original
claims and limitations remain in force. See the [quickstart](RETRY_CHECK.md) to run
your own checks and [related tools](RELATED_TOOLS.md) for existing alternatives.

The retained reports were captured before the final SIGTERM cleanup patch. Their
manifest preserves the exact source hashes from that run. CI runs the final revision
on Python 3.10 and 3.12, including cancellation regression tests and both quickstarts.
