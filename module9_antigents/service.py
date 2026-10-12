"""Opt-in, namespaced HTTP Strands agent/antigent for Akamai workshop Module 9.

Read-only and tool-free by default; never includes or accesses held-out oracle.
No persistent sessions, no mutable tools, no background self-training.
"""
from __future__ import annotations
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import BoundedSemaphore
from .bridge import make_chat

ROLE_INSTRUCTIONS = {
 'actor': 'You are an agentic scientific reasoner. Solve the user request without fabricating observations. When asked for elementary cellular automata, end with ANSWER: followed by exactly 8 bits, or ANSWER: ABSTAIN.',
 'antigent': 'You are an antigentic independent challenger. Given a task and candidate, identify a concrete possible flaw and, if possible, suggest a corrected solution. You have NO oracle, no ground truth and no training privileges. End with ANSWER: followed by 8 bits or ANSWER: ABSTAIN for ECA.',
 'random_control': 'You are an uninformative control challenger. Restate the given task answer without claiming external validation. End with ANSWER: followed by 8 bits or ANSWER: ABSTAIN for ECA.',
 'adjudicator': 'You are an adjudicating agent. Review two provided candidates, independently check their reasoning without an oracle, and decide. End with ANSWER: followed by 8 bits or ANSWER: ABSTAIN for ECA.'
}
MAX_BODY=16384

def validate_request(obj):
    if not isinstance(obj,dict) or obj.get('role') not in ROLE_INSTRUCTIONS:
        raise ValueError('role must be actor, antigent, random_control, adjudicator')
    prompt=obj.get('prompt')
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>4096:
        raise ValueError('prompt must be 1..4096 characters')
    candidate=obj.get('candidate','')
    if not isinstance(candidate,str) or len(candidate)>256:
        raise ValueError('candidate must be at most 256 characters')
    if obj['role'] in ('antigent','adjudicator','random_control') and not candidate:
        raise ValueError('challenger/adjudicator requires candidate text')
    return obj['role'],prompt,candidate

def serve(host='0.0.0.0',port=8090,*, chat_factory=make_chat):
    cfg={'base_url':os.environ.get('VLLM_BASE_URL','http://vllm:8000/v1'),
         'model':os.environ.get('MODEL_NAME',''),
         'max_tokens_per_call':int(os.environ.get('MAX_TOKENS_PER_CALL','128')),
         'temperature':0, 'api_key_env':'VLLM_API_KEY'}
    if not cfg['model'] or cfg['model'].startswith('SET_'):
        raise ValueError('MODEL_NAME must match the verified /v1/models ID')
    max_parallel=int(os.environ.get('MAX_PARALLEL_ANTIGENTS','6'))
    if max_parallel<1 or max_parallel>16:
        raise ValueError('MAX_PARALLEL_ANTIGENTS must be in 1..16')
    bound=BoundedSemaphore(max_parallel)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,fmt,*args):
            # Do not log prompts, candidates, replies, or source IPs by default.
            return
        def respond(self,status,payload):
            body=json.dumps(payload,sort_keys=True).encode()
            self.send_response(status)
            self.send_header('Content-Type','application/json')
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers();self.wfile.write(body)
        def do_GET(self):
            if self.path=='/health': self.respond(200,{'status':'READY','role_model':'STRANDS_AGENT','model':cfg['model']})
            else: self.respond(404,{'error':'NOT_FOUND'})
        def do_POST(self):
            if self.path!='/invoke': return self.respond(404,{'error':'NOT_FOUND'})
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 0<n<=MAX_BODY: return self.respond(413,{'error':'BAD_LENGTH'})
                req=json.loads(self.rfile.read(n))
                role,prompt,candidate=validate_request(req)
            except (ValueError,TypeError,UnicodeDecodeError,json.JSONDecodeError):
                return self.respond(400,{'error':'INVALID_REQUEST'})
            if not bound.acquire(blocking=False): return self.respond(429,{'error':'CONCURRENCY_CAP'})
            try:
                chat=chat_factory(cfg,allow_contract_tool=False)
                user=prompt if role=='actor' else f'Task:\n{prompt}\nCandidate:\n{candidate}'
                output,tokens,wall=chat([{'role':'system','content':ROLE_INSTRUCTIONS[role]},
                                         {'role':'user','content':user}])
                self.respond(200,{'role':role,'answer':output,'completion_tokens':tokens,
                                  'wall_s':wall,'usage_state':'OBSERVED' if tokens is not None else 'UNKNOWN',
                                  'model':cfg['model'],'training_state':'NOT_EXECUTED'})
            except Exception as exc:
                self.respond(502,{'error':'BACKEND_FAILURE','type':type(exc).__name__})
            finally: bound.release()
    server=ThreadingHTTPServer((host,port),Handler)
    print(f'Module9 antigent service listening on {host}:{port}',flush=True)
    server.serve_forever()

if __name__=='__main__':
    serve(port=int(os.environ.get('PORT','8090')))
