import json,hashlib,time,os,importlib.util,platform
from pathlib import Path
from datetime import datetime,timezone
import torch
R=Path(__file__).resolve().parent;C=json.loads((R/'TRAIN_PREREGISTRATION.json').read_text());O=R/'train_results';O.mkdir(exist_ok=True)
from vita_metrics import checkpoint_sha256 as sha, atomic_write_json as write, merkle_root as root, throughput, throughput_acceleration
assert sha(R/'view.jsonl')==C['view_sha256'];assert sha(R/C['parent_checkpoint'])==C['parent_sha256']
spec=importlib.util.spec_from_file_location('model',R/'recovered_r4.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
torch.set_num_threads(C['threads']);torch.use_deterministic_algorithms(True);torch.manual_seed(C['seed'])
rows=[json.loads(x) for x in (R/'view.jsonl').read_text().splitlines() if x.strip()]
train=sorted([x for x in rows if x['split']=='train'],key=lambda x:x['row_id'])[:512];val=sorted([x for x in rows if x['split']=='validation'],key=lambda x:x['row_id']);assert len(train)==512 and len(val)==320
st=torch.load(R/C['parent_checkpoint'],map_location='cpu',weights_only=True);model=m.MSMTiny();model.load_state_dict(st['model_state_dict']);opt=torch.optim.AdamW(model.parameters(),lr=C['lr']);opt.load_state_dict(st['optimizer_state_dict'])
for g in opt.param_groups:g['lr']=C['lr']
S={'run_id':C['run_id'],'status':'RUNNING','config':C,'config_sha256':sha(R/'TRAIN_PREREGISTRATION.json'),'torch':torch.__version__,'python':platform.python_version(),'started_at_utc':datetime.now(timezone.utc).isoformat(),'steps':[],'validation':[],'test_set_evaluated':False,'gpu_used':False}
leaves=[]
def validation(label):
 model.eval();pred=[];t0=time.monotonic()
 with torch.no_grad():
  for i in range(0,len(val),64):
   b=val[i:i+64];a,d,e=model(torch.tensor([x['input_ids'] for x in b],dtype=torch.long))
   pred.extend({'row_id':r['row_id'],'logits':aa.tolist(),'delta_g_star':float(dd),'evidence_weight':float(ee)} for r,aa,dd,ee in zip(b,a,d,e))
 p=O/(label+'.predictions.jsonl');p.write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in pred));commit={'sha256':sha(p),'rows':320};write(O/(label+'.COMMIT.json'),commit);assert sha(p)==commit['sha256']
 a=torch.tensor([x['logits'] for x in pred]);d=torch.tensor([x['delta_g_star'] for x in pred]);e=torch.tensor([x['evidence_weight'] for x in pred]);yc=torch.tensor([x['anticube_index'] for x in val]);yd=torch.tensor([x['delta_g_star_target'] for x in val]);ye=torch.tensor([x['evidence_weight_target'] for x in val]);ce=float(torch.nn.functional.cross_entropy(a,yc));mse=float(torch.nn.functional.mse_loss(d,yd));l1=float(torch.nn.functional.l1_loss(e,ye))
 rec={'label':label,'answer_commitment':commit['sha256'],'anticube_accuracy':float((a.argmax(1)==yc).float().mean()),'anticube_ce':ce,'delta_g_star_mse':mse,'evidence_weight_l1':l1,'loss':ce+0.1*mse+0.1*l1,'rows':320,'duration_s':time.monotonic()-t0};S['validation'].append(rec);leaves.append(rec)
def save():S['merkle_root']=root(leaves);write(O/'summary.json',S)
validation('baseline');save()
prev=None
for step in range(1,9):
 b=train[(step-1)*64:step*64];model.train();t0=time.monotonic();opt.zero_grad(set_to_none=True);loss,metrics,_=m.batch_loss(model,b,'cpu');loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step();t1=time.monotonic()
 cp=O/('checkpoint-%04d.pt'%step);torch.save({'model_state_dict':model.state_dict(),'optimizer_state_dict':opt.state_dict(),'step':step,'parent_sha256':C['parent_sha256'],'torch_rng_state':torch.get_rng_state()},cp)
 count=sum(len(r['input_ids']) for r in b);rate=throughput(count,t1-t0);mid=(t0+t1)/2
 rec={'step':step,'checkpoint_sha256':sha(cp),'rows':64,'input_id_positions':count,'duration_s':t1-t0,'input_id_positions_per_s':rate,'input_id_positions_per_s2':None if prev is None else throughput_acceleration(prev[0],prev[1],rate,mid),'metrics':metrics,'failures_count':0};prev=(rate,mid);leaves.append(rec);S['steps'].append(rec);write(O/('STEP-%04d.json'%step),rec);save()
 if step%4==0:validation('step-%04d'%step);save()
S['status']='COMPLETED';S['finished_at_utc']=datetime.now(timezone.utc).isoformat();S['executed_optimizer_steps']=8;S['units']={'input_id_positions_per_s':'input ID positions/s; includes padding if present','input_id_positions_per_s2':'input ID positions/s²; difference of per-step rates over midpoint separation','delta_g_star_mse':'squared project target units','anticube_accuracy':'fraction'};save()
