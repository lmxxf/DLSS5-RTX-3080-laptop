from pathlib import Path
import sys,ctypes as c,json,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from codegen import decode,render
from v23.decode import decode as evenodd
from v24.codegen import jit_render
src=(p.parent/'v2/check_primitives.py').read_text();exec(src[:src.index('# All 65536 byte pairs')]);b.dp.mapped_fp16_sources=b.forward_mapped_fp16_sources;b.even_odd_decode_lines=evenodd
# K coordinate proof, including both A row groups and both B K banks.
slots=0
for lane in range(32):
 g,t=divmod(lane,4)
 for phase in [0,1]:
  perm=lambda j:2*j-(j&1)+2*phase
  for reg in range(4):
   for e in range(2):assert (g+8*(reg%2),4*t+e+2*phase+16*(reg//2))==(g+8*(reg%2),perm(2*t+e+8*(reg//2)));slots+=1
  for reg in range(2):
   for e in range(2):assert (4*t+e+2*phase+16*reg,g)==(perm(2*t+e+8*reg),g);slots+=1
assert sorted([2*j-(j&1)+2*phase for phase in [0,1] for j in range(16)])==list(range(32))
i=np.arange(65536,dtype=np.uint32);poison=np.arange(256,dtype=np.uint32)*257;x=(i[:,None]|(poison[None,:]<<16)).reshape(-1)
body='mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;ld.global.u32 %r0,[%sp];.reg .b32 e0,e1,l0,l1,dlssnr_fp8_scale;mov.b32 dlssnr_fp8_scale,0x5c005c00;'+ '\n'.join(evenodd('%r0','e0','e1')+decode('%r0','l0','l1'))+'mul.wide.u32 %off,%idx,16;add.u64 %dp,%dp,%off;st.global.v4.u32 [%dp],{e0,e1,l0,l1};'
for rotate in [False,True]:
 inp=(x<<16)|(x>>16) if rotate else x;r=execute(body,inp,len(inp)*4).reshape(-1,4);lo=(r[:,0]&65535)|((r[:,1]&65535)<<16);hi=(r[:,0]>>16)|(r[:,1]&0xffff0000);assert np.array_equal(lo,r[:,2]) and np.array_equal(hi,r[:,3])
raw='mma.sync.aligned.m16n8k32.row.col.f16.e4m3.e4m3.f16 {%r6,%r7}, {%r0,%r1,%r2,%r3}, {%r4,%r5}, {%r8,%r9};';matches=list(b.dp.FP8_MMA_PATTERN.finditer(raw));rng=np.random.default_rng(2600)

def encode_matrix(A,B,A8,B8):
 nw=len(A);packed=np.zeros((nw,32,18),np.uint32)
 for lane in range(32):
  g,t=divmod(lane,4)
  for reg in range(6):
   vals=[]
   for by in range(4):
    if reg<4:val=A[:,g+8*(reg%2),4*t+by+16*(reg//2)];byte=A8[:,g+8*(reg%2),4*t+by+16*(reg//2)]
    else:val=B[:,4*t+by+16*(reg-4),g];byte=B8[:,4*t+by+16*(reg-4),g]
    packed[:,lane,reg]|=byte.astype(np.uint32)<<(by*8);vals.append(val.astype(np.float16).view(np.uint16).astype(np.uint32))
   packed[:,lane,6+2*reg]=vals[0]|(vals[1]<<16);packed[:,lane,7+2*reg]=vals[2]|(vals[3]<<16)
 return packed

def run_pair(data,mask):
 mapping={f'%r{i}':(f'%r{100+2*i}',f'%r{101+2*i}',-1) for i in range(6) if mask&(1<<i)};nw=len(data)
 old=jit_render(matches,mapping,builder=b);new=render(matches,mapping,builder=b)
 assert '0x5410' not in new and '0x7632' not in new
 body='.reg .b32 '+','.join(f'%r{i}' for i in range(100,112))+';.reg .b32 old0,old1;mul.wide.u32 %off,%idx,72;add.u64 %sp,%sp,%off;'+''.join(f'ld.global.u32 %r{i},[%sp+{4*i}];' for i in range(6))+''.join(f'ld.global.u32 %r{100+i},[%sp+{4*(6+i)}];' for i in range(12))+'mov.b32 %r8,0x38003800;mov.b32 %r9,0x38003800;'+old+'mov.b32 old0,%r6;mov.b32 old1,%r7;'+new+'mul.wide.u32 %off,%idx,16;add.u64 %dp,%dp,%off;st.global.v4.u32 [%dp],{old0,old1,%r6,%r7};'
 mo=execute(body,data.reshape(-1),nw*32*4,nw*32).reshape(nw,32,4);outs=[]
 for part in [0,1]:
  out=np.empty((nw,16,8),np.float32)
  for lane in range(32):
   g,t=divmod(lane,4)
   for reg in [0,1]:
    word=mo[:,lane,part*2+reg];h=np.stack([word&65535,word>>16],axis=1).astype(np.uint16).view(np.float16);out[:,g+8*reg,2*t:2*t+2]=h
  outs.append(out)
 return outs
# All 64 assignments of the six original operand registers to mapped/encoded.
A=rng.integers(-2,3,(16,16,32));B=rng.integers(-2,3,(16,32,8));enc=np.array([0xc0,0xb8,0,0x38,0x40],np.uint32);data=encode_matrix(A,B,enc[A+2],enc[B+2]);gold=(A@B+.5).astype(np.float32)
for mask in range(64):
 old,new=run_pair(data,mask);assert np.array_equal(old,gold) and np.array_equal(new,gold),mask
# Random finite E4M3 and genuinely unquantized mapped FP16 effective matrices.
def fp8(byte):
 ex=((byte&127)>>3).astype(np.int32);ma=byte&7;v=np.where(ex==0,ma*2.**-9,(1+ma/8)*2.**(ex-7));return np.where(byte&128,-v,v).astype(np.float16)
results=[]
for mask in [0,15,63]:
 A8=rng.integers(0,0x49,(256,16,32),dtype=np.uint32)|(rng.integers(0,2,(256,16,32),dtype=np.uint32)<<7);B8=rng.integers(0,0x49,(256,32,8),dtype=np.uint32)|(rng.integers(0,2,(256,32,8),dtype=np.uint32)<<7);Af=fp8(A8);Bf=fp8(B8);Ah=rng.normal(0,.5,Af.shape).astype(np.float16) if mask else Af;Bh=rng.normal(0,.5,Bf.shape).astype(np.float16) if mask==63 else Bf
 data=encode_matrix(Ah,Bh,A8,B8);old,new=run_pair(data,mask);Ae=Ah if mask&15==15 else Af;Be=Bh if mask&48==48 else Bf;gold=(Ae.astype(np.float64)@Be.astype(np.float64)+.5).astype(np.float32)
 def error(v):
  d=v.astype(float)-gold;return {'rmse':float(np.sqrt(np.mean(d*d))),'mae':float(np.mean(abs(d))),'p99_abs':float(np.quantile(abs(d),.99)),'maxabs':float(np.max(abs(d))),'nonfinite':int(np.count_nonzero(~np.isfinite(v)))}
 results.append({'mapped_mask':mask,'matrix_cases':256,'FP32_gold':'FP16 effective inputs multiplied/summed in float64, rounded to float32; C=0.5','evenodd':error(old),'lowhigh':error(new),'output_bitdiff':int(np.count_nonzero(old.view(np.uint32)!=new.view(np.uint32)))})
assert all(r['evenodd']['nonfinite']==r['lowhigh']['nonfinite']==0 for r in results)
r={'coordinate_slots':slots,'original_K_from_K16':'2*j-(j&1)+2*phase; not contiguous global K halves','decode_pair_tests':33554432,'decode_permutation_bitdiff':0,'exact_integer_matrix_cases_per_mask':16,'mapped_masks_tested':64,'exact_matrix_mismatches':0,'random_effective_input_results':results}
(p/'primitives.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));ck(cu.cuCtxDestroy_v2(ctx))
