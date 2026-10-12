import hashlib,json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cell_akamai_handoff as h

def test_pilot_bytes():
 assert hashlib.sha256((h.ROOT/'data'/'eca_pilot_inputs_v1.jsonl').read_bytes()).hexdigest()==h.ECA_SHA
 assert len(h.eca_dataset())==32

def test_oracle_rule90():
 i={'rule':90,'initial_state':[0,0,0,1,0,0,0,0]}
 assert h.eca_truth(i)=='00101000'

def test_parser():
 assert h.parse_answer('foo ANSWER: 01010101')=='01010101'
 assert h.parse_answer('ANSWER: ABSTAIN')=='ABSTAIN'
 assert h.parse_answer('nonsense') is None

def test_one_flag():
 b=['--model=Qwen/Qwen3-4B','--max-num-seqs=32','--max-model-len=8192']
 a=h.expected_tune(b,64)
 assert a==['--model=Qwen/Qwen3-4B','--max-num-seqs=64','--max-model-len=8192']
 try:h.expected_tune(b,32)
 except ValueError:pass
 else:assert False

def test_metric_parse_and_counts():
 s='vllm:generation_tokens_total{model="a"} 50\nvllm:generation_tokens_total{model="b"} 10\n#HELP ignored\nvllm:num_requests_waiting 3\n'
 p=h.metric_parse(s)
 assert p['vllm:generation_tokens_total']==60
 assert p['vllm:num_requests_waiting']==3

def test_mcnemar():
 assert h.mcnemar(0,0)==1
 assert h.mcnemar(5,0)==.0625

def test_scoring_refuses_tamper(tmp_path):
 d=tmp_path/'run';d.mkdir();(d/'answers.jsonl').write_text('{}\n');(d/'items.jsonl').write_text('');(d/'config.json').write_text('{}')
 h.write_json(d/'COMMIT.json',{'answers_sha256':'0'*64,'items_sha256':'0'*64,'config_sha256':'0'*64})
 try:h.score_eca(d)
 except ValueError as e:assert 'HASH MISMATCH' in str(e)
 else:assert False

def test_fake_end_to_end_scoring_and_quality(tmp_path,monkeypatch):
 """Synthetic fixture only; no inference endpoint or GPU touched."""
 import re
 monkeypatch.setattr(h,'RUNS',tmp_path)
 def fake(env,prompt,max_tokens=96):
  m=re.search(r'Wolfram rule (\d+).*?Current state \(index 0\.\.7\): ([01]{8})',prompt)
  if m:
   item={'rule':int(m.group(1)),'initial_state':[int(x) for x in m.group(2)]}
   answer=h.eca_truth(item)
  else:answer='01010101'
  return dict(ok=True,completion_tokens=16,prompt_tokens=48,text='ANSWER: '+answer,wall_s=.04,finish_reason='stop')
 monkeypatch.setattr(h,'infer',fake)
 monkeypatch.setattr(h,'deployment',lambda ns:{'args':['--max-num-seqs=32','--model=Qwen/Qwen3-4B'],'image':'vllm-test'})
 env=dict(served_model='Qwen/Qwen3-4B',namespace='fixture',base_url='http://fixture/v1')
 q=h.quality_epoch(env,'syntheticfixture',n_items=8)
 s=h.score_quality(q)
 assert s['exact_match_count']==8 and s['completion_tokens_total']==128
 p=h.run_eca(env,n_items=8)
 score=h.score_eca(p)
 assert score['sample_size']==8 and all(z['correct']==8 for z in score['evaluation'])
 assert (p/'COMMIT.json').is_file()
 # Do not allow cherry-picked row drops to masquerade as a full panel even if an attacker rehashes.
 rows=(p/'answers.jsonl').read_text().splitlines()
 (p/'answers.jsonl').write_text('\n'.join(rows[:-1])+'\n')
 commit=h.read_json(p/'COMMIT.json');commit['answers_sha256']=h.digest_bytes((p/'answers.jsonl').read_bytes());h.write_json(p/'COMMIT.json',commit)
 try:h.score_eca(p)
 except ValueError as e:assert 'panel' in str(e)
 else:assert False
