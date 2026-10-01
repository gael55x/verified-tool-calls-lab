"""Sequential predeclared experiment. python3 -m vtc.evaluate --out DIR"""
import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

from .model import (Environment, LEVELS, PATTERNS, TASKS, canonical, digest,
                    duplicate_count, fixture, full_predicate, main_tape,
                    paper_predicate, stress_tape, task_predicate)
from .wrappers import MODES, run_wrapper

FIELDS = ("case_id", "input_id", "suite", "task", "condition", "seed", "profile",
          "mode", "reported_success", "truth_at_return", "truth_final",
          "safe_at_return", "safe_final", "false_success_at_return", "false_success_final",
          "false_failure_at_return", "false_failure_final", "duplicate_effects",
          "missing_stages_final", "calls", "retries", "reads", "writes_at_return",
          "writes_final", "latency_ticks", "horizon_ticks", "input_sha256")


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def wilson(k, n):
    z = 1.959963984540054
    d = 1 + z*z/n
    mid = (k/n + z*z/(2*n))/d
    half = z*math.sqrt((k/n)*(1-k/n)/n + z*z/(4*n*n))/d
    return [round(mid-half, 6), round(mid+half, 6)]


def missing_stages(action, state):
    if action.task == "activate_customer":
        return int(not state.get("customer")) + int(not paper_predicate(action, state)) + int(not state.get("messages"))
    return (int(not paper_predicate(action, state)) + int(not state.get("records"))
            + int(not any(r.get("status") == "RECORDED" for r in state.get("records", []))))


def episode(meta, input_data):
    action = fixture(meta["task"], meta["seed"])
    from .model import Fault
    tape = [Fault(**f) for f in input_data["tape"]]
    env = Environment(tape, supported=meta["profile"] == "supported")
    result = run_wrapper(meta["mode"], env.port(), action)
    at_return = env.truth_snapshot(action)
    latency, writes_at_return = env.tick, env.writes
    env.note("evaluator_at_return", state=at_return)
    env.settle(8)
    final = env.truth_snapshot(action)
    env.note("evaluator_final", state=final, pending=0)
    truth_return, truth_final = task_predicate(action, at_return), task_predicate(action, final)
    safe_return, safe_final = full_predicate(action, at_return), full_predicate(action, final)
    row = dict(meta, reported_success=int(result), truth_at_return=int(truth_return),
               truth_final=int(truth_final), safe_at_return=int(safe_return), safe_final=int(safe_final),
               false_success_at_return=int(result and not safe_return),
               false_success_final=int(result and not safe_final),
               false_failure_at_return=int(not result and safe_return),
               false_failure_final=int(not result and safe_final),
               duplicate_effects=duplicate_count(action, final),
               missing_stages_final=missing_stages(action, final),
               calls=env.calls, retries=env.calls-1, reads=env.reads,
               writes_at_return=writes_at_return, writes_final=env.writes,
               latency_ticks=latency, horizon_ticks=8, input_sha256=digest(input_data))
    assertions = dict(case_id=meta["case_id"], action=asdict(action),
                      at_return=at_return, final=final,
                      checks={k: row[k] for k in FIELDS if k not in meta
                              and k != "input_sha256"})
    return row, assertions, env.trace


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        for condition in ("all", row["condition"]):
            groups[(row["suite"], row["profile"], row["mode"], condition)].append(row)
    metrics = ("reported_success", "truth_final", "safe_final", "false_success_final",
               "false_failure_final")
    summaries = []
    for (suite, profile, mode, condition), values in sorted(groups.items()):
        item = dict(suite=suite, profile=profile, mode=mode, condition=condition, n=len(values))
        for metric in metrics:
            k = sum(r[metric] for r in values)
            item[metric] = dict(count=k, rate=round(k/len(values), 6))
            if suite == "main":
                item[metric]["wilson95_descriptive"] = wilson(k, len(values))
        item["duplicate_episodes"] = sum(r["duplicate_effects"] > 0 for r in values)
        for metric in ("duplicate_effects", "calls", "reads", "writes_final", "latency_ticks"):
            item[metric + "_sum"] = sum(r[metric] for r in values)
        summaries.append(item)
    pairs = defaultdict(dict)
    for row in rows:
        if row["suite"] == "main" and row["mode"] in ("retry_only", "paper_literal"):
            pairs[(row["profile"], row["task"], row["condition"], row["seed"])][row["mode"]] = row
    paired = []
    for profile in ("supported", "unsupported"):
        a_only = b_only = both = neither = 0
        for key, pair in pairs.items():
            if key[0] != profile:
                continue
            a, b = pair["retry_only"]["safe_final"], pair["paper_literal"]["safe_final"]
            a_only += a and not b; b_only += b and not a
            both += a and b; neither += not a and not b
        paired.append(dict(profile=profile, pairs=150, retry_only_only=a_only,
                           literal_only=b_only, both=both, neither=neither))
    return dict(total_episodes=len(rows), groups=summaries, paired_safe_final=paired,
                interpretation="Seeded simulator fixtures, not LLM or production success rates")


