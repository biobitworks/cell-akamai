"""Akamai workshop Modules 8/9 companion. No external model calls on import.
Source predecessors: akamai-developers/akamai-workshop-ai-inference @454b43269216c1f92dd8d7e2711649e38cb888cb,
Claude cell-akamai PR #5 @73001e73eeada4aee4f3b32fa4a0671cca255601.
Local authoring tests are synthetic; only operator-run Jupyter creates inference observations.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import hashlib, json, math, os, random, re, statistics, subprocess, threading, time, uuid, zipfile
import requests

UPSTREAM_SHA='454b43269216c1f92dd8d7e2711649e38cb888cb'
CLAUDE_SHA='73001e73eeada4aee4f3b32fa4a0671cca255601'
ECA_SHA='69ced0ca1cf77a00446e2b3db03564eb487b2f2b15e68c34590ee8e96b07c274'
ARMS=('B0_FIXED','B1_GENESIS','B2_GENESIS_DAISY','B3_RANDOM_CONTROL')
POLICY_ID='GENESIS_POLICY_PROXY_V0_NOT_THE_RECOVERED_GENESIS_TRANSFORMER'
SYS="You simulate elementary cellular automata exactly. End with one final line ANSWER: <8 bits> (or ANSWER: ABSTAIN). Be concise."
ROOT=Path(__file__).resolve().parent
RUNS=ROOT/'runs'
RUNS.mkdir(exist_ok=True)

def now():return datetime.now(timezone.utc).isoformat()
def digest_bytes(b): return hashlib.sha256(b).hexdigest()
def digest_obj(x):return digest_bytes(json.dumps(x,sort_keys=True,separators=(',',':')).encode())
def write_json(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,sort_keys=True,indent=2,default=str)+'\n')
def read_json(p):return json.loads(Path(p).read_text())
def new_run(name):
 dest=RUNS/f'{name}_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}_{uuid.uuid4().hex[:7]}'
 dest.mkdir(parents=True,exist_ok=False);dest.chmod(0o700);return dest

def safe_env():
 host=os.getenv('VLLM_HOST','http://vllm:8000/v1').rstrip('/')
 if not host.endswith('/v1'):raise ValueError('VLLM_HOST must end with /v1')
 url=urlsplit(host)
 if url.scheme not in ('http','https') or not url.hostname:raise ValueError('Invalid VLLM_HOST')
 ns=os.getenv('NAMESPACE','')
 if not ns:
  q=kubectl(['config','view','--minify','-o','jsonpath={..namespace}'],check=False)
  ns=q.stdout.strip() or 'default'
 return dict(base_url=host,metrics_url=host[:-3]+'/metrics',namespace=ns,model_env=os.getenv('MODEL_NAME','UNKNOWN'),workshop_sha=UPSTREAM_SHA)

def kubectl(args,check=True,input_data=None,timeout=35):
 p=subprocess.run(['kubectl',*args],input=input_data,text=True,capture_output=True,timeout=timeout)
 if check and p.returncode!=0:raise RuntimeError('kubectl '+ ' '.join(args[:5])+' failed: '+p.stderr[-1100:])
 return p

def deployment(ns):
 d=json.loads(kubectl(['-n',ns,'get','deployment','vllm','-o','json']).stdout)
 co=[c for c in d['spec']['template']['spec']['containers'] if c.get('name')=='vllm']
 if len(co)!=1:raise ValueError('Cannot identify unique vllm container')
 c=co[0];args=c.get('args',[])
 return dict(namespace=ns,resource_version=d['metadata'].get('resourceVersion'),generation=d['metadata'].get('generation'),
             image=c.get('image'),args=args,model_flag=next((a.split('=',1)[1] for a in args if a.startswith('--model=')),None),
             resources=c.get('resources',{}),image_status='DECLARED_NOT_DIGEST_ATTESTED')

def served_model(env):
 key=os.getenv('VLLM_API_KEY','not-needed')
 r=requests.get(env['base_url']+'/models',headers={'Authorization':f'Bearer {key}'},timeout=12);r.raise_for_status()
 names=[x['id'] for x in r.json().get('data',[])]
 if len(names)!=1:raise ValueError(f'Expected one served model, got {names}')
 return names[0]

def preflight(out=None):
 e=safe_env();m=served_model(e);d=deployment(e['namespace'])
 if d['model_flag']!=m:raise ValueError(f'Deployment --model {d["model_flag"]} != live model {m}')
 e.update(served_model=m,deployment=d,checked_at=now(),served_precision='UNKNOWN_UNLESS_MODEL_AND_RUNTIME_VERIFIED')
 if out:write_json(Path(out)/'preflight.json',e)
 return e

def metric_parse(data):
 # Sum each labeled counter/gauge across series, excluding histograms not needed here.
 out={}
 for ln in data.splitlines():
  if not ln or ln.startswith('#'):continue
  m=re.match(r'([^\s{]+)(?:\{[^}]*\})?\s+([-+\deE.]+)(?:\s+\S+)?$',ln.strip())
  if not m:continue
  try:v=float(m.group(2))
  except ValueError:continue
  if math.isfinite(v):out[m.group(1)]=out.get(m.group(1),0)+v
 return out

def metric_probe(env,out,label):
 p=Path(out)/f'metrics_{label}.prom'
 try:
  r=requests.get(env['metrics_url'],timeout=7);r.raise_for_status();p.write_bytes(r.content)
  return dict(available=True,sha256=digest_bytes(r.content),path=p.name,summary=metric_parse(r.text))
 except Exception as exc:
  return dict(available=False,error=type(exc).__name__,sha256=None,summary={})

def metric_summary(m):
 keys=['vllm:generation_tokens_total','vllm:prompt_tokens_total','vllm:num_requests_running','vllm:num_requests_waiting',
       'vllm:kv_cache_usage_perc','vllm:gpu_cache_usage_perc','vllm:num_preemptions_total',
       'vllm:time_to_first_token_seconds_sum','vllm:time_to_first_token_seconds_count',
       'vllm:time_per_output_token_seconds_sum','vllm:time_per_output_token_seconds_count']
 return {k:m.get(k) for k in keys}

def infer(env,prompt,max_tokens=96):
 t0=time.perf_counter();model=env['served_model']; key=os.getenv('VLLM_API_KEY','not-needed')
 body={'model':model,'messages':[{'role':'system','content':'Answer briefly and accurately.'},{'role':'user','content':prompt}],
       'temperature':0,'max_tokens':max_tokens}
 if 'qwen3' in model.lower():body['chat_template_kwargs']={'enable_thinking':False}
 try:
  r=requests.post(env['base_url']+'/chat/completions',headers={'Authorization':f'Bearer {key}'},json=body,timeout=150)
  elapsed=time.perf_counter()-t0;r.raise_for_status();j=r.json();choice=j['choices'][0]
  usage=j.get('usage') or {}
  tok=usage.get('completion_tokens');inp=usage.get('prompt_tokens');content=choice.get('message',{}).get('content') or ''
  return dict(ok=True,prompt_sha256=digest_bytes(prompt.encode()),text=content,output_sha256=digest_bytes(content.encode()),
              completion_tokens=tok if type(tok)==int else None,prompt_tokens=inp if type(inp)==int else None,
              wall_s=elapsed,finish_reason=choice.get('finish_reason'),ttfc_ms=None,ttfc_status='NOT_MEASURED_NONSTREAM')
 except Exception as exc:
  return dict(ok=False,prompt_sha256=digest_bytes(prompt.encode()),completion_tokens=None,prompt_tokens=None,
              wall_s=time.perf_counter()-t0,error=type(exc).__name__+': '+str(exc)[:200],text='',ttfc_ms=None)

def sample_metrics(env,stop,samples):
 while not stop.is_set():
  try:
   s=requests.get(env['metrics_url'],timeout=3);s.raise_for_status()
   samples.append(dict(t_utc=now(),**metric_summary(metric_parse(s.text))))
  except Exception as e:samples.append(dict(t_utc=now(),error=type(e).__name__))
  stop.wait(.3)

def make_load_prompts(count,max_chars=800):
 filler='Cell-Akamai dedicated GPU inference: measure batching, queueing and KV cache under reproducible workloads. '
 return [f'Cell-Akamai fixed benchmark request {i:03d}. '+(filler*12)[:max_chars]+'\nSummarize the technical point in one short sentence.' for i in range(count)]

def load_epoch(env,label,levels=(1,4,8,16),per_level=16,max_tokens=96,config=None):
 if per_level<2 or per_level>32 or any(c>16 or c<1 for c in levels):raise ValueError('Safety cap: per_level 2..32, concurrency <=16')
 out=new_run('M08_'+label)
 config=config or deployment(env['namespace'])
 write_json(out/'identity.json',dict(env=env,config=config,phase=label,measurands={'batch_tok_s':'sum verified completion tokens / batch wall_s',
                 'request_tok_s':'completion tokens / request wall_s','ttfc':'NOT_MEASURED',
                 'upstream_loadtest_token_counter':'CHUNK_COUNT_NOT_TOKEN_COUNT'},timestamp=now(),status='IN_PROGRESS'))
 cells=[]
 for c in levels:
  cell=out/f'c{c:02d}';cell.mkdir()
  before=metric_probe(env,cell,'before')
  samples=[];stop=threading.Event();sampler=threading.Thread(target=sample_metrics,args=(env,stop,samples),daemon=True)
  prompts=make_load_prompts(per_level)
  sampler.start();start=time.perf_counter()
  with ThreadPoolExecutor(max_workers=c) as ex:rows=list(ex.map(lambda p:infer(env,p,max_tokens),prompts))
  elapsed=time.perf_counter()-start;stop.set();sampler.join(timeout=5)
  after=metric_probe(env,cell,'after')
  for i,r in enumerate(rows):r['request_index']=i
  (cell/'request_rows.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
  (cell/'metric_samples.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in samples))
  write_json(cell/'metric_receipts.json',{'before':before,'after':after})
  known=all(x['ok'] and x['completion_tokens'] is not None for x in rows)
  nt=sum(x['completion_tokens'] for x in rows) if known else None
  counter='vllm:generation_tokens_total'
  delta=None
  if before['available'] and after['available']:
   ba=before['summary'].get(counter);aa=after['summary'].get(counter)
   if ba is not None and aa is not None:delta=aa-ba
  status=('OBSERVED_WITH_COUNTER_AGREEMENT' if nt is not None and delta==nt else
          'OBSERVED_WITH_INTERFERENCE_OR_COUNTER_MISMATCH' if nt is not None and delta is not None else
          'OBSERVED_USAGE_COUNTER_NOT_AVAILABLE' if nt is not None else 'INCOMPLETE_UNKNOWN_USAGE_OR_REQUEST_FAILURE')
  lat=[x['wall_s'] for x in rows if x['ok']]
  cell_summary=dict(label=label,concurrency=c,n_requests=len(rows),ok=sum(x['ok'] for x in rows),failed=sum(not x['ok'] for x in rows),
      total_completion_tokens=nt,batch_wall_s=elapsed,aggregate_completion_tokens_per_s=nt/elapsed if nt is not None else None,
      request_avg_tok_s_mean=statistics.mean([x['completion_tokens']/x['wall_s'] for x in rows]) if known else None,
      latency_p50_ms=percentile(lat,.5)*1000 if lat else None,latency_p95_ms=percentile(lat,.95)*1000 if lat else None,
      metric_generation_delta=delta,metric_counter_status=status,
      peak_running=max([z.get('vllm:num_requests_running') or 0 for z in samples],default=None),
      peak_waiting=max([z.get('vllm:num_requests_waiting') or 0 for z in samples],default=None),
      peak_kv_fraction=max([z.get('vllm:kv_cache_usage_perc') if z.get('vllm:kv_cache_usage_perc') is not None else (z.get('vllm:gpu_cache_usage_perc') or 0) for z in samples],default=None),
      ttft_ms='NOT_COMPUTED_WITHOUT_SCOPED_HISTOGRAM',tokens_per_s2='NOT_COMPUTED_FOR_CONCURRENT_REQUESTS')
  cells.append(cell_summary);write_json(cell/'summary.json',cell_summary)
  print('M08',label,'c=',c,'valid=',cell_summary['ok'],'/',per_level,'tokens/s=',cell_summary['aggregate_completion_tokens_per_s'],status,flush=True)
 write_json(out/'summary.json',dict(phase=label,model=env['served_model'],namespace=env['namespace'],config=config,
                                   workload=dict(levels=list(levels),per_level=per_level,max_tokens=max_tokens,prompt_version='CAKM_M08_FIXED_V1'),cells=cells))
 return out

def percentile(values,q):
 if not values:return None
 s=sorted(values);return s[min(len(s)-1,max(0,math.ceil(q*len(s))-1))]

def flag_value(args,flag):
 a=[x for x in args if x.startswith(flag+'=')]
 if len(a)!=1:raise ValueError(f'Expected unique flag {flag}, found {len(a)}')
 return a[0].split('=',1)[1]

def expected_tune(base_args,new_value,flag='--max-num-seqs'):
 if flag!='--max-num-seqs':raise ValueError('Only max-num-seqs supported in this handoff')
 old=flag_value(base_args,flag)
 if not str(new_value).isdigit() or int(new_value) not in (16,32,64,128):raise ValueError('Use tested bounded candidates 16,32,64,128')
 if str(new_value)==old:raise ValueError('New value must differ from original')
 return [f'{flag}={new_value}' if x.startswith(flag+'=') else x for x in base_args]

def apply_tune(env,before_path,new_value=64,authorize=False):
 base=read_json(Path(before_path)/'summary.json')['config'];now_d=deployment(env['namespace'])
 if now_d['args']!=base['args'] or now_d['image']!=base['image']:
  raise ValueError('Live deployment drifted from measured baseline; refuse to tune')
 args=expected_tune(base['args'],new_value)
 plan={'from':flag_value(base['args'],'--max-num-seqs'),'to':str(new_value),'flag':'--max-num-seqs',
       'namespace':env['namespace'],'old_args':base['args'],'new_args':args,'model':env['served_model'],
       'authorize':authorize,'mutation':'replace one container args array with kubectl JSON patch test guard'}
 write_json(Path(before_path)/'tune_plan.json',plan)
 if not authorize:
  print('SAFE PREVIEW: no patch. Set AUTHORIZE_ONE_FLAG_ROLLOUT=True after reviewing tune_plan.json');return plan
 # Test both old args and resource version to prevent lost updates. Deployment path c[0] assumed only after verification.
 raw=json.loads(kubectl(['-n',env['namespace'],'get','deployment','vllm','-o','json']).stdout)
 containers=raw['spec']['template']['spec']['containers'];idx=[i for i,c in enumerate(containers) if c['name']=='vllm']
 if len(idx)!=1:raise ValueError('Cannot identify vllm container')
 if containers[idx[0]]['args']!=base['args'] or raw['metadata']['resourceVersion']!=now_d['resource_version']:
  raise ValueError('Concurrent deployment change; refuse to patch')
 ptr=f'/spec/template/spec/containers/{idx[0]}/args'
 patch=[{'op':'test','path':'/metadata/resourceVersion','value':raw['metadata']['resourceVersion']},
        {'op':'test','path':ptr,'value':base['args']},{'op':'replace','path':ptr,'value':args}]
 kubectl(['-n',env['namespace'],'patch','deployment','vllm','--type=json','-p',json.dumps(patch)],timeout=40)
 rollout=kubectl(['-n',env['namespace'],'rollout','status','deployment/vllm','--timeout=12m'],timeout=780)
 after=deployment(env['namespace'])
 if after['args']!=args or served_model(env)!=env['served_model']:raise ValueError('Rollout finished but config/model verification FAILED')
 write_json(Path(before_path)/'tune_actual.json',dict(patch=patch,post_deployment=after,rollout_stdout=rollout.stdout,status='EXECUTED_VERIFIED_CONFIGURATION',timestamp=now()))
 return plan

def compare_tune(before,after):
 a=read_json(Path(before)/'summary.json');b=read_json(Path(after)/'summary.json')
 A=a['config'];B=b['config']
 if a['model']!=b['model'] or A['image']!=B['image']:raise ValueError('Model or image mismatch')
 xa=A['args'];xb=B['args'];expect=expected_tune(xa,flag_value(xb,'--max-num-seqs'))
 if xb!=expect:raise ValueError('Changed more than one serving flag')
 if a['workload']!=b['workload']:raise ValueError('Workload changed across before/after')
 results=[]
 for u,v in zip(a['cells'],b['cells']):
  if u['concurrency']!=v['concurrency']:raise ValueError('Concurrency mismatch')
  t=u['aggregate_completion_tokens_per_s'];z=v['aggregate_completion_tokens_per_s']
  results.append(dict(concurrency=u['concurrency'],before_tokens_per_s=t,after_tokens_per_s=z,
         throughput_ratio=(z/t if t and z is not None else None),before_p95_ms=u['latency_p95_ms'],after_p95_ms=v['latency_p95_ms'],
         before_quality_state='NOT_TESTED_IN_M08_LOAD',after_quality_state='NOT_TESTED_IN_M08_LOAD',
         measurement_state=('OBSERVED_2_EPOCHS' if t is not None and z is not None else 'INCOMPLETE')))
 comparison={'state':'OBSERVED_PAIRED_WORKLOAD_NONRANDOMIZED_ORDER','claim_ceiling':'Descriptive one-flag tuning; temporal confounding remains; quality needs M09 evaluation',
     'before':str(before),'after':str(after),'change':{'flag':'--max-num-seqs','from':flag_value(xa,'--max-num-seqs'),'to':flag_value(xb,'--max-num-seqs')},'rows':results}
 write_json(Path(after)/'comparison.json',comparison)
 return comparison

def eca_dataset():
 p=ROOT/'data'/'eca_pilot_inputs_v1.jsonl';data=p.read_bytes()
 if digest_bytes(data)!=ECA_SHA:raise ValueError('Frozen ECA input dataset SHA mismatch')
 return [json.loads(line) for line in data.splitlines()]

def eca_prob(it):
 return (f"Elementary cellular automaton, Wolfram rule {it['rule']}, width 8, periodic (wrap-around) boundary. "
         f"Neighborhood left,center,right as integer L*4+C*2+R; new cell = bit (that number) of rule number. "
         f"Current state (index 0..7): {''.join(map(str,it['initial_state']))}. Give the state after ONE step.")

def eca_truth(it):
 b=it['initial_state'];r=it['rule'];n=len(b)
 return ''.join(str((r>>((b[(i-1)%n]<<2)|(b[i]<<1)|b[(i+1)%n]))&1) for i in range(n))

def parse_answer(t):
 x=re.findall(r'ANSWER:\s*([01]{8}|ABSTAIN)',t or '')
 return x[-1] if x else None

def run_eca(env,n_items=8,max_tokens=128,call_cap=3,token_cap=384):
 if n_items not in (4,8,16,32):raise ValueError('Allowed pilot sizes 4,8,16,32; balanced across rules')
 items=eca_dataset();per=n_items//4;items=[v for rule in (30,90,110,184) for v in items if v['rule']==rule][:n_items] if False else [v for rule in (30,90,110,184) for v in [x for x in items if x['rule']==rule][:per]]
 if len(items)!=n_items:raise ValueError('Dataset balance incomplete')
 out=new_run('M09_ECA_B0_B3');dataset_bytes=(ROOT/'data'/'eca_pilot_inputs_v1.jsonl').read_bytes()
 write_json(out/'config.json',dict(dataset_sha256=ECA_SHA,selected_ids=[i['item_id'] for i in items],n_items=n_items,
     served_model=env['served_model'],namespace=env['namespace'],host=env['base_url'],precision='UNKNOWN_UNLESS_VERIFIED',
     max_tokens_per_call=max_tokens,item_call_cap=call_cap,item_token_cap=token_cap,decode='greedy_zero_temperature',
     genesis_policy=POLICY_ID,split='PILOT_NONCONFIRMATORY',preregistration='DRAFT_UNFROZEN',
     oracle='SCORING_PROCESS_ONLY_AFTER_HASH_COMMIT',self_training='NOT_TESTED',start=now()))
 (out/'items.jsonl').write_text(''.join(json.dumps(i,sort_keys=True)+'\n' for i in items))
 def call(rec,p):
  x=infer(env,p,max_tokens)
  rec['calls'].append(x);return parse_answer(x.get('text',''))
 records=[]
 for arm in ARMS:
  for it in items:
   rec=dict(arm=arm,item_id=it['item_id'],calls=[]);p=eca_prob(it)
   try:
    if arm=='B0_FIXED': ans=[call(rec,SYS+'\n'+p)]
    elif arm=='B1_GENESIS':
     ans=[call(rec,SYS+'\n'+p+suffix) for suffix in ('',' Work cell by cell, listing neighborhoods.',' Verify by recomputing the rule table first.')]
    else:
     a1=call(rec,SYS+'\n'+p)
     if arm=='B2_GENESIS_DAISY':
      a2=call(rec,SYS+'\n'+p+f' A candidate answer is {a1}. Independently find any wrong cell and give corrected full state.')
     else:
      ix=random.Random(f'20261012-{it["item_id"]}').randrange(8)
      a2=call(rec,SYS+'\n'+p+f' A candidate answer is {a1}. Recheck cell {ix} and restate the full state.')
     adj=call(rec,SYS+'\n'+p+f' Two candidate answers: A={a1}, B={a2}. Pick by recomputing; reply ANSWER: <8 bits>.')
     ans=[adj]
    valid=[a for a in ans if a]
    final=sorted(valid,key=lambda a:(-valid.count(a),a))[0] if valid else None
    usage=[x['completion_tokens'] for x in rec['calls']]
    rec.update(final_answer=final,n_calls=len(rec['calls']),tokens_total=sum(usage) if all(type(x)==int for x in usage) else None,
               wall_s_total=sum(x['wall_s'] for x in rec['calls']),over_budget=len(usage)>call_cap or
               (all(type(x)==int for x in usage) and sum(usage)>token_cap),
               failure='MODEL_CALL_FAILED' if any(not x['ok'] for x in rec['calls']) else None)
   except Exception as ex:rec.update(final_answer=None,n_calls=len(rec['calls']),tokens_total=None,over_budget=True,failure=type(ex).__name__)
   records.append(rec)
   print('M09',arm,it['item_id'],rec.get('final_answer'),'calls',rec.get('n_calls'),flush=True)
 data=''.join(json.dumps(r,sort_keys=True)+'\n' for r in records).encode()
 (out/'answers.jsonl').write_bytes(data)
 config_sha=digest_bytes((out/'config.json').read_bytes());items_sha=digest_bytes((out/'items.jsonl').read_bytes())
 write_json(out/'COMMIT.json',dict(answers_sha256=digest_bytes(data),items_sha256=items_sha,config_sha256=config_sha,
              dataset_sha256=ECA_SHA,policy_id=POLICY_ID,oracle_accessed=False,committed_at=now(),status='ANSWERS_COMMITTED_BEFORE_SCORING'))
 return out

def mcnemar(b,c):
 n=b+c
 if n==0:return 1.
 return min(1.,2*sum(math.comb(n,j) for j in range(min(b,c)+1))/2**n)

def score_eca(out):
 out=Path(out);receipt=read_json(out/'COMMIT.json');config=read_json(out/'config.json')
 for fname,key in [('answers.jsonl','answers_sha256'),('items.jsonl','items_sha256'),('config.json','config_sha256')]:
  if digest_bytes((out/fname).read_bytes())!=receipt[key]:raise ValueError(f'{fname} HASH MISMATCH; refuse scoring')
 if receipt['dataset_sha256']!=ECA_SHA or config['dataset_sha256']!=ECA_SHA or receipt['policy_id']!=config['genesis_policy']:
  raise ValueError('Dataset/policy identity mismatch')
 dataset=eca_dataset();source={i['item_id']:i for i in dataset}
 items=[json.loads(x) for x in (out/'items.jsonl').read_text().splitlines()]
 if len(set(x['item_id'] for x in items))!=len(items):raise ValueError('Duplicate item IDs')
 for i in items:
  if i!=source.get(i['item_id']):raise ValueError('Input item not identical to frozen dataset')
 if sorted(i['item_id'] for i in items)!=sorted(config['selected_ids']):raise ValueError('Item selector mismatch')
 recs=[json.loads(x) for x in (out/'answers.jsonl').read_text().splitlines()]
 expected={(a,i['item_id']) for a in ARMS for i in items}
 keys=[(r['arm'],r['item_id']) for r in recs]
 if len(recs)!=len(expected) or len(set(keys))!=len(keys) or set(keys)!=expected:raise ValueError('Incomplete/duplicate panel, refusing scores')
 right={a:{} for a in ARMS};results=[]
 for a in ARMS:
  subset=[r for r in recs if r['arm']==a]
  for r in subset:
   truth=eca_truth(source[r['item_id']]);ok=(r.get('final_answer')==truth and not r.get('over_budget') and not r.get('failure'))
   right[a][r['item_id']]=bool(ok)
  known=all(r.get('tokens_total') is not None for r in subset)
  correct=sum(right[a].values()); total_tok=sum(r['tokens_total'] for r in subset) if known else None
  results.append(dict(arm=a,n=len(subset),correct=correct,exact_match_accuracy=correct/len(subset),
             failures=sum(bool(r.get('failure')) for r in subset),over_budget=sum(bool(r.get('over_budget')) for r in subset),
             abstentions=sum(r.get('final_answer')=='ABSTAIN' for r in subset),parse_errors=sum(not r.get('final_answer') for r in subset),
             completion_tokens=total_tok,tokens_per_correct=(total_tok/correct if correct and known else None),
             status='PILOT_OBSERVED_IF_ENDPOINT_VERIFIED'))
 comparisons=[]
 for a,b in [('B2_GENESIS_DAISY','B3_RANDOM_CONTROL'),('B1_GENESIS','B0_FIXED'),('B2_GENESIS_DAISY','B1_GENESIS')]:
  x=sum(right[a][i] and not right[b][i] for i in config['selected_ids']);y=sum(right[b][i] and not right[a][i] for i in config['selected_ids'])
  comparisons.append(dict(a=a,b=b,a_only_correct=x,b_only_correct=y,p_exact=mcnemar(x,y)))
 outcome=dict(status='PILOT_NONCONFIRMATORY',sample_size=len(items),model=config['served_model'],evaluation=results,comparisons=comparisons,
              claim_ceiling='ECA synthetic only; B1 GENESIS PROXY; B2/B3 challenge content differs; no independent biological claim',
              antigence='POLICY_CHALLENGE_ONLY_NOT_WEIGHT_UPDATE',anticube='NOT_COMPUTED',delta_g_star='NOT_COMPUTED',timestamp=now())
 write_json(out/'analysis.json',outcome)
 return outcome

def locate_workshop():
 candidates=[Path.cwd(),*Path.cwd().parents,Path.home()/'akamai-workshop-ai-inference',Path.home()/'workshop']
 if os.getenv('WORKSHOP_REPO'):candidates.insert(0,Path(os.environ['WORKSHOP_REPO']))
 for p in candidates:
  if (p/'09_optional_agents_on_k8s'/'agent'/'agent.py').is_file() and (p/'08_tune_and_evaluate'/'08_tune_and_evaluate.ipynb').is_file():return p.resolve()
  if (p/'akamai-workshop-ai-inference'/'09_optional_agents_on_k8s'/'agent'/'agent.py').is_file():return (p/'akamai-workshop-ai-inference').resolve()
 raise FileNotFoundError('Set WORKSHOP_REPO to the clone containing modules 08 and 09; nothing was modified')

def deploy_upstream_agent(env,authorize=False):
 repo=locate_workshop();py=repo/'09_optional_agents_on_k8s'/'agent'/'agent.py'
 manifest=repo/'09_optional_agents_on_k8s'/'manifests'/'agent.yaml'
 plan=dict(source_agent=str(py),source_manifest=str(manifest),code_sha256=digest_bytes(py.read_bytes()),namespace=env['namespace'],
           served_model=env['served_model'],action='APPLY_NAMESPACE_SCOPED_UPSTREAM_SA_AGENT',authorized=authorize)
 if not authorize:return plan
 ns=env['namespace']
 cm=kubectl(['-n',ns,'create','configmap','agent-code',f'--from-file=agent.py={py}','--dry-run=client','-o','yaml']).stdout
 kubectl(['-n',ns,'apply','-f','-'],input_data=cm)
 kubectl(['-n',ns,'apply','-f',str(manifest)])
 kubectl(['-n',ns,'set','env','deployment/sa-agent',f'MODEL_NAME={env["served_model"]}'])
 kubectl(['-n',ns,'rollout','restart','deployment/sa-agent'])
 kubectl(['-n',ns,'rollout','status','deployment/sa-agent','--timeout=5m'],timeout=340)
 plan.update(state='EXECUTED_AGENT_DEPLOYMENT',completed_at=now())
 return plan

def exercise_upstream_agent(env,questions=None,concurrency=6):
 if concurrency not in (2,4,6):raise ValueError('Agent concurrency cap 2/4/6')
 questions=questions or [
  'What should I check before adding a GPU node pool to LKE?',
  'How do I write an EdgeWorker for the CDN?',
  'What model and endpoint are you running on?',
  'To serve a 4B model, what does an RTX 4000 Ada cost per month? Use the pricing tool.',
  'In two sentences, what is a NodeBalancer?',
  'In two sentences, what is an Object Storage lifecycle policy?',
  'In two sentences, when should I use a VPC?',
  'In two sentences, what does a Cloud Firewall do?']
 out=new_run('M09_UPSTREAM_K8S_AGENT')
 write_json(out/'agent_config.json',dict(namespace=env['namespace'],model=env['served_model'],source_repo_sha=UPSTREAM_SHA,
          request_set='UPSTREAM_SCOPE_PRICING_BATCH_EXTENDED_V1',questions=questions,concurrency=concurrency,started=now()))
 p=subprocess.Popen(['kubectl','-n',env['namespace'],'port-forward','svc/sa-agent','18080:8080'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 def ask(q):
  t=time.perf_counter()
  try:
   r=requests.post('http://127.0.0.1:18080',json={'message':q},timeout=240);j=r.json()
   return dict(ok=r.ok and 'answer' in j,question=q,response=j.get('answer'),error=j.get('error'),wall_s=time.perf_counter()-t,http_status=r.status_code)
  except Exception as exc:return dict(ok=False,question=q,error=type(exc).__name__,wall_s=time.perf_counter()-t)
 try:
  ready=False
  for _ in range(30):
   if p.poll() is not None:raise RuntimeError('Port-forward exited; check pod and service readiness')
   try:
    r=requests.get('http://127.0.0.1:18080',timeout=1)
    if r.status_code==200:ready=True;break
   except requests.RequestException:pass
   time.sleep(.5)
  if not ready:raise RuntimeError('Agent port-forward did not become ready')
  before=metric_probe(env,out,'before')
  samples=[];stop=threading.Event();sampler=threading.Thread(target=sample_metrics,args=(env,stop,samples),daemon=True)
  # First four are sequential and test scope/model/pricing; final six use the same upstream agent concurrently.
  checks=[ask(q) for q in questions[:4]]
  sampler.start();start=time.perf_counter()
  with ThreadPoolExecutor(max_workers=concurrency) as ex:batch=list(ex.map(ask,(questions+[questions[0]])[2:2+concurrency]))
  wall=time.perf_counter()-start;stop.set();sampler.join(timeout=5)
  after=metric_probe(env,out,'after')
  (out/'metric_samples.jsonl').write_text(''.join(json.dumps(s,sort_keys=True)+'\n' for s in samples))
  write_json(out/'metric_receipts.json',dict(before=before,after=after))
  write_json(out/'agent_results.json',dict(checks=checks,batch=batch,batch_wall_s=wall,
       responses_ok=sum(r['ok'] for r in checks+batch),responses_total=len(checks+batch),
       peak_running=max([x.get('vllm:num_requests_running') or 0 for x in samples],default=None),
       peak_waiting=max([x.get('vllm:num_requests_waiting') or 0 for x in samples],default=None),
       peak_kv_fraction=max([x.get('vllm:kv_cache_usage_perc') or x.get('vllm:gpu_cache_usage_perc') or 0 for x in samples],default=None),
       note='Agent tool invocation internally is not observed directly through HTTP output; pricing answer alone is not proof of tool call. Source implements pricing tool.' ))
  return out
 finally:
  p.terminate()
  try:p.wait(timeout=4)
  except subprocess.TimeoutExpired:p.kill()

def export_zip(include_raw=True):
 # Raw answers only include synthetic ECA + public workshop prompts; no secrets or kubeconfig.
 output=ROOT/f'CELL_AKAMAI_M08_M09_RESULTS_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}.zip'
 manifest=[]
 with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for p in sorted([*(RUNS.rglob('*')),ROOT/'cell_akamai_handoff.py',ROOT/'data'/'eca_pilot_inputs_v1.jsonl',*(ROOT/'notebooks').glob('*.ipynb')]):
   if not p.is_file():continue
   if not include_raw and (p.name.endswith('.prom') or p.name in ('answers.jsonl','request_rows.jsonl')):continue
   rel=p.relative_to(ROOT).as_posix();manifest.append(dict(path=rel,sha256=digest_bytes(p.read_bytes()),bytes=p.stat().st_size))
   z.write(p,rel)
  report=dict(schema='CAKM_M08_M09_RESULT_ARCHIVE_V1',generated_utc=now(),source=UPSTREAM_SHA,
     claude_predecessor=CLAUDE_SHA,files=manifest,mmr='NOT_COMPUTED',mmr_committed=False,signature='NOT_SIGNED',
     independent_akamai_reexecution='NOT_TESTED_BY_ORCHESTRATOR',raw_included=include_raw)
  z.writestr('ARCHIVE_MANIFEST.json',json.dumps(report,indent=2,sort_keys=True))
 return output

def quality_epoch(env,label,n_items=8,max_tokens=128):
 """Small fixed-task exact-match quality check of serving configs, distinct from B0-B3 causal policy test."""
 if n_items not in (4,8,16,32):raise ValueError('Quality panel must be 4/8/16/32')
 full=eca_dataset();n=n_items//4
 items=[x for r in (30,90,110,184) for x in [z for z in full if z['rule']==r][:n]]
 out=new_run('M08_QUALITY_'+label)
 config=deployment(env['namespace'])
 write_json(out/'identity.json',dict(model=env['served_model'],config=config,namespace=env['namespace'],label=label,
             input_dataset_sha=ECA_SHA,selected_ids=[i['item_id'] for i in items],status='IN_PROGRESS',time=now()))
 rows=[]
 # Predictor never computes or imports oracle, only calls model.
 for item in items:
  obs=infer(env,SYS+'\n'+eca_prob(item),max_tokens=max_tokens)
  rows.append(dict(item_id=item['item_id'],observed=obs,answer=parse_answer(obs.get('text',''))))
  print('M08 quality',label,item['item_id'],'status',obs['ok'],flush=True)
 raw=''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows).encode()
 (out/'answers.jsonl').write_bytes(raw)
 receipt={'answer_sha256':digest_bytes(raw),'identity_sha256':digest_bytes((out/'identity.json').read_bytes()),
          'dataset_sha256':ECA_SHA,'status':'ANSWER_COMMITTED_NO_ORACLE_YET','timestamp':now()}
 write_json(out/'COMMIT.json',receipt)
 return out

def score_quality(out):
 out=Path(out);commit=read_json(out/'COMMIT.json');identity=read_json(out/'identity.json')
 if commit['answer_sha256']!=digest_bytes((out/'answers.jsonl').read_bytes()):raise ValueError('Answer digest mismatch')
 if commit['identity_sha256']!=digest_bytes((out/'identity.json').read_bytes()):raise ValueError('Config digest mismatch')
 if commit['dataset_sha256']!=ECA_SHA or identity['input_dataset_sha']!=ECA_SHA:raise ValueError('Dataset digest mismatch')
 source={i['item_id']:i for i in eca_dataset()};rows=[json.loads(x) for x in (out/'answers.jsonl').read_text().splitlines()]
 if [r['item_id'] for r in rows]!=identity['selected_ids'] or len(rows)!=len(set(r['item_id'] for r in rows)):
  raise ValueError('Missing/reordered/duplicate rows')
 valid=sum(r['answer']==eca_truth(source[r['item_id']]) and r['observed']['ok'] for r in rows)
 observed_usage=all(isinstance(r['observed']['completion_tokens'],int) for r in rows)
 result=dict(phase=identity['label'],n=len(rows),exact_match_count=valid,exact_match_fraction=valid/len(rows),
             completion_tokens_total=sum(r['observed']['completion_tokens'] for r in rows) if observed_usage else None,
             dataset_sha256=ECA_SHA,source_class='OBSERVED_IF_ENDPOINT_VERIFIED',split='PILOT_NONCONFIRMATORY',
             status='EXECUTED_OPERATOR_HOST_IF_RECEIPT_VALID',claim_ceiling='Small frozen ECA quality panel; no inference causality from phase change')
 write_json(out/'quality_summary.json',result)
 return result

def compare_quality(before,after):
 b=read_json(Path(before)/'quality_summary.json');a=read_json(Path(after)/'quality_summary.json')
 x=read_json(Path(before)/'identity.json');y=read_json(Path(after)/'identity.json')
 if x['selected_ids']!=y['selected_ids'] or x['model']!=y['model']:raise ValueError('Nonmatched quality comparison')
 result=dict(before=b,after=a,delta_accuracy=a['exact_match_fraction']-b['exact_match_fraction'],
             state='SMALL_NONCONFIRMATORY_PAIRED_QUALITY_PANEL')
 write_json(Path(after)/'quality_comparison.json',result)
 return result
