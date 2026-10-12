"""Local synthetic fixture endpoint for notebook smoke execution ONLY.
Never use its results as a genuine inference or Genesis/DAISY claim.
"""
from __future__ import annotations
import json,re,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

def predict(message):
    p=' '.join(m.get('content','') for m in message)
    rule=int(re.search(r'RULE:\s*(\d+)',p).group(1));bits=[int(x) for x in re.search(r'STATE:\s*([01]{8})',p).group(1)];n=len(bits)
    return ''.join(str((rule >> (bits[(i-1)%n]*4+bits[i]*2+bits[(i+1)%n]))&1) for i in range(n))
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path!='/v1/chat/completions':self.send_error(404);return
        n=int(self.headers.get('Content-Length','0'));p=json.loads(self.rfile.read(n));result=predict(p['messages']);output='ANSWER: '+result
        obj={'id':'MOCK_FIXTURE_ONLY','choices':[{'message':{'content':output}}],
             'usage':{'completion_tokens':12,'prompt_tokens':60,'total_tokens':72}}
        body=json.dumps(obj).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if self.path=='/metrics':
            body=(b'# TYPE vllm:kv_cache_usage_perc gauge\nvllm:kv_cache_usage_perc 0.12\n'
               b'vllm:num_requests_running 0\nvllm:num_requests_waiting 0\n')
            self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        elif self.path=='/v1/models':
            body=json.dumps({'data':[{'id':'MOCK_ECA_FIXTURE'}]}).encode();self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        else:self.send_error(404)
    def log_message(self,*args):pass

def start():
    host=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=host.serve_forever,daemon=True);thread.start()
    return host,f'http://127.0.0.1:{host.server_address[1]}/v1'
