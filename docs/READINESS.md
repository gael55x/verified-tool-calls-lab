# Readiness review — 2 October 2026

The review below describes the original simulator release. The subsequent real HTTP/SQLite contract tool has its own evidence and independent review in [RETRY_RESULTS.md](RETRY_RESULTS.md). Its disposable durable fixture does not establish production readiness.

Reviewer: Codex. Reviewed public source at `c155a551f2a96bc879ce7005c3462cefd126f60c`; this update changes presentation and adds continuous verification, not measured policies, protocol or scientific artifacts. The underlying run-002 source is identified by its frozen hashes in `evidence/run-002/run_manifest.json`.

**Decision: ready as a reproducible research lab. Not ready as a production SDK or evidence of business ROI.** Professional presentation must make that scope easier to understand, not imply author endorsement or deployment approval.

Priority: P1 blocks a production/reliability claim; P2 limits adoption or interpretation. These are review priorities, not a claim that intentional counterexamples are implementation defects.

## AI researcher perspective

**What holds:** explicit literal-versus-engineering distinction, paired latent fault tapes, retained negative results, a locally predeclared protocol and an independent artifact audit. Four policies face the same fixture definitions. Raw traces expose the important mechanism: verification cannot rule out a future commit from an earlier request.

**P1 — external validity remains untested.** Two scripted compound actions replace an LLM agent, and server semantics are chosen by this study. Therefore the 144/150 supported-key result does not reproduce the paper's LLM success rates or predict a deployed agent's performance. Evidence: [protocol](../PROTOCOL.md), [source mapping](SOURCE_MAPPING.md), [limitations](LIMITATIONS.md).

**P2 — novelty is a bounded mechanism study.** Literal pseudocode fidelity and explicit failure traces are useful; verification and idempotency are established techniques. Twenty-five reused seed streams are not 150 independent experiments. Keep descriptive counts; do not turn the Wilson intervals into a generalization/significance claim.

Next falsifiable experiment: freeze one real API's documented idempotency and visibility contract, adapt a disposable local service, and compare all four policies under the same fault schedule. Record deviations before running. A live LLM extension needs fixed model/prompt versions and repeat/cost accounting; it is a separate experiment.

## Business perspective

**Useful now:** a developer education and integration-risk assessment tool for teams building agents that cause side effects. A stakeholder can inspect exactly when a “successful” tool response becomes unsafe, without connecting an account or spending on model calls.

**P1 — no supported product or savings claim.** There is no customer validation, external API integration, durable backend, incident reduction measurement or operating-cost model. The lab should be evaluated as a research asset, not sold as “safe retries for any tool.”

The counter-result matters commercially: under unsupported keys, verify-only safely completes 130/150 main cases versus engineering's 117/150. Engineering produces 28 duplicate episodes. Stronger verification can authorize unsafe repair when the server contract is weak. [Exact table](RESULTS.md).

Pilot gate: choose a concrete side-effect workflow and its owner; document acceptable duplicates, false success, false failure and latency before testing. Demonstrate value over the existing policy on representative workloads and include integration/maintenance costs. No numeric ROI target is invented here.

## Software engineering perspective

**What holds:** small standard-library modules with separate effect simulation, wrapper policy, evaluation and audit responsibilities. No credentials or network are needed. Output directories prevent overwrite; manifests preserve source and result identities. Tests cover partial effects, idempotency-key drift, poll exhaustion and late commits.

**P1 — the supported server contract is modeled, not built.** An in-memory reservation plus per-stage receipt is not durable storage, process recovery or a distributed exactly-once protocol. Caller operation IDs are assumed durable. The copied-view interface is not a security sandbox. Keep the lab API internal to experiments until an adapter's contracts are explicitly tested.

**P2 — onboarding and drift detection needed work.** This update embeds both result charts in the README, states expected command output, corrects stale review/rendering status and adds CI for tests, a new evaluation, artifact audit and byte-identical replay. The scientific implementation remains unchanged. Normal Python is required for the assertion-based auditor; do not use `-O`.

## AI QA evaluator perspective

**Verified in this review:** all 26 tests passed; a fresh 2,160-episode evaluation passed the auditor; all five scientific artifacts matched run-002 byte for byte. This is stronger than a green unit suite alone, but it only verifies the declared fixture model.

**P1 — a correct message is not a correct outcome.** Score full final state and exactly one append at tick 8, plus false success, false failure and duplicate episodes. Keep supported and unsupported profiles separate. The late-commit demo intentionally changes from safe at return to unsafe after settling.

**P2 — missing deployment coverage:** real concurrency, OS/process crashes, key expiry, durable caller recovery, adverse delays beyond tick 8, external API schema drift and stochastic LLM behavior. A production acceptance matrix must add these without relabeling simulator ticks as milliseconds or designed stress weights as incident probabilities.

Golden artifact comparison detects regression, not independent truth. The auditor recomputes predicates from traces, but both are local code; this Codex review is separate AI review, not external human peer review.

## Originality and attribution

A bounded GitHub repository/README search on 2 October 2026 for `2608.02645` returned six repositories. Relevant inspected public READMEs include [verified-tool](https://github.com/yadukpb/verified-tool), describing a TypeScript side-effect wrapper and reconciliation contracts, and [reprise](https://github.com/freyesperales/dev-experiment-038), describing an offline retry-stack safety checker. Their claims were not independently tested; no code was copied or executed.

This supersedes an inference of exclusivity from the earlier [eligibility search](../research/ELIGIBILITY.md). It does not identify either project as the paper authors' official implementation. Our distinctive artifact is this exact four-policy, two-contract, fully retained experiment and its counterexamples. **Independent implementation is supportable; “we are the only ones” is not.** Search indexing, private code and later work remain unknown.

## Contributing and acceptance

Run the README's test/evaluate/audit/compare sequence from the repository root before proposing a change. For graph-only changes, regenerate with `python3 scripts/render_result_graphs.py --out repro-output/figures` and compare the figure data. Use a new output directory each time.

Preserve frozen runs, protocol and historical provenance. A policy, generator or scoring change needs a failing counterexample, a documented protocol amendment and a new named run; never edit old data to make a test pass. State expected changes and retain negative outcomes. Contributions must include provenance/license information and synthetic or explicitly redistributable inputs. Do not commit credentials, private traces or unpublished article drafts. Report issues and propose focused pull requests through this repository's GitHub page.
