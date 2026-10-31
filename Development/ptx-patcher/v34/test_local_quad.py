import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));import local_quad as q
class Stats:
 def add(self,*a):pass
class Tests(unittest.TestCase):
 def fuse(self,body):
  q.AUDIT.clear();text='.visible .entry test(){\n.reg .b32 %r<16>;\n.reg .b16 %rs<16>;\n.reg .pred %p<4>;\n'+body+'\nret;\n}';out=q.fuse_quads(text,Stats(),False);return q.AUDIT[0]['fused'],out
 def pair(self):return 'cvt.rn.satfinite.e4m3x2.f16x2 %rs0,%r0;\ncvt.rn.satfinite.e4m3x2.f16x2 %rs1,%r1;\nmov.b32 %r2,{%rs0,%rs1};\n'
 def test_basic(self):self.assertEqual(self.fuse(self.pair())[0],1)
 def test_global_reused_names(self):self.assertEqual(self.fuse(self.pair()+self.pair())[0],2)
 def test_nested_scope(self):self.assertEqual(self.fuse('{\n'+self.pair()+'\n}')[0],1)
 def test_live_in_successor(self):self.assertEqual(self.fuse(self.pair()+'bra $L_use;\n$L_use:\ncvt.u32.u16 %r8,%rs0;')[0],0)
 def test_conditional_overwrite(self):self.assertEqual(self.fuse(self.pair()+'@%p0 mov.b16 %rs0,0;\ncvt.u32.u16 %r8,%rs0;')[0],0)
 def test_unconditional_overwrite(self):self.assertEqual(self.fuse(self.pair()+'mov.b16 %rs0,0;\ncvt.u32.u16 %r8,%rs0;')[0],1)
 def test_loop_backedge_read(self):self.assertEqual(self.fuse('$L_loop:\ncvt.u32.u16 %r8,%rs0;\n'+self.pair()+'@%p0 bra $L_loop;')[0],0)
 def test_loop_backedge_kill(self):self.assertEqual(self.fuse('$L_loop:\n'+self.pair()+'@%p0 bra $L_loop;')[0],1)
 def test_source_changed(self):self.assertEqual(self.fuse(self.pair().replace('cvt.rn.satfinite.e4m3x2.f16x2 %rs1','mov.b32 %r0,0;\ncvt.rn.satfinite.e4m3x2.f16x2 %rs1'))[0],0)
 def test_intermediate_read(self):self.assertEqual(self.fuse(self.pair().replace('cvt.rn.satfinite.e4m3x2.f16x2 %rs1','cvt.u32.u16 %r8,%rs0;\ncvt.rn.satfinite.e4m3x2.f16x2 %rs1'))[0],0)
 def test_guarded_down(self):self.assertEqual(self.fuse('@%p0 '+self.pair())[0],0)
 def test_guarded_pack(self):self.assertEqual(self.fuse(self.pair().replace('mov.b32 %r2','@%p0 mov.b32 %r2'))[0],0)
 def test_inner_overwrite_does_not_kill_root(self):self.assertEqual(self.fuse(self.pair()+'{ .reg .b16 %rs0; mov.b16 %rs0,0; }\ncvt.u32.u16 %r8,%rs0;')[0],0)
 def test_inner_read_is_other_binding(self):self.assertEqual(self.fuse(self.pair()+'{ .reg .b16 %rs0; mov.b16 %rs0,0; cvt.u32.u16 %r8,%rs0; }')[0],1)
if __name__=='__main__':unittest.main()
