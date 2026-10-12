from pathlib import Path
import hashlib,json,tempfile,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.dataset import make_item,oracle,freeze
from scripts.experiment import run_sweep,ARMS,run_item
from scripts.score import score_run,verify_oracle
from scripts.mock_endpoint import start
from scripts.export import export_run

class ConcurrentPilotTests(unittest.TestCase):
 def test_seed_matches_claude_contract(self):
  item=make_item(30,50000)
  import numpy as np
  self.assertEqual(item['initial_state'],np.random.default_rng(50000).integers(0,2,size=8,dtype=np.int64).tolist())
  self.assertTrue(verify_oracle(item,oracle(item)))
 def test_dataset_split_isolation(self):
  with tempfile.TemporaryDirectory() as td:
   manifest=freeze(td)
   seen=set()
   for split in ('calibration','pilot','holdout_proposed'):
    items=[json.loads(l) for l in (Path(td)/f'{split}_items.jsonl').read_text().splitlines()]
    self.assertEqual(len(items),manifest['splits'][split]['n_items'])
    for it in items:
     key=(it['rule'],tuple(it['initial_state']))
     self.assertNotIn(key,seen);seen.add(key)
 def test_end_to_end_fixture_with_server_usage_and_tamper_detection(self):
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);manifest=freeze(td/'data')
   items=[json.loads(l) for l in (td/'data/pilot_items.jsonl').read_text().splitlines()]
   server,url=start()
   try:
    idx=run_sweep(items,td/'runs',endpoint=url,model='MOCK_ECA_FIXTURE',concurrencies=(1,2),max_items=4,
      source_class='SYNTHETIC_FIXTURE',backend='LOCAL_MOCK_NOT_AKAMAI')
   finally:server.shutdown();server.server_close()
   self.assertEqual(len(idx['results']),8)
   scored=score_run(td/'runs/RUN_INDEX.json',td/'data/pilot_items.jsonl',td/'data/pilot_oracle.jsonl')
   self.assertTrue(all(x['exact_match_accuracy']==1 for x in scored))
   self.assertTrue(all(x['tokens_per_s'] is not None for x in scored))
   z=export_run(td/'runs',td/'artifact.zip');self.assertGreater(z['files'],8)
   f=td/'runs'/idx['results'][0]['path'];f.write_bytes(f.read_bytes()+b'\n')
   with self.assertRaisesRegex(ValueError,'HASH MISMATCH'):
    score_run(td/'runs/RUN_INDEX.json',td/'data/pilot_items.jsonl',td/'data/pilot_oracle.jsonl')

if __name__=='__main__':unittest.main()
