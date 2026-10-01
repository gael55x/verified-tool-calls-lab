"""Artifact audit independently rederives state predicates without model helpers.

This is author verification, NOT an independent technical review by another person.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path


def safe(action,state):
    p=action['payload']
    if action['task']=='activate_customer':
        c=state.get('customer',{}); m=state.get('messages',[])
        truth=(c.get('id')==p['customer_id'] and c.get('status')=='ACTIVE'
               and c.get('activated_at') is not None and len(m)==1
               and m[0].get('customer_id')==p['customer_id'])
        return bool(truth),bool(truth),max(0,len(m)-1)
    row=state.get('row',{}); records=state.get('records',[])
    truth=(row.get('invoice_id')==p['invoice_id'] and row.get('amount')==p['amount']
           and any(r.get('invoice_id')==p['invoice_id'] and r.get('amount')==p['amount']
                   and r.get('status')=='RECORDED' for r in records))
    return bool(truth),bool(truth and len(records)==1),max(0,len(records)-1)


def audit(folder):
    folder=Path(folder)
    manifest=json.loads((folder/'results_manifest.json').read_text())
    for name,h in manifest['sha256'].items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==h, name
    rows=list(csv.DictReader((folder/'cases.csv').open()))
    assert len(rows)==2160 and len({r['case_id'] for r in rows})==2160
    counts=Counter(r['suite'] for r in rows)
    assert counts=={'main':1200,'stress':960}, counts
    assertions={a['case_id']:a for a in map(json.loads,(folder/'assertions.jsonl').open())}
    traces=defaultdict(list)
    for e in map(json.loads,(folder/'traces.jsonl').open()): traces[e['case_id']].append(e)
    inputs=json.loads((folder/'inputs.json').read_text())
    paired=defaultdict(set)
    for row in rows:
        cid=row['case_id']; a=assertions[cid]; ev=traces[cid]
        assert [e['seq'] for e in ev]==list(range(len(ev))), cid
        assert ev[-1]['kind']=='evaluator_final' and ev[-1]['pending']==0
        assert ev[-1]['state']==a['final']
        assert next(e['state'] for e in ev if e['kind']=='evaluator_at_return')==a['at_return']
        for suffix,state in [('at_return',a['at_return']),('final',a['final'])]:
            truth,safe_success,dup=safe(a['action'],state)
            assert int(row['truth_'+suffix])==truth, cid
            assert int(row['safe_'+suffix])==safe_success, cid
            assert int(row['false_success_'+suffix])==(int(row['reported_success']) and not safe_success),cid
            assert int(row['false_failure_'+suffix])==(not int(row['reported_success']) and safe_success),cid
        assert int(row['duplicate_effects'])==dup
        dispatch=[e for e in ev if e['kind']=='dispatch']
        assert len(dispatch)==int(row['calls'])<=2
        assert int(row['retries'])==len(dispatch)-1
        assert sum(e['kind']=='read' for e in ev)==int(row['reads'])
        assert sum(e['kind']=='commit_stage' for e in ev)==int(row['writes_final'])
        append_stage=2 if row['task']=='activate_customer' else 1
        append_commits=sum(e['kind']=='commit_stage' and e['stage']==append_stage for e in ev)
        assert max(0,append_commits-1)==dup, cid
        if row['mode'] in ('engineering','paper_literal'):
            assert len({e['key'] for e in dispatch})==1 and dispatch[0]['key'], cid
        if row['mode']=='paper_literal': assert int(row['reads'])<=1
        if row['mode']=='engineering': assert int(row['reads'])<=3
        encoded=json.dumps(inputs[row['input_id']],sort_keys=True,separators=(',',':')).encode()
        assert hashlib.sha256(encoded).hexdigest()==row['input_sha256']
        for index,e in enumerate(dispatch): assert e['fault']==inputs[row['input_id']]['tape'][index]
        paired[row['input_id']].add(row['input_sha256'])
        # Truth transitions only at committed effect events, never reads.
        committed={}
        for e in ev:
            if e['kind']=='commit_stage': committed=e['state']
            if e['kind']=='evaluator_at_return': assert e['state']==committed
            if e['kind']=='evaluator_final': assert e['state']==committed
    assert all(len(s)==1 for s in paired.values())
    # Expected scientific counterexamples must be present; clean control must pass.
    stress=[r for r in rows if r['suite']=='stress']
    clean=[r for r in stress if r['condition']=='clean']
    assert len(clean)==80 and all(int(r['safe_final']) and int(r['reported_success']) for r in clean)
    controls=[r for r in stress if r['condition']=='commit_timeout' and r['mode']=='retry_only']
    assert len(controls)==20 and all(int(r['duplicate_effects'])==1 for r in controls)
    false_ack=[r for r in stress if r['condition']=='false_success' and r['mode']=='paper_literal']
    assert len(false_ack)==20 and all(int(r['false_success_final']) for r in false_ack)
    last_retry=[r for r in stress if r['condition']=='no_effect_timeout' and r['mode']=='paper_literal']
    assert len(last_retry)==20 and all(int(r['false_failure_final']) for r in last_retry)
    # Reaggregate independently and cross-check summary counts.
    summary=json.loads((folder/'summary.json').read_text())
    for g in summary['groups']:
        group=[r for r in rows if r['suite']==g['suite'] and r['profile']==g['profile']
               and r['mode']==g['mode'] and (g['condition']=='all' or r['condition']==g['condition'])]
        assert len(group)==g['n']
        for metric in ('reported_success','truth_final','safe_final','false_success_final','false_failure_final'):
            k=sum(int(r[metric]) for r in group)
            assert k==g[metric]['count'] and round(k/len(group),6)==g[metric]['rate']
        assert sum(int(r['duplicate_effects'])>0 for r in group)==g['duplicate_episodes']
    result=dict(status='PASS',episodes=len(rows),paired_input_families=len(paired),
                checks='hashes, matrix, states, commits, keys, tape pairing, controls, aggregates',
                independent_review=False)
    print(json.dumps(result,sort_keys=True)); return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True)
    audit(p.parse_args().run)
