from pathlib import Path
import sys,subprocess,json,re
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import v29.codegen as old;old.MODE="fast";import codegen as new
bin=Path('/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin');rows={};art=p/'artifacts';art.mkdir(exist_ok=True)
for mode in ['baseline','pack8','pack5']:
 new.MODE=mode;g=old if mode=='baseline' else new
 text='.version 8.0\n.target sm_86\n.address_size 64\n.visible .entry test(.param .u64 src,.param .u64 dst){\n.reg .b64 s,d; .reg .b32 r; .reg .b16 o;\nld.param.u64 s,[src];ld.param.u64 d,[dst];ld.global.u32 r,[s];\n'+'\n'.join(g.declarations()+g.pack('r','o'))+'\nst.global.u16 [d],o;ret;}\n';f=art/f'{mode}-pack.ptx';f.write_text(text);out=f.with_suffix('.cubin');subprocess.run([str(bin/'ptxas'),'-arch=sm_86','-O4',str(f),'-o',str(out)],check=True);s=subprocess.check_output([str(bin/'cuobjdump'),'-sass',str(out)],text=True);(p/f'{mode}-pack.sass').write_text(s);ops=re.findall(r'/\*[0-9a-f]+\*/\s+(?:@!?P\d+\s+)?([A-Z][A-Z0-9_.]*)',s);rows[mode]=ops
(p/'isolated-sass.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
