import unittest
from up_pair import analyze
HEAD='.visible .entry test(){.reg .b32 %r<16>;.reg .b16 %rs<8>;.reg .pred %p<2>;\nld.param.u32 %r0,[arg];\n'
class Tests(unittest.TestCase):
 def rows(self,body):return analyze(HEAD+body+'\nret;}',cfg=True)[1]
 def test_safe_cross_block(self):
  r=self.rows('mov.b32 {%rs0,%rs1},%r0;bra $L;\n$L:\ncvt.rn.f16x2.e4m3x2 %r1,%rs0;cvt.rn.f16x2.e4m3x2 %r2,%rs1;');self.assertTrue(all(x['eligible'] for x in r))
 def test_diamond_clobber(self):
  r=self.rows('mov.b32 {%rs0,%rs1},%r0;@%p0 bra $A;bra $B;\n$A:\nmov.b32 %r0,1;bra $M;\n$B:\nbra $M;\n$M:\ncvt.rn.f16x2.e4m3x2 %r1,%rs0;');self.assertFalse(r[0]['eligible'])
 def test_guarded_clobber(self):
  r=self.rows('mov.b32 {%rs0,%rs1},%r0;bra $A;\n$A:\n@%p0 mov.b32 %r0,1;bra $M;\n$M:\ncvt.rn.f16x2.e4m3x2 %r1,%rs0;');self.assertFalse(r[0]['eligible'])
 def test_unreachable_clobber(self):
  r=self.rows('mov.b32 {%rs0,%rs1},%r0;bra $M;\n$D:\nmov.b32 %r0,1;\nret;\n$M:\ncvt.rn.f16x2.e4m3x2 %r1,%rs0;');self.assertTrue(r[0]['eligible'])
 def test_loop_after_use_clobbers(self):
  r=self.rows('mov.b32 {%rs0,%rs1},%r0;bra $M;\n$M:\ncvt.rn.f16x2.e4m3x2 %r1,%rs0;mov.b32 %r0,1;@%p0 bra $M;');self.assertFalse(r[0]['eligible'])
 def test_loop_without_clobber(self):
  r=self.rows('mov.b32 {%rs0,%rs1},%r0;bra $M;\n$M:\ncvt.rn.f16x2.e4m3x2 %r1,%rs0;@%p0 bra $M;');self.assertTrue(r[0]['eligible'])
 def test_undefined_half_path(self):
  r=self.rows('@%p0 bra $A;bra $M;\n$A:\nmov.b32 {%rs0,%rs1},%r0;bra $M;\n$M:\ncvt.rn.f16x2.e4m3x2 %r1,%rs0;');self.assertFalse(r[0]['eligible'])
if __name__=='__main__':unittest.main()
