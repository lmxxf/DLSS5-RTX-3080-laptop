import unittest,subprocess
from build_sm86_modules import upgrade_ir_alignments
class AlignmentIR(unittest.TestCase):
 def test_sizes_and_preserved_stronger_alignment(self):
  ir='''@s = addrspace(3) global [64 x i8] undef, align 1
@strong = addrspace(3) global [64 x i8] undef, align 32
define void @check(i32* %p, <2 x i32>* %p2, <4 x i32>* %p4, i8* %byte) {
entry:
 %a = load i32, i32* %p, align 1
 %b = load <2 x i32>, <2 x i32>* %p2, align 2
 %c = load <4 x i32>, <4 x i32>* %p4, align 4
 store <4 x i32> %c, <4 x i32>* %p4, align 8
 %d = load i8, i8* %byte, align 1
 ret void
}
'''
  out=upgrade_ir_alignments(ir)
  self.assertIn('@s = addrspace(3) global [64 x i8] undef, align 16',out)
  self.assertIn('@strong = addrspace(3) global [64 x i8] undef, align 32',out)
  self.assertIn('load i32, i32* %p, align 4',out)
  self.assertIn('load <2 x i32>, <2 x i32>* %p2, align 8',out)
  self.assertIn('load <4 x i32>, <4 x i32>* %p4, align 16',out)
  self.assertIn('store <4 x i32> %c, <4 x i32>* %p4, align 16',out)
  self.assertIn('load i8, i8* %byte, align 1',out)
  self.assertEqual(out,upgrade_ir_alignments(out))
  p=subprocess.run(['opt-14','-verify','-disable-output','-'],input=out,text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr)
 def test_cap8(self):
  x='%v = load <4 x i32>, <4 x i32>* %p, align 2'
  self.assertTrue(upgrade_ir_alignments(x,8).endswith('align 8'))
  x='%v = load <4 x i32>, <4 x i32>* %p, align 32'
  self.assertTrue(upgrade_ir_alignments(x,8).endswith('align 32'))
if __name__=='__main__':unittest.main()
