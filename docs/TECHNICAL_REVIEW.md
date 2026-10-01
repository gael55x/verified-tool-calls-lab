# Technical review record, separate from editorial draft

Status: **original independent technical/provenance review PASSED; engineering-v2/scientific re-review PASSED; independent editorial review PENDING; Medium article unpublished.** The parent reports that re-review passed 26 tests, 960 boundary combinations, a fresh 2,160-episode evaluation, audits and scientific-file hashes. The documentation corrections recorded below required no scientific rerun. No Claude model was used by the code-fix task. The earlier local CLI auth observation is historical, scoped to that environment; route verification and editorial work belong to the separate owner. Credentials/keychain contents were not inspected, authentication was not changed, and no paid prompts were sent by that task.

## Historical run-001 author-verification record

Run-001 evaluated revision `0a30de840b7841110bb758aa835340feeb00d9fa`. Protocol revision `3e12355bff34e089b88af72bab7dda24aea5f5f2` was locally predeclared before the implementation commit; protocol SHA remains `2ba3d4d87898c51dba18980cf4cf7488215bb7965b2ad671cb40a38fd75bd4dc`. Within this historical run-001 record, no protocol amendment was made after seeing its outcomes. The later run-002 correction was separately declared in `PROTOCOL_AMENDMENT_002.md`; this historical statement does not exclude that documented amendment.

All 23 tests passed sequentially, with no skipped tests. The 2,160-case matrix completed without missing/excluded cells. Both the delivered run and a sequential replay passed the artifact auditor; five scientific files matched byte for byte. The auditor rederived success/duplicate claims without importing the simulator's predicate helpers, verified committed effect traces, stable retry keys, paired tapes, call/read/write bounds, and source/result hashes. A separate arithmetic check recalculated Wilson endpoints, paired discordant counts and aggregate call/read/write/virtual-delay totals. Receipts and logs are retained.

The raw evaluated source is frozen at the revision above. Later reporting/diagram/prose files do not change the measured code. Results are counts over declared fixtures, with no cherry-picked exclusions. Every article number is mapped to evidence. Scientific counterexamples are successful tests of expected limitations, not silently treated as harness errors.

## Findings and current disposition

| Finding | Severity for a production guarantee | Disposition in this repo |
|---|---|---|
| SUCCESS branch bypasses verification | High | Preserved in literal mode; false acknowledgement test demonstrates it. Engineering checks full predicate |
| N=1 literal loop can discard final retry response | High for truthful completion reports | Preserved; regression test and raw case. Engineering inspects final response |
| Displayed predicate omits task-required effects/status | High | Preserved and explicitly mapped; engineering uses narrative-complete predicate |
| Stale FALSE/late non-idempotent commit can duplicate | High | Retained counterexample; no wrapper guarantee claimed |
| Partial repair safety depends on per-stage server receipts | High | Strong supported profile explicitly modeled; unsupported outcomes retain duplicates |
| Timestamp bucket/operation identity/restart semantics unspecified | High | Tests expose sensitivity. Engineering assumes caller retains durable ID; no durable storage implemented |
| Environment and API decomposition underdetermined in paper | Material replication limit | Compound action, precedence, delays and key semantics predeclared; no LLM percentage replication claimed |
| Verification-only can outperform engineering under unsupported keys | Material result | Retained tables and explanation; no guaranteed winner |
| Seed streams reused across task types | Statistical limit | Wilson intervals labeled descriptive; no p-values or population inference |
| Python capability interface is not a security sandbox | Scope limit | Public API/AST/copy tests only; deliberate introspection outside scope |
| Independent reviewer was unavailable during initial author verification | Historical limitation, now closed | Independent original/provenance and engineering-v2/scientific reviews subsequently passed; editorial review and publication approval remain separate |

## Independent review scope and editorial gate

The completed technical reviews covered the evaluated commit, the paper's Algorithm 1 and displayed/narrative postconditions, README commands, raw counterexample traces and the declared assumptions. Relevant boundaries include the compound-action simplification, stage-receipt/pending-reservation contract, false-success definitions, settling horizon, UNKNOWN behavior, key identity and paired seeds. Changes affecting measured code require a newly frozen evaluation; documentation-only corrections preserve the existing scientific files. Old evidence remains available.

Editorial review should check Gaille's voice and execution attribution, distinguish paper-versus-local numbers, avoid invented anecdotes, and retain limits/review status. User-authorized Claude editorial work is owned separately and still requires final user Medium approval. The earlier technical review task created no schedule, remote push or publication.

## Correction record (run-002)

Independent reviewer task `01a0f6a7-22f0-76eb-ab88-274c8bd1f02f` passed the original 23-test matrix/audits/replay and locally verified original commit ancestry/eight source hashes. This result is recorded from the parent report in `evidence/independent-review-001.json`; no external/public timestamp is claimed.

The reviewer found an engineering last-poll FALSE could execute a retry without post-retry verification capacity. Engineering v2 now reserves a remaining poll before retrying. Three added regression tests pass; 26 total tests pass. The exact probe now makes one call rather than two and conservatively returns failure without a new unverified effect. A penultimate-poll FALSE still allows a retry and verified completion. Literal-paper mode is AST-identical.

Correction amendment commit `2ee93dea16466ace9771fb234a6f0618a2085954` precedes evaluated source `e64c0305b27afc5269d6eef75a50ebad6fe046d2`. Run-002 and its replay both pass the 2,160-case auditor. Five scientific files are byte-identical to each other and run-001: no aggregate gain is claimed. Current manifests and reviewer-probe traces are retained. The subsequent independent engineering-v2/scientific re-review passed; it is separate from the original review and editorial approval.

Each 150-row method aggregate reuses 25 seed streams across two tasks and three levels. Wilson bounds are descriptive and do not assert independent 95% coverage. False-success denominators are all episodes. Supported keys model reservations and durable stage contracts; Gemini/LangGraph percentages are not reproduced.

MIT for our original code was explicitly approved by the user and is present in both local repos, with third-party exclusions/attribution retained. Parent verified authenticated `gael55x` through connected Chrome. Rendering and Claude route verification are now handled by separate parent-coordinated tasks; this task performs neither installation nor Claude transmission. The private original Git bundle is excluded from public files/history; its verified digest and ancestry reference are included.

## Documentation-only corrections after scientific re-review

The wrapper sequence now qualifies the effect channel as full, partial, delayed or absent and stops immediately on a definitive FAILURE retry response, without verification. The separate late-commit diagram is unchanged. The historical run-001 record and later amendment are explicitly separated, obsolete reviewer-unavailable wording is closed, and release notes distinguish both private evaluated revisions from the public import. Those historical documentation corrections did not change measured code, protocol/amendment, tests or evaluation files and required no new experiment.
