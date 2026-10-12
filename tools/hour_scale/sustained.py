#!/usr/bin/env python3
"""Durable hosted BF16 windows. Raw responses private; Merkle receipts public."""
import concurrent.futures as cf,datetime as dt,fcntl,hashlib,json,os,re,subprocess,threading,time,urllib.request,uuid
from pathlib import Path
from runner import load_prompts,atomic,percentile
NAMESPACE='workshop-s05';MODEL='Qwen/Qwen3-4B';URL='http://vllm:8000';BASE=Path(__file__).resolve().parent
STOP=threading.Event()
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(o):return json.dumps(o,sort_keys=True,separators=(',',':')).encode()
def merkle(leaves):
 nodes=[hashlib.sha256(b'\x00'+bytes.fromhex(v)).digest() for v in leaves]
 if not nodes:return None
 while len(nodes)>1:nodes=[hashlib.sha256(b'\x01'+nodes[i]+nodes[min(i+1,len(nodes)-1)]).digest() for i in range(0,len(nodes),2)]
 return nodes[0].hex()
def kinetics(samples):
 rates=[];acc=[]
 for a,b in zip(samples,samples[1:]):
  if b['t']<=a['t'] or a.get('counter') is None or b.get('counter') is None or b['counter']<a['counter']:continue
  rates.append({'t':(a['t']+b['t'])/2,'tokens_per_s':(b['counter']-a['counter'])/(b['t']-a['t']),'segment':(a['t'],b['t'])})
 for a,b in zip(rates,rates[1:]):
  if a['segment'][1]!=b['segment'][0]:continue
  acc.append({'t':(a['t']+b['t'])/2,'tokens_per_s2':(b['tokens_per_s']-a['tokens_per_s'])/(b['t']-a['t'])})
 return {'rates':rates,'acceleration':acc}
def kube(*args):return subprocess.check_output(['kubectl','--request-timeout=15s','-n',NAMESPACE,*args],text=True,stderr=subprocess.DEVNULL)
def deployment():
 d=json.loads(kube('get','deployment','vllm','-o','json'));c=d['spec']['template']['spec']['containers'][0]
 return {'args':c['args'],'image':c['image'],'ready':d['status'].get('readyReplicas',0),'generation':d['metadata']['generation']}
def metrics():
 text=urllib.request.urlopen(URL+'/metrics',timeout=10).read().decode();v={}
 for name,key in [('generation_tokens_total','counter'),('num_requests_running','running'),('num_requests_waiting','waiting'),('num_preemptions_total','preemptions'),('kv_cache_usage_perc','kv_fraction')]:
  values=[]
  for line in text.splitlines():
   if line.startswith('vllm:'+name+'{') and 'model_name="'+MODEL+'"' in line:
    try:values.append(float(line.rsplit(' ',1)[1]))
    except ValueError:pass
  v[key]=sum(values) if values else None
 return v

