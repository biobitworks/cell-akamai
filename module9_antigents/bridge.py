"""Optional Strands-vLLM adapter for Claude's unchanged Lane B `run_item`.

One fresh Strands agent per harness model call. No oracle or scoring tools.
The default is a tool-free parity measurement; an optional read-only contract
lookup illustrates Akamai Module 9 tool use but is NOT a parity benchmark.
"""
from __future__ import annotations
import hashlib
import os
import time
from typing import Any, Callable


def role_for(messages: list[dict]) -> str:
    if len(messages) != 2 or [m.get('role') for m in messages] != ['system', 'user']:
        raise ValueError('Expected one isolated system and user prompt per harness call')
    s = messages[1].get('content', '')
    if not isinstance(s, str):
        raise ValueError('Prompt content must be text')
    if 'Two candidate answers: A=' in s:
        return 'adjudicator'
    if 'A candidate answer is' in s and 'Independently find any cell' in s:
        return 'antigent_challenger'
    if 'A candidate answer is' in s and 'Please re-check cell' in s:
        return 'random_control_challenger'
    return 'actor'


def token_usage(result: Any) -> int | None:
    metrics = getattr(result, 'metrics', None)
    data = getattr(metrics, 'accumulated_usage', None) if metrics is not None else None
    if isinstance(data, dict):
        n = data.get('outputTokens')
        return n if type(n) is int and n >= 0 else None
    return None


def response_text(result: Any) -> str:
    message = getattr(result, 'message', None)
    if not isinstance(message, dict):
        raise ValueError('Strands did not return a structured message')
    parts = message.get('content')
    if not isinstance(parts, list):
        raise ValueError('Strands message content missing')
    texts = [p['text'] for p in parts if isinstance(p, dict) and isinstance(p.get('text'), str)]
    if not texts:
        raise ValueError('Strands has no text answer')
    return ''.join(texts)


def default_agent_factory(cfg: dict, system_prompt: str, role: str, allow_contract_tool: bool):
    try:
        from strands import Agent, tool
        from strands.models.openai import OpenAIModel
    except ImportError as e:
        raise RuntimeError("Install 'strands-agents[openai]' on the execution host") from e
    base_url = cfg['base_url'].rstrip('/')
    if not base_url.endswith('/v1'):
        raise ValueError('Use an OpenAI-compatible /v1 endpoint')
    key = os.environ.get(cfg.get('api_key_env', 'VLLM_API_KEY'), 'not-needed')
    model = OpenAIModel(client_args={'api_key': key, 'base_url': base_url}, model_id=cfg['model'],
                        params={'max_tokens': cfg['max_tokens_per_call'], 'temperature': cfg['temperature']})
    tools = []
    if allow_contract_tool:
        @tool
        def eca_task_contract() -> str:
            """Read the public ECA task syntax, NOT task answers or the oracle."""
            return 'width 8; periodic boundary; Wolfram index=4*left+2*center+right; exactly one step'
        tools = [eca_task_contract]
    return Agent(model=model, system_prompt=system_prompt, tools=tools, callback_handler=None)


def make_chat(cfg: dict, *, agent_factory: Callable | None = None,
              trace_sink: Callable[[dict], None] | None = None,
              allow_contract_tool: bool = False) -> Callable[[list[dict]], tuple[str, int | None, float]]:
    if not cfg.get('model') or not cfg.get('base_url'):
        raise ValueError('Endpoint and exact model ID are required')
    if not isinstance(cfg.get('max_tokens_per_call'), int) or cfg['max_tokens_per_call'] < 1:
        raise ValueError('Bounded per-call token cap required')
    factory = agent_factory or default_agent_factory

    def chat(messages: list[dict]) -> tuple[str, int | None, float]:
        role = role_for(messages)
        # Use a fresh agent on every call; no cross-item/session carryover.
        agent = factory(cfg, messages[0]['content'], role, allow_contract_tool)
        start = time.perf_counter()
        result = agent(messages[1]['content'])
        elapsed = time.perf_counter() - start
        output = response_text(result)
        usage = token_usage(result)
        if trace_sink:
            trace_sink({'role': role,
                        'input_sha256': hashlib.sha256(messages[1]['content'].encode()).hexdigest(),
                        'output_sha256': hashlib.sha256(output.encode()).hexdigest(),
                        'completion_tokens': usage, 'wall_s': elapsed,
                        'runtime': 'STRANDS_OPENAI_COMPATIBLE',
                        'tool_enabled': bool(allow_contract_tool)})
        return output, usage, elapsed
    return chat
