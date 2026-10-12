"""Freeze reproducible ECA items with exact Claude Lane B numpy.default_rng(seed) semantics.
Do not expose the scored oracle to the inference runner.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
RULES=(30,90,110,184)
EXCLUDED={41031,41032,41033,41034}
def canonical_json(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(b):
    return hashlib.sha256(b).hexdigest()
def make_item(rule,seed):
    state=np.random.default_rng(seed).integers(0,2,size=8,dtype=np.int64).tolist()
    return {'schema':'cell-akamai.eca.item.v1','item_id':f'ECA-{rule}-{seed}',
            'rule':rule,'seed':seed,'width':8,'initial_state':state,
            'generator':'numpy.default_rng(seed).integers(0,2,size=8,dtype=np.int64)',
            'source_class':'SYNTHETIC_DETERMINISTIC'}
def oracle(it):
    # Used for corpus freeze/checks ONLY, not imported into experiment.py.
    x=it['initial_state']; rule=it['rule']; n=len(x)
    return ''.join(str((rule >> ((x[(i-1)%n]*4)+(x[i]*2)+x[(i+1)%n])) & 1) for i in range(n))
def freeze(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    groups={'calibration':(47000,8),'pilot':(50000,8),'holdout_proposed':(51000,16)}
    used={r:set() for r in RULES};manifest={'schema':'cell-akamai.eca.dataset_manifest.v1',
      'generator_contract':'matches Claude lane_b/harness/items.py numpy default_rng per seed',
      'task':'ECA_NEXT_ROW','rules':RULES,'width':8,
      'split_admission':{'calibration':'TUNING_ONLY','pilot':'PILOT_NONCONFIRMATORY','holdout_proposed':'UNFROZEN_NO_TUNING'},
      'oracle_contract':'periodic Wolfram neighborhood L*4+C*2+R','splits':{},
      'overlap_policy':'No identical (rule,state) pairs across splits; deterministic skipped seeds recorded.'}
    for label,(start,per_rule) in groups.items():
        items=[];skips=[];seed=start
        for rule in RULES:
            count=0
            while count<per_rule:
                if seed in EXCLUDED:raise AssertionError('excluded seed')
                item=make_item(rule,seed)
                key=tuple(item['initial_state'])
                if key in used[rule]:skips.append({'rule':rule,'seed':seed,'duplicate_state':''.join(map(str,key))})
                else:used[rule].add(key);items.append(item);count+=1
                seed+=1
        # items and oracles are distinct files. Only score.py may consume oracle files.
        gold=[{'item_id':it['item_id'],'correct_next_row':oracle(it),'source_class':'SYNTHETIC_DETERMINISTIC'} for it in items]
        for suffix,records in [('items',items),('oracle',gold)]:
            path=root/f'{label}_{suffix}.jsonl';body=''.join(canonical_json(x)+'\n' for x in records).encode('utf-8');path.write_bytes(body)
            manifest['splits'].setdefault(label,{})[f'{suffix}_sha256']=digest(body)
        manifest['splits'][label].update({'n_items':len(items),'initial_seed':start,'next_seed_exclusive':seed,'skipped_duplicate_seeds':skips,'n_rules':len(RULES)})
    (root/'DATASET_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    return manifest
if __name__=='__main__':
    import sys
    print(json.dumps(freeze(sys.argv[1] if len(sys.argv)>1 else 'data'),indent=2))
