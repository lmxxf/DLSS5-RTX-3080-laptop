"""Verify V-only rewrites cover register/shared Q variants and preserve Q/K."""
from pathlib import Path
import unittest
from phase9_transform import transform,c32_mapped_lowreg
class VBridge(unittest.TestCase):
 def test_real_variants(self):
  root=Path(__file__).resolve().parents[1]/'phase8/artifacts/selected/modules'
  for module,n in [('c32-wave1-fast',1),('c32-wave1',1),('c64-wave2-fast',2)]:
   p=root/(module+'.generated.cu')
   if not p.exists():self.skipTest('archived CU absent')
   before=p.read_text();after=transform(before)
   self.assertEqual(after.count('if(part==2){q[')-before.count('if(part==2){q['),n)
   self.assertEqual(after.count('(part==2?sm86_d_bytes_to_ab(a):sm86_preshuffle_fp8(a))'),n)
   self.assertIn('if(part<2)',after)
 def test_mapped_policy_keeps_other_kinds_fast(self):
  p=Path(__file__).resolve().parents[1]/'phase8/artifacts/selected/modules/c32-wave1-fast.generated.cu'
  if not p.exists():self.skipTest('archive absent')
  text=c32_mapped_lowreg(transform(p.read_text()))
  self.assertIn('template<uint Site,uint Kind,bool Lowreg=false>',text)
  self.assertGreater(text.count('cw_kind,(!Up&&cw_kind==1)>'),5)
  self.assertIn('if constexpr(!Lowreg)return __builtin_amdgcn_cvt_pk_fp8_f32',text)
  self.assertIn('.reg .pred p_sub, p_sat, p_nan;',text)
if __name__=='__main__':unittest.main()
