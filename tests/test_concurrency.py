import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools' / 'concurrency' / 'run_concurrency.py'
spec = importlib.util.spec_from_file_location('run_concurrency', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_dataset_digest_balanced_no_labels():
    data = (ROOT / 'dataset/eca_pilot_inputs_v1.jsonl').read_bytes()
    manifest = json.loads((ROOT / 'dataset/eca_pilot_manifest_v1.json').read_text())
    assert m.sha(data) == manifest['sha256']
    a = m.parse_items(data, 8)
    assert [r['rule'] for r in a] == [30, 90, 110, 184] * 2
    assert len({r['item_id'] for r in a}) == 8
    assert all('oracle' not in r and 'answer' not in r for r in a)


def test_preview_no_network_no_run_files(tmp_path):
    cfg = tmp_path / 'pilot.json'
    cfg.write_text(json.dumps({'model': 'PLACEHOLDER', 'base_url': 'invalid'}))
    out = tmp_path / 'raw_run'
    plan = m.main(['--dataset', str(ROOT / 'dataset/eca_pilot_inputs_v1.jsonl'),
                   '--manifest', str(ROOT / 'dataset/eca_pilot_manifest_v1.json'),
                   '--config', str(cfg), '--limit-items', '8', '--concurrency', '1', '2',
                   '--output-root', str(out)])
    assert plan['declared_max_model_calls'] == 160
    assert plan['state'] == 'PROPOSED'
    assert not out.exists()


def test_digest_tampering_rejected(tmp_path):
    cfg = tmp_path / 'pilot.json'
    cfg.write_text('{}')
    tamper = tmp_path / 'items.jsonl'
    tamper.write_bytes((ROOT / 'dataset/eca_pilot_inputs_v1.jsonl').read_bytes() + b'\n')
    with pytest.raises(ValueError, match='SHA-256'):
        m.main(['--dataset', str(tamper), '--manifest', str(ROOT / 'dataset/eca_pilot_manifest_v1.json'),
                '--config', str(cfg)])


def test_summary_fails_closed_when_usage_unknown():
    s = m.summarize([{'tokens_total': None, 'n_calls': 1, 'final_answer': '00000000',
                    'item_elapsed_s': 1.2}], 'B0_FIXED', 1, 2.5)
    assert s['aggregate_completion_tokens_per_s'] is None
    assert s['token_count_status'] == 'UNKNOWN'
    assert s['inter_request_tokens_per_s2'] is None


def test_mocked_threaded_paired_commit_and_no_oracle(tmp_path):
    fake = tmp_path / 'fake_lane_b.py'
    fake.write_text('''GENESIS_POLICY="PROXY_FIXTURE"\ndef make_chat(cfg): return None\ndef run_item(arm, it, chat, cfg):\n  n=1 if arm=="B0_FIXED" else 3\n  return {"item_id":it["item_id"],"arm":arm,"calls":[{"completion_tokens":5}]*n,"final_answer":"00000000","tokens_total":5*n,"wall_s_total":0.001,"n_calls":n,"over_budget":False}\n''')
    cfg=tmp_path/'config.json';cfg.write_text(json.dumps({'model':'fixture','base_url':'http://127.0.0.1:11434/v1','decode_seed':123}))
    run=m.main(['--dataset',str(ROOT/'dataset/eca_pilot_inputs_v1.jsonl'), '--manifest',str(ROOT/'dataset/eca_pilot_manifest_v1.json'),
       '--config',str(cfg),'--harness',str(fake),'--backend','SYNTHETIC_FIXTURE','--limit-items','4',
       '--concurrency','1','2','--output-root',str(tmp_path/'runs'),'--execute'], injected_chat=lambda *a:None)
    assert len(json.loads((run/'bench_cells.json').read_text())['rows'])==8
    for c in (1,2):
        p=run/f'c{c:02d}_paired_for_scoring'
        dat=(p/'answers.jsonl').read_bytes()
        committed=json.loads((p/'COMMIT.json').read_text())
        assert hashlib.sha256(dat).hexdigest()==committed['answers_sha256']
        assert committed['oracle_accessed'] is False
        assert len(dat.splitlines())==16
    assert json.loads((run/'run_manifest.json').read_text())['state']=='COMPLETED_WITH_RESULT_OR_FAILURE_ROWS'


def test_dashboard_aggregate_only(tmp_path):
    spec = importlib.util.spec_from_file_location('serve_dashboard', ROOT/'tools/concurrency/serve_dashboard.py')
    d = importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
    data = d.load_sanitized(tmp_path/'runs')
    assert data['rows'] == []
    assert "fetch('/data.json'" in d.HTML
    run = tmp_path/'runs'/'concurrency-01';run.mkdir(parents=True)
    (run/'run_manifest.json').write_text(json.dumps({'run_id':'myrun','module':'07','stage':'bf16','backend':'AKAMAI_VLLM','state':'COMPLETE','secret':'TOPSECRET'}))
    (run/'bench_cells.json').write_text(json.dumps({'rows':[{'arm':'B0_FIXED','concurrency':2,'aggregate_completion_tokens_per_s':19.0,'secret':'TOPSECRET'}]}))
    results=d.load_sanitized(tmp_path/'runs')
    encoded=json.dumps(results)
    assert results['rows'][0]['aggregate_completion_tokens_per_s']==19
    assert 'TOPSECRET' not in encoded
