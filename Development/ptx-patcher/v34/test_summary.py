from pathlib import Path
import re,statistics as st,unittest
s=(Path(__file__).resolve().parent/'summarize.py').read_text();ns={'re':re,'st':st};exec(s[s.index('def direction'):s.index('\nout=')],ns)
class TestDirection(unittest.TestCase):
 def test_variant_name_is_not_direction(self):
  rs=[]
  for d,order in [('forward',['baseline','shared_forward','shared_forward','baseline']),('reverse',['shared_forward','baseline','baseline','shared_forward'])]:
   for j,v in enumerate(order):
    value=10 if v=='baseline' else (9 if d=='forward' else 11);rs.append({'name':f'{d}-shared_forward-{j}','variant':v,'metrics':{'gpu_median_ms':value,'gpu_min_ms':value}})
  r=ns['summarize'](rs,'baseline','shared_forward');self.assertAlmostEqual(r['directions']['forward']['gain_percent'],10);self.assertAlmostEqual(r['directions']['reverse']['gain_percent'],-10);self.assertAlmostEqual(r['gain_percent'],0)
 def test_repeat_prefix(self):self.assertEqual(ns['direction']({'name':'repeat-reverse-shared_forward-2'}),'reverse')
if __name__=='__main__':unittest.main()
