import unittest
from pathlib import Path
import build_sm86_modules as build
from phase14_transform import fix_legacy_attention_abi
from phase2_transform import masked,end_at
class AttentionABI(unittest.TestCase):
 def source(self):
  r=Path(__file__).resolve().parent;mod=next(m for m in build.parse_ps1_modules(r/'build-modules.ps1') if m['name']=='deep_fast-packed-fast')
  old=build.PHASE14_ATTENTION_ABI;build.PHASE14_ATTENTION_ABI=False
  try:return build.assemble_module_source(mod,str(r),str(r/'sm86_compat.h'))
  finally:build.PHASE14_ATTENTION_ABI=old
 def test_exact_two_consumers_only(self):
  raw=self.source();fixed=fix_legacy_attention_abi(raw);m=masked(raw);a=m.index('{',m.index('void vit_attention_fused_body('));z=end_at(m,a,'{','}')
  expected=raw[a+1:z].replace('a=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(q[k/16],y,a);','a=sm86_wmma_fp8_preshuffled_a(q[k/16],y,a);').replace('acc[c]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(xb,y,acc[c]);','acc[c]=sm86_wmma_fp8_preshuffled_a(xb,y,acc[c]);')
  self.assertEqual(fixed,raw[:a+1]+expected+raw[z:])
 def test_fail_closed_and_noop(self):
  self.assertEqual(fix_legacy_attention_abi('no attention here'),'no attention here')
  with self.assertRaises(AssertionError):fix_legacy_attention_abi(self.source().replace('q[0]=sm86_preshuffle_fp8(q[0]);',''))
if __name__=='__main__':unittest.main()
