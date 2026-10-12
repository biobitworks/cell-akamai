"""Independent oracle/scoring. This module must NOT be imported by the live runner.
Independent code path re-derives Wolfram ECA labels rather than trusting answer texts.
"""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
from .experiment import ARMS,canon,sha # utilities only; NO oracle import

def verify_oracle(it,answer):
    bits=it['initial_state'];rule=int(it['rule']);n=len(bits)
    out=[]
    for i in range(n):
        bit_index=4*bits[(i-1)%n]+2*bits[i]+bits[(i+1)%n]
        out.append('1' if (rule & (1<<bit_index)) else '0')
    return ''.join(out)==answer

def score_run(index_path,items_path,oracle_path=None):
    index_path=Path(index_path);out=index_path.parent
    items={v['item_id']:v for v in map(json.loads,Path(items_path).read_text().splitlines())}
    oracle_rows=({v['item_id']:v for v in map(json.loads,Path(oracle_path).read_text().splitlines())}
        if oracle_path else {})
    if len(items)!=len(set(items)):raise ValueError('duplicate task identity')
    for item_id,gold in oracle_rows.items():
        if not verify_oracle(items[item_id],gold['correct_next_row']):raise ValueError('oracle mismatch '+item_id)
    idx=json.loads(index_path.read_text());derived=[];correct_rows=[]
    for ref in idx['results']:
        f=Path(ref['path']);f=f if f.exists() or f.is_absolute() else (out/f)
        data=f.read_bytes();
        if sha(data)!=ref['sha256']:raise ValueError('BLOCK HASH MISMATCH '+str(f))
        r=json.loads(data);allrows=r['records'];counts=0;known=0;errors=0
        for rec in allrows:
            if rec['item_id'] not in items:raise ValueError('unknown item '+rec['item_id'])
            gold=oracle_rows.get(rec['item_id'])
            if gold is None:correct=None
            else:
                truth=gold['correct_next_row'];correct=rec['final_answer']==truth and rec['status']=='OBSERVED'
                known+=1;counts+=int(bool(correct))
            errors+=int(rec['status']=='FAILED')
            correct_rows.append({'concurrency':r['concurrency'],'repeat':r['repeat'],
                'arm':r['arm'],'item_id':rec['item_id'],'correct':correct,
                'n_calls':rec['n_calls'],'status':rec['status'],'reported_completion_tokens':rec['completion_tokens_total']})
        derived.append({'concurrency':r['concurrency'],'repeat':r['repeat'],'arm':r['arm'],
          'n_items':len(allrows),'n_scored':known,'exact_match_accuracy':counts/known if known else None,
          'correct_items_per_s':counts/r['duration_s'] if known else None,'failures':errors,
          'tokens_per_s':r['output_tokens_per_s'],'items_per_s':r['items_per_s'],
          'tokens_per_correct_item':r['completion_tokens_total']/counts if counts and r['completion_tokens_total'] is not None else None,
          'tokens_per_s2_inter_window':None,'tokens_per_s2_state':'NOT_COMPUTED_UNTIL_REPEATED_MATCHED_WINDOWS',
          'kv_peak_fraction':r['kv_peak_fraction'],'waiting_peak':r['waiting_requests_peak'],
          'source_class':r['source_class'],'claim_ceiling':'NONCONFIRMATORY_PROXY_ECA_ONLY'})
    # Within-matched-(arm,concurrency) consecutive repeats only; different concurrency
    # levels are configurations, NOT measurements of token-level acceleration.
    for arm in ARMS:
        for cc in sorted(set(x['concurrency'] for x in derived)):
            grp=sorted((x for x in derived if x['arm']==arm and x['concurrency']==cc),key=lambda z:z['repeat'])
            for x0,x1 in zip(grp,grp[1:]):
                if x0['tokens_per_s'] is None or x1['tokens_per_s'] is None:continue
                x1['tokens_per_s2_state']='NOT_COMPUTED_NO_STABLE_MIDPOINT_TIMES'
    (out/'SCORED_SUMMARY.json').write_bytes(canon({'schema':'cell-akamai.concurrency_scores.v1',
       'status':'DERIVED_EVIDENCE' if oracle_rows else 'NOT_SCORED_ORACLE_MISSING',
       'rows':derived,'independent_oracle':bool(oracle_rows),'mmr':'NOT_COMMITTED','signed':False})+b'\n')
    (out/'SCORED_ITEMS.jsonl').write_bytes(b''.join(canon(r)+b'\n' for r in correct_rows))
    return derived
