from pathlib import Path
import sys,ctypes as c,json,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
import codegen as gen
import v29.codegen as old
old.MODE='fast'
src=(p.parent/'v2/check_primitives.py').read_text();exec(src[:src.index('# All 65536 byte pairs')])
results={};load='mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;ld.global.u32 %r0,[%sp];\n';store='\ncvt.u32.u16 %r1,old16;cvt.u32.u16 %r2,new16;mul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r1,%r2};'
for mode in ['pack8','pack5','pack5_quad']:
 gen.MODE=mode;checks=[]
 for rotate in [False,True]:
  i=np.arange(65536,dtype=np.uint32);poison=np.arange(256,dtype=np.uint32)*257;x=(i[:,None]|(poison[None,:]<<16)).reshape(-1)
  if rotate:x=(x<<16)|(x>>16)
  if mode!='pack5_quad':body=load+'\n'.join(old.declarations()+gen.declarations()+['.reg .b16 old16,new16;']+old.pack('%r0','old16')+gen.pack('%r0','new16'))+store
  else:body=load+'xor.b32 %r3,%r0,0xa55a5aa5;\n'+'\n'.join(gen.declarations()+['.reg .b16 o0,o1;']+gen.pack('%r0','o0')+gen.pack('%r3','o1'))+'\nmov.b32 %r1,{o0,o1};\n'+'\n'.join(gen.quad('%r0','%r3','%r2'))+'\nmul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r1,%r2};'
  r=execute(body,x,2*len(x)).reshape(-1,2);bad=r[:,0]!=r[:,1];rec={'rotate':rotate,'pairs':len(x),'mismatch_pairs':int(bad.sum())}
  if mode=='pack5':
   lane=16 if rotate else 0;mask=((r[:,0]>>(8 if rotate else 0))&255)!=((r[:,1]>>(8 if rotate else 0))&255);rec['varying_half_mismatch_values']=len(np.unique((x[mask]>>lane)&65535))
  else:assert not bad.any(),(mode,rec)
  checks.append(rec)
 results[mode]=checks;print(mode,checks,flush=True)
(p/'primitives.json').write_text(json.dumps(results,indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx))
