from pathlib import Path
import sys,ctypes as c,json,numpy as np,subprocess,re
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
import v31.codegen as old;old.MODE='pack5';import pack_range as new
from v26.codegen import decode
src=(p.parent/'v2/check_primitives.py').read_text();exec(src[:src.index('# All 65536 byte pairs')]);records=[];load='mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;ld.global.u32 %r0,[%sp];';store='mul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r1,%r2};'
allh=np.arange(65536,dtype=np.uint32);hf=allh.astype(np.uint16).view(np.float16);bounded=allh[np.isfinite(hf)&(np.abs(hf)<=448)];positive=allh[np.isfinite(hf)&(hf>=0)&(hf<=448)&((allh&0x8000)==0)]
for kind,domain in [('pack4',bounded),('pack3',positive)]:
 for rotate in [False,True]:
  idx=np.arange(65536,dtype=np.uint32);lo=domain[idx%len(domain)];hi=domain[(np.arange(256,dtype=np.uint32)*127)%len(domain)];data=(lo[:,None]|(hi[None,:]<<16)).reshape(-1)
  if rotate:data=(data<<16)|(data>>16)
  body=load+'\n'.join(old.declarations()+new.declarations()+['.reg .b16 a,z;']+old.pack('%r0','a')+new.pack('%r0','z',kind)+['cvt.u32.u16 %r1,a;','cvt.u32.u16 %r2,z;'])+store
  out=execute(body,data,len(data)*2).reshape(-1,2);bad=int(np.count_nonzero(out[:,0]!=out[:,1]));assert bad==0;records.append({'test':kind,'domain_half_count':len(domain),'pairs':len(data),'rotate':rotate,'mismatches':bad});print(records[-1],flush=True)
# New all-byte inverse codec, including old decoder's +/-480 for 7f/ff.
i=np.arange(65536,dtype=np.uint32);poison=np.arange(256,dtype=np.uint32)*257;data=(i[:,None]|(poison[None,:]<<16)).reshape(-1)
for rotate in [False,True]:
 x=(data<<16)|(data>>16) if rotate else data
 body=load+'\n'.join(['.reg .b32 lo,hi,dlssnr_fp8_scale;','mov.b32 dlssnr_fp8_scale,0x5c005c00;']+decode('%r0','lo','hi')+new.declarations()+['.reg .b16 a,z;']+new.pack('lo','a','pack4')+new.pack('hi','z','pack4')+['mov.b32 %r2,{a,z};','mov.b32 %r1,%r0;'])+store
 out=execute(body,x,len(x)*2).reshape(-1,2);bad=int(np.count_nonzero(out[:,0]!=out[:,1]));assert bad==0;records.append({'test':'all-byte inverse including reserved codes','pairs':len(x),'rotate':rotate,'mismatches':bad})
# Standalone ptxas -O4 evidence, not assumed instruction counts.
ptxas='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/ptxas';obj=ptxas.replace('ptxas','cuobjdump');sass={}
for kind in ['pack4','pack3']:
 body=load+'\n'.join(new.declarations()+['.reg .b16 a;']+new.pack('%r0','a',kind)+['cvt.u32.u16 %r1,a;'])+'mul.wide.u32 %off,%idx,4;add.u64 %dp,%dp,%off;st.global.u32 [%dp],%r1;'
 text='.version 8.0\n.target sm_86\n.address_size 64\n.visible .entry test(.param .u64 src,.param .u64 dst){\n.reg .b32 %idx,%a,%t,%r0,%r1; .reg .b64 %off,%sp,%dp;\nld.param.u64 %sp,[src];ld.param.u64 %dp,[dst];mov.u32 %a,%ctaid.x;mov.u32 %t,%tid.x;mad.lo.u32 %idx,%a,32,%t;\n'+body+'ret;}'
 f=p/f'artifacts/{kind}.ptx';f.write_text(text);cuout=p/f'artifacts/{kind}.cubin';r=subprocess.run([ptxas,'-arch=sm_86','-O4',str(f),'-o',str(cuout)],text=True,capture_output=True);assert r.returncode==0,r.stderr;text=subprocess.check_output([obj,'-sass',str(cuout)],text=True);ops=re.findall(r'/\*[0-9a-f]+\*/\s+(?:@!?P\d+\s+)?([A-Z][A-Z0-9_.]*)',text);parsed=[(m[1],m[2]) for m in re.finditer(r'/\*[0-9a-f]+\*/\s+(?:@!?P\d+\s+)?([A-Z][A-Z0-9_.]*)\s+([^;]+);',text)];last=next(i for i in range(len(parsed)-1,-1,-1) if parsed[i][0].startswith('STG'));need={re.findall(r'R\d+',parsed[last][1])[-1]};core=[]
 for op,arg in parsed[:last][::-1]:
  rr=re.findall(r'R\d+',arg)
  if not rr or rr[0] not in need:continue
  need.remove(rr[0])
  if op.startswith('LDG'):continue
  need.update(rr[1:])
  if op.split('.')[0] in ['HMUL2','HMNMX2','LEA','LOP3','PRMT']:core.append(op)
 core=core[::-1];sass[kind]={'core':core,'core_count':len(core),'sass':text,'ptxas_args':['-arch=sm_86','-O4'],'compiler_output':r.stdout+r.stderr}
(p/'primitive-tests.json').write_text(json.dumps(records,indent=2)+'\n');(p/'isolated-sass.json').write_text(json.dumps(sass,indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx));print('PASS',sass.keys())
