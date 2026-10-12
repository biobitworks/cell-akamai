import json,hashlib,time,os
from pathlib import Path
import numpy as np,torch
from torch import nn
R=Path(__file__).resolve().parent
H=json.loads((R/'INPUT_MANIFEST.json').read_text())
for name,h in H.items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h
torch.set_num_threads(2)
class Adapter(nn.Module):
 def __init__(self,n,g):
  super().__init__();self.target_scale=nn.Embedding(n,1);self.gene_scale=nn.Parameter(torch.zeros(g));self.global_scale=nn.Parameter(torch.tensor(0.0))
 def forward(self,t,p):return (1+self.global_scale+self.target_scale(t)+self.gene_scale.unsqueeze(0))*p[t]
prior=np.load(R/'prior.npy');ids=np.load(R/'target_ids.npy');state=torch.load(R/'BEST_MODEL.pt',map_location='cpu',weights_only=True);m=Adapter(*prior.shape);m.load_state_dict(state['model'],strict=True);m.eval();start=time.monotonic()
with torch.no_grad():pred=m(torch.tensor(ids),torch.tensor(prior)).numpy()
duration=time.monotonic()-start;O=R/'results';O.mkdir(exist_ok=True);commits={}
for name,a in {'no_change':np.zeros_like(pred),'train_only_fixed_prior':prior[ids],'frozen_genesis_r3':pred}.items():
 p=O/(name+'.npy');np.save(p,a);commits[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'shape':list(a.shape)}
receipt={'run_id':'AKAMAI-GENESIS-VCC2025-CPU-HOLDOUT-20261012-RECOVERY-01','status':'PREDICTIONS_COMMITTED','prediction_commitments':commits,'input_manifest':H,'duration_s':duration,'device':'cpu','torch':torch.__version__,'heldout_X_available_to_predictor':False,'failures_count':0,'memory_limit_bytes':1073741824,'rows':len(ids),'genes':prior.shape[1]}
p=O/'PREDICTION_COMMITMENTS.json';p.write_text(json.dumps(receipt,indent=2)+'\n');print('PREDICTIONS_COMMITTED')
