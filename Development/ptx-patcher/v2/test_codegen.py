from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build_sm86_dlls as b
class EvenOddCodegen(unittest.TestCase):
 def test_lane_local_and_operands(self):
  raw='mma.sync.aligned.m16n8k32.row.col.f16.e4m3.e4m3.f16 {%r6,%r7}, {%r0,%r1,%r2,%r3}, {%r4,%r5}, {%r6,%r7};'
  matches=list(b.dp.FP8_MMA_PATTERN.finditer(raw));b.dp.mapped_fp16_sources=b.forward_mapped_fp16_sources
  s=b.fast_render_fp8_mma_run(matches,{})
  self.assertNotIn('shfl.',s);self.assertNotIn('prmt.',s);self.assertNotIn('dlssnr_lane',s)
  self.assertIn('{dlssnr_fp16_0_0, dlssnr_fp16_1_0, dlssnr_fp16_2_0, dlssnr_fp16_3_0}',s)
  self.assertIn('{dlssnr_fp16_0_1, dlssnr_fp16_1_1, dlssnr_fp16_2_1, dlssnr_fp16_3_1}',s)
  self.assertEqual(s.count('mma.sync.aligned.m16n8k16'),2)
if __name__=='__main__':unittest.main()
