import unittest,sys
from pathlib import Path
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'hip'))
from transform import transform
class StreamOrder(unittest.TestCase):
 def test_target_scope_and_order(self):
  text=(r/'phase12/artifacts/selected/modules/c32-wave1-fast.generated.cu').read_text()
  for site,cond in [('prefix','Prefix'),('post','Post')]:
   result=transform(text,site)
   self.assertEqual(result.count('if constexpr('+cond+'){if constexpr(W16==1)'),0)
   self.assertIn('if constexpr(W16==1){if constexpr('+cond+'){',result)
   self.assertEqual(result.count('i2 activation=sm86_d_bytes_to_ab(a);'),1)
   # Each chain visits hp0 then hp1, h2 order unchanged, no arithmetic replacement.
   self.assertIn('hp==0?cp.lo:cp.hi,activation,ffn[ci]',result)
   for original in ['h8 rounded=cw_rtz_half8(ffn[ci]);','sm86_pack_ad_producer<false>(__sm86_c_to_ampere(acc))']:
    self.assertEqual(text.count(original),result.count(original))
 def test_fail_closed(self):
  with self.assertRaises(ValueError):transform('', 'prefix')
if __name__=='__main__':unittest.main()
