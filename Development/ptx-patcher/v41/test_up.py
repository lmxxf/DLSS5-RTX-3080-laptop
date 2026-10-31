import unittest
from up_pair import analyze,lower
HEAD='.visible .entry test(){.reg .b32 %r<16>; .reg .b16 %rs<8>; .reg .pred %p<2>;\n'
class Stats:
 def add(self,*a):pass
class Tests(unittest.TestCase):
 def runpart(self,body):
  text=HEAD+body+'\nret;}';return text,analyze(text)[1]
 def test_two_halves(self):
  t,r=self.runpart('mov.b32 {%rs0,%rs1},%r0; cvt.rn.f16x2.e4m3x2 %r1,%rs0; cvt.rn.f16x2.e4m3x2 %r2,%rs1;');self.assertTrue(all(x['eligible'] for x in r));self.assertNotIn('mov.b32 {%rs0',lower(t,Stats(),0));self.assertIn('0xb3a2',lower(t,Stats(),0))
 def test_overwrite(self):
  _,r=self.runpart('mov.b32 {%rs0,%rs1},%r0;mov.b32 %r0,0;cvt.rn.f16x2.e4m3x2 %r1,%rs0;');self.assertEqual(r[0]['reason'],'source_overwritten')
 def test_low_alias_kills_high(self):
  _,r=self.runpart('mov.b32 {%rs0,%rs1},%r0;cvt.rn.f16x2.e4m3x2 %r0,%rs0;cvt.rn.f16x2.e4m3x2 %r1,%rs1;');self.assertTrue(r[0]['eligible']);self.assertFalse(r[1]['eligible'])
 def test_guard(self):
  _,r=self.runpart('@%p0 mov.b32 {%rs0,%rs1},%r0;cvt.rn.f16x2.e4m3x2 %r1,%rs0;');self.assertFalse(r[0]['eligible'])
 def test_cross_block(self):
  _,r=self.runpart('mov.b32 {%rs0,%rs1},%r0;bra $L;\n$L:\ncvt.rn.f16x2.e4m3x2 %r1,%rs0;');self.assertEqual(r[0]['reason'],'cross_block')
 def test_other_user_retains_split(self):
  t,r=self.runpart('mov.b32 {%rs0,%rs1},%r0;cvt.rn.f16x2.e4m3x2 %r1,%rs0;cvt.rn.f16x2.e4m3x2 %r2,%rs1;st.global.u16 [%r4],%rs1;');self.assertIn('mov.b32 {%rs0',lower(t,Stats(),0))
if __name__=='__main__':unittest.main()
