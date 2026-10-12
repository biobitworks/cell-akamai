"""Deterministic unit fixtures; never GPU evidence."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('runner',Path(__file__).parents[2]/'tools/hour_scale/runner.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def row(i=0,phase='MEASURED',failure=False):return dict(request_id=str(i),phase=phase,failure=failure,failure_categories=['HTTP'] if failure else [],completion_tokens=20,prompt_tokens=10,latency_ms=100,completed_measured_s=1.5)
class Metrics(unittest.TestCase):
 def test_usage_not_chunks(self):
  r=row();r['chunks']=500;s=m.summarize([r],10,3600,1);self.assertEqual(s['output_tokens_per_s'],2);self.assertEqual(s['units']['output_tokens_per_s'],'tokens/s')
 def test_warmup_excluded(self):self.assertEqual(m.summarize([row(1,'WARMUP'),row(2)],10,3600,1)['requests'],1)
 def test_duration(self):self.assertEqual(m.summarize([row()],3599,3600,1)['state'],'RUNNING')
 def test_duration_complete(self):self.assertEqual(m.summarize([row()],3600,3600,1)['state'],'COMPLETED_UNSCORED')
 def test_empty(self):self.assertIsNone(m.summarize([],0,3600,1)['latency_p95_ms'])
 def test_failures(self):
  s=m.summarize([row(failure=True)],10,3600,1);self.assertEqual(s['output_tokens_per_s'],0);self.assertEqual(s['failure_percent'],100)
 def test_unknown_usage(self):
  r=row();r['completion_tokens']=None;self.assertIsNone(m.summarize([r],10,3600,1)['output_tokens_per_s'])
 def test_duplicate(self):
  with self.assertRaises(ValueError):m.summarize([row(),row()],10,3600,1)
 def test_percentile_interpolation(self):self.assertEqual(m.percentile([0,100],.95),95)
 def test_no_timing_fabrication(self):self.assertIsNone(m.summarize([row()],10,3600,1)['ttft_ms'])
 def test_lock_serializes(self):
  with tempfile.TemporaryDirectory() as d:
   with m.gpu_lock(str(Path(d)/'lock')):
    with self.assertRaises(BlockingIOError):
     with m.gpu_lock(str(Path(d)/'lock')):pass
 def test_atomic_snapshot(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.json';m.atomic(p,{'n':1});m.atomic(p,{'n':2});self.assertEqual(json.loads(p.read_text()),{'n':2})
 def test_representations(self):
  root=Path(__file__).parents[2]/'evidence/20261012/successor'
  a,_=m.load_prompts(root,'genesis','original')
  for rep in ('fco','fcg'):self.assertEqual(a,m.load_prompts(root,'genesis',rep)[0])
 def test_oracle_forbidden(self):
  with self.assertRaises(ValueError):m.load_prompts(Path(__file__).parents[2]/'evidence/20261012/successor','evaluator','original')
if __name__=='__main__':unittest.main()
