#!/usr/bin/env python3
"""Local aggregate-only durable puller. Never deploys or submits inference."""
import datetime as dt,hashlib,io,json,os,re,subprocess,sys,time,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from sustained import merkle,canonical
ROOT=Path(__file__).resolve().parents[2];RID=sys.argv[1];POD=sys.argv[2];REMOTE=sys.argv[3];env=dict(os.environ,KUBECONFIG=str(Path.home()/'.kube/s05.yaml'))
TARGET=ROOT/'evidence/live'/RID;TARGET.mkdir(parents=True,exist_ok=True)
def command(args):return subprocess.check_output(args,cwd=ROOT,env=env,stderr=subprocess.DEVNULL)
def git(*args):return command(['git',*args]).decode().strip()
last=None;failures=0
while True:
 try:
  script="import pathlib,io,zipfile,sys; p=pathlib.Path("+repr(REMOTE)+")/'public'; b=io.BytesIO(); z=zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED); [(z.writestr(f.name,f.read_bytes())) for f in p.glob('*.json')];z.close();sys.stdout.buffer.write(b.getvalue())"
  payload=command(['kubectl','--request-timeout=20s','-n','workshop-s05','exec',POD,'--','/home/coder/workshop/.venv/bin/python','-c',script]);failures=0
  with zipfile.ZipFile(io.BytesIO(payload)) as z:
   assert z.testzip() is None
   for name in z.namelist():
    assert Path(name).name==name and name.endswith('.json')
    data=z.read(name);obj=json.loads(data)
    def scan(v):
     if isinstance(v,dict):
      for k,x in v.items():
       assert k.lower() not in ('response','messages','content','reasoning_content','api_key','authorization','kubeconfig','password','secret')
       scan(x)
     elif isinstance(v,list):
      for x in v:scan(x)
     elif isinstance(v,str):assert not re.search(r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN.*PRIVATE KEY',v)
    scan(obj)
    if name.startswith('checkpoint-'):
     receipt={k:v for k,v in obj.items() if k not in ('checkpoint_id','receipt_sha256','merkle_root','merkle_leaves','merkle_construction')}
     assert hashlib.sha256(canonical(receipt)).hexdigest()==obj['receipt_sha256']
     assert obj['merkle_leaves'][-1]==obj['receipt_sha256'] and merkle(obj['merkle_leaves'])==obj['merkle_root']
    p=TARGET/name
    if p.exists() and name.startswith('checkpoint-'):assert p.read_bytes()==data
    tmp=p.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(p)
  state=json.loads((TARGET/'STATE.json').read_text());key=(state.get('completed_windows'),state.get('state'),(TARGET/'FAILURE.json').exists())
  if key!=last:
   subprocess.run(['python3','-m','pytest','-q','tests/hour_scale'],cwd=ROOT,env=dict(env,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'),check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   git('add',str(TARGET.relative_to(ROOT)))
   if git('diff','--cached','--name-only'):
    git('commit','-m',f'Preserve live inference checkpoint {RID} windows {key[0]}','-m','🤖 Generated with Codex','-m','Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>')
    git('push');sha=git('rev-parse','HEAD');remote=git('ls-remote','origin','refs/heads/lane/akamai-m08-m09-results-20261012').split()[0];assert sha==remote
    body=ROOT/'private'/'issue_live.md';body.parent.mkdir(exist_ok=True);body.write_text(f'Live sustained checkpoint: {RID}; completed windows {key[0]}/48; state {key[1]}. PROVISIONAL, not final hour-scale completion. Verified remote SHA [{sha}](https://github.com/biobitworks/cell-akamai/tree/{sha}/evidence/live/{RID}). Merkle receipt digests independently rechecked after pull. Anticube and ΔG* NOT_COMPUTED. Raw responses remain private. NEXT_ACTION: continue serialized windows while access remains; retain interruption receipts.\n')
    subprocess.run(['gh','issue','comment','1','--repo','biobitworks/cell-akamai','--body-file',str(body)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
   last=key
  (ROOT/'private'/'puller_status.json').write_text(json.dumps(dict(last_success_utc=dt.datetime.now(dt.timezone.utc).isoformat(),run_id=RID,state=state,verified_remote_sha=git('rev-parse','HEAD'))))
  if state.get('state')=='COMPLETED_UNSCORED' or (TARGET/'FAILURE.json').exists():break
 except Exception as e:
  failures+=1;(ROOT/'private').mkdir(exist_ok=True);(ROOT/'private'/'puller_failure.json').write_text(json.dumps(dict(exception=type(e).__name__,consecutive_failures=failures,when=dt.datetime.now(dt.timezone.utc).isoformat(),action='Retain all local data; retry connection, never restart benchmark')))
  if failures>=10:break
 time.sleep(30)
