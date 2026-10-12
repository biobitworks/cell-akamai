import sys,hashlib,json,pytest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import six_dataset_fco_fcg as sd

def test_six_files_and_source():
 x=sd.validate();assert x['status']=='PASS' and x['raw_source_sha256']==sd.ECA_ORIGINAL_SHA
 assert all(k['row_count']==32 and k['reconstruction_exact'] for k in x['summary'].values())
 assert len(x['files'])==9

def test_oracle_independent():
 assert sd.oracle({'initial_state':[0,0,0,1,0,0,0,0],'rule':90})=='00101000'

def test_safe_input_prompts():
 for role,pairs in sd.compare_inputs():
  assert len(pairs)==32
  assert all(raw['prompt']==fc['payload']['prompt'] for raw,fc in pairs)
  assert all('reference_answer' not in raw for raw,fc in pairs)

def test_content_occurrence_and_edges():
 for role in sd.LABELS:
  obj=sd.records(sd.FCO/f'{role}.jsonl')
  edges=sd.records(sd.FCG/f'{role}.jsonl')
  assert len(set(z['occurrence_id'] for z in obj))==32
  assert len(edges)==(32 if role=='genesis' else 64)

def test_local_root_recomputes():
 a=sd.validate()['local_file_merkle'];b=sd.validate()['local_file_merkle']
 assert a==b and a['size']==9
 assert a['root_sha256']==a['levels'][-1][0]

def test_detect_tamper_without_mutating_source():
 a=sd.records(sd.ORIGINAL/'genesis.jsonl')[0]
 b={**a,'prompt':a['prompt']+' TAMPERED'}
 assert sd.fid('genesis',0,a)!=sd.fid('genesis',0,b)

def test_verify_zip_input_source():
 import cell_akamai_handoff as cak
 assert cak.ECA_SHA==sd.ECA_ORIGINAL_SHA
