import unittest,subprocess
from pathlib import Path
from phase11_transform import pack_ffn_half_features
class HalfStore(unittest.TestCase):
 def test_finite_half_roundtrip_llvm(self):
  src='''define <8 x half> @fold(<8 x half> %h) {
entry:
 %f=fpext <8 x half> %h to <8 x float>
 %r=fptrunc <8 x float> %f to <8 x half>
 ret <8 x half> %r
}
'''
  p=subprocess.run(['opt-14','-O3','-verify','-S','-o','-','-'],input=src,text=True,capture_output=True)
  self.assertEqual(p.returncode,0,p.stderr);self.assertNotIn('fpext',p.stdout);self.assertNotIn('fptrunc',p.stdout)
 def test_packed_normal_bias_cannot_carry_between_halves(self):
  maximum_low_field=(0x7f<<9)+(0x5f40>>7)+0xc0
  self.assertEqual(maximum_low_field,0xff7e)
  self.assertLess(maximum_low_field,0x10000)
  for a in range(0x2400,0x5f01):
   r=a+0x3f+((a>>7)&1)
   self.assertEqual(((r>>7)+0xc0)&255,(r>>7)-64)
 def test_only_ffn_feature_site_changes(self):
  p=Path(__file__).resolve().parents[1]/'phase10/artifacts/selected/modules/c32-wave1-fast.generated.cu'
  if not p.exists():self.skipTest('baseline generated source absent')
  before=p.read_text();after=pack_ffn_half_features(before)
  self.assertIn('h8 rounded=cw_rtz_half8(ffn[ci]);',after)
  self.assertIn('cw_rtz_half8(summed)',after)
  self.assertIn('a=cw_pack8<1,cw_kind,(!Up&&cw_kind==1)>(a_t);',after)
  self.assertEqual(after.count('i2 a=sm86_pack_half_h8_e4m3(rounded);'),1)
if __name__=='__main__':unittest.main()
