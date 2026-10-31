import unittest,bisect
from pack_range import Range,b
HEAD='.visible .entry test(){\n.reg .b32 %r<16>;\n.reg .b16 %rs<8>;\n.reg .pred %p<4>;\n'
class Tests(unittest.TestCase):
 def classify(self,body):
  text=HEAD+body+'\ncvt.rn.satfinite.e4m3x2.f16x2 %rs0,%r8;\nret;\n}';r=Range(text);m=list(b.dp.FP8_DOWN_PATTERN.finditer(text))[-1];point=bisect.bisect_right(r.o.starts,m.start())-1;z=r.value('%r8',point);return 'pack3' if not z[2] and z[3] and z[0]>=0 and z[1]<=448 else 'pack4' if not z[2] and z[0]>=-448 and z[1]<=448 else 'generic'
 def test_positive(self):self.assertEqual(self.classify('mov.b32 %r8,0x3c003c00;'),'pack3')
 def test_signed(self):self.assertEqual(self.classify('mov.b32 %r8,0xbc003c00;'),'pack4')
 def test_negative_zero(self):self.assertEqual(self.classify('mov.b32 %r8,0x80000000;'),'pack4')
 def test_nan(self):self.assertEqual(self.classify('mov.b32 %r8,0x7e007e00;'),'generic')
 def test_inf(self):self.assertEqual(self.classify('mov.b32 %r8,0x7c007c00;'),'generic')
 def test_abs_clamp(self):self.assertEqual(self.classify('ld.param.u32 %r0,[arg];abs.f16x2 %r1,%r0;min.f16x2 %r8,%r1,0x5f005f00;'),'pack3')
 def test_named_half(self):self.assertEqual(self.classify('mov.b32 %r0,0;{.reg .f16 low;cvt.rn.f16.f32 low,%r0;mov.b32 %r8,{low,low};}'),'pack3')
 def test_named_signed_clamp(self):self.assertEqual(self.classify('ld.param.u32 %r0,[arg];max.f32 %r1,%r0,0fc3e00000;min.f32 %r2,%r1,0f43e00000;{.reg .f16 low;cvt.rn.f16.f32 low,%r2;mov.b32 %r8,{low,low};}'),'pack4')
 def test_merged_unknown(self):self.assertEqual(self.classify('mov.b32 %r8,0;@%p0 ld.param.u32 %r8,[arg];'),'generic')
if __name__=='__main__':unittest.main()
