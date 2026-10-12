import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('dash',Path(__file__).parents[2]/'tools/hour_scale/serve_dashboard.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Dashboard(unittest.TestCase):
 def test_actual_updates_and_partial_write(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'latest.json';s=m.Snapshot();p.write_text(json.dumps(dict(checkpoint_id=1,output_tokens_per_s=2,response='PRIVATE')))
   self.assertEqual(s.read(p)['output_tokens_per_s'],2);self.assertNotIn('response',s.read(p))
   p.write_text('{');self.assertEqual(s.read(p)['checkpoint_id'],1)
   p.write_text(json.dumps(dict(checkpoint_id=2,output_tokens_per_s=4)));self.assertEqual(s.read(p)['output_tokens_per_s'],4)
