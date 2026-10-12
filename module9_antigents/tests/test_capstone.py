import json
import sys
from pathlib import Path
import pytest
from module9_antigents import run_capstone


def test_run_capstone_does_not_claim_any_results_from_preview(tmp_path):
    dataset = tmp_path/'items.jsonl'
    # Use a real deterministic row but no oracle answer.
    row={'item_id':'ECA-30-50000','rule':30,'seed':50000,'width':8,'initial_state':[0,1,1,0,1,0,1,0]}
    dataset.write_text(json.dumps(row)+'\n')
    import hashlib
    manifest=tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'sha256':'sha256:'+hashlib.sha256(dataset.read_bytes()).hexdigest()}))
    cfg=tmp_path/'config.json'
    cfg.write_text(json.dumps({'base_url':'http://vllm:8000/v1','model':'Qwen/Qwen3-4B','max_tokens_per_call':64,'temperature':0,'decode_seed':1,'item_token_cap':192,'item_call_cap':3}))
    # Fake dependency modules, only for preview/run plumbing, never GPU metrics.
    helper=tmp_path/'existing_helper.py'
    helper.write_text('''import hashlib,importlib.util,sys,json\nfrom pathlib import Path\ndef sha(x): return 'sha256:'+hashlib.sha256(x).hexdigest()\ndef load_claude(path):\n spec=importlib.util.spec_from_file_location('fake_claude',path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod\ndef parse_items(raw,limit): return [json.loads(x) for x in raw.splitlines() if x][:limit]\ndef write_json(path,value): path.write_text(json.dumps(value))\ndef run_batch(items,c,arm,claude,chat,cfg,seed):\n records=[claude.run_item(arm,it,chat,cfg) for it in items]\n return records,{'arm':arm,'concurrency':c,'items':len(records),'aggregate_completion_tokens_per_s':None}\n''')
    claude=tmp_path/'fake_claude.py'
    claude.write_text('''GENESIS_POLICY='FAKE_TEST_ONLY'\ndef run_item(arm,item,chat,cfg):\n out,tokens,wall=chat([{'role':'system','content':'test'},{'role':'user','content':item['item_id']}])\n return {'arm':arm,'item_id':item['item_id'],'final_answer':'01010101','tokens_total':tokens,'n_calls':1,'wall_s_total':wall,'over_budget':False,'calls':[]}\n''')
    cli=['--dataset',str(dataset),'--manifest',str(manifest),'--config',str(cfg),'--harness',str(claude),'--concurrency-helper',str(helper),'--limit-items','1','--levels','1','--output-root',str(tmp_path/'runs')]
    result=run_capstone.main(cli)
    assert result['mode']=='PREVIEW'
    assert result['source_class']=='NOT_TESTED'
    assert not (tmp_path/'runs').exists()
    folder=run_capstone.main(cli+['--execute'],chat_override=lambda _: ('ANSWER: 01010101',7,.01))
    panel=folder/'c01_paired_for_scoring'
    assert len((panel/'answers.jsonl').read_text().splitlines())==4
    assert json.loads((panel/'COMMIT.json').read_text())['source_class']=='SYNTHETIC_FIXTURE'
    assert json.loads((folder/'run_manifest.json').read_text())['antigentic_weight_updates']=='NOT_EXECUTED'


