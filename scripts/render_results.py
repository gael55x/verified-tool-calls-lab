"""Generate result tables and an original SVG from verified retained outputs.

Stdlib only. This reporting script is not used by the measurement code.
"""
from pathlib import Path
import json
from html import escape

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'evidence/run-002'
summary=json.loads((DATA/'summary.json').read_text())
groups={ (g['suite'],g['profile'],g['mode']):g for g in summary['groups'] if g['condition']=='all'}
modes=('retry_only','verify_only','paper_literal','engineering')
profiles=('unsupported','supported')
labels={'retry_only':'Retry only','verify_only':'Verify only','paper_literal':'Paper literal','engineering':'Engineering'}

lines=['# Measured local results','',
       'Source revision: `'+json.loads((DATA/'run_manifest.json').read_text())['source_revision']+'`. Source/protocol/amendment hashes and runtime are in `evidence/run-002/run_manifest.json`; exact artifact hashes are in `results_manifest.json`.', '',
       '**2,160 episodes completed, no excluded or failed harness cells.** Main: 1,200. Designed stress: 960. These are CPU simulator outcomes, not reproduced Gemini/LangGraph results. The 26-test log, author artifact audit and byte-identical replay are retained in `evidence/`. Five scientific files also match preserved run-001; no aggregate improvement is claimed. The added reviewer probe demonstrates withholding the last-poll retry. Original independent review passed; correction re-review is pending.','',
       'Safe final completion means full required state and exactly one append effect at tick 8. False success/failure uses that same safety definition and the wrapper return. Duplicate episodes count committed append effects beyond one, not repeated API calls. Counts are out of all episodes, not out of reported successes. Invoice ordinary truth success is separate in raw output.','']
for suite,n in [('main',150),('stress',120)]:
 lines += [f'## {suite.title()} aggregates', '',
           '| Server profile | Method | N | Safe final | Reported success | Duplicate episodes | False success final | False failure final |',
           '|---|---|---:|---:|---:|---:|---:|---:|']
 for profile in profiles:
  for mode in modes:
   g=groups[(suite,profile,mode)]
   vals=(g['safe_final']['count'],g['reported_success']['count'],g['duplicate_episodes'],g['false_success_final']['count'],g['false_failure_final']['count'])
   lines.append(f'| {profile} | {mode} | {g["n"]} | '+' | '.join(str(v) for v in vals)+' |')
 lines.append('')
lines += ['The supported profile affects keyed methods only. Baselines omit keys, so their outcomes are identical across profiles. Supported means durable stage receipts and pending reservations in the simulator, not arbitrary server support.', '',
          '## Main safe-final intervals and paired outcomes', '',
          '| Profile | Method | Safe final proportion | Wilson 95% descriptive interval |',
          '|---|---|---:|---:|']
for profile in profiles:
 for mode in modes:
  g=groups[('main',profile,mode)]; lo,hi=g['safe_final']['wilson95_descriptive']
  lines.append(f'| {profile} | {mode} | {g["safe_final"]["count"]}/{g["n"]} | {lo:.6f} to {hi:.6f} |')
lines += ['', 'Each 150-row aggregate reuses 25 seed streams across two tasks and three levels. Wilson bounds are descriptive and do not assert independent 95% population coverage. Environment assumptions were selected here; no population/generalization or significance claim follows.', '',
          '| Profile | Paired fixtures | Both safe | Literal only safe | Retry only safe | Neither safe |',
          '|---|---:|---:|---:|---:|---:|---:|']
for p in summary['paired_safe_final']:
 lines.append(f'| {p["profile"]} | {p["pairs"]} | {p["both"]} | {p["literal_only"]} | {p["retry_only_only"]} | {p["neither"]} |')