def evaluate(out):
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"output already exists; choose a new directory: {out}")
    out.mkdir(parents=True)
    root = Path(__file__).resolve().parent.parent
    amendment = root/'PROTOCOL_AMENDMENT_002.md'
    sources = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(list((root/'vtc').glob('*.py')) + list((root/'tests').glob('*.py'))
                               + [root/'PROTOCOL.md'] + ([amendment] if amendment.exists() else []))}
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root,
                              capture_output=True, text=True, check=True).stdout.strip()
    write_json(out/'run_manifest.json', dict(source_revision=revision, source_sha256=sources,
               protocol_sha256=sources['PROTOCOL.md'], python=sys.version, platform=platform.platform(),
               protocol_amendment_sha256=sources.get('PROTOCOL_AMENDMENT_002.md'),
               engineering_version='v2-reserved-verification',
               started_at_utc=datetime.now(timezone.utc).isoformat(), expected_episodes=2160))
    inputs, rows = {}, []
    with (out/'cases.csv').open('w', newline='') as cf, \
            (out/'assertions.jsonl').open('w') as af, (out/'traces.jsonl').open('w') as tf:
        writer = csv.DictWriter(cf, fieldnames=FIELDS); writer.writeheader()
        for suite, conditions, seeds in [('main', LEVELS, range(42,67)),
                                         ('stress', PATTERNS, range(42,47))]:
            for task in TASKS:
                for condition in conditions:
                    for seed in seeds:
                        action = fixture(task, seed)
                        tape, flags = main_tape(seed, condition) if suite == 'main' else (stress_tape(condition), None)
                        input_id = f'{suite}/{task}/{condition}/{seed}'
                        input_data = dict(action=asdict(action), tape=[asdict(f) for f in tape],
                                          flags=flags, seed=seed)
                        inputs[input_id] = input_data
                        for profile in ('supported', 'unsupported'):
                            for mode in MODES:
                                case_id = f'{input_id}/{profile}/{mode}'
                                meta = dict(case_id=case_id, input_id=input_id, suite=suite,
                                            task=task, condition=condition, seed=seed, profile=profile, mode=mode)
                                row, assertions, trace = episode(meta, input_data)
                                writer.writerow(row); rows.append(row)
                                af.write(canonical(assertions)+'\n')
                                for event in trace:
                                    tf.write(canonical(dict(case_id=case_id, **event))+'\n')
    if len(rows) != 2160:
        raise AssertionError('wrong matrix size')
    write_json(out/'inputs.json', inputs)
    summary = summarize(rows); write_json(out/'summary.json', summary)
    artifacts = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
    write_json(out/'results_manifest.json', dict(source_revision=revision, sha256=artifacts))
    print(f'Wrote {len(rows)} episodes to {out}')
    for group in summary['groups']:
        if group['condition'] == 'all':
            print(group['suite'], group['profile'], group['mode'], 'n='+str(group['n']),
                  'safe='+str(group['safe_final']['count']),
                  'dup='+str(group['duplicate_episodes']),
                  'false_success='+str(group['false_success_final']['count']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    evaluate(parser.parse_args().out)
