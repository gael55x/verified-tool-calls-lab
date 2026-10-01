# Mermaid figure handoff, separate from stable code candidate

These are original editable Mermaid sources, packaged with the corrected engineering-v2 candidate. Source paper: Mansoor, Phadke & Rana, [arXiv:2608.02645v1](https://arxiv.org/abs/2608.02645), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). No paper figures copied. Medium should receive rendered images; native Mermaid rendering is not assumed.

## verified-call-modes.mmd

Caption: Responses and effects travel separately. Literal mode preserves Algorithm 1's early SUCCESS exit and N=1 loop boundary. Engineering v2 adds complete verification and final-response inspection, reserving verification capacity before retrying; it still relies on the service's execution contract.

Alt text: Sequence diagram contrasting literal-paper and engineering wrappers. The synthetic API can commit before an ambiguous reply. A read-only verifier determines skip, retry or bounded polling; stale FALSE reads can authorize unsafe retries. Literal SUCCESS bypasses verification and its last retry response may be uninspected.

Evidence: paper Algorithm 1, source mapping and `vtc/wrappers.py`. This is an algorithm exposition rather than a measured deployment result.

## late-commit-counterexample.mmd

Caption: A correct read at return does not cancel an earlier request. In the unsupported-key fixture, the retry commits at tick 1, verification passes, and the original request appends a duplicate at tick 2.

Alt text: The first invoice request times out and remains pending. At tick 1 a FALSE read permits a retry; it commits and a full verifier observes one correct record. After the wrapper returns success, the earlier request commits a second record. The evaluator rejects safe completion at tick 8.

Evidence: `evidence/run-002/traces.jsonl`, case `stress/record_invoice/delayed_commit/42/unsupported/engineering` and corresponding CSV/assertion row. Scientific data are identical to run-001. Ticks are virtual logical time.

## Rendering status

No permitted existing Mermaid CLI was found on PATH or in the inspected standard global package locations. No installation, paid model call or external rendering service was attempted. The original evaluation chart is already SVG; native/browser visual preview was blocked in this environment, and no workaround was used. PNG diagrams remain pending.

If a supported local Mermaid CLI becomes available, render with an output width of at least 1192 pixels, for example `mmdc -i verified-call-modes.mmd -o verified-call-modes.png -w 1600 -b white` and the analogous command for the counterexample. These commands are instructions for a future permitted renderer, not commands executed here. Inspect the actual PNG dimensions, line wrapping and text before embedding it in Medium. Independent technical/source review should validate the branches and captions first.

Parent update: a separate task is installing the user-approved project-local Mermaid CLI and rendering these sources in its own workspace. This code-fix task does not duplicate installation. PNG assets can be integrated after the stable correction checkpoint. User-approved personal-project Claude transmission is handled by another owner after supported authentication verification; this task makes no Claude call.
