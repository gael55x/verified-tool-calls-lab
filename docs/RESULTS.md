# Measured local results

Source revision: `e64c0305b27afc5269d6eef75a50ebad6fe046d2`. Source/protocol/amendment hashes and runtime are in `evidence/run-002/run_manifest.json`; exact artifact hashes are in `results_manifest.json`.

**2,160 episodes completed, no excluded or failed harness cells.** Main: 1,200. Designed stress: 960. These are CPU simulator outcomes, not reproduced Gemini/LangGraph results. The 26-test log, author artifact audit and byte-identical replay are retained in `evidence/`. Five scientific files also match preserved run-001; no aggregate improvement is claimed. The added reviewer probe demonstrates withholding the last-poll retry. Original independent review and engineering-v2/scientific re-review passed; see [TECHNICAL_REVIEW.md](TECHNICAL_REVIEW.md). Editorial approval is separate.

Safe final completion means full required state and exactly one append effect at tick 8. False success/failure uses that same safety definition and the wrapper return. Duplicate episodes count committed append effects beyond one, not repeated API calls. Counts are out of all episodes, not out of reported successes. Invoice ordinary truth success is separate in raw output.

## Main aggregates

| Server profile | Method | N | Safe final | Reported success | Duplicate episodes | False success final | False failure final |
|---|---|---:|---:|---:|---:|---:|---:|
| unsupported | retry_only | 150 | 101 | 130 | 42 | 33 | 4 |
| unsupported | verify_only | 150 | 130 | 124 | 0 | 16 | 22 |
| unsupported | paper_literal | 150 | 110 | 124 | 20 | 16 | 2 |
| unsupported | engineering | 150 | 117 | 117 | 28 | 2 | 2 |
| supported | retry_only | 150 | 101 | 130 | 42 | 33 | 4 |
| supported | verify_only | 150 | 130 | 124 | 0 | 16 | 22 |
| supported | paper_literal | 150 | 130 | 124 | 0 | 16 | 22 |
| supported | engineering | 150 | 144 | 142 | 0 | 0 | 2 |

## Stress aggregates

| Server profile | Method | N | Safe final | Reported success | Duplicate episodes | False success final | False failure final |
|---|---|---:|---:|---:|---:|---:|---:|
| unsupported | retry_only | 120 | 45 | 120 | 55 | 75 | 0 |
| unsupported | verify_only | 120 | 60 | 50 | 0 | 30 | 40 |
| unsupported | paper_literal | 120 | 50 | 50 | 20 | 30 | 30 |
| unsupported | engineering | 120 | 70 | 70 | 30 | 10 | 10 |
| supported | retry_only | 120 | 45 | 120 | 55 | 75 | 0 |
| supported | verify_only | 120 | 60 | 50 | 0 | 30 | 40 |
| supported | paper_literal | 120 | 70 | 50 | 0 | 30 | 50 |
| supported | engineering | 120 | 100 | 90 | 0 | 0 | 10 |

The supported profile affects keyed methods only. Baselines omit keys, so their outcomes are identical across profiles. Supported means durable stage receipts and pending reservations in the simulator, not arbitrary server support.

## Main safe-final intervals and paired outcomes

| Profile | Method | Safe final proportion | Wilson 95% descriptive interval |
|---|---|---:|---:|
| unsupported | retry_only | 101/150 | 0.594769 to 0.743242 |
| unsupported | verify_only | 130/150 | 0.803020 to 0.912002 |
| unsupported | paper_literal | 110/150 | 0.657385 to 0.797628 |
| unsupported | engineering | 117/150 | 0.707177 to 0.838840 |
| supported | retry_only | 101/150 | 0.594769 to 0.743242 |
| supported | verify_only | 130/150 | 0.803020 to 0.912002 |
| supported | paper_literal | 130/150 | 0.803020 to 0.912002 |
| supported | engineering | 144/150 | 0.915487 to 0.981541 |

Each 150-row aggregate reuses 25 seed streams across two tasks and three levels. Wilson bounds are descriptive and do not assert independent 95% population coverage. Environment assumptions were selected here; no population/generalization or significance claim follows.

| Profile | Paired fixtures | Both safe | Literal only safe | Retry only safe | Neither safe |
|---|---:|---:|---:|---:|---:|---:|
| supported | 150 | 95 | 35 | 6 | 14 |
| unsupported | 150 | 95 | 15 | 6 | 34 |

Per-level/per-task rows and input tapes remain available in the CSV and summary JSON. Stress percentages are not incident-rate estimates; the equal-weight schedules were designed to reveal failure boundaries.

## Calls, reads, writes and virtual delay (main totals)

| Profile | Method | Calls | Verifier reads | Committed stage writes | Return latency ticks, sum |
|---|---|---:|---:|---:|---:|
| unsupported | retry_only | 206 | 0 | 568 | 0 |
| unsupported | verify_only | 150 | 52 | 422 | 52 |
| unsupported | paper_literal | 172 | 52 | 482 | 52 |
| unsupported | engineering | 188 | 211 | 528 | 91 |
| supported | retry_only | 206 | 0 | 568 | 0 |
| supported | verify_only | 150 | 52 | 422 | 52 |
| supported | paper_literal | 172 | 52 | 422 | 52 |
| supported | engineering | 188 | 204 | 436 | 84 |

Ticks are virtual simulator time, not seconds or a throughput/overhead benchmark. Stage writes count actual applied stage transitions; repeated upserts count as writes but are not duplicate append effects.

## Boundary findings

Literal mode can report success without reading state, accept an incomplete displayed predicate, and return failure after a clean retry. Under supported keys, it has no duplicates here but still 16 false-success and 22 false-failure episodes out of 150 main fixtures. Zero duplicates does not mean correct completion reporting.

With unsupported keys, verify_only has 130 safe final episodes versus engineering's 117 out of 150; engineering has 28 duplicate episodes versus literal's 20. More complete verification authorizes repair attempts that can create additional records when the API cannot dedupe partial/late effects. These outcomes are retained rather than selecting a universally winning policy.

The delayed-commit stress case lets engineering verify one correct record and return success before an earlier request later creates a second. The literal one-iteration case can fail even though its retry completed. See `docs/CLAIM_EVIDENCE.md` for exact case IDs and `article/figures/main-safe-completion.svg` for the original data figure.
