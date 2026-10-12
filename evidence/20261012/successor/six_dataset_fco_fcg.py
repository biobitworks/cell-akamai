"""Successor six-dataset representation experiment. Fully local construction, never pretrained model output."""
from __future__ import annotations
import hashlib,json,math,statistics,time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'data'
ORIGINAL=BASE/'original';FCO=BASE/'fco';FCG=BASE/'fcg'
LABELS=('genesis','vita_daisy','evaluator')
ECA_ORIGINAL_SHA='69ced0ca1cf77a00446e2b3db03564eb487b2f2b15e68c34590ee8e96b07c274'


def encode(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def sh(b):return hashlib.sha256(b).hexdigest()
def records(path):
 return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def lines(rows): return b''.join(encode(r)+b'\n' for r in rows)
def write_bytes(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def oracle(item):
 x=item['initial_state'];r=item['rule'];sz=len(x)
 return ''.join(str((r>>((x[(i-1)%sz]<<2)|(x[i]<<1)|x[(i+1)%sz]))&1) for i in range(sz))
def prompt(item):
 return (f"Elementary cellular automaton, Wolfram rule {item['rule']}, width 8, periodic (wrap-around) boundary. "
         "Neighborhood (left,center,right) as a 3-bit number L*4+C*2+R; new cell = bit (that number) of the rule number. "
         f"Current state (index 0..7): {''.join(map(str,item['initial_state']))}. Give the state after ONE step. "
         "End with ANSWER: <8 bits> or ANSWER: ABSTAIN.")
def raw_rows():
 items=records(BASE/'eca_pilot_inputs_v1.jsonl')
 if sh((BASE/'eca_pilot_inputs_v1.jsonl').read_bytes())!=ECA_ORIGINAL_SHA or len(items)!=32:
  raise ValueError('Frozen original ECA source fails identity or coverage')
 gen=[];daisy=[];evals=[]
 for item in items:
  id=item['item_id'];q=prompt(item)
  gen.append({'item_id':id,'rule':item['rule'],'initial_state':item['initial_state'],'source_eca_sha256':ECA_ORIGINAL_SHA,
              'prompt':q,'model_answer':None,'execution_state':'NOT_TESTED','kind':'GENESIS_POLICY_INPUT_FIXTURE_NOT_ACTUAL_GENESIS_MODEL'})
  cand=''.join(map(str,item['initial_state']))  # DOES NOT use evaluator truth or model output
  daisy.append({'item_id':id,'genesis_item_id':id,'rule':item['rule'],'candidate_answer':cand,
                'candidate_origin':'DETERMINISTIC_PLACEHOLDER_NOT_MODEL_OUTPUT','prompt':q+' A candidate is '+cand+
                '. Check each neighborhood independently and output the corrected row.','execution_state':'NOT_TESTED',
                'kind':'VITA_DAISY_CHALLENGE_INPUT_FIXTURE_NOT_ACTUAL_DAISY_TRACE'})
  evals.append({'item_id':id,'reference_answer':oracle(item),'rule':item['rule'],'source_eca_sha256':ECA_ORIGINAL_SHA,
                'evaluation_access':'EVALUATOR_ONLY_DO_NOT_SEND_TO_MODEL','kind':'DETERMINISTIC_ECA_ORACLE_NOT_BIOLOGICAL_GROUND_TRUTH',
                'execution_state':'EXECUTED_LOCALLY_DETERMINISTIC_COMPUTATION'})
 return {'genesis':gen,'vita_daisy':daisy,'evaluator':evals}
def fid(name,i,row):
 content='sha256:'+sh(encode(row))
 occurrence='fcoocc:'+sh(encode({'source_role':name,'ordinal':i,'source_content_id':content,'construction':'CAKM_FCO_FCG_PROJECTION_V1'}))
 return content,occurrence

def build(replace=False):
 originals=raw_rows();result={};gen_ids={r['item_id']:fid('genesis',i,r)[1] for i,r in enumerate(originals['genesis'])}
 for name in LABELS:
  raw=originals[name];src=ORIGINAL/f'{name}.jsonl';co=FCO/f'{name}.jsonl';ed=FCG/f'{name}.jsonl'
  objects=[];edges=[]
  for i,r in enumerate(raw):
   id,occ=fid(name,i,r)
   objects.append({'schema':'CAKM_FCO_PROJECTION_V1','object_type':'DatasetRow','role':name,'row_ordinal':i,
                   'content_id':id,'occurrence_id':occ,'source_record_sha256':sh(encode(r)),'payload':r,
                   'claim_ceiling':'DETERMINISTIC_TRANSFORM_ONLY_NOT_CANONICAL_PROJECT_ADMISSION'})
   edges.append({'schema':'CAKM_FCG_EDGE_V1','relation':'projects_source_row','from_occurrence':occ,
                 'to_source_content':id,'source_role':name,'row_ordinal':i})
   if name!='genesis':
    edges.append({'schema':'CAKM_FCG_EDGE_V1','relation':'linked_by_item_id_not_causality',
                  'from_occurrence':occ,'to_occurrence':gen_ids[r['item_id']],
                  'item_id':r['item_id'],'source_role':name})
  files={src:lines(raw),co:lines(objects),ed:lines(edges)}
  for p,contents in files.items():
   if p.exists() and not replace and p.read_bytes()!=contents: raise ValueError(f'Existing dataset mutated: {p}')
   write_bytes(p,contents)
  result[name]={'row_count':len(raw),'raw_sha256':sh(files[src]),'fco_sha256':sh(files[co]),'fcg_sha256':sh(files[ed]),
                'raw_bytes':len(files[src]),'fco_bytes':len(files[co]),'fcg_bytes':len(files[ed]),
                'reconstruction_exact':all(o['payload']==raw[i] and o['source_record_sha256']==sh(encode(raw[i])) for i,o in enumerate(objects))}
 return result

def merkle(files):
 # Separate local file Merkle tree, NOT a project MMR, signed witness, or canonical science commitment.
 leaves=[]
 for rel in sorted(files):
  content_hash=bytes.fromhex(files[rel])
  leaf=hashlib.sha256(b'\x00'+rel.encode()+b'\x00'+content_hash).digest()
  leaves.append({'path':rel,'sha256':files[rel],'leaf_sha256':leaf.hex()})
 level=[bytes.fromhex(e['leaf_sha256']) for e in leaves]
 if not level:raise ValueError('empty tree')
 heights=[[z.hex() for z in level]]
 while len(level)>1:
  level=[hashlib.sha256(b'\x01'+level[i]+level[min(i+1,len(level)-1)]).digest() for i in range(0,len(level),2)]
  heights.append([z.hex() for z in level])
 return {'schema':'CAKM_LOCAL_SIX_FILE_MERKLE_V1','construction':'paths_sorted_utf8; SHA256(00 || path_utf8 || 00 || file_SHA256_bytes) leaves; SHA256(01 || left || right) internal; odd duplicates last; no bagged MMR peaks',
         'root_sha256':level[0].hex(),'size':len(leaves),'leaves':leaves,'levels':heights,'state':'LOCAL_VERIFIED_CONSTRUCTION_NOT_PROJECT_MMR'}

def validate():
 summary=build(replace=False)
 source=BASE/'eca_pilot_inputs_v1.jsonl'
 files={str(p.relative_to(ROOT)):sh(p.read_bytes()) for cat in (ORIGINAL,FCO,FCG) for p in cat.glob('*.jsonl')}
 assert len(files)==9
 for name in LABELS:
  raw=records(ORIGINAL/f'{name}.jsonl');objects=records(FCO/f'{name}.jsonl');edges=records(FCG/f'{name}.jsonl')
  assert len(raw)==len(objects)==32
  byid={o['occurrence_id'] for o in objects}
  for i,(r,o) in enumerate(zip(raw,objects)):
   content_id,occ=fid(name,i,r)
   assert o['content_id']==content_id and o['occurrence_id']==occ and o['payload']==r
   assert any(e.get('from_occurrence')==occ and e['relation']=='projects_source_row' for e in edges)
  assert len(edges)==32 if name=='genesis' else len(edges)==64
 assert all(not any(k in obj for k in ['reference_answer','truth','label']) for row in records(ORIGINAL/'genesis.jsonl')+records(ORIGINAL/'vita_daisy.jsonl') for obj in [row])
 tree=merkle(files)
 report={'status':'PASS','summary':summary,'raw_source_sha256':sh(source.read_bytes()),'files':files,
         'local_file_merkle':tree,'project_mmr':'NOT_COMPUTED','signature':'NOT_SIGNED',
         'actual_genesis_execution':'NOT_TESTED','actual_vita_daisy_execution':'NOT_TESTED',
         'recovery_of_historical_before_transform':'NOT_VERIFIED',
         'evaluator':'EXECUTED_LOCALLY_DETERMINISTIC_ORACLE_NOT_GPU',
         'transform':'EXECUTED_LOCAL','claim_ceiling':'INPUT_FIXTURES_AND_DETERMINISTIC_CUSTODY_TRANSFORM_ONLY'}
 return report

def compare_inputs():
 """Returns paired matching prompt bytes by raw source versus FCO resolve, forbids evaluator input."""
 for name in ('genesis','vita_daisy'):
  raw=records(ORIGINAL/f'{name}.jsonl');obj=records(FCO/f'{name}.jsonl')
  for x,y in zip(raw,obj):
   assert encode(x)==encode(y['payload'])
   assert x['prompt']==y['payload']['prompt']
  yield name,list(zip(raw,obj))

def run_live(n_items=8,max_tokens=96):
 """Paired GPU inference with same prompt exactly, presentation isolated from evaluator until scoring."""
 if n_items<1 or n_items>32: raise ValueError('max 32 items')
 import cell_akamai_handoff as cak
 env=cak.preflight();run=cak.new_run('M09_SIX_DATASET_COMPARE');rows=[]
 for name,pairs in compare_inputs():
  for i,(raw,fco) in enumerate(pairs[:n_items]):
   # Interleave path order by item index to reduce monotone warmup confounding.
   for path in (('raw','fco') if i%2==0 else ('fco','raw')):
    src=raw if path=='raw' else fco['payload']
    text=src['prompt']
    tic=time.perf_counter_ns()
    output=cak.infer(env,text,max_tokens=max_tokens)
    retrieval_ms=(time.perf_counter_ns()-tic)/1e6-output['wall_s']*1000
    rows.append({'dataset':name,'path':path,'item_id':raw['item_id'],'prompt_sha256':sh(text.encode()),
                 'completion_tokens':output.get('completion_tokens'),'prompt_tokens':output.get('prompt_tokens'),
                 'wall_s':output['wall_s'],'ok':output['ok'],'answer':cak.parse_answer(output.get('text','')),
                 'model_output_sha256':output.get('output_sha256'),'retrieval_overhead_ms_approx':max(0,retrieval_ms),
                 'note':'IDENTICAL_PROMPT_TEXT; DIFFERENCE_IS_LOCAL_RETRIEVAL_PATH_AND_STOCHASTIC_EXECUTION'})
 write_bytes(run/'paired_outputs.jsonl',lines(rows))
 manifest={'schema':'CAKM_SIX_DATASET_LIVE_PILOT_V1','model':env['served_model'],'deployment':env['deployment'],
           'n_items':n_items,'rows_sha256':sh((run/'paired_outputs.jsonl').read_bytes()),
           'evaluator_oracle_used_before_answer_commit':False,'status':'RAW_ANSWERS_COMMITTED_UNSCORED',
           'no_training_claim':True,'source_dataset_local_root':validate()['local_file_merkle']['root_sha256']}
 (run/'COMMIT.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
 return run

def score_live(run):
 run=Path(run);commit=json.loads((run/'COMMIT.json').read_text());rows=records(run/'paired_outputs.jsonl')
 if sh((run/'paired_outputs.jsonl').read_bytes())!=commit['rows_sha256']:raise ValueError('Answer digest mismatch')
 truth={r['item_id']:r['reference_answer'] for r in records(ORIGINAL/'evaluator.jsonl')}
 n=commit['n_items'];report=[]
 for name in ('genesis','vita_daisy'):
  for path in ('raw','fco'):
   hits=[r for r in rows if r['dataset']==name and r['path']==path]
   if len(hits)!=n or len({h['item_id'] for h in hits})!=n:raise ValueError('Missing duplicate or unmatched item×representation')
   successes=sum(r['ok'] and r['answer']==truth[r['item_id']] for r in hits)
   toks=[r['completion_tokens'] for r in hits]
   report.append({'dataset':name,'representation':path,'n':n,'correct':successes,'exact_accuracy':successes/n,
                  'completion_tokens_total':sum(toks) if all(type(t)==int for t in toks) else None,
                  'wall_s_total':sum(r['wall_s'] for r in hits),
                  'status':'OBSERVED_PILOT_NOT_CONFIRMATORY'})
 res={'state':'EXECUTED_INDEPENDENT_SCORER','paired_n_per_dataset':n,'metrics':report,
      'no_causal_performance_improvement_claim':True,'raw_answer_sha256':commit['rows_sha256']}
 (run/'SCORE.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
 return res
