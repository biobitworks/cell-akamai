"""Bounded, read-only per-arm concurrent agentic/antigentic proxy experiment.
No oracle access. Every counted completion token comes from server response usage.
The four arms are orchestration PROXIES (not canonical Genesis/Vita DAISY weights).
"""
from __future__ import annotations
import concurrent.futures, hashlib, json, os, random, re, statistics, threading, time, urllib.error, urllib.request
from pathlib import Path

ARMS=('B0_FIXED','B1_GENESIS','B2_GENESIS_DAISY','B3_RANDOM_CONTROL')
POLICY_BINDINGS={
 'B0_FIXED':'single_model_call_baseline',
 'B1_GENESIS':'GENESIS_POLICY_PROXY_V0_NOT_RECOVERED_GENESIS',
 'B2_GENESIS_DAISY':'DAISY_CHALLENGE_PROXY_V0_NOT_TRAINED',
 'B3_RANDOM_CONTROL':'seeded_random_cell_recheck_proxy'
}
SYSTEM="You simulate elementary cellular automata exactly. End with 'ANSWER: <8 bits>' or 'ANSWER: ABSTAIN'."
def sha(b:bytes):return hashlib.sha256(b).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf8')
def prompt(it):
    bits=''.join(str(c) for c in it['initial_state'])
    return (f"RULE: {it['rule']} STATE: {bits}. Elementary cellular automaton, Wolfram rule {it['rule']}, width 8, periodic boundary. "
            "Neighborhood L*4+C*2+R defines bit position of Wolfram rule. Compute exactly ONE synchronous step. "
            "Return the final state as ANSWER: <8 bits>.")
def parse(text):
    values=re.findall(r'ANSWER:\s*([01]{8}|ABSTAIN)',text or '',flags=re.I)
    return values[-1].upper() if values else None

