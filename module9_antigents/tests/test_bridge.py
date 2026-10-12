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

def test_failed_agent_preserves_sdk_usage_and_partial_hash():
    import hashlib
    calls=[]; logs=[]
    class FailingAgent:
        event_loop_metrics=SimpleNamespace(accumulated_usage={'inputTokens':11,'outputTokens':32,'totalTokens':43})
        messages=[{'role':'assistant','content':[{'text':'partial answer'}]}]
        def __call__(self, prompt):
            raise RuntimeError('bounded response stopped')
    def factory(cfg, sys, role, allow_tool):
        calls.append((role,allow_tool))
        return FailingAgent()
    chat=make_chat(CFG, agent_factory=factory, trace_sink=logs.append)
    msg=[{'role':'system','content':'task'}, {'role':'user','content':'state?'}]
    with pytest.raises(RuntimeError) as err:
        chat(msg)
    assert err.value.strands_accumulated_usage == {'inputTokens':11,'outputTokens':32,'totalTokens':43}
    assert logs[0]['completion_tokens'] == 32
    assert logs[0]['accumulated_usage'] == err.value.strands_accumulated_usage
    assert logs[0]['output_sha256'] == hashlib.sha256(b'partial answer').hexdigest()
    assert logs[0]['failure_type'] == 'RuntimeError'

def test_real_openai_model_request_shape_offline():
    pytest.importorskip('strands.models.openai')
    from module9_antigents.bridge import default_agent_factory
    cfg={**CFG,'extra_body':{'chat_template_kwargs':{'enable_thinking':False}}}
    agent=default_agent_factory(cfg,'system','actor',False)
    model=agent.model
    message=[{'role':'user','content':[{'text':'Say hello.'}]}]
    request=model.format_request(message,None,system_prompt='system')
    assert 'tools' not in request
    assert request['extra_body']==cfg['extra_body']
    assert request['max_tokens']==CFG['max_tokens_per_call']
    assert model.client_args['max_retries']==0

def test_config_rejects_missing_bound():
    with pytest.raises(ValueError): make_chat({'base_url': CFG['base_url'],'model':CFG['model']})
