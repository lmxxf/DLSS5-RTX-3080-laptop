from pathlib import Path
import sys,subprocess,json,re
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import codegen as g
g.MODE='pack5';bin=Path('/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin');out={}
for name in ['two_pack5','pack5_quad']:
 body=g.quad('r0','r1','z') if name=='pack5_quad' else g.declarations()+['.reg .b16 o0,o1;']+g.pack('r0','o0')+g.pack('r1','o1')+['mov.b32 z,{o0,o1};']
 txt='.version 8.0\n.target sm_86\n.address_size 64\n.visible .entry test(.param .u64 src,.param .u64 dst){\n.reg .b64 s,d;.reg .b32 r0,r1,z;ld.param.u64 s,[src];ld.param.u64 d,[dst];ld.global.v2.u32 {r0,r1},[s];\n'+'\n'.join(body)+'\nst.global.u32 [d],z;ret;}';f=p/f'artifacts/{name}.ptx';f.write_text(txt);subprocess.run([str(bin/'ptxas'),'-arch=sm_86','-O4',str(f),'-o',str(f.with_suffix('.cubin'))],check=True);sass=subprocess.check_output([str(bin/'cuobjdump'),'-sass',str(f.with_suffix('.cubin'))],text=True);(p/f'{name}.sass').write_text(sass);out[name]=re.findall(r'/\*[0-9a-f]+\*/\s+(?:@!?P\d+\s+)?([A-Z][A-Z0-9_.]*)',sass)
(p/'quad-sass.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