def http_chat(endpoint,model,messages,timeout=120,max_tokens=128,temperature=0,seed=20261012,api_key='not-needed'):
    payload={'model':model,'messages':messages,'max_tokens':max_tokens,'temperature':temperature,'seed':seed,'stream':False}
    if 'qwen3' in model.lower():
        payload['chat_template_kwargs']={'enable_thinking':False}
    data=canon(payload);req=urllib.request.Request(endpoint.rstrip('/')+'/chat/completions',data=data,
          headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
    start=time.monotonic_ns()
    with urllib.request.urlopen(req,timeout=timeout) as response:
        raw=response.read()
    end=time.monotonic_ns();obj=json.loads(raw)
    response_text=(obj['choices'][0]['message'].get('content') or '')
    reported=obj.get('usage',{}).get('completion_tokens')
    if not (type(reported) is int and reported>=0):reported=None
    return {'content':response_text,'usage_completion_tokens':reported,'duration_ns':end-start,
      'start_mono_ns':start,'end_mono_ns':end,'response_id':obj.get('id'),
      'http_json_sha256':sha(raw),'response_text_sha256':sha(response_text.encode('utf8'))}

def run_item(arm,it,client,seed=20261012,max_tokens=128):
    rec={'item_id':it['item_id'],'arm':arm,'policy_binding':POLICY_BINDINGS[arm],
         'calls':[],'status':'OBSERVED','source_class':'OBSERVED','final_answer':None}
    p=prompt(it)
    def call(user):
        result=client([{'role':'system','content':SYSTEM},{'role':'user','content':user}])
        rec['calls'].append({k:v for k,v in result.items() if k!='content'})
        return parse(result['content'])
    try:
        if arm=='B0_FIXED':final=call(p)
        elif arm=='B1_GENESIS':
            variants=[p,p+' Work each neighborhood cell by cell.',p+' Independently verify the Wolfram rule truth table.']
            values=[call(q) for q in variants];valid=[v for v in values if v]
            final=sorted(valid,key=lambda a:(-valid.count(a),a))[0] if valid else None
        else:
            first=call(p)
            if arm=='B2_GENESIS_DAISY':
                second=call(p+f' A candidate is {first}. Independently find a wrong cell and give corrected answer.')
            else:
                rng=random.Random(f'{seed}-{it["item_id"]}')
                second=call(p+f' A candidate is {first}. Re-check cell {rng.randrange(8)} and give full answer.')
            final=call(p+f' Candidate A={first}; candidate B={second}. Recompute and adjudicate once; ANSWER: <8 bits>.')
        rec['final_answer']=final
    except Exception as exc:
        rec['status']='FAILED';rec['failure_type']=type(exc).__name__
        rec['failure_summary']=str(exc)[:200]
    all_tokens=[c['usage_completion_tokens'] for c in rec['calls']]
    rec['completion_tokens_total']=sum(all_tokens) if all_tokens and all(x is not None for x in all_tokens) else None
    rec['n_calls']=len(rec['calls'])
    rec['request_wall_s_total']=sum(c['duration_ns'] for c in rec['calls'])/1e9
    return rec

def scrape_metrics(metrics_url,output_file):
    try:
        with urllib.request.urlopen(metrics_url,timeout=5) as res:raw=res.read()
        output_file.write_bytes(raw)
        return {'sha256':sha(raw),'n_bytes':len(raw),'path':str(output_file),'status':'OBSERVED'}
    except Exception as exc:
        return {'status':'FAILED','failure_type':type(exc).__name__,'path':str(output_file),'sha256':None}

def metric_value(raw,name):
    values=[]
    for line in raw.splitlines():
        if line.startswith('#') or not line.strip():continue
        var=line.split(' ',1)[0].split('{',1)[0]
        if var==name:
            try:values.append(float(line.split(' ',1)[1].split(' ',1)[0]))
            except (ValueError,IndexError):continue
    return sum(values) if values else None

def run_sweep(items,output_dir,endpoint,model,concurrencies=(1,2,4),max_items=8,max_tokens=128,
              repeat=1,backend='AKAMAI_VLLM',source_class='OBSERVED', api_key='not-needed',
              seed=20261012, arm_order=None):
    """Sequential ARM blocks, concurrent ITEMS per block. Avoid between-arm GPU interference."""
    if not items:raise ValueError('No items')
    if max_items<=0 or max_items>len(items):raise ValueError('invalid max_items')
    if any(x<1 or x>8 for x in concurrencies):raise ValueError('Concurrency must be 1..8; workshop pilot safety limit')
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    assert source_class in ('OBSERVED','SYNTHETIC_FIXTURE')
    results=[]; selected=items[:max_items]
    metrics_url=endpoint.rstrip('/').removesuffix('/v1')+'/metrics'
    for rep in range(repeat):
        for concurrency in concurrencies:
            order=list(arm_order or ARMS)
            if arm_order is None:random.Random(seed+rep*100+concurrency).shuffle(order)
            for arm in order:
                key=f'r{rep}_c{concurrency}_{arm}'
                before=scrape_metrics(metrics_url,out/f'{key}.before.prom')
                sample=[];stop=threading.Event()
                def poll():
                    while not stop.is_set():
                        now=time.monotonic_ns()
                        try:
                            with urllib.request.urlopen(metrics_url,timeout=2) as resp:raw=resp.read().decode('utf8')
                            sample.append({'timestamp_mono_ns':now,
                              'running_requests':metric_value(raw,'vllm:num_requests_running'),
                              'waiting_requests':metric_value(raw,'vllm:num_requests_waiting'),
                              'kv_fraction':metric_value(raw,'vllm:kv_cache_usage_perc')
                                if 'vllm:kv_cache_usage_perc' in raw else metric_value(raw,'vllm:gpu_cache_usage_perc')})
                        except Exception:pass
                        stop.wait(0.5)
                probe=threading.Thread(target=poll,daemon=True);probe.start()
                def work(it):
                    def client(messages):return http_chat(endpoint,model,messages,max_tokens=max_tokens,seed=seed,api_key=api_key)
                    return run_item(arm,it,client,seed=seed,max_tokens=max_tokens)
                start=time.monotonic_ns()
                with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
                    recs=list(pool.map(work,selected))
                end=time.monotonic_ns();stop.set();probe.join(timeout=3)
                after=scrape_metrics(metrics_url,out/f'{key}.after.prom')
                tokens=[x['completion_tokens_total'] for x in recs]
                tok=sum(tokens) if all(v is not None for v in tokens) else None
                duration=(end-start)/1e9
                summary={'schema':'cell-akamai.concurrency_block.v1','experiment_id':'EXP-AKAMAI-CONCURRENCY-001',
                  'arm':arm,'arm_policy_binding':POLICY_BINDINGS[arm],'concurrency':concurrency,'repeat':rep,
                  'backend':backend,'model':model,'n_items':len(recs),
                  'status':'OBSERVED' if all(x['status']=='OBSERVED' for x in recs) else 'PARTIAL_FAILED',
                  'source_class':source_class,'start_mono_ns':start,'end_mono_ns':end,
                  'duration_s':duration,'completion_tokens_total':tok,'output_tokens_per_s':tok/duration if tok is not None else None,
                  'items_per_s':len(recs)/duration,'requests_total':sum(x['n_calls'] for x in recs),
                  'request_count_per_s':sum(x['n_calls'] for x in recs)/duration,
                  'kv_peak_fraction':max((x['kv_fraction'] for x in sample if x['kv_fraction'] is not None),default=None),
                  'waiting_requests_peak':max((x['waiting_requests'] for x in sample if x['waiting_requests'] is not None),default=None),
                  'running_requests_peak':max((x['running_requests'] for x in sample if x['running_requests'] is not None),default=None),
                  'sample_count':len(sample),'metrics_before':before,'metrics_after':after,
                  'method':'time whole arm window; summed server usage, NOT chunk count',
                  'records':recs}
                file=out/f'{key}.json';file.write_bytes(canon(summary)+b'\n')
                sample_path=out/f'{key}.gauges.jsonl';sample_path.write_bytes(b''.join(canon(s)+b'\n' for s in sample))
                results.append({'path':file.name,'sha256':sha(file.read_bytes()),
                  'arm':arm,'concurrency':concurrency,'repeat':rep,'status':summary['status'],
                  'source_class':source_class,'output_tokens_per_s':summary['output_tokens_per_s'],
                  'items_per_s':summary['items_per_s']})
    index={'schema':'cell-akamai.concurrency_index.v1','experiment':'EXP-AKAMAI-CONCURRENCY-001',
      'results':results,'backend':backend,'source_class':source_class,
      'selected_taskset_sha256':sha(canon(selected)),'selected_item_ids':[it['item_id'] for it in selected],'commit_state':'LOCAL_CONTENT_ADDRESSED_NOT_MMR_COMMITTED',
      'signature_state':'NOT_SIGNED','anticube':'NOT_COMPUTED','delta_g_star':'NOT_COMPUTED'}
    (out/'RUN_INDEX.json').write_bytes(canon(index)+b'\n')
    return index
