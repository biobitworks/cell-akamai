"""Non-deploying candidate: choose a proxy policy only using CALIBRATION evidence.
This is NOT model training and NOT a production Vita DAISY admission.
"""
from pathlib import Path
import hashlib,json

def propose(calibration_score_json,baseline_accuracy_floor=0.0):
    p=Path(calibration_score_json);e=json.loads(p.read_text())
    if e.get('status')!='DERIVED_EVIDENCE':raise ValueError('No scored calibration evidence')
    if 'calibration' not in str(p).lower():raise ValueError('REFUSE: path must identify calibration; not pilot/holdout')
    rows=[r for r in e['rows'] if r['exact_match_accuracy'] is not None and r['failures']==0]
    options=[r for r in rows if r['arm'] in ('B1_GENESIS','B2_GENESIS_DAISY','B3_RANDOM_CONTROL')
             and r['exact_match_accuracy']>=baseline_accuracy_floor]
    ranked=sorted(options,key=lambda z:(-z['correct_items_per_s'],-z['exact_match_accuracy'],z['arm']))
    candidate=ranked[0] if ranked else None
    return {'schema':'cell-akamai.policy_candidate.v1','state':'PROPOSED_NOT_ADMITTED',
      'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
      'selected_proxy_arm':candidate['arm'] if candidate else None,
      'freeze_status':'NOT_FROZEN','native_genesis':'NOT_TESTED','native_daisy_training':'NOT_TESTED',
      'evidence':'calibration proxy selection only; rerun matched controls before any claims',
      'mmr':'NOT_COMMITTED','signature':'NOT_SIGNED'}
