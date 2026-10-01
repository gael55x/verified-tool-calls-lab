"""Render fixed run-002 aggregate graphs from checked, frozen local data."""

import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "evidence/run-002"
SUITES = {"main": 150, "stress": 120}
PROFILES = ("unsupported", "supported")
METHODS = {
    "retry_only": "Retry only",
    "verify_only": "Verify only",
    "paper_literal": "Paper literal",
    "engineering": "Engineering v2",
}
METRICS = (
    ("safe_final", "Safe final completion", "#176c55"),
    ("duplicate_episodes", "Duplicate-effect episodes", "#9c4a20"),
    ("false_success_final", "False success at tick 8", "#70449a"),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_counts():
    result_manifest = json.loads((DATA / "results_manifest.json").read_text())
    for name, expected in result_manifest["sha256"].items():
        assert digest((DATA / name).read_bytes()) == expected, name
    assert json.loads((DATA / "run_manifest.json").read_text())["source_revision"] == result_manifest["source_revision"]
    summary = json.loads((DATA / "summary.json").read_text())
    expected_keys = {(suite, profile, mode) for suite in SUITES for profile in PROFILES for mode in METHODS}
    all_groups = [g for g in summary["groups"] if g["condition"] == "all"]
    assert len(all_groups) == len(expected_keys)
    groups = {
        (g["suite"], g["profile"], g["mode"]): g
        for g in all_groups
    }
    assert set(groups) == expected_keys and summary["total_episodes"] == 2160
    counts = defaultdict(lambda: {"n": 0, "safe_final": 0, "duplicate_episodes": 0, "false_success_final": 0})
    with (DATA / "cases.csv").open(newline="") as file:
        for case in csv.DictReader(file):
            key = (case["suite"], case["profile"], case["mode"])
            assert key in expected_keys
            item = counts[key]
            item["n"] += 1
            item["safe_final"] += int(case["safe_final"])
            item["duplicate_episodes"] += int(case["duplicate_effects"]) > 0
            item["false_success_final"] += int(case["false_success_final"])
    assert sum(item["n"] for item in counts.values()) == 2160
    for key in expected_keys:
        item, group = counts[key], groups[key]
        assert item["n"] == group["n"] == SUITES[key[0]], key
        for metric, _, _ in METRICS:
            published = group[metric] if metric == "duplicate_episodes" else group[metric]["count"]
            assert item[metric] == published, (key, metric)
    return counts, result_manifest["source_revision"]


def graph(suite, counts):
    n = SUITES[suite]
    title = "Main study" if suite == "main" else "Designed stress cases"
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1700" height="885" viewBox="0 0 1700 885" role="img">',
        f"<title>{title}: three measured outcomes by method and API contract</title>",
        f"<desc>Each bar starts at zero and is labeled with its exact count out of {n} synthetic episodes. Two API contracts and four methods are shown for safe final completion, duplicate-effect episodes, and false success at tick 8.</desc>",
        '<rect width="1700" height="885" fill="#ffffff"/>',
        '<g font-family="Arial, Helvetica, sans-serif" fill="#172033">',
        f'<text x="40" y="51" font-size="30" font-weight="bold">{title}: verified tool-call outcomes</text>',
        f'<text x="40" y="87" font-size="19">Scripted synthetic cases · {n} episodes per method and API contract · bars show fraction of episodes</text>',
    ]
    for column, (_, heading, _) in enumerate(METRICS):
        left = 255 + column * 470
        parts.append(f'<text x="{left}" y="130" font-size="20" font-weight="bold">{escape(heading)}</text>')
        for tick in (0, 25, 50, 75, 100):
            x = left + 310 * tick / 100
            parts.append(f'<line x1="{x:g}" y1="179" x2="{x:g}" y2="750" stroke="#dce3ea"/>')
            parts.append(f'<text x="{x:g}" y="169" font-size="15" text-anchor="middle">{tick}%</text>')
    for block, profile in enumerate(PROFILES):
        top = 210 + block * 290
        contract = "API ignores idempotency keys" if profile == "unsupported" else "Strong supported keys: stage receipts + pending reservations"
        parts.append(f'<text x="40" y="{top}" font-size="21" font-weight="bold">{escape(contract)}</text>')
        for row, (mode, label) in enumerate(METHODS.items()):
            y = top + 43 + row * 52
            parts.append(f'<text x="40" y="{y+6}" font-size="18">{escape(label)}</text>')
            for column, (metric, _, color) in enumerate(METRICS):
                left = 255 + column * 470
                count = counts[(suite, profile, mode)][metric]
                width = 310 * count / n
                if count:
                    parts.append(f'<rect x="{left}" y="{y-14}" width="{width:.3f}" height="28" fill="{color}"/>')
                else:
                    parts.append(f'<circle cx="{left}" cy="{y}" r="4" fill="none" stroke="{color}" stroke-width="2"/>')
                parts.append(f'<text x="{left+width+10:.3f}" y="{y+6}" font-size="17" font-weight="bold">{count}/{n}</text>')
    parts += [
        f'<text x="40" y="797" font-size="16">Source: evidence/run-002/cases.csv, checked against summary.json. Count/denominator shown for every bar.</text>',
        '<text x="40" y="825" font-size="16">Main and stress are separate designs. Reused seeds and fixed fixtures are correlated; no inferential CI or population claim.</text>',
        '<text x="40" y="853" font-size="16">Supported keys are a strong modeled contract, not arbitrary APIs. No LLM or production result is claimed.</text>',
        '</g></svg>',
    ]
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="new output directory or one without these generated files")
    out = parser.parse_args().out
    counts, revision = checked_counts()
    out.mkdir(parents=True, exist_ok=True)
    text = io.StringIO()
    writer = csv.writer(text, lineterminator="\n")
    writer.writerow(("suite", "profile", "method", "metric", "numerator", "denominator"))
    for suite in SUITES:
        for profile in PROFILES:
            for mode in METHODS:
                for metric, _, _ in METRICS:
                    writer.writerow((suite, profile, mode, metric, counts[(suite, profile, mode)][metric], SUITES[suite]))
    outputs = {
        "result-graph-data.csv": text.getvalue(),
        "main-results.svg": graph("main", counts),
        "stress-results.svg": graph("stress", counts),
    }
    for name, content in outputs.items():
        with (out / name).open("x") as file:
            file.write(content)
    manifest = {
        "evaluated_source_revision": revision,
        "case_rows_checked": 2160,
        "generator_sha256": digest(Path(__file__).read_bytes()),
        "definitions": {
            "safe_final": "full required state and exactly one append effect at tick 8",
            "duplicate_episodes": "episodes with at least one extra committed append effect by tick 8",
            "false_success_final": "wrapper reported success but safe_final is false at tick 8",
        },
        "input_sha256": {name: digest((DATA / name).read_bytes()) for name in ("cases.csv", "summary.json", "run_manifest.json", "results_manifest.json")},
        "output_sha256": {name: digest(content.encode()) for name, content in outputs.items()},
    }
    with (out / "RESULT_GRAPH_MANIFEST.json").open("x") as file:
        json.dump(manifest, file, indent=2, sort_keys=True)
        file.write("\n")
    print(f"Verified 2,160 raw cases against summary; wrote 48 observations and two SVGs to {out}")


if __name__ == "__main__":
    main()