def main():
 os.umask(0o077);root=Path(os.environ['CAKM_DATASET_ROOT']);out=Path(os.environ['CAKM_RUN_ROOT']);out.mkdir(parents=True,exist_ok=False);pub=out/'public';pub.mkdir();private=out/'private';private.mkdir()
 rid=out.name;source=os.environ['CAKM_SOURCE_SHA'];leaves=[];receipts=[];seq=0;mutex=threading.Lock()
 lock=open('/tmp/cell-akamai-shared-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 config=deployment();config_hash=digest(canonical(config))
 assert config['ready']==1 and any(a=='--model='+MODEL for a in config['args'])
 models=json.load(urllib.request.urlopen(URL+'/v1/models',timeout=10));assert any(x['id']==MODEL for x in models['data'])
 assert kube('auth','can-i','get','deployments').strip()=='yes'
 pod=next(x['metadata']['name'] for x in json.loads(kube('get','pods','-o','json'))['items'] if x['metadata']['name'].startswith('vllm-') and x['status']['phase']=='Running')
 hardware=kube('exec',pod,'--','nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader').strip()
 logs=kube('logs',pod,'--tail=500');assert 'bfloat16' in logs,'BF16 precision not freshly attested'
 for _ in range(3):
  m=metrics();assert m['running']==0 and m['waiting']==0,'Endpoint not idle';time.sleep(2)
 plan={'run_id':rid,'parent_run_id':'concurrency-07-bf16_fullmatrix_reference-20261012T203417Z-225f0b49','source_commit':source,'model_id':MODEL,'model_revision':'UNKNOWN_UNPINNED_WORKSHOP_CACHE','precision':'BF16_LOG_VERIFIED','hardware':hardware,'namespace':NAMESPACE,'serving_config':config,'serving_config_sha256':config_hash,'runtime':'PLAIN_CLIENT','policy_arm':'DIRECT_FIXTURE_PROMPT_NOT_LANE_B_POLICY','max_tokens':256,'temperature':0,'enable_thinking':False,'seed':20261012,'windows_per_dataset':12,'target_active_s_per_window':300,'warmup_s_per_window':15,'datasets':['GEN-RAW','GEN-FCG','DAISY-RAW','DAISY-FCG'],'expected_windows':48,'expected_measured_hours':4,'max_requests_per_dataset':100000,'max_completion_tokens_per_dataset':25600000,'EVAL_RAW':'NOT_ADMITTED_ORACLE_TARGETS','EVAL_FCG':'NOT_ADMITTED_ORACLE_TARGETS','anticube':'NOT_COMPUTED_NO_VALIDATED_IMPLEMENTATION','delta_g_star':'NOT_COMPUTED_NO_VALIDATED_FORMULA','claim_ceiling':'OBSERVED_INFERENCE_ONLY_NO_IMPROVEMENT','start_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'execution_path':'EXISTING_HOSTED_WORKSHOP_NO_CLUSTER_PROVISIONING'}
 datasets=[]
 for role in ('genesis','vita_daisy'):
  for rep in ('original','fcg'):
   rows,report=load_prompts(root,role,rep);assert len(rows)==32
   datasets.append((role,rep,rows,report))
 plan['dataset_hashes']=report['files'];atomic(pub/'PLAN.json',plan);atomic(pub/'STATE.json',dict(state='PREFLIGHT_VERIFIED',completed_windows=0,expected_windows=48,run_id=rid,source_commit=source))
 def checkpoint(receipt):
  nonlocal seq
  seq+=1;leaf=digest(canonical(receipt));leaves.append(leaf);entry=dict(receipt,checkpoint_id=seq,receipt_sha256=leaf,merkle_root=merkle(leaves),merkle_leaves=list(leaves),merkle_construction='SHA256(00||receipt_digest) leaves; SHA256(01||left||right); odd duplicate; unsigned local tree, not project MMR')
  atomic(pub/f'checkpoint-{seq:06}.json',entry);receipts.append(entry);atomic(pub/'LATEST.json',entry)
  atomic(pub/'STATE.json',dict(state='RUNNING' if seq<48 else 'COMPLETED_UNSCORED',completed_windows=seq,expected_windows=48,run_id=rid,source_commit=source))
 try:
  import random
  for role,rep,rows,report in datasets:
   levels=[1,2,4,8]*3;random.Random('20261012:'+role+':'+rep).shuffle(levels);requests_total=[0]
   for window,c in enumerate(levels,1):
    if STOP.is_set():raise RuntimeError('STOP_REQUESTED')
    assert deployment()==config,'Stale serving config'
    m=metrics();assert m['running']==0 and m['waiting']==0,'Nonidle window boundary'
    wid=f'{role}-{rep}-w{window:02}-c{c}';ledger=private/(wid+'.jsonl');measure=[];samples=[];errors=[];active=[0];counter=[0];warm=[True];begin=[None];unique=set();lookup=[0.0]
    def request_loop(end):
     while time.monotonic()<end and not STOP.is_set():
      with mutex:
       if requests_total[0]>=100000:STOP.set();errors.append('REQUEST_BUDGET_EXHAUSTED');return
       n=counter[0];counter[0]+=1;requests_total[0]+=1;active[0]+=1
      start_request_utc=dt.datetime.now(dt.timezone.utc).isoformat();t0=time.monotonic();item=rows[n%len(rows)];payload={'model':MODEL,'messages':[{'role':'user','content':item['prompt']}],'temperature':0,'max_tokens':256,'stream':False,'chat_template_kwargs':{'enable_thinking':False}}
      response={};failure=None
      try:
       req=urllib.request.Request(URL+'/v1/chat/completions',canonical(payload),{'Content-Type':'application/json','Authorization':'Bearer not-needed'})
       with urllib.request.urlopen(req,timeout=120) as r:response=json.load(r)
      except Exception as e:failure=type(e).__name__
      endtime=time.monotonic();usage=response.get('usage') or {};finish=[x.get('finish_reason') for x in response.get('choices',[])];pt=usage.get('prompt_tokens');ct=usage.get('completion_tokens')
      if not failure and (type(pt) is not int or type(ct) is not int):failure='MISSING_USAGE'
      rec={'request_id':wid+'-'+str(n),'item_id':item['item_id'],'phase':'WARMUP' if warm[0] else 'MEASURED','start_utc':start_request_utc,'elapsed_s':endtime-t0,'prompt_tokens':pt,'completion_tokens':ct,'finish_reasons':finish,'failure':failure,'response':response}
      with mutex:
       active[0]-=1
       with ledger.open('a') as f:f.write(json.dumps(rec)+'\n');f.flush()
       if not warm[0]:measure.append({k:v for k,v in rec.items() if k!='response'});unique.add(item['item_id'])
       if len(measure)>=20 and sum(bool(x['failure']) for x in measure)/len(measure)>.2:errors.append('HTTP_OR_USAGE_FAILURE_RATE_EXCEEDS_20_PERCENT');STOP.set()
    def period(seconds,measured):
     start=time.monotonic();end=start+seconds
     with cf.ThreadPoolExecutor(max_workers=c) as pool:
      jobs=[pool.submit(request_loop,end) for _ in range(c)];last=0;check=0
      while not all(j.done() for j in jobs):
       now=time.monotonic()
       if measured and now-last>=10:
        try:
         mm=metrics();samples.append(dict(mm,t=now-start));last=now
         atomic(pub/'LIVE.json',dict(run_id=rid,window_id=wid,concurrency=c,state='RUNNING_PROVISIONAL',elapsed_measured_s=now-start,target_s=300,completed_windows=seq,expected_windows=48,source_commit=source,last_counter_sample=mm,units={'counter':'tokens','running':'requests','waiting':'requests'},checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
         if mm['running'] is not None and mm['running']>c:errors.append('EXTERNAL_LOAD_SUSPECTED');STOP.set()
        except Exception as e:errors.append('METRICS_'+type(e).__name__);STOP.set()
       if now-check>=30:
        if deployment()!=config:errors.append('CONFIG_DRIFT');STOP.set()
        check=now
       time.sleep(.5)
      for j in jobs:j.result()
     return time.monotonic()-start
    period(15,False);warm[0]=False;startutc=dt.datetime.now(dt.timezone.utc).isoformat();elapsed=period(300,True)
    answerhash=digest(ledger.read_bytes());atomic(private/(wid+'.COMMIT.json'),{'answers_sha256':answerhash,'workload_sha256':digest(canonical(rows)),'config_sha256':config_hash})
    known=all(type(x['completion_tokens']) is int and type(x['prompt_tokens']) is int for x in measure if not x['failure']);good=[x for x in measure if not x['failure']];tokens=sum(x['completion_tokens'] for x in good) if known else None
    kinetics10=kinetics(samples);kinetics30=kinetics(samples[::3]);datasetid=('GEN' if role=='genesis' else 'DAISY')+('-RAW' if rep=='original' else '-FCG')
    receipt={'schema':'CAKM_SUSTAINED_WINDOW_V1','run_id':rid,'parent_run_id':plan['parent_run_id'],'dataset_id':datasetid,'dataset_sha256':report['files'],'representation':rep,'model_id':MODEL,'model_revision':plan['model_revision'],'precision':plan['precision'],'hardware':hardware,'runtime':'PLAIN_CLIENT','policy_arm':plan['policy_arm'],'source_commit':source,'serving_config_sha256':config_hash,'workload_sha256':digest(canonical(rows)),'concurrency':c,'window_id':wid,'repetition_order':levels,'start_utc':startutc,'end_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'elapsed_monotonic_s':elapsed,'active_target_s':300,'prompt_tokens':sum(x['prompt_tokens'] for x in good) if known else None,'completion_tokens':tokens,'requests':len(measure),'unique_items':len(unique),'failures':sum(bool(x['failure']) for x in measure),'truncated':sum('length' in x['finish_reasons'] for x in measure),'latency_p50_ms':percentile([x['elapsed_s']*1000 for x in measure],.5),'latency_p95_ms':percentile([x['elapsed_s']*1000 for x in measure],.95),'latency_p99_ms':percentile([x['elapsed_s']*1000 for x in measure],.99),'output_tokens_per_s':tokens/elapsed if tokens is not None else None,'requests_per_s':len(good)/elapsed,'valid_answer_tokens_per_s':None,'independent_scoring':'PENDING_AFTER_ANSWER_COMMIT','ttft_ms':None,'tpot_ms':None,'timing_reason':'NONSTREAMING_USAGE_TRANSPORT','raw_answer_commitment_sha256':answerhash,'metrics_10s':kinetics10,'metrics_30s':kinetics30,'counter_samples':samples,'errors':errors,'evidence_state':'VALID_WINDOW_UNSCORED' if elapsed>=300 and not errors and measure else 'FAILED_OR_INCOMPLETE_WINDOW','units':{'output_tokens_per_s':'tokens/s','acceleration':'tokens/s²','latency':'ms','duration':'s','concurrency':'sessions'},'anticube':'NOT_COMPUTED','delta_g_star':'NOT_COMPUTED','provisional':True,'retrieval_overhead_s':None,'retrieval_reason':'Dataset loaded/reconstructed before measured model-only windows; end-to-end lookup condition NOT_TESTED'}
    checkpoint(receipt)
    if errors or not measure:raise RuntimeError('Window failed; inspect private log and public receipt')
  atomic(pub/'STATE.json',dict(state='COMPLETED_UNSCORED',completed_windows=seq,expected_windows=48,run_id=rid,source_commit=source))
 except Exception as e:
  atomic(pub/'FAILURE.json',dict(state='STOPPED_WITH_RETAINED_WINDOWS',exception_type=type(e).__name__,completed_windows=seq,run_id=rid,source_commit=source,when_utc=dt.datetime.now(dt.timezone.utc).isoformat()));raise
if __name__=='__main__':main()