lines += ['', 'Per-level/per-task rows and input tapes remain available in the CSV and summary JSON. Stress percentages are not incident-rate estimates; the equal-weight schedules were designed to reveal failure boundaries.', '',
          '## Calls, reads, writes and virtual delay (main totals)', '',
          '| Profile | Method | Calls | Verifier reads | Committed stage writes | Return latency ticks, sum |',
          '|---|---|---:|---:|---:|---:|']
for profile in profiles:
 for mode in modes:
  g=groups[('main',profile,mode)]
  lines.append(f'| {profile} | {mode} | {g["calls_sum"]} | {g["reads_sum"]} | {g["writes_final_sum"]} | {g["latency_ticks_sum"]} |')
lines += ['', 'Ticks are virtual simulator time, not seconds or a throughput/overhead benchmark. Stage writes count actual applied stage transitions; repeated upserts count as writes but are not duplicate append effects.', '',
          '## Boundary findings', '',
          'Literal mode can report success without reading state, accept an incomplete displayed predicate, and return failure after a clean retry. Under supported keys, it has no duplicates here but still 16 false-success and 22 false-failure episodes out of 150 main fixtures. Zero duplicates does not mean correct completion reporting.', '',
          'With unsupported keys, verify_only has 130 safe final episodes versus engineering\'s 117 out of 150; engineering has 28 duplicate episodes versus literal\'s 20. More complete verification authorizes repair attempts that can create additional records when the API cannot dedupe partial/late effects. These outcomes are retained rather than selecting a universally winning policy.', '',
          'The delayed-commit stress case lets engineering verify one correct record and return success before an earlier request later creates a second. The literal one-iteration case can fail even though its retry completed. See `docs/CLAIM_EVIDENCE.md` for exact case IDs and `article/figures/main-safe-completion.svg` for the original data figure.']
(ROOT/'docs/RESULTS.md').write_text('\n'.join(lines)+'\n')

svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="760" viewBox="0 0 1000 760">',
     '<rect width="1000" height="760" fill="#ffffff"/>',
     '<g font-family="Arial, sans-serif" fill="#172033">',
     '<text x="36" y="42" font-size="25" font-weight="bold">Safe completion depends on the server contract</text>',
     '<text x="36" y="70" font-size="16">Local scripted main fixtures; safe final completions out of 150 per row</text>']
start,end=250,820
for j,profile in enumerate(profiles):
 top=125+j*275
 title='API ignores keys' if profile=='unsupported' else 'Strong supported keys: per-stage receipts + pending reservations'
 svg.append(f'<text x="36" y="{top}" font-size="18" font-weight="bold">{escape(title)}</text>')
 for tick in (0,30,60,90,120,150):
  x=start+(end-start)*tick/150
  svg.append(f'<line x1="{x}" x2="{x}" y1="{top+22}" y2="{top+213}" stroke="#e3e8ef"/>')
  svg.append(f'<text x="{x}" y="{top+235}" font-size="12" text-anchor="middle">{tick}</text>')
 for i,mode in enumerate(modes):
  g=groups[('main',profile,mode)]; y=top+47+i*48
  k=g['safe_final']['count']; width=(end-start)*k/150
  color='#285e8d' if mode!='engineering' else '#197667'
  svg.append(f'<text x="36" y="{y+5}" font-size="16">{labels[mode]}</text>')
  svg.append(f'<rect x="{start}" y="{y-14}" width="{width}" height="28" fill="{color}"/>')
  svg.append(f'<text x="{start+width+10}" y="{y+5}" font-size="15">{k}/150</text>')
svg += ['<text x="36" y="690" font-size="14">Data: evidence/run-002/summary.json. Designed simulator assumptions; no LLM or production claims.</text>',
        '<text x="36" y="716" font-size="14">Original figure. Inspired by Mansoor, Phadke &amp; Rana, arXiv:2608.02645v1; paper CC BY 4.0.</text>',
        '</g></svg>']
(ROOT/'article/figures/main-safe-completion.svg').write_text('\n'.join(svg)+'\n')
print('Generated docs/RESULTS.md and original SVG from retained summary')
