#!/usr/bin/env python3
"""Akamai Module 9: Strands actor/antigent vs workshop-compatible plain client.

Imports Claude's unmodified B0-B3 policy and the PR #7 concurrency helpers.
Commits answers prior to Claude's independent score_lane_b.py. No oracle here.
DEFAULT: preview, zero endpoint calls.  Never mark fixture responses observed.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import uuid
from urllib.parse import urlparse

from module9_antigents.bridge import make_chat

ARMS = ('B0_FIXED','B1_GENESIS','B2_GENESIS_DAISY','B3_RANDOM_CONTROL')

def load_module(path: Path, name: str):
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def build_plan(args):
    helper = load_module(Path(args.concurrency_helper), 'module9_existing_concurrency')
    claude = helper.load_claude(Path(args.harness))
    raw = Path(args.dataset).read_bytes()
    manifest = json.loads(Path(args.manifest).read_text())
    if helper.sha(raw) != manifest['sha256']:
        raise ValueError('Frozen dataset digest mismatch')
    cfg_raw = Path(args.config).read_bytes()
    cfg = json.loads(cfg_raw)
    items = helper.parse_items(raw, args.limit_items)
    if len(set(args.levels)) != len(args.levels) or any(c < 1 or c > 8 for c in args.levels):
        raise ValueError('Concurrency levels must be unique and within 1..8 for Module 9 pilot')
    calls = len(items) * 10 * len(args.levels)
    if calls > args.max_calls:
        raise ValueError(f'Planned {calls} calls exceeds capped {args.max_calls}')
    endpoint = urlparse(cfg.get('base_url',''))
    if endpoint.scheme not in ('http','https') or not endpoint.hostname:
        raise ValueError('Missing actual endpoint')
    if not cfg.get('model') or 'SET_ME' in cfg['model']:
        raise ValueError('Model ID not pinned')
    if args.allow_contract_tool and args.runtime != 'strands':
        raise ValueError('Contract tool requires Strands')
    plan = {'module':'09', 'policy_arms':list(ARMS), 'runtime':args.runtime,
            'concurrency_levels':args.levels, 'items_per_arm':len(items),
            'planned_max_model_calls':calls, 'dataset_sha256':helper.sha(raw),
            'config_sha256':helper.sha(cfg_raw), 'model':cfg['model'],
            'endpoint_host':endpoint.hostname, 'mode':'EXECUTE' if args.execute else 'PREVIEW',
            'evaluation':'PILOT_NONCONFIRMATORY', 'source_class':'NOT_TESTED',
            'antigentic_weight_updates':'NOT_EXECUTED', 'anticube':'NOT_COMPUTED',
            'delta_g_star':'NOT_COMPUTED','project_mmr':'NOT_COMMITTED',
            'strand_contract_tool_enabled':args.allow_contract_tool,
            'tool_budget_comparable':not args.allow_contract_tool,
            'source_claude_harness_sha256':helper.sha(Path(args.harness).read_bytes()),
            'source_concurrency_helper_sha256':helper.sha(Path(args.concurrency_helper).read_bytes())}
    return helper, claude, items, cfg, plan

def main(argv=None, chat_override=None):
    ap = argparse.ArgumentParser()
    for name in ('dataset','manifest','config','harness','concurrency-helper'):
        ap.add_argument('--'+name, required=True)
    ap.add_argument('--runtime',choices=['plain','strands'], default='strands')
    ap.add_argument('--levels',nargs='+',type=int, default=[1,2,4,8])
    ap.add_argument('--limit-items',type=int,default=8)
    ap.add_argument('--max-calls',type=int,default=500)
    ap.add_argument('--output-root', default='runs/module9')
    ap.add_argument('--allow-contract-tool',action='store_true',help='Module 9 tool-use demonstration only, not parity benchmark')
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args(argv)
    helper, claude, items, cfg, plan = build_plan(args)
    if not args.execute:
        print(json.dumps(plan, indent=2))
        return plan
    run_id = 'module09-' + args.runtime + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    folder = Path(args.output_root) / run_id
    folder.mkdir(parents=True, exist_ok=False)
    os.chmod(folder, 0o700)
    injected_fixture = chat_override is not None
    cfg_runtime = dict(cfg)
    cfg_runtime['api_key_env_value'] = os.environ.get(cfg.get('api_key_env','VLLM_API_KEY'), 'not-needed')
    raw_trace_path = folder/'role_traces.jsonl'
    def trace(event):
        # Trace lines contain only hashes and numeric diagnostics; no replies.
        with raw_trace_path.open('a') as f: f.write(json.dumps(event, sort_keys=True)+'\n')
    chat = chat_override or (make_chat(cfg_runtime,trace_sink=trace,allow_contract_tool=args.allow_contract_tool)
                             if args.runtime=='strands' else claude.make_chat(cfg_runtime))
    plan.update({'run_id':run_id,'state':'IN_PROGRESS','source_class':'SYNTHETIC_FIXTURE' if injected_fixture else 'OBSERVED_ENDPOINT_ATTEMPT',
                 'model_revision':'UNKNOWN','actual_precision':'UNKNOWN',
                 'workshop_source_sha':'454b43269216c1f92dd8d7e2711649e38cb888cb',
                 'receipt_signing':'NOT_SIGNED','independent_oracle_score':'NOT_TESTED'})
    helper.write_json(folder/'run_manifest.json',plan)
    try:
        summary=[]
        for c in args.levels:
            all_records=[]
            for arm in ARMS:
                records, stats=helper.run_batch(items,c,arm,claude,chat,cfg_runtime,cfg.get('decode_seed',0))
                all_records.extend(records)
                stats['runtime']=args.runtime
                stats['module']='09'
                stats['source_class']='SYNTHETIC_FIXTURE' if injected_fixture else 'OBSERVED_ENDPOINT_ATTEMPT'
                stats['tool_enabled']=args.allow_contract_tool
                summary.append(stats)
                helper.write_json(folder/'bench_cells.json', {'run_id':run_id,'status':'IN_PROGRESS','rows':summary})
            # Answers are committed before independent scorer reads them, with complete paired arms.
            panel=folder/f'c{c:02d}_paired_for_scoring'
            panel.mkdir()
            ordered=sorted(all_records,key=lambda r:(r['arm'],r['item_id']))
            (panel/'answers.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in ordered))
            (panel/'items.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in items))
            digest=hashlib.sha256((panel/'answers.jsonl').read_bytes()).hexdigest()
            helper.write_json(panel/'COMMIT.json', {'answers_sha256':digest,
                'config_sha256':hashlib.sha256(Path(args.config).read_bytes()).hexdigest(),
                'dataset_sha256':plan['dataset_sha256'],
                'genesis_policy':getattr(claude,'GENESIS_POLICY','UNKNOWN'),
                'oracle_accessed':False,'source_class':plan['source_class'],'runtime':args.runtime,
                'model':cfg['model'],'module':'09'})
        helper.write_json(folder/'bench_cells.json',{'run_id':run_id,'status':'COMPLETED_WITH_RECEIPTS', 'rows':summary})
        plan['state']='COMPLETED_WITH_RECEIPTS'
    except BaseException as exc:
        plan['state']='FAILED'
        plan['error_type']=type(exc).__name__
        raise
    finally:
        helper.write_json(folder/'run_manifest.json',plan)
    print('RUN_FOLDER',folder)
    return folder

if __name__=='__main__':
    main()
