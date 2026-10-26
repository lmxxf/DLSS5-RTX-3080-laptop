import unittest
from pathlib import Path
from phase18_transform import transform,apply_c256_cap
class PackingGuards(unittest.TestCase):
 def test_byteout_shuffles_before_lane_clipping(self):
  compat=(Path(__file__).resolve().parent/'sm86_compat.h').read_text()
  for condition in ['x>=sx','full||(x>=sx)']:
   body='\nusing f8=sm86_f8;\nvoid swin_wave2_body(){f8 result[2];if('+condition+'){uint dest=0;for(uint ci=0;ci<2;ci++){if constexpr(ByteOut){i2 a;float a_t[8];for(uint e=0;e<8;e++)a_t[e]=result[ci][e];a=w2_pack8(a_t);store(a);}}}}'
   text=transform(compat+body,['byteout']);start=text.index('void swin_wave2_body(');text=text[start:]
   self.assertLess(text.index('sm86_d_to_rdna4_half_bits'),text.index('if('+condition+')'))
   guarded=text[text.index('if('+condition+')'):];self.assertNotIn('__sm86_c_to_ampere',guarded)
 def test_cap_override_is_not_sticky(self):
  p=''.join('.visible .entry '+n+'()\n.maxntid 256,1,1\n.maxnreg 226\n{ret;}\n' for n in ['c256_wave2_bi_bo_w16','c256_wave2_bi_w16'])
  q=apply_c256_cap(p,168);self.assertEqual(q.count('.maxnreg 168'),2);z=apply_c256_cap(q,128);self.assertEqual(z.count('.maxnreg 128'),2);self.assertNotIn('maxnreg 168',z)
  self.assertEqual(z.replace('.maxnreg 128','.maxnreg 226'),p)
if __name__=='__main__':unittest.main()
