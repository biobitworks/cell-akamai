"""Synthetic numerical traces only, never GPU evidence."""
import importlib.util,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[2]/'tools/hour_scale'))
from sustained import merkle,kinetics,digest
class Kinetics(unittest.TestCase):
 def test_constant(self):self.assertEqual(kinetics([{'t':0,'counter':0},{'t':10,'counter':100},{'t':20,'counter':200}])['acceleration'][0]['tokens_per_s2'],0)
 def test_positive_units(self):self.assertEqual(kinetics([{'t':0,'counter':0},{'t':10,'counter':100},{'t':20,'counter':300}])['acceleration'][0]['tokens_per_s2'],1)
 def test_negative(self):self.assertEqual(kinetics([{'t':0,'counter':0},{'t':10,'counter':200},{'t':20,'counter':300}])['acceleration'][0]['tokens_per_s2'],-1)
 def test_reset_no_bridge(self):self.assertFalse(kinetics([{'t':0,'counter':100},{'t':10,'counter':200},{'t':20,'counter':0},{'t':30,'counter':100}])['acceleration'])
 def test_missing_out_of_order(self):self.assertFalse(kinetics([{'t':1,'counter':None},{'t':0,'counter':1}])['rates'])
 def test_merkle_tamper(self):
  a=digest(b'a');b=digest(b'b');self.assertNotEqual(merkle([a,b]),merkle([a,a]));self.assertEqual(merkle([a,b]),merkle([a,b]))
