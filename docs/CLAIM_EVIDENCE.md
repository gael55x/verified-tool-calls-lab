# Claim-to-evidence map

Current corrected run: `evidence/run-002`, evaluated revision `e64c0305b27afc5269d6eef75a50ebad6fe046d2`, engineering v2. Original run-001 remains intact and identifies development revision `0a30de840b7841110bb758aa835340feeb00d9fa`. Five scientific artifacts are byte-identical across both runs; the fixed boundary is demonstrated by added probe/regression evidence. No aggregate improvement is claimed.

Run-file names below refer to **publicly included** `evidence/run-002/` unless another path is explicit. Summary selectors use `condition=all`; false-success denominators are all episodes. Each 150-row main aggregate reuses 25 seed streams across two tasks and three levels. Wilson bounds are descriptive, with no asserted independent 95% population coverage. Strong supported keys assume modeled reservations/per-stage durable contracts. Gemini/LangGraph results are not reproduced.

| Claim | Publicly included evidence | Selector/check |
|---|---|---|
| Eligible first submission date; bounded code search | `research/ELIGIBILITY.md`, `research/search-facts.json`, [official arXiv record](https://arxiv.org/abs/2608.02645) | v1 July 31, 2026; no universal code-absence claim |
| No usable implementation located | Public search facts and title/ID count JSON | total_count=0; 27 public author repos screened; unindexed/private code remains possible |
| Locally predeclared before implementation commit | `evidence/predeclaration.json`, `evidence/provenance-reference.json`, `evidence/independent-review-001.json` | chain independently verified; not external timestamp/public preregistration |
| Correction declared before corrected implementation | `PROTOCOL_AMENDMENT_002.md`, `evidence/predeclaration-002.json`, public Git ancestry | amendment 2ee93de precedes evaluated e64c030 |
| 26 tests passed | `evidence/test-log-002.txt` | exit_code=0; no skips; three additional regression tests |
| 2,160 episodes without exclusions | `cases.csv`, `summary.json`, `evidence/verification-002.json` | main=1200; stress=960; 270 input families times 8 methods/profiles |
| Corrected replay reproduces exactly | `evidence/verification-002.json`, `vtc.compare` | five scientific files identical to replay and preserved run-001 |
| Unsupported main duplicates: retry 42/150, literal 20/150 | `summary.json`, `cases.csv` | retry_only/paper_literal duplicate_episodes=42/20 |
| Literal main false success 16/150 in each profile | same public run files | paper_literal false_success_final.count=16 |
| Supported main engineering safe 144/150, zero duplicates/false success | same | supported/engineering |
| Unsupported engineering safe 117/150, duplicates 28/150, false success 2/150 | same | unsupported/engineering |
| Unsupported verify-only safe 130/150, false success 16/150, false failure 22/150 | same | unsupported/verify_only |
| Literal SUCCESS accepts a PENDING invoice record without a read | `assertions.jsonl`, `traces.jsonl`, `cases.csv` | stress/record_invoice/partial_success/42/unsupported/paper_literal: reported=1, truth=0, reads=0 |
| Literal's clean final retry completes but returns failure | same | stress/record_invoice/no_effect_timeout/42/unsupported/paper_literal: calls=2, safe_final=1, reported=0 |
| Verified return can precede a late unsupported duplicate | same | stress/record_invoice/delayed_commit/42/unsupported/engineering: safe_at_return=1, safe_final=0, duplicate=1 |
| Engineering v2 withholds final-poll retry lacking verification capacity | `evidence/reviewer-probe-002.json`, regression tests | exact probe: v1 calls2/reads3/failure/safe state; v2 calls1/reads3/failure/no effect; both tasks |
| Penultimate FALSE can retry and verify in the reserved poll | test source/log | calls2/reads3; TRUE verification after retry |
| Stage receipts/pending reservations affect safety | public run traces and tests | supported suppresses repeats; unsupported partial/late effects can duplicate |
| Key recreation/identity sensitivities are tested | test source/log | simulations, not actual process restart or invoice-domain guarantees |
| Original candidate independently verified | `evidence/independent-review-001.json` | original a7c9fe5 matrix, tests, audit, replay and provenance passed |
| Corrected candidate needs re-review | `docs/TECHNICAL_REVIEW.md` | author verification completed; correction review pending |
| Original chart values come from current data | `article/figures/main-safe-completion.svg`, reporting script | run-002 safe_final counts, n=150 |
| Editable original Mermaid sequences are included | `article/figures/*.mmd`, `DIAGRAMS.md` | v2 retry capacity and late-commit case; PNG rendering pending |

## Private reviewer archive: excluded files

Downloaded paper PDF/HTML/extracted text, full third-party profile/API/search/README snapshots, original developer Git archive/bundle and the unpublished Medium draft remain in a separate **private reviewer archive**, not this checkout. Public readers can use the [official HTML](https://arxiv.org/html/2608.02645v1), [official PDF](https://arxiv.org/pdf/2608.02645v1), included search facts and synthetic outputs. The private bundle's digest/chain are recorded publicly; the bundle itself must not be published. The draft still requires editorial review and final user Medium approval. Excluded files are not implied to exist at local paths here.
