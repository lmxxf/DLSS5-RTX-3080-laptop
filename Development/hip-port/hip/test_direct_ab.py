"""Audit narrow transformation sites, exclusions, bounds and LLVM SSA removal."""
from pathlib import Path
import unittest,re,subprocess
from phase8_transform import transform
from build_sm86_modules import cancel_wmma_shuffles_ir
class DirectAbTests(unittest.TestCase):
 def test_real_sites(self):
  root=Path(__file__).resolve().parents[1]/'phase7/artifacts/selected/modules'
  if not (root/'c32-wave1-fast.generated.cu').exists():self.skipTest('archived generated CU unavailable')
  for module,expected in [('c32-wave1-fast',3),('c64-wave2-fast',7)]:
   p=root/(module+'.generated.cu')
   if not p.exists():p=root.parent.parent/'step12/modules'/(module+'.generated.cu')
   a=p.read_text();b=transform(a)
   self.assertEqual(b.count('sm86_d_bytes_to_ab(')-a.count('sm86_d_bytes_to_ab('),expected)
   self.assertIn('sm86_preshuffle_fp8',b) # Coordinate-dependent sites remain.
 def test_ssa_bridge_eliminates_both_maps(self):
  s="""declare <4 x i32> @__sm86_c_to_ampere(<8 x float>)
declare <8 x float> @__sm86_d_to_rdna4(<4 x i32>)
declare <8 x float> @unpack(<4 x i32>)
define <8 x float> @bridge(<4 x i32> %ad) {
entry:
 %d = call <8 x float> @__sm86_d_to_rdna4(<4 x i32> %ad)
 %c = call <4 x i32> @__sm86_c_to_ampere(<8 x float> %d)
 %r = call <8 x float> @unpack(<4 x i32> %c)
 ret <8 x float> %r
}
"""
  ir=cancel_wmma_shuffles_ir(s)
  self.assertNotIn('call <8 x float> @__sm86_d_to_rdna4',ir)
  self.assertNotIn('call <4 x i32> @__sm86_c_to_ampere',ir)
  p=subprocess.run(['opt-14','-verify','-disable-output','-'],input=ir,text=True,capture_output=True)
  self.assertEqual(p.returncode,0,p.stderr)
 def test_bounds(self):
  s='__attribute__((launch_bounds(64))) void split_ffn_one_w2f8_w16(){}\n__attribute__((launch_bounds(32))) void vit_stream_project_n64_bb_bout(){}'
  self.assertIn('launch_bounds(64,8)',transform(s))
  self.assertIn('launch_bounds(32,16)',transform(s))
  self.assertEqual(transform(s,bounds=False),s)
if __name__=='__main__':unittest.main()
