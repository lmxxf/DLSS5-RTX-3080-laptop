from pathlib import Path
import sys,json,numpy as np,subprocess,re,collections
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from pack_range import pack,declarations
from quad import code
src=(p.parent/'v2/check_primitives.py').read_text();exec(src[:src.index('# All 65536 byte pairs')]);records=[];i=np.arange(65536,dtype=np.uint32);poison=np.arange(256,dtype=np.uint32)*257;x=(i[:,None]|(poison[None,:]<<16)).reshape(-1)
load='mul.wide.u32 %off,%idx,8;add.u64 %sp,%sp,%off;ld.global.v2.u32 {%r0,%r3},[%sp];'
ref='\n'.join(declarations()+['.reg .b16 pl,ph;']+pack('%r0','pl','pack4')+pack('%r3','ph','pack4')+['mov.b32 %r1,{pl,ph};'])
for rotate in [False,True]:
 a=(x<<16)|(x>>16) if rotate else x;data=np.stack([a,a^np.uint32(0xa55a5aa5)],axis=1).reshape(-1)
 body=load+ref+'\n'.join(code('%r0','%r3','%r2'))+'mul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r1,%r2};';out=execute(body,data,len(data),len(a)).reshape(-1,2);bad=int(np.count_nonzero(out[:,0]!=out[:,1]));assert bad==0;records.append({'rotate':rotate,'quad_cases':len(a),'mismatches':bad,'domain':'all 65536 low-half bit patterns x256 opposite-half poison patterns, xor-related second half2 input, rotated second pass; finite, subnormal, +/-0, Inf, NaN included'});print(records[-1],flush=True)
tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/ptxas';evidence={}
for name,calc,dst in [('two_pack4_join',ref,'%r1'),('pack4_quad','\n'.join(code('%r0','%r3','%r2')),'%r2')]:
 text='.version 8.0\n.target sm_86\n.address_size 64\n.visible .entry test(.param .u64 src,.param .u64 dst){.reg .b32 %idx,%a,%t,%r0,%r1,%r2,%r3;.reg .b64 %sp,%dp,%off;ld.param.u64 %sp,[src];ld.param.u64 %dp,[dst];mov.u32 %a,%ctaid.x;mov.u32 %t,%tid.x;mad.lo.u32 %idx,%a,32,%t;'+load+calc+'mul.wide.u32 %off,%idx,4;add.u64 %dp,%dp,%off;st.global.u32 [%dp],'+dst+';ret;}'
 f=p/f'artifacts/{name}.ptx';f.write_text(text);r=subprocess.run([tool,'-arch=sm_86','-O4',str(f),'-o',str(f.with_suffix('.cubin'))],capture_output=True,text=True);assert r.returncode==0,r.stderr;sass=subprocess.check_output([tool.replace('ptxas','cuobjdump'),'-sass',str(f.with_suffix('.cubin'))],text=True);parsed=[(m[1],m[2]) for m in re.finditer(r'/\*[0-9a-f]+\*/\s+(?:@!?P\d+\s+)?([A-Z][A-Z0-9_.]*)\s+([^;]+);',sass)];last=next(j for j in range(len(parsed)-1,-1,-1) if parsed[j][0].startswith('STG'));need={re.findall(r'R\d+',parsed[last][1])[-1]};core=[]
 for op,args in parsed[:last][::-1]:
  regs=re.findall(r'R\d+',args)
  if not regs:continue
  dest={regs[0]}
  if op.startswith('LDG'):
   count=4 if '.128' in op else 2 if '.64' in op else 1;dest={f'R{int(regs[0][1:])+j}' for j in range(count)}
  if not dest&need:continue
  need-=dest
  if op.startswith('LDG'):continue
  need.update(regs[1:])
  if op.split('.')[0] in ['HMUL2','LEA','LOP3','PRMT']:core.append(op)
 core=core[::-1];evidence[name]={'core':core,'core_count':len(core),'scope':'store-value backwards slice; LDG64 defines both registers; address LEAs excluded','sass':sass,'ptxas_O4':True,'compiler_output':r.stdout+r.stderr}
assert collections.Counter(x.split('.')[0] for x in evidence['pack4_quad']['core'])=={'HMUL2':2,'LEA':2,'LOP3':2,'PRMT':1},evidence
(p/'quad-primitive.json').write_text(json.dumps({'passed':True,'tests':records,'total_quad_cases':sum(r['quad_cases'] for r in records),'relative_reference':'two existing V4.0 Pack4 operations plus mov.b32 concatenation; no new clamp removal','machine_evidence':evidence},indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx));print('core counts',{n:r['core_count'] for n,r in evidence.items()})
