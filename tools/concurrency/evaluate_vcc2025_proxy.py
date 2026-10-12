import json,hashlib,time,os
from pathlib import Path
import numpy as np,h5py,torch
from torch import nn
R=Path(__file__).resolve().parent;C=json.loads((R/'PREREGISTRATION.json').read_text());O=R/'results';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def write(name,x):
 p=O/(name+'.tmp');p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');os.replace(p,O/name)
def col(obs,key):
 x=obs[key]
 if isinstance(x,h5py.Group):
  cats=x['categories'][:];v=[cats[int(i)] for i in x['codes'][:]]
 else:v=x[:]
 return np.array([y.decode() if isinstance(y,bytes) else str(y) for y in v],dtype=object)
def axis(f):
 k=f['var'].attrs.get('_index','_index');k=k.decode() if isinstance(k,bytes) else k
 return [x.decode() if isinstance(x,bytes) else str(x) for x in f['var'][k][:]]
def hv(s):return int(hashlib.sha256(('KAGGLE-GENESIS-VITA-R3-20261010|'+s).encode()).hexdigest(),16)
class Adapter(nn.Module):
 def __init__(self,n,g):
  super().__init__();self.target_scale=nn.Embedding(n,1);self.gene_scale=nn.Parameter(torch.zeros(g));self.global_scale=nn.Parameter(torch.tensor(0.0))
 def forward(self,t,p):return (1+self.global_scale+self.target_scale(t)+self.gene_scale.unsqueeze(0))*p[t]
start=time.monotonic();torch.set_num_threads(2)
for name,v in C['data_preflight'].items():
 if isinstance(v,dict):assert sha(R/name)==v['sha256']
assert sha(R/'BEST_MODEL.pt')==C['checkpoint_sha256']
with h5py.File(R/'control_batch_pseudobulk.h5ad','r') as fc,h5py.File(R/'target_batch_pseudobulk.h5ad','r') as ft:
 assert axis(fc)==axis(ft) and len(set(axis(fc)))==len(axis(fc))
 cb=col(fc['obs'],'batch');cm=np.log1p(np.asarray(fc['X'][:],dtype=np.float32)/np.maximum(np.asarray(fc['obs']['cells'][:],dtype=np.float32)[:,None],1));cmap={b:i for i,b in enumerate(cb)}
 bb=col(ft['obs'],'batch');tt=col(ft['obs'],'target_gene');cells=np.asarray(ft['obs']['cells'][:],dtype=np.float32);groups=sorted(set(bb),key=hv);test=set(groups[:8]);train=set(groups[12:]);valid=set(groups[8:12]);assert not test&(train|valid)
 tr=sorted(np.flatnonzero(np.isin(bb,list(train))).tolist(),key=lambda i:hv('train_'+str(i)))[:2500];te=sorted(np.flatnonzero(np.isin(bb,list(test))).tolist(),key=lambda i:hv('holdout_'+str(i)))[:C['heldout_rows']];assert not set(tr)&set(te)
 targets=sorted(set(tt));tid={v:i for i,v in enumerate(targets)};ng=ft['X'].shape[1];sums=np.zeros((len(targets),ng),dtype=np.float64);counts=np.zeros(len(targets),dtype=np.int64)
 train_ix=sorted(tr)
 for begin in range(0,len(train_ix),32):
  ix=train_ix[begin:begin+32];x=np.asarray(ft['X'][ix],dtype=np.float32);y=np.log1p(x/np.maximum(cells[ix,None],1))-cm[[cmap[bb[i]] for i in ix]];t=np.array([tid[tt[i]] for i in ix]);np.add.at(sums,t,y);np.add.at(counts,t,1);prior=(sums/np.maximum(counts[:,None],1)).astype(np.float32)
 checkpoint=torch.load(R/'BEST_MODEL.pt',map_location='cpu',weights_only=True);model=Adapter(len(targets),ng);model.load_state_dict(checkpoint['model'],strict=True);model.eval();ix=sorted(te);t=np.array([tid[tt[i]] for i in ix])
 with torch.no_grad():pred=model(torch.tensor(t),torch.tensor(prior)).numpy()
 arrays={'no_change':np.zeros_like(pred),'train_only_fixed_prior':prior[t],'frozen_genesis_r3':pred};commit={}
 for name,a in arrays.items():
  p=O/(name+'.npy');np.save(p,a);commit[name]={'sha256':sha(p),'shape':list(a.shape)}
 write('PREDICTION_COMMITMENTS.json',{'predictions':commit,'heldout_row_ids_sha256':hashlib.sha256(canon(ix)).hexdigest(),'heldout_X_read':False,'rows':len(ix)})
 for name,v in commit.items():assert sha(O/(name+'.npy'))==v['sha256']
 # First heldout expression access: after all prediction files and commitments exist.
 actual=np.log1p(np.asarray(ft['X'][ix],dtype=np.float32)/np.maximum(cells[ix,None],1))-cm[[cmap[bb[i]] for i in ix]]
 losses={name:np.mean((a.astype(np.float64)-actual.astype(np.float64))**2,axis=1) for name,a in arrays.items()}
 batch=np.array([bb[i] for i in ix]);clusters=sorted(set(batch));delta=losses['frozen_genesis_r3']-losses['train_only_fixed_prior'];rng=np.random.default_rng(C['seed']);boot=[]
 for _ in range(1000):
  chosen=rng.choice(clusters,size=len(clusters),replace=True);vals=np.concatenate([delta[batch==b] for b in chosen]);boot.append(float(vals.mean()))
 summary={'run_id':C['run_id'],'status':'COMPLETED','config':C,'config_sha256':sha(R/'PREREGISTRATION.json'),'device':'cpu','torch':torch.__version__,'rows':len(ix),'genes':ng,'batches':len(clusters),'gene_axis_exact_match':True,'predictions_committed_before_holdout_truth':True,'prediction_commitments':commit,'mse':{name:float(v.mean()) for name,v in losses.items()},'paired_mse_delta_genesis_minus_prior':float(delta.mean()),'paired_batch_bootstrap_95_interval':np.percentile(boot,[2.5,97.5]).tolist(),'uncovered_targets':int(sum(counts[t]==0)),'duration_s':time.monotonic()-start,'failures_count':0,'training_performed':False,'official_vcc_score':False,'units':{'mse':'squared log1p per-cell pseudobulk residual','duration_s':'s'}}
 write('summary.json',summary)
