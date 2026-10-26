"""Guard against restoring packed totals only inside the scalar fallback."""
from pathlib import Path
import unittest,re
class TailRestore(unittest.TestCase):
 def test_compiled_contract_uses_final_accumulator(self):
  p=Path(__file__).resolve().parent
  for mod in ['deep_fast-packed','deep_fast-packed-fast','vit-stream-fast']:
   s=(p/f'artifacts/tail/modules/{mod}.generated.cu').read_text()
   body=s.split('void vit_contract_blocked_body(')[1].split('// Fragment-weight twin')[0]
   restore=body.index('total[n]=__sm86_d_to_rdna4(packed_total[n])')
   tail=body.index('if constexpr(ByteFOut){')
   self.assertLess(restore,tail)
   self.assertEqual(body.count('total[n]=__sm86_d_to_rdna4(packed_total[n])'),1)
if __name__=='__main__':unittest.main()
