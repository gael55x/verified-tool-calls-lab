# Verified tool calls: a local mechanism replication

An original Python standard-library implementation of the control flow in [Mansoor, Phadke & Rana, arXiv:2608.02645v1](https://arxiv.org/abs/2608.02645), with explicit engineering adaptations and falsifiable synthetic counterexamples. Owner: Gael2. Isolated personal repo; no employer code.

**This is not a reproduction of the paper's Gemini Flash-Lite/LangGraph LLM results.** A scripted compound action replaces the agent, and several undisclosed environment choices are declared in [PROTOCOL.md](PROTOCOL.md). `paper_literal` preserves Algorithm 1's early SUCCESS return, N=1 iteration bound and final-response omission. `engineering` is a different algorithm and uses stronger predicates/server assumptions. Neither is an exactly-once guarantee.

## Run locally

Python 3.10+ and Git for revision recording; verified on Python 3.12.14. No dependency installation, API keys, models, network, payment systems or databases required for tests/evaluation. Run from the repository root. Commands execute sequentially.

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

## What is measured

The paired main study has 1,200 episodes: two tasks, three fault levels, four methods, 25 seeds and two server profiles. Within each server profile the original paper-shaped two-method subset has 300 episodes. Another 960 episodes cover 12 prescribed faults with five payload fixtures. Total: 2,160. These weights are designed by the protocol, not estimates of real incident frequency.

`activate_customer` has three internal stages: create, activate, append welcome. `record_invoice` has three: update row, append record, mark RECORDED. The literal verifier uses the paper's displayed predicates, which omit part of those tasks; engineering verifies all stages and exactly one append. The truth evaluator also measures invoice final-state success separately from safe success, since a correct recorded invoice can coexist with a duplicate record.

Response, effect and visible state are separate channels. Delays use virtual ticks and an event queue. Supported keys require durable per-stage receipts and pending-operation reservation; unsupported APIs ignore keys. This strong supported contract is modeled, not implemented as a production persistence backend. False acknowledgements and stale FALSE reads remain explicit counterexamples.

Files: `vtc/model.py` implements synthetic effects/read views; `vtc/wrappers.py` contains four policies; `vtc/evaluate.py` generates retained data; `vtc/audit.py` independently recomputes artifact assertions; `tests/test_mechanism.py` exercises counterexamples. The auditor is an author verification tool, not an independent technical reviewer.

## Evidence and review

See [source mapping](docs/SOURCE_MAPPING.md), [eligibility](research/ELIGIBILITY.md), [limitations](docs/LIMITATIONS.md), [results](docs/RESULTS.md), [claim map](docs/CLAIM_EVIDENCE.md), and [technical review record](docs/TECHNICAL_REVIEW.md). Result/review/article files were added after the verified run. The unpublished Medium draft is excluded from this public repository and retained in the separate local research checkout. Independent technical/provenance review and engineering-v2/scientific re-review passed. Editorial review and final user approval still gate Medium publication. Claude was checked with version/auth commands only; no billable prompt was sent by the earlier code-fix task.

The [measured result graphs](article/figures/RESULT_GRAPHS.md) provide full-size SVG/PNG images, exact counts for both API contracts and both evaluation suites, source data, and reproduction commands.

There are no schedules or automated third-party messages in this project. The abandoned webhook workspace is separate and untouched.

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

Each 150-row aggregate reuses 25 seed streams across two tasks and three levels. Wilson bounds are descriptive, not independent 95% population coverage; false-success rates use all episodes. Strong supported keys model reservations and durable stage contracts rather than all APIs. Mermaid sources, captions and alt text are in `article/figures/DIAGRAMS.md`; PNG rendering is pending an existing permitted renderer.
