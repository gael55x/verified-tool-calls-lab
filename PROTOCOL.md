# Predeclared mechanism replication protocol

Owner: Gael2. Declared 2026-10-01 before implementation or experiment. Target: arXiv:2608.02645v1. Eligibility record in `research/ELIGIBILITY.md`. Original stdlib-only CPU simulator, not the authors' code or an LLM replication.

## Tasks and truth boundary

Each episode issues one scripted compound synthetic API action, with three internal stages. `activate_customer` creates a customer, sets ACTIVE and activated_at, and appends one welcome message. `record_invoice` updates invoice_id/amount, appends a corresponding record, and sets its status RECORDED. The paper describes multistage tasks but does not specify exact API decomposition: our compound-action choice is a declared simplification. Payloads are synthetic integer amounts/IDs; no money is transferred. No actual plugin/server, payment, network, account or employer data is used.

Only the evaluator can access hidden committed state. Wrappers receive a capability interface with execute, response, read and virtual wait. Verifiers inspect read views, never truth. Virtual time advances effects/visibility through a deterministic event queue; reads themselves do not write task effects. All faults are logical simulator faults, not process, OS, network or power crashes. There is no concurrency claim.

Truth success requires all three stages and correct values; activation requires exactly one welcome. Invoice final-state success allows >=1 correct RECORDED record to expose the distinction between final state and safe execution. Separately, safe task success requires exactly one message/record, no incorrect field, and no duplicate committed append effect. Repeated calls and repeated upserts are not duplicates. Count only committed append effects beyond one per logical task, including partial writes and late arrivals.

## Compared methods

| Mode | Specified behavior |
|---|---|
| retry_only | Execute without key. Inspect initial and up to one retry response. Retry any non-success, no verification |
| verify_only | Execute without key. SUCCESS accepted. Definitive FAILURE rejected. On ambiguity, wait one tick, verify displayed paper predicate once; no retry |
| paper_literal | Algorithm 1 verbatim control flow, N=1. Stable SHA-256 key over agent ID, action type, canonical payload and timestamp bucket captured once. SUCCESS accepted; FAILURE rejected; ambiguous -> wait(i) -> displayed paper predicate; TRUE success; UNKNOWN next loop; FALSE executes same key. Exhaustion failure, no final retry inspection |
| engineering | Explicit adaptation: full task predicate; verify SUCCESS; inspect final retry result; max one retry with up to three total verification polls; UNKNOWN polls without spending retry; durable logical operation ID replaces timestamp bucket in key. Definitive FAILURE still stops. It can return failure with correct eventual state or fail when side effects cannot be undone |

Literal predicates normalize the equation's lowercase `activate` to the task's ACTIVE enum: activation status and non-null activated_at; invoice row exists and matches invoice_id/amount. They intentionally omit the additional narrative requirements. This explicit token normalization is the only correction in the literal predicate. The full predicate in engineering checks the three task stages and exactly one append effect.

Two server profiles: `supported` has durable per-key, per-stage dedupe and pending-operation reservation, with repairable partial operations; `unsupported` ignores keys. This is an idealized **strong** supported contract, beyond the paper's unspecified implementation. It is not enough merely to attach a client header. Persisting partial-stage receipts lets a retry finish missing stages without repeating append effects; this assumption is tested and stated, not claimed to exist in arbitrary APIs.

## Paired seeded main study

2 tasks × 3 levels × 4 methods × 25 seeds (42..66) × 2 server profiles = 1,200 episodes. Each server profile has a 300-episode paper-shaped primary subset (retry_only vs paper_literal), plus verify_only/engineering extensions. Original study used Gemini Flash-Lite ReAct/LangGraph; this study has no LLM, prompts, tokens, paid API calls or packages. Percentages cannot be compared numerically to its LLM success rates.

Fault probabilities, from paper Table 1, are ordered timeout/delayed visibility/partial success/conflict: low .05/.05/.03/.02, medium .20/.15/.10/.05, high .35/.25/.15/.10. Generate four independent Bernoulli flags for each possible attempt before any method runs; same per-seed tape and payload across all modes and server profiles. Consumption is indexed by attempt, not a mutable PRNG cursor. Unknown original precedence is resolved explicitly: conflict -> definitive FAILURE/no writes; otherwise partial applies first two stages; timeout overrides response to AMBIGUOUS; delayed visibility returns AMBIGUOUS and hides writes for two ticks; partial alone returns SUCCESS. Fresh attempt flags apply even to a deduped request's response. Payload seed is held paired. No claim this scheduling matches undisclosed original code.

## Designed stress matrix

2 tasks × 12 patterns × 4 modes × 2 server profiles × 5 seeds (42..46) = 960 episodes. Patterns: clean; commit then timeout; false SUCCESS/no effect; partial SUCCESS; no-effect timeout then clean retry; delayed visibility/stale FALSE; delayed visibility/UNKNOWN; delayed commit; UNKNOWN forever/no effect; definitive conflict then clean next attempt; partial AMBIGUOUS then clean; commit after polling budget. Each pattern's first attempt is prescribed; next attempt is clean unless a pending/read condition says otherwise. These are equally weighted designed cases, not estimates of incident prevalence. Total: 2,160 episodes. No significance claims from stress fixtures. Test counterexamples for incomplete predicates, stable keys, supported/unsupported delayed retries, timeout polling, boundary return, key collision across two legitimate operations, and timestamp bucket changes on restart.

## Bounds and measurement

wait(i)=i virtual ticks. Delayed view becomes visible at tick 2. Delayed commit at tick 2 or 5 as fixture declares. Terminal state is measured both at wrapper return and after fixed tick 8; pending operations must then be empty. A verifier's FALSE on a stale read may be wrong; UNKNOWN cannot imply no effect. No state peek to fix this.

Record reported success, truth success at return/final, safe success at return/final, false success at return/final, false failure at return/final, duplicate effects, missing stages, API executions/retries, verifier reads, actual committed stage writes, virtual latency and settling horizon. Main proportions get Wilson 95% descriptive intervals and paired discordant counts; intervals describe these finite seeded fixtures, not a production population. No optional runtime/throughput benchmark.

Retain manifest/payloads/fault tapes, event JSONL with dispatch/response/read/state/commit/key decisions, per-episode assertions and CSV, summaries, tests, source mapping, sources and hashes. Unexpected exceptions, incomplete matrix, broken baseline sensitivity, mismatched paired tapes, hidden-state reads, or divergent reruns fail verification. Expected scientific failures are retained results, not harness errors. Predeclared controls: clean tasks must pass; retry_only must duplicate commit-then-timeout under unsupported profile; paper_literal must expose false SUCCESS/no-effect and final-response omission counterexamples. Engineering is not guaranteed to win.

## Integrity and review gate

Commit protocol plus dated hash receipt before code. Run tests sequentially, then evaluation, independent artifact audit, and byte-for-byte deterministic replay. Freeze code revision used by evaluation, retain exact source/results manifests, then draft original prose/figure from verified outputs. Audit is separate from article polishing. Author audit is not independent technical review. No verified independent reviewer is invoked by this protocol; independent technical and editorial review remain REQUIRED before publication. No publication, pushes, schedules, other-project edits, new services or auth changes.
