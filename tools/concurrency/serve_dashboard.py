#!/usr/bin/env python3
"""Local sanitized dashboard; ONLY serves aggregate concurrency summaries, not raw answers."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HTML = '''<!DOCTYPE html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Cell-Akamai — controlled inference concurrency</title>
<style>body{background:#0b1221;color:#e4edf8;font:14px system-ui,sans-serif;margin:0}main{max-width:1100px;margin:25px auto;padding:15px}h1{font-size:25px}h2{font-size:18px}small{color:#a8bbcc}.section{border:1px solid #293c53;border-radius:12px;background:#141e31;padding:18px;margin:12px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}.metric{background:#1b2a43;padding:12px;border-radius:8px}table{width:100%;border-collapse:collapse;font-size:12px}td,th{text-align:left;padding:9px;border-bottom:1px solid #304158} .scroll{overflow:auto}svg{width:100%;height:auto;max-height:310px}strong{color:#8fe3d0}button{padding:7px;border:1px solid #345;background:#213049;color:#fff} .empty{padding:30px;text-align:center;color:#bac9d4}</style></head>
<body><main><h1>Cell-Akamai · concurrency / science inference</h1><p><a href="/evidence" style="color:#8fe3d0">Open the evidence dashboard (Akamai GPU runs, six datasets, B0–B3, Modules 8/9) →</a></p>
<p>Workshop modules 05–09 · Frozen ECA pilot · Genesis policy proxy vs DAISY challenge · Append-only receipts</p>
<div class="section"><div class="grid"><div class="metric">Dashboard ingestion <strong id="state">LOADING</strong></div><div class="metric">Validated cells <strong id="cells">—</strong></div><div class="metric">Signed/MMR <strong>NOT_SIGNED / NOT_COMMITTED</strong></div><div class="metric">Scientific improvement <strong>NOT_ESTABLISHED</strong></div></div><p><small>Imported Akamai Qwen reference receipts are separate, not concurrency or FP8/speculative results. Tokens/s uses actual endpoint usage. Streamed chunks are never tokenizer tokens. Concurrent tokens/s² is undefined here; sequential Lane A derivative is a distinct measure.</small></p></div>
<div class="section"><h2>Aggregate completion-token throughput (tokens/s) versus concurrency</h2><div id="throughput" class="empty">NOT_TESTED · No concurrent GPU receipts</div></div>
<div class="section"><h2>Item latency p95 (ms) versus concurrency</h2><div id="latency" class="empty">NOT_TESTED · No concurrent GPU receipts</div></div>
<div class="section"><h2>Backend, model stage and evaluation controls</h2><div class="scroll"><table><thead><tr><th>Run / module</th><th>Backend / stage</th><th>Arm</th><th>c</th><th>Items</th><th>Calls</th><th>Completion tok/s</th><th>Latency p95 ms</th><th>Failures</th><th>Evidence</th></tr></thead><tbody id="rows"></tbody></table></div></div>
<div class="section"><h2>Scientific comparison / negative results</h2><p>After an answer file SHA-256 commitment, Claude's independent ECA scorer can populate exact-match accuracy, Hamming error, McNemar discordance, abstentions and tokens/correct item. No run is labeled true Genesis until its policy identity is verified; DAISY antigentic challenges are not weight updates.</p><div id="science">NOT_TESTED / NOT_ADMITTED</div><p><small>Akamai vLLM configurations (BF16 / FP8 / speculative / tuned) and local Ollama models are shown in separate tables; they are not one comparison. B1 = GENESIS_POLICY_PROXY_V0 (not the recovered Genesis policy). B2 DAISY challenges are inference-time, not weight training. B0 makes 1 call per item and B1–B3 make 3, so arms are not compute-matched. Anticube and ΔG* are NOT_COMPUTED.</small></p></div>
<p><small>Read-only local server, loopback interface, serves aggregate JSON only. Raw replies, protected prompts, credentials and manifests are not exposed. TTFC differs from server TTFT; model precision must be verified from deployment metadata.</small></p>
</main><script>
const $=id=>document.getElementById(id), e=s=>String(s??'UNKNOWN').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>n===null||n===undefined||!Number.isFinite(n)?'—':n.toFixed(2);
const COLORS=['#80dace','#f8bd70','#a4b9ff','#ff92bc','#93e080','#d9aafc'];
function plot(id,rows,key,label){const xs=[...new Set(rows.map(x=>x.concurrency))].sort((a,b)=>a-b), groups=[...new Set(rows.map(x=>x.backend+'/'+x.stage+'/'+x.arm))]; if(!xs.length||!rows.some(x=>Number.isFinite(x[key]))){$(id).innerHTML='<div class="empty">NOT_TESTED — No supported '+e(label)+' data</div>';return;}const w=900,h=280,p=45,max=Math.max(1,...rows.map(r=>r[key]).filter(Number.isFinite))*1.1;let html='<svg viewBox="0 0 900 280" role="img" aria-label="'+e(label)+' by concurrency"><path stroke="#6d829b" fill="none" d="M45 15V235H865"/>'; xs.forEach((x,i)=>{let px=p+(w-2*p)*(xs.length===1?0.5:i/(xs.length-1)); html+='<text x="'+px+'" y="258" fill="#bdcbdb" text-anchor="middle" font-size="13">c='+x+'</text>'});groups.forEach((g,k)=>{let rr=rows.filter(x=>x.backend+'/'+x.stage+'/'+x.arm===g&&Number.isFinite(x[key]));if(!rr.length)return; const color=COLORS[k%COLORS.length]; const points=rr.map(r=>[p+(w-2*p)*(xs.length===1?0.5:xs.indexOf(r.concurrency)/(xs.length-1)),h-p-195*r[key]/max]); html+='<polyline fill="none" stroke="'+color+'" stroke-width="2" points="'+points.map(z=>z.join(',')).join(' ')+'"/>';points.forEach(pt=>html+='<circle r="4" fill="'+color+'" cx="'+pt[0]+'" cy="'+pt[1]+'"/>')});html+='</svg><p><small>'+groups.map((g,k)=>'<span style="color:'+COLORS[k%COLORS.length]+'">● '+e(g)+'</span>').join(' &nbsp; ')+'</small></p>';$(id).innerHTML=html;}
function science(ss){if(!ss.length){$('science').textContent='NOT_TESTED / NOT_ADMITTED';return}
const fams=[['Akamai vLLM configurations',x=>String(x.backend_family).startsWith('AKAMAI_')],['Local Ollama models',x=>/OLLAMA/.test(String(x.backend_family))],['Synthetic fixtures (plumbing only, not model performance)',x=>x.backend_family==='SYNTHETIC_FIXTURE']];
const pct=v=>Number.isFinite(v)?(100*v).toFixed(1)+'%':'—';let html='';
for(const [title,f] of fams){const runs=ss.filter(f);if(!runs.length)continue;html+='<h3>'+e(title)+'</h3><div class="scroll"><table><thead><tr><th>Run / family / model</th><th>c</th><th>Arm</th><th>Exact match</th><th>Hamming</th><th>Abstain</th><th>Calls</th><th>Tokens / correct</th><th>Source</th></tr></thead><tbody>';
for(const s of runs){for(const r of s.rows){html+='<tr><td>'+e(s.run_id)+'<br>'+e(s.backend_family)+' · '+e(s.served_model_requested)+'</td><td>'+e(r.concurrency)+'</td><td>'+e(r.arm)+'</td><td>'+pct(r.exact_match_accuracy)+' ('+e(r.correct)+'/'+e(r.n_items)+')</td><td>'+fmt(r.mean_hamming_error)+'</td><td>'+pct(r.abstention_rate)+'</td><td>'+e(r.model_calls)+'</td><td>'+fmt(r.tokens_per_correct_item)+'</td><td>'+e(r.source_class)+'</td></tr>'}
for(const p of s.panels.filter(p=>p.state!=='SCORED'))html+='<tr><td colspan="9">c='+e(p.concurrency)+' REFUSED: '+e(p.reason)+'</td></tr>'}
html+='</tbody></table></div>';const cs=runs.flatMap(s=>s.contrasts.map(c=>Object.assign({run:s.run_id},c)));
if(cs.length)html+='<div class="scroll"><table><thead><tr><th>Run</th><th>c</th><th>Contrast</th><th>A only</th><th>B only</th><th>Both right</th><th>Both wrong</th><th>McNemar p (Holm)</th></tr></thead><tbody>'+cs.map(c=>'<tr><td>'+e(c.run)+'</td><td>'+e(c.concurrency)+'</td><td>'+e(c.A)+' vs '+e(c.B)+'</td><td>'+e(c.A_only_correct)+'</td><td>'+e(c.B_only_correct)+'</td><td>'+e(c.both_correct)+'</td><td>'+e(c.both_wrong)+'</td><td>'+fmt(c.p_holm)+'</td></tr>').join('')+'</tbody></table></div>'}
$('science').innerHTML=html+'<p><small>PILOT_NONCONFIRMATORY. Exact-match is scored only after each answers.jsonl SHA-256 commitment verifies; refused panels stay listed.</small></p>'}
async function refresh(){try{const r=await fetch('/data.json',{cache:'no-store'});let data=await r.json(),rr=data.rows||[];$('state').textContent=rr.length?'LOCAL AGGREGATES':'NOT_TESTED';$('cells').textContent=String(rr.length);$('rows').innerHTML=rr.map(r=>'<tr><td>'+e(r.run_id)+' / '+e(r.module)+'</td><td>'+e(r.backend)+' / '+e(r.stage)+'</td><td>'+e(r.arm)+'</td><td>'+e(r.concurrency)+'</td><td>'+e(r.items)+'</td><td>'+e(r.model_calls_observed)+'</td><td>'+fmt(r.aggregate_completion_tokens_per_s)+'</td><td>'+fmt(r.latency_p95_ms)+'</td><td>'+e(r.failed_or_abstained_or_over_budget)+'</td><td>'+e(r.state)+'</td></tr>').join('');plot('throughput',rr,'aggregate_completion_tokens_per_s','throughput (tokens/s)');science(data.science||[]);plot('latency',rr,'latency_p95_ms','latency p95 (ms)')}catch(err){$('state').textContent='READ_FAILED'}}refresh();setInterval(refresh,4000);
</script></body></html>'''


def load_sanitized(root):
    rows = []
    if not root.is_dir():
        return {"schema":"cell_akamai.concurrent_summary.v1","rows":rows,"science":[]}
    for p in sorted(root.glob('concurrency-*/bench_cells.json')):
        try:
            o = json.loads(p.read_text())
            m = json.loads((p.parent/'run_manifest.json').read_text())
            for r in o.get('rows',[]):
                rows.append({k:r.get(k) for k in ('arm','concurrency','items','model_calls_observed','aggregate_completion_tokens_per_s',
                    'latency_p95_ms','failed_or_abstained_or_over_budget','token_count_status')}
                    | {'module':m.get('module'),'run_id':m.get('run_id'), 'backend':m.get('backend'),
                       'stage':m.get('stage'),'state':m.get('state')})
        except (OSError,ValueError,TypeError):
            continue
    science = []
    for p in sorted(root.glob('concurrency-*/lane_b_concurrency_summary.json')):
        try:
            s = json.loads(p.read_text())
            if s.get('schema') != 'cell_akamai.lane_b_concurrency_summary.v1':
                continue
            keep = ('concurrency','arm','source_class','n_items','correct','exact_match_accuracy','mean_hamming_error','abstention_rate',
                    'model_calls','tokens_per_correct_item')
            science.append({k: s.get(k) for k in ('run_id','backend_family','served_model_requested','precision_verified','split')}
                           | {'rows': [{k: r.get(k) for k in keep} for r in s.get('rows', [])],
                              'panels': [{k: q.get(k) for k in ('concurrency','state','reason')} for q in s.get('panels', [])],
                              'contrasts': [{k: c.get(k) for k in ('concurrency','A','B','A_only_correct','B_only_correct','both_correct','both_wrong','p_holm')} for c in s.get('contrasts', [])]})
        except (OSError, ValueError, TypeError):
            continue
    return {"schema":"cell_akamai.concurrent_summary.v1","rows":rows,"science":science}


def serve(root, host='127.0.0.1', port=8765):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                body=HTML.encode();typ='text/html; charset=utf-8'
            elif self.path in ('/evidence', '/evidence/'):
                body=(Path(__file__).resolve().parents[1]/'dashboard'/'evidence.html').read_bytes();typ='text/html; charset=utf-8'
            elif self.path in ('/evidence.json', '/evidence/evidence.json'):
                vs=sorted((Path(__file__).resolve().parents[2]/'evidence'/'dashboard').glob('DASHBOARD_EVIDENCE_INDEX.v*.json'),key=lambda q:int(q.stem.split('.v')[-1]))
                if not vs:
                    self.send_error(404);return
                body=vs[-1].read_bytes();typ='application/json'
            elif self.path == '/data.json':
                body=json.dumps(load_sanitized(root)).encode();typ='application/json'
            else:
                self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type',typ)
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)))
            self.end_headers();self.wfile.write(body)
    server=ThreadingHTTPServer((host,port),Handler)
    print(f'Local dashboard: http://{host}:{port}/')
    server.serve_forever()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--runs',default='runs/concurrency');parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args();serve(Path(args.runs),port=args.port)
