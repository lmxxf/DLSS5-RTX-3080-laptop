import subprocess
import unittest
from build_sm86_modules import cancel_wmma_shuffles_ir

class DeferredUnpackIR(unittest.TestCase):
    def test_cse_stays_in_basic_block_and_zero_folds(self):
        source='''declare <4 x i32> @__sm86_unpack_fp8(<2 x i32>) #0
define <4 x i32> @check(<2 x i32> %x) {
entry:
  %a = call <4 x i32> @__sm86_unpack_fp8(<2 x i32> %x)
  %b = call <4 x i32> @__sm86_unpack_fp8(<2 x i32> %x)
  br label %next
next:
  %c = call <4 x i32> @__sm86_unpack_fp8(<2 x i32> %x)
  %z = call <4 x i32> @__sm86_unpack_fp8(<2 x i32> zeroinitializer)
  %bc = xor <4 x i32> %b, %c
  %out = xor <4 x i32> %bc, %z
  ret <4 x i32> %out
}
attributes #0 = { noinline }
'''
        result=cancel_wmma_shuffles_ir(source)
        self.assertEqual(result.count('call <4 x i32> @__sm86_unpack_fp8'),2)
        self.assertIn('%b = add <4 x i32> %a, zeroinitializer',result)
        self.assertIn('%z = add <4 x i32> zeroinitializer, zeroinitializer',result)
        self.assertIn('next:\n  %c = call',result)
        self.assertNotIn('noinline',result)
        self.assertIn('alwaysinline',result)
        p=subprocess.run(['opt-14','-verify','-disable-output','-'],input=result,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
if __name__=='__main__':unittest.main()
