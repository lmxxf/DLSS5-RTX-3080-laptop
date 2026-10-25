import unittest,re
from phase10_transform import apply_register_caps,optimize_fp8,REGISTER_CAPS
class Phase10Tests(unittest.TestCase):
 def test_caps_are_narrow_and_idempotent(self):
  source='\n'.join(f'.visible .entry {n}()\n.maxntid 64,1,1\n{{ret;}}' for n in list(REGISTER_CAPS)+['untouched'])
  result=apply_register_caps(source)
  self.assertEqual(result.count('.maxnreg '),9)
  self.assertEqual(apply_register_caps(result),result)
  self.assertNotIn('.maxnreg',result[result.index('.entry untouched'):])
 def test_zero_and_float_residual_semantics(self):
  source='''float cw_z(float x){return __builtin_amdgcn_fmed3f(x,-448.f,448.f);}
float w2_z(float x){return __builtin_amdgcn_fmed3f(x+0.f,-448.f,448.f);}
float residual(float x){return __builtin_amdgcn_fmed3f(x,-448.f,448.f)*2.f;}
'''
  result=optimize_fp8(source)
  self.assertIn('cw_z(float x){return (x);}',result)
  self.assertIn('w2_z(float x){return (x+0.f);}',result)
  self.assertIn('residual(float x){return __builtin_amdgcn_fmed3f',result)
if __name__=='__main__':unittest.main()
