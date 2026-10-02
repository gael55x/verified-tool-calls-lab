# Verified Tool Calls Lab

Test whether retrying an operation creates duplicate work. Run a real local HTTP/SQLite example, connect your Python client, and keep the check in CI. Includes the original reproducible research simulator. Python standard library; the bundled tests need no API keys or paid services.

**Status: local/CI testing tool and research lab. Not a production retry SDK or an exactly-once guarantee.** Maintained by Gaille Amolong; an independent project, not an official implementation endorsed by the paper's authors.

Original implementation of the control flow in [Mansoor, Phadke & Rana, arXiv:2608.02645v1](https://arxiv.org/abs/2608.02645v1), with explicitly labeled engineering adaptations and synthetic counterexamples. See the [four-perspective readiness review](docs/READINESS.md) for research validity, business value, engineering readiness and QA coverage.

**This is not a reproduction of the paper's Gemini Flash-Lite/LangGraph LLM results.** A scripted compound action replaces the agent, and several undisclosed environment choices are declared in [PROTOCOL.md](PROTOCOL.md). `paper_literal` preserves Algorithm 1's early SUCCESS return, N=1 iteration bound and final-response omission. `engineering` is a different algorithm and uses stronger predicates/server assumptions. Neither is an exactly-once guarantee.


Read the [technical walkthrough](docs/WALKTHROUGH.md) for the implementation, measured evidence, runnable examples and Mermaid diagrams. Proposed external integrations are labeled separately from implemented behavior.

## Catch a duplicate-write bug in a few minutes

Python 3.10+ on Linux or macOS, from the cloned repository root. Use a Python
interpreter of that version (for example `python3.12` if `python3` is older).

```sh
mkdir -p repro-output
python3 -m vtc.check --profile broken --out repro-output/retry-broken
# Expected exit 1 — the clean control passes; four fault cases create duplicates.
python3 -m vtc.check --profile durable --out repro-output/retry-durable
# Expected exit 0 — exactly one correct ticket in all five cases.
```

The service really writes SQLite rows over HTTP. It drops a reply after commit,
releases a delayed write after a retry, overlaps two attempts and restarts its
process on the same database. JSON and Markdown reports separate what the client
reported from the final records. A missing fault or incomplete observation cannot
receive PASS. Each output directory must be new.

Use your own `function(base_url, operation_id) -> bool` against the fixture with
`--client yourmodule:create_ticket`, or supply test-only hooks for your own service
with `--adapter yourmodule:factory`. The fixture expects a specific ticket protocol;
this is not automatic integration with every API. Read the [complete quickstart and
adapter contract](docs/RETRY_CHECK.md), [measured integration results](docs/RETRY_RESULTS.md)
and [related tools](docs/RELATED_TOOLS.md). Use disposable local test services only.

The practical benefit is a regression test that can catch duplicate work before a
retry-policy change ships. We have demonstrated this in the included reference
application; we have not measured customer adoption or incident reduction.

## Reproduce the original research experiment


Python 3.10+ and Git for revision recording; replay verified on Python 3.12.0 and historical run on 3.12.14. Clone this repository, then run from its root. The original simulator evaluation uses no models, network or databases. The expanded test suite also uses loopback HTTP, child processes and temporary SQLite databases. No external services or payments are involved. Run Python normally, without `-O`: the artifact auditor uses assertions.

```sh
python3 -m unittest discover -s tests -v
python3 -m vtc.evaluate --out repro-output/run-002
python3 -m vtc.audit --run repro-output/run-002
```

Choose a new output directory on each evaluation. Existing results are never overwritten. On a Git checkout the evaluator records HEAD plus individual source hashes. The frozen delivered run lives in `evidence/run-002`; use its `run_manifest.json` for the historical evaluated revision and source hashes. That revision is not in this public repo's clean Git history.

```sh
python3 -m vtc.audit --run evidence/run-002
python3 -m vtc.compare evidence/run-002 repro-output/run-002
```

`vtc.compare` checks byte identity of the five scientific artifacts, excluding run metadata such as timestamp, platform and HEAD. The delivered source manifest separately identifies the evaluated files. Official source links and sanitized search facts are included. Downloaded paper/profile/search archives remain private reviewer evidence and are excluded from this public checkout.

Expected: the full test suite passes (including the original 26 mechanism tests), **2,160 simulator episodes**, audit `PASS`, and `PASS: five scientific artifacts byte-identical`. These checks establish reproducibility for the declared simulator, not safety of an external API.

## Results at a glance

![Main results: safe completion, duplicate effects and false success for four policies under two server contracts](article/figures/main-results.png)

With strong supported keys, engineering v2 safely completes **144/150** main cases versus **101/150** for retry-only, with zero duplicate or false-success episodes in this set. When keys are ignored, engineering safely completes **117/150**, below verify-only's **130/150**, and creates duplicates in **28/150**. There is no universally best policy here.

![Designed stress results: the same outcomes across prescribed failure cases](article/figures/stress-results.png)

Each main bar uses 150 episodes; each stress bar uses 120. False success is divided by **all episodes**, not reported successes. Fixed fixtures and reused seeds do not estimate production incident rates. [Full-size graphs, data and reproduction](article/figures/RESULT_GRAPHS.md) · [Exact results and interpretation](docs/RESULTS.md).

## When to use this lab

- **Developers:** inspect the late-commit demo below, then add a fault case before proposing a retry policy. For your own client, use the HTTP contract checks above. Neither component is a drop-in production retry SDK.
- **AI evaluators:** score final state, duplicate effects and false success separately from the agent's success message. Retain paired inputs and traces.
- **Stakeholders:** use this as evidence for an integration experiment. Any deployment case still needs real server contracts, process-crash/concurrency tests and measured operational costs. No customer ROI or reliability SLA has been established.

## What is measured

The paired main study has 1,200 episodes: two tasks, three fault levels, four methods, 25 seeds and two server profiles. Within each server profile the original paper-shaped two-method subset has 300 episodes. Another 960 episodes cover 12 prescribed faults with five payload fixtures. Total: 2,160. These weights are designed by the protocol, not estimates of real incident frequency.

`activate_customer` has three internal stages: create, activate, append welcome. `record_invoice` has three: update row, append record, mark RECORDED. The literal verifier uses the paper's displayed predicates, which omit part of those tasks; engineering verifies all stages and exactly one append. The truth evaluator also measures invoice final-state success separately from safe success, since a correct recorded invoice can coexist with a duplicate record.

Response, effect and visible state are separate channels. Delays use virtual ticks and an event queue. Supported keys require durable per-stage receipts and pending-operation reservation; unsupported APIs ignore keys. This strong supported contract is modeled, not implemented as a production persistence backend. False acknowledgements and stale FALSE reads remain explicit counterexamples.

Files: `vtc/model.py` implements synthetic effects/read views; `vtc/wrappers.py` contains four policies; `vtc/evaluate.py` generates retained data; `vtc/audit.py` independently recomputes artifact assertions; `tests/test_mechanism.py` exercises counterexamples. The auditor is an author verification tool, not an independent technical reviewer.

## Evidence and review

See [source mapping](docs/SOURCE_MAPPING.md), [eligibility](research/ELIGIBILITY.md), [limitations](docs/LIMITATIONS.md), [results](docs/RESULTS.md), [claim map](docs/CLAIM_EVIDENCE.md), and [technical review record](docs/TECHNICAL_REVIEW.md). Result/review/article files were added after the verified run. The unpublished Medium draft is excluded from this public repository and retained in the separate local research checkout. Independent technical/provenance review and engineering-v2/scientific re-review passed. Editorial review and final user approval still gate Medium publication. Claude was checked with version/auth commands only; no billable prompt was sent by the earlier code-fix task.

The [measured result graphs](article/figures/RESULT_GRAPHS.md) provide full-size SVG/PNG images, exact counts for both API contracts and both evaluation suites, source data, and reproduction commands.

Original code is [MIT licensed](LICENSE); paper attribution and third-party exclusions are in [NOTICE](NOTICE.md). For contribution rules and the remaining adoption gates, see [READINESS.md](docs/READINESS.md). Other public implementations exist; this project's contribution is its explicit comparison and retained counterexamples, not exclusivity.

## Small demo

This shows a verified return followed by a duplicate when an older request completes and the API ignores keys.

```sh
python3 - <<'PY'
from vtc.model import Environment, fixture, stress_tape, full_predicate, duplicate_count
from vtc.wrappers import run_wrapper
action = fixture("record_invoice", 42)
env = Environment(stress_tape("delayed_commit"), supported=False)
reported = run_wrapper("engineering", env.port(), action)
print("reported success:", reported)
print("safe at return:", full_predicate(action, env.truth_snapshot(action)))
env.settle(8)
print("safe after settling:", full_predicate(action, env.truth_snapshot(action)))
print("duplicate committed effects:", duplicate_count(action, env.truth_snapshot(action)))
PY
```

Expected: reported success True; safe at return True; safe after settling False; one duplicate effect. These are logical simulator events.

This public repository was created with one clean import commit, [`775498c`](https://github.com/gael55x/verified-tool-calls-lab/commit/775498c3893f6eab866e71b9d851ab440093c4cd), whose 58-file tree matches the reviewed release archive. Neither run-001's private development revision `0a30de840b7841110bb758aa835340feeb00d9fa` nor run-002's evaluated revision `e64c0305b27afc5269d6eef75a50ebad6fe046d2` is an ancestor in this public Git history. Their identities remain provenance references; `RELEASE_PROVENANCE.json` and the run manifests map them to frozen source hashes and results. The public import verifies the released bytes, not the private commit ancestry. See `docs/RELEASE_REVIEW.md` for excluded archives and review scope.

## Corrected engineering budget (run-002)

Engineering v2 only executes a retry when at least one verification poll remains. A FALSE on the last poll returns failure without creating an unverified side effect. Literal-paper mode is unchanged. The correction and probe are documented in `PROTOCOL_AMENDMENT_002.md` and `evidence/reviewer-probe-002.json`. All 26 tests and the corrected 2,160-episode audit pass. Five scientific outputs match run-001 exactly; no aggregate improvement is claimed. The original run, original-source mapping and local provenance are preserved.

Each 150-row aggregate reuses 25 seed streams across two tasks and three levels. Wilson bounds are descriptive, not independent 95% population coverage; false-success rates use all episodes. Strong supported keys model reservations and durable stage contracts rather than all APIs. Mermaid sources, captions and alt text are in [DIAGRAMS.md](article/figures/DIAGRAMS.md); measured result charts are available above as PNG and in the figure directory as SVG.
