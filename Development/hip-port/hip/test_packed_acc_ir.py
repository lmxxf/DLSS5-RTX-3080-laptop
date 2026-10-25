"""Type-check the packed accumulator SSA rewrites with the actual LLVM verifier."""
import subprocess
import unittest
from build_sm86_modules import cancel_wmma_shuffles_ir

DECLS = '''declare <4 x i32> @__sm86_c_to_ampere(<8 x float>)
declare <8 x float> @__sm86_d_to_rdna4(<4 x i32>)
declare <4 x i32> @step(<4 x i32>)
'''

class PackedAccumulatorIR(unittest.TestCase):
    def verify(self, body):
        ir = cancel_wmma_shuffles_ir(DECLS + body)
        p = subprocess.run(['opt-14', '-verify', '-disable-output', '-'],
                           input=ir, text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr + '\n' + ir)
        return ir

    def test_zero_and_direct(self):
        ir = self.verify('''define <4 x i32> @test(<4 x i32> %a) {
entry:
  %d = call <8 x float> @__sm86_d_to_rdna4(<4 x i32> %a)
  %c = call <4 x i32> @__sm86_c_to_ampere(<8 x float> %d)
  %z = call <4 x i32> @__sm86_c_to_ampere(<8 x float> zeroinitializer)
  %r = or <4 x i32> %c, %z
  ret <4 x i32> %r
}
''')
        self.assertNotIn('call <4 x i32> @__sm86_c_to_ampere', ir)

    def test_loop_nonzero_preheader(self):
        ir = self.verify('''define <8 x float> @test(<8 x float> %initial, i1 %again) {
entry:
  br label %loop
loop:
  %p = phi <8 x float> [ %initial, %entry ], [ %d, %loop ]
  %c = call <4 x i32> @__sm86_c_to_ampere(<8 x float> %p)
  %v = call <4 x i32> @step(<4 x i32> %c)
  %d = call <8 x float> @__sm86_d_to_rdna4(<4 x i32> %v)
  br i1 %again, label %loop, label %exit
exit:
  %out = phi <8 x float> [ %d, %loop ]
  ret <8 x float> %out
}
''')
        self.assertIn('%p = phi <4 x i32>', ir)
        self.assertIn('%amp_out = phi <4 x i32>', ir)

if __name__ == '__main__':
    unittest.main()
