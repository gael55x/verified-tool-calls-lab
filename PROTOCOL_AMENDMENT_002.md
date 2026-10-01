# Predeclared correction for evaluation run-002

Declared 2026-10-01, before corrected code and run-002. Original protocol, run-001, and its source revision remain preserved. This amendment responds to independent reviewer task `01a0f6a7-22f0-76eb-ab88-274c8bd1f02f` and does not change literal-paper mode, task fixtures, fault tapes, seeds, server profiles, metrics, matrix size or settling horizon.

## Engineering v2 budget rule

The original engineering implementation could execute a retry after its final verification poll. Although it inspected that response, it had no capacity left to verify the retry's effects. Reviewer probe: first attempt has no effect, AMBIGUOUS response, UNKNOWN until tick 3; second attempt is clean. With three polls, v1 makes two calls and returns failure despite a correct final state.

Engineering v2 reserves at least one remaining verification poll before executing a retry. A FALSE result on the final poll does not authorize a new execution; the wrapper returns failure with the current state. UNKNOWN still spends a poll and never alone authorizes retry. Retries remain capped at one and total verifier reads at three. A retry response is inspected; a subsequent full verification consumes the reserved poll unless a definitive FAILURE already permits stopping. Invalid nonpositive poll bounds or negative retry bounds are rejected before dispatch. This rule is an explicitly labeled engineering deviation, not a correction to Algorithm 1.

Regression coverage must demonstrate: the exact reviewer probe causes no unverifiable retry; a penultimate-poll FALSE can retry and verify within the third poll; a one-poll FALSE cannot retry; invalid budgets cannot dispatch. Retain original-versus-corrected probe traces. All scientific failures remain results, and no aggregate improvement is assumed.

Run the same 2,160-episode matrix in a new `evidence/run-002` directory and compare its scientific outputs to run-001, reporting any differences or unchanged counts. Freeze a new evaluated revision and source/amendment hashes. Run tests sequentially, artifact audit and deterministic replay. Original predeclaration/implementation commit objects and ancestry are provided in a private reviewer bundle, excluded from the public candidate.

## Statistical and release interpretation retained

Each 150-row main-method aggregate reuses 25 seed streams across two tasks and three levels. Wilson bounds are descriptive and have no asserted independent 95% population coverage. False-success counts use all episodes as the denominator. The supported server models pending reservations and per-stage durable contracts, not every API supporting a key. Gemini/LangGraph outcomes remain unreproduced. Independent review of the correction and source/license checks still gate public release; the Medium draft has separate editorial and final user approval gates.
