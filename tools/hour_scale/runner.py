#!/usr/bin/env python3
"""Hour-scale closed-loop client. Private ledgers; public aggregates only."""
import argparse, concurrent.futures, contextlib, datetime, fcntl, hashlib, json, math, os
from pathlib import Path
import threading, time, urllib.request, urllib.error, uuid

UNITS={'output_tokens_per_s':'tokens/s','input_tokens_per_s':'tokens/s','requests_per_s':'requests/s','latency_p95_ms':'ms','elapsed_measured_s':'s','concurrency':'sessions'}
def sha(b): return hashlib.sha256(b).hexdigest()
def atomic(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n');os.replace(tmp,path)
def percentile(values,q):
    if not values:return None
    values=sorted(values);x=(len(values)-1)*q;i=int(x);return values[i]+(values[min(i+1,len(values)-1)]-values[i])*(x-i)
def summarize(rows,elapsed,target,c):
    ids=[r['request_id'] for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate request accounting')
    measured=[r for r in rows if r['phase']=='MEASURED']
    good=[r for r in measured if not r['failure']]
    usage_known=all(r['completion_tokens'] is not None and r['prompt_tokens'] is not None for r in good)
    tokens=sum(r['completion_tokens'] for r in good) if usage_known else None
    prompt=sum(r['prompt_tokens'] for r in good) if usage_known else None
    rates=lambda n:n/elapsed if elapsed>0 and n is not None else None
    failures={k:sum(k in r.get('failure_categories',[]) for r in measured) for k in ('HTTP','TIMEOUT','TRANSPORT','MISSING_USAGE','PARSE','TRUNCATION','QUALITY')}
    bins={}
    for r in good:
        if r['completion_tokens'] is not None:
            key=str(math.floor(r['completed_measured_s']));bins[key]=bins.get(key,0)+r['completion_tokens']
    return dict(state='COMPLETED_UNSCORED' if elapsed>=target else 'RUNNING',provisional=True,elapsed_measured_s=elapsed,target_s=target,concurrency=c,requests=len(measured),successful_requests=len(good),failures=failures,failure_count=len(measured)-len(good),failure_percent=100*(len(measured)-len(good))/len(measured) if measured else None,output_tokens_per_s=rates(tokens),input_tokens_per_s=rates(prompt),requests_per_s=rates(len(good)),total_completion_tokens=tokens,valid_answer_tokens_per_s=None,valid_answer_reason='Independent scoring pending; HTTP success is not answer validity',latency_p50_ms=percentile([r['latency_ms'] for r in measured],.5),latency_p95_ms=percentile([r['latency_ms'] for r in measured],.95),latency_p99_ms=percentile([r['latency_ms'] for r in measured],.99),ttft_ms=None,inter_token_latency_ms=None,decode_tokens_per_s=None,missing_timing_reason='Nonstreaming usage-counted transport; no token arrival timestamps',completion_binned_tokens_per_s=bins,bin_semantics='All completion tokens attributed to request completion in 1-second bins; not token emission timing',units=UNITS)
@contextlib.contextmanager
def gpu_lock(path):
    f=open(path,'a+')
    try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);yield
    finally:f.close()
def load_prompts(root,role,representation):
    root=Path(root);report=json.loads((root/'data/SIX_DATASET_VERIFICATION.json').read_text())
    for rel,digest in report['files'].items():
        if sha((root/rel).read_bytes())!=digest:raise ValueError('Dataset hash mismatch: '+rel)
    if role not in ('genesis','vita_daisy'):raise ValueError('Evaluator is oracle-only, never inference input')
    read=lambda p:[json.loads(s) for s in p.read_text().splitlines() if s]
    raw=read(root/'data/original'/f'{role}.jsonl');objects=read(root/'data/fco'/f'{role}.jsonl');edges=read(root/'data/fcg'/f'{role}.jsonl')
    if len(raw)!=len(objects) or any(a!=b['payload'] for a,b in zip(raw,objects)):raise ValueError('FCO reconstruction mismatch')
    byid={o['occurrence_id']:o for o in objects}
    projected=[e for e in edges if e['relation']=='projects_source_row']
    if len(projected)!=len(raw) or len({e['from_occurrence'] for e in projected})!=len(raw):raise ValueError('FCG coverage mismatch')
    if any(e['from_occurrence'] not in byid or byid[e['from_occurrence']]['content_id']!=e['to_source_content'] for e in projected):raise ValueError('FCG link mismatch')
    rows=raw if representation=='original' else [o['payload'] for o in objects] if representation=='fco' else [byid[e['from_occurrence']]['payload'] for e in sorted(projected,key=lambda e:e['row_ordinal'])]
    if rows!=raw:raise ValueError('Resolved representation changed workload')
    return rows,report

def run(args):
    os.umask(0o077)
    if args.duration<3600:raise ValueError('Measured duration must be >=3600 seconds')
    if args.concurrency not in (1,2,4,8):raise ValueError('Capacity extension requires separate preflight')
    rows,report=load_prompts(args.dataset_root,args.role,args.representation)
    cfg=json.loads(Path(args.config).read_text());pre=json.loads(Path(args.preflight).read_text())
    required=('namespace','served_model','precision','hardware','permissions_verified','idle_verified','deployment_args_sha256')
    if any(not pre.get(k) or pre[k]=='UNKNOWN' for k in required):raise ValueError('Incomplete live preflight')
    if pre['namespace']!='workshop-s05' or pre['served_model']!=cfg['model']:raise ValueError('Identity mismatch')
    age=time.time()-datetime.datetime.fromisoformat(pre['checked_at_utc']).timestamp()
    if not 0<=age<=300:raise ValueError('Preflight must be refreshed within 5 minutes')
    plan=dict(role=args.role,representation=args.representation,concurrency=args.concurrency,target_s=args.duration,warmup_s=args.warmup,dataset_hashes=report['files'],config_sha256=sha(Path(args.config).read_bytes()),source_commit=args.source_sha,source_file_sha256=sha(Path(__file__).read_bytes()),preflight=pre,max_requests=args.max_requests,max_completion_tokens=args.max_requests*cfg['max_tokens'],retry_policy='NO_RETRIES',schedule='Closed-loop sessions; deterministic cyclic rows',source_class='OBSERVED_IF_ENDPOINT_SUCCESS')
    if not args.execute:print(json.dumps(plan,indent=2));return
    rid='hour-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    folder=Path(args.private_root)/rid;folder.mkdir(parents=True,exist_ok=False)
    atomic(folder/'run_manifest.json',dict(plan,run_id=rid,state='RUNNING'))
    ledger=folder/'requests.private.jsonl';records=[];mutex=threading.Lock();counter=[0];start=[None];phase=['WARMUP'];checkpoint=[0]
    def snapshot(reason):
        checkpoint[0]+=1;elapsed=max(0,time.monotonic()-start[0]) if start[0] else 0
        value=dict(summarize(records,elapsed,args.duration,args.concurrency),run_id=rid,checkpoint_id=checkpoint[0],reason=reason,source_commit=args.source_sha,config_sha256=plan['config_sha256'],dataset_hashes=report['files'],checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),answer_ledger_sha256=sha(ledger.read_bytes()) if ledger.exists() else None,NEXT_ACTION='Continue measurement' if elapsed<args.duration else 'Independent score after verifying ledger commitment')
        atomic(Path(args.public_root)/rid/f'checkpoint-{checkpoint[0]:06}.json',value);atomic(Path(args.public_root)/'latest.json',value)
    def session(index,end):
        while time.monotonic()<end:
            with mutex:
                if counter[0]>=args.max_requests:return
                n=counter[0];counter[0]+=1
            item=rows[n%len(rows)];begin=time.monotonic();fail=[];response={}
            payload=dict(model=cfg['model'],messages=[dict(role='user',content=item['prompt'])],temperature=0,max_tokens=cfg['max_tokens'],stream=False)
            if 'extra_body' in cfg:payload.update(cfg['extra_body'])
            try:
                request=urllib.request.Request(cfg['base_url'].rstrip('/')+'/chat/completions',json.dumps(payload).encode(),{'Content-Type':'application/json','Authorization':'Bearer '+os.environ.get('VLLM_API_KEY','none')})
                with urllib.request.urlopen(request,timeout=120) as result:response=json.load(result)
            except urllib.error.HTTPError:fail.append('HTTP')
            except TimeoutError:fail.append('TIMEOUT')
            except Exception:fail.append('TRANSPORT')
            usage=response.get('usage') or {};pt=usage.get('prompt_tokens');ct=usage.get('completion_tokens');finish=[v.get('finish_reason') for v in response.get('choices',[])]
            if not fail and (type(pt) is not int or type(ct) is not int):fail.append('MISSING_USAGE')
            categories=fail+(['TRUNCATION'] if 'length' in finish else [])
            row=dict(request_id=f'{rid}-{n}',item_id=item['item_id'],session=index,phase=phase[0],latency_ms=(time.monotonic()-begin)*1000,completed_measured_s=max(0,time.monotonic()-start[0]) if start[0] else None,prompt_tokens=pt,completion_tokens=ct,finish_reasons=finish,failure=bool(fail),failure_categories=categories,response=response)
            with mutex:
                with ledger.open('a') as f:f.write(json.dumps(row)+'\n');f.flush()
                records.append({k:v for k,v in row.items() if k!='response'})
    with gpu_lock(args.lock):
        def period(seconds):
            end=time.monotonic()+seconds
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
                jobs=[pool.submit(session,i,end) for i in range(args.concurrency)];last=time.monotonic()
                while not all(j.done() for j in jobs):
                    time.sleep(1)
                    if start[0] and time.monotonic()-last>=args.checkpoint_seconds:
                        with mutex:snapshot('PERIODIC')
                        last=time.monotonic()
                for j in jobs:j.result()
        period(args.warmup);phase[0]='MEASURED';start[0]=time.monotonic()
        with mutex:snapshot('WARMUP_COMPLETE')
        period(args.duration)
        elapsed=time.monotonic()-start[0]
        with mutex:snapshot('CELL_END')
        state='COMPLETED_UNSCORED' if elapsed>=args.duration else 'INCOMPLETE_BUDGET_EXHAUSTED'
        atomic(folder/'COMMIT.json',dict(run_id=rid,answers_sha256=sha(ledger.read_bytes()),state=state,elapsed_measured_s=elapsed,source_commit=args.source_sha,config_sha256=plan['config_sha256']))
        atomic(folder/'run_manifest.json',dict(plan,run_id=rid,state=state))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('dataset-root','config','preflight','source-sha'):p.add_argument('--'+name,required=True)
    p.add_argument('--role',choices=['genesis','vita_daisy'],required=True);p.add_argument('--representation',choices=['original','fco','fcg'],required=True)
    p.add_argument('--concurrency',type=int,default=1);p.add_argument('--duration',type=float,default=3600);p.add_argument('--warmup',type=float,default=60);p.add_argument('--checkpoint-seconds',type=int,default=900);p.add_argument('--max-requests',type=int,default=100000)
    p.add_argument('--private-root',default='runs/hour_scale');p.add_argument('--public-root',default='evidence/hour_scale');p.add_argument('--lock',default='/tmp/cell-akamai-shared-gpu.lock');p.add_argument('--execute',action='store_true');run(p.parse_args())
