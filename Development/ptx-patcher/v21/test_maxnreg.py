from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));import build_sm86_dlls as b
class CapControl(unittest.TestCase):
 def test_only_existing_caps_change(self):
  s='.version 8.0\n.visible .entry test()\n.maxntid 128,1,1\n.maxnreg 128\n{\n.reg .b32 r<168>;\n}\n.maxnreg 168\n'
  self.assertEqual(b.override_maxnreg(s,None),(s,0));new,n=b.override_maxnreg(s,255);self.assertEqual(n,2);self.assertEqual(new,s.replace('.maxnreg 128','.maxnreg 255').replace('.maxnreg 168','.maxnreg 255'))
  for v in [0,256]:
   with self.assertRaises(ValueError):b.override_maxnreg(s,v)
if __name__=='__main__':unittest.main()
