import unittest
from pathlib import Path
from phase12_transform import pack_c32_av
class ProducerScope(unittest.TestCase):
 def test_only_av_and_fail_closed(self):
  p=Path(__file__).resolve().parents[1]/'phase11/artifacts/selected/modules/c32-wave1-fast.generated.cu'
  if not p.exists():self.skipTest('archived Phase11 generated source absent')
  before=p.read_text();after=pack_c32_av(before)
  self.assertEqual(after.count('i2 a=sm86_pack_ad_producer<false>(__sm86_c_to_ampere(acc));'),1)
  for marker in ['a=cw_pack8<3,cw_kind,(!Up&&cw_kind==1)>(a_t);','sm86_pack_half_h8_e4m3(rounded)']:
   self.assertEqual(before.count(marker),after.count(marker))
  with self.assertRaises(AssertionError):pack_c32_av('')
if __name__=='__main__':unittest.main()
