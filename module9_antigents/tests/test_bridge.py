"""Fixture-only bridge unit tests, no GPU inference or SDK installation required."""
from types import SimpleNamespace
import pytest
from module9_antigents.bridge import make_chat, role_for, token_usage, response_text

CFG = {'base_url':'http://vllm:8000/v1', 'model':'Qwen/Qwen3-4B',
       'max_tokens_per_call':64, 'temperature':0}

def test_role_classification():
    system = {'role':'system','content':'Test'}
    def role(prompt): return role_for([system, {'role':'user','content':prompt}])
    assert role('ECA state bits') == 'actor'
    assert role('A candidate answer is 00000000. Independently find any cell that is wrong') == 'antigent_challenger'
    assert role('A candidate answer is 00000000. Please re-check cell 2') == 'random_control_challenger'
    assert role('Two candidate answers: A=0, B=1') == 'adjudicator'
    with pytest.raises(ValueError): role_for([system])

def test_metrics_fail_closed():
    assert token_usage(SimpleNamespace(metrics=SimpleNamespace(accumulated_usage={'outputTokens':27}))) == 27
    assert token_usage(SimpleNamespace(metrics=SimpleNamespace(accumulated_usage={'outputTokens':True}))) is None
    assert token_usage(SimpleNamespace(metrics=SimpleNamespace(accumulated_usage={}))) is None
    assert token_usage(SimpleNamespace()) is None

def test_response_is_text_only():
    assert response_text(SimpleNamespace(message={'content':[{'text':'ANSWER: '},{'text':'01010101'}]})) == 'ANSWER: 01010101'
    with pytest.raises(ValueError): response_text(SimpleNamespace(message={'content':[{'toolUse':'x'}]}))

def test_fresh_agent_and_trace():
    calls=[]; logs=[]
    def factory(cfg, sys, role, allow_tool):
        calls.append((cfg['model'],sys,role,allow_tool))
        return lambda prompt: SimpleNamespace(message={'content':[{'text':'ANSWER: 01010101'}]},
           metrics=SimpleNamespace(accumulated_usage={'outputTokens':9}))
    chat=make_chat(CFG, agent_factory=factory, trace_sink=logs.append)
    msg=[{'role':'system','content':'task'}, {'role':'user','content':'state?'}]
    out1=chat(msg); out2=chat(msg)
    assert out1[0]=='ANSWER: 01010101' and out2[1]==9
    assert len(calls)==2 and len(logs)==2
    assert 'input_sha256' in logs[0] and 'ANSWER:' not in str(logs)
    assert logs[0]['tool_enabled'] is False

def test_config_rejects_missing_bound():
    with pytest.raises(ValueError): make_chat({'base_url': CFG['base_url'],'model':CFG['model']})
