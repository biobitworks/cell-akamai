#!/usr/bin/env python3
"""Loopback aggregate dashboard retaining last valid atomic snapshot."""
import argparse,json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from datetime import datetime,timezone
FIELDS=('state','provisional','elapsed_measured_s','target_s','concurrency','requests','successful_requests','failures','failure_count','failure_percent','output_tokens_per_s','input_tokens_per_s','requests_per_s','latency_p50_ms','latency_p95_ms','latency_p99_ms','ttft_ms','inter_token_latency_ms','decode_tokens_per_s','units','run_id','checkpoint_id','reason','source_commit','config_sha256','dataset_hashes','checked_at_utc','answer_ledger_sha256','NEXT_ACTION','completed_cells','expected_cells','verified_remote_sha')
class Snapshot:
 def __init__(self):self.last={'state':'PENDING','provisional':True}
 def read(self,path):
  try:
   obj=json.loads(Path(path).read_text())
   if not isinstance(obj,dict) or not isinstance(obj.get('checkpoint_id'),int):raise ValueError('Invalid checkpoint')
   self.last={k:obj[k] for k in FIELDS if k in obj};self.last['last_successful_refresh_utc']=datetime.now(timezone.utc).isoformat()
  except (OSError,ValueError,TypeError):pass
  return self.last
HTML='''<!doctype html><meta charset="utf-8"><title>CELL-AKAMAI live evidence</title><style>body{background:#101b2c;color:#d8e8ef;font:18px system-ui;margin:40px}pre{white-space:pre-wrap}strong{color:#82dec6}</style><h1>CELL-AKAMAI · Live evaluation</h1><strong>PROVISIONAL · incomplete runs are not final results</strong><p>Output/input: tokens/s · latency: ms · concurrency: sessions · duration: s</p><pre id="data">Loading verified aggregate snapshot…</pre><script>async function refresh(){try{let r=await fetch('/data.json',{cache:'no-store'});document.getElementById('data').textContent=JSON.stringify(await r.json(),null,2)}catch(e){}}refresh();setInterval(refresh,4000)</script>'''
def serve(path,port):
 snapshot=Snapshot()
 class Handler(BaseHTTPRequestHandler):
  def do_GET(self):
   if self.path=='/':body=HTML.encode();typ='text/html'
   elif self.path=='/data.json':body=json.dumps(snapshot.read(path)).encode();typ='application/json'
   else:self.send_error(404);return
   self.send_response(200);self.send_header('Content-Type',typ);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
 ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--snapshot',default='evidence/hour_scale/latest.json');p.add_argument('--port',type=int,default=8767);a=p.parse_args();serve(a.snapshot,a.port)
