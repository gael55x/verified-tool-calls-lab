# Paper-to-code mapping and departures

Official sources: [arXiv HTML v1](https://arxiv.org/html/2608.02645v1) and [official PDF v1](https://arxiv.org/pdf/2608.02645v1), Mansoor, Phadke & Rana. **Private reviewer archive only, excluded from this public checkout:** the downloaded PDF and extracted text used to read all 12 pages. Those files are not available at local paths in this checkout. Paper license: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This is original code, not author-provided code.

| Paper location | Local implementation | Verification / interpretation |
|---|---|---|
| Algorithm 1 execute before loop, PDF p7 | `vtc.wrappers.paper_literal`: execute before range(1,n+1) | N=0 behavior also preserves initial execution; evaluation uses N=1 |
| Algorithm 1 SUCCESS branch | immediate True, no read | `test_literal_false_success_without_effect` |
| Algorithm 1 definitive FAILURE branch | immediate False, no read or retry | `test_definitive_failure_shortcircuits_verification` |
| Algorithm 1 AMBIGUOUS/backoff | wait(i) virtual ticks, then verifier | Backoff shape absent in paper; linear ticks are declared |
| Algorithm 1 TRUE / UNKNOWN / FALSE | return / continue / execute same key | `test_n_is_iteration_not_retry_budget`, `test_stable_key_across_retry` |
| Algorithm 1 loop exhaustion | False without final response inspection | `test_literal_last_retry_response_not_inspected` |
| Section 4.3 displayed activation formula | status ACTIVE and activated_at non-null | Explicit `activate` -> ACTIVE enum normalization; welcome omitted, as displayed |
| Section 4.3 displayed invoice formula | row exists; invoice ID and amount match | Required record and RECORDED status not in displayed formula; retained omission |
| Section 4.2 narrative tasks | compound API with three internal stages | Simplified API decomposition, not an LLM-selected multistage tool sequence |
| Section 4.4 verifier three values/read-only | copied visible views or UNKNOWN; `verify` | No truth access by wrapper; intentionally stale FALSE is possible |
| Section 4.5 key hash | SHA-256 of canonical agent/type/payload/bucket | Hash/canonicalization/bucket width unspecified; bucket fixed at call creation |
| Section 4.5 underlying support condition | supported or ignored keys | Supported profile adds stronger per-stage repair/reservation contract |
| Section 4.6 one retry / N=1 | literal loop N=1, versus labeled bounded adaptation | Source does not resolve loop-iteration/poll/retry mismatch; no silent fix |
| Table 1 fault probabilities | `LEVELS`, `main_tape` | Independent Bernoulli flags; precedence/latency choices declared in protocol |
| Main study 25 seeds from 42 and two tasks | range(42,67), paired precomputed tapes | Extended four methods/two profiles; two-method subset retained |
| Section 5.2 retry-only / verify-only ablation | explicit baseline functions | Prompt/model behavior replaced by deterministic dispatch; verify-only omits key |
| Section 5.4 task success/duplicate side effects | return and final truth; append effect counts | Reads/calls/writes/false outcomes/virtual latency added as local metrics |
| Wilson intervals | `vtc.evaluate.wilson` | Descriptive seeded-fixture intervals, not deployment inference |

## Engineering mode, explicitly different

Engineering checks full narrative task completion, including exactly one append; verifies SUCCESS as well as AMBIGUOUS; reads the final retry response; allows three verification polls with one execution retry; UNKNOWN spends a poll, not the execution retry budget; uses caller operation ID rather than timestamp bucket. It keeps the definitive FAILURE stop. It cannot undo committed duplicates, prevent late unsupported commits, or prove safety from a stale/incomplete verifier. Repairing partial operations safely relies on modeled durable stage receipts.

Engineering v2 (run-002) reserves at least one remaining verification poll before issuing a retry. A FALSE on the last poll cannot authorize a new execution. Invalid nonpositive poll or negative retry bounds are rejected before dispatch. This explicit engineering deviation fixes the independently reviewed final-poll boundary; literal-paper mode is unchanged. See `PROTOCOL_AMENDMENT_002.md`, `evidence/reviewer-probe-002.json` and the three added regression tests. The 2,160 existing matrix fixtures have unchanged scientific outputs; the additional probe demonstrates the withheld retry rather than an aggregate improvement.

No Gemini, LangGraph, LangChain, prompt loop or actual MCP/plugin integration was implemented. Table 1 does not specify whether faults are independent, categorical or ordered, whether keys are accepted by each tool, how partial writes are deduped, or how read views become consistent. Each choice here is an experimental assumption. Main and designed-stress outcomes are kept separate. No figure or code from the authors was copied.

Public-candidate provenance: original run-001 development objects and ancestry are available in a private reviewer bundle, excluded from publication, and were independently verified. `evidence/provenance-reference.json` records its digest and exact chain. The claim is locally predeclared before the implementation commit, not externally timestamped or publicly preregistered. Run-002's evaluated revision is directly present in this checkout's history. Source manifests separately identify both versions.
