"""Actual HTTP/SSE plumbing through a SYNTHETIC_FIXTURE test server.
Nothing produced by this test is an Akamai observation.
"""
from __future__ import annotations
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from cell_akamai.collect import collect_experiment
from cell_akamai.dashboard import write_dashboard
from cell_akamai.replay import verify_run


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/metrics":
            payload = b'vllm:kv_cache_usage_perc{model_name="test/model"} 0.25\nvllm:num_requests_running{model_name="test/model"} 1\n'
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == "/v1/models":
            self._json({"object":"list","data":[{"id":"test/model","object":"model","created":0,"owned_by":"test"}]})
        else:
            self.send_error(404)

    def _json(self, payload):
        b=json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        n=int(self.headers.get("Content-Length","0"))
        self.rfile.read(n)
        self.send_response(200)
        self.send_header("Content-Type","text/event-stream")
        self.end_headers()
        chunks=[
            {"id":"fake-1","object":"chat.completion.chunk","created":0,"model":"test/model","choices":[{"index":0,"delta":{"role":"assistant","content":"A "},"finish_reason":None}]},
            {"id":"fake-1","object":"chat.completion.chunk","created":0,"model":"test/model","choices":[{"index":0,"delta":{"content":"B"},"finish_reason":"stop"}]},
            {"id":"fake-1","object":"chat.completion.chunk","created":0,"model":"test/model","choices":[],"usage":{"prompt_tokens":5,"completion_tokens":2,"total_tokens":7}}
        ]
        for c in chunks:
            self.wfile.write(f"data: {json.dumps(c)}\n\n".encode())
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def test_synthetic_fake_server_and_tamper_detection(tmp_path):
    # Install a tiny synthetic SDK-shaped HTTP/SSE adapter for this offline test.
    # The hosted notebook uses the real OpenAI SDK, never this fixture adapter.
    import sys
    import types
    import urllib.request
    import contextlib

    def to_obj(d):
        if isinstance(d, dict): return types.SimpleNamespace(**{k: to_obj(v) for k,v in d.items()})
        if isinstance(d, list): return [to_obj(v) for v in d]
        return d

    class FakeOpenAI:
        def __init__(self, base_url, api_key, timeout): self.base_url = base_url
        @property
        def chat(self): return types.SimpleNamespace(completions=types.SimpleNamespace(create=self.create))
        def create(self, **kwargs):
            def generator():
                req=urllib.request.Request(self.base_url+'/chat/completions', data=json.dumps(kwargs).encode(), headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req, timeout=3) as reply:
                    for line in reply:
                        if line.startswith(b'data: '):
                            part=line[len(b'data: '):].strip()
                            if part != b'[DONE]': yield to_obj(json.loads(part))
            return generator()

    fake_sdk=types.ModuleType('openai')
    fake_sdk.OpenAI=FakeOpenAI
    former_sdk=sys.modules.get('openai')
    sys.modules['openai']=fake_sdk
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    worker=threading.Thread(target=server.serve_forever,daemon=True)
    worker.start()
    try:
        folder=collect_experiment(base_url=f"http://127.0.0.1:{server.server_port}/v1", model="test/model",
                                  prompt="synthetic", run_count=2, output_root=tmp_path/"runs",
                                  max_tokens=16, metric_interval_s=3,
                                  source_class="SYNTHETIC_FIXTURE")
        assert verify_run(folder)["status"] == "PASS"
        obs=[json.loads(x) for x in (folder/"inference_observations.jsonl").read_text().splitlines()]
        assert len(obs)==2
        assert all(x["source_class"]=="SYNTHETIC_FIXTURE" for x in obs)
        assert all(x["completion_tokens"]==2 for x in obs)
        dash=write_dashboard(tmp_path/"runs", output=tmp_path/"dashboard.html")
        assert dash.exists() and "SYNTHETIC_FIXTURE" in dash.read_text()
        # Byte tampering must be noticed even when values still parse.
        with (folder/"inference_observations.jsonl").open("ab") as f:
            f.write(b"\n")
        assert verify_run(folder)["status"]=="FAILED"
    finally:
        server.shutdown()
        server.server_close()
        if former_sdk is None: sys.modules.pop('openai',None)
        else: sys.modules['openai']=former_sdk
