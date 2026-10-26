from pathlib import Path
import sys,ctypes as c,json,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
art=p/'artifacts';art.mkdir(exist_ok=True)
cu=c.CDLL('/usr/lib/wsl/lib/libcuda.so.1')
def ck(x):assert x==0,x
ck(cu.cuInit(0));dev=c.c_int();ck(cu.cuDeviceGet(c.byref(dev),0));ctx=c.c_void_p();ck(cu.cuCtxCreate_v2(c.byref(ctx),0,dev))
def execute(body,inp,words,threads=None):
 ptx='''.version 8.0
.target sm_86
.address_size 64
.visible .entry test(.param .u64 src,.param .u64 dst){
.reg .b32 %idx,%t,%a,%r0,%r1,%r2,%r3,%r4,%r5,%r6,%r7,%r8,%r9;
.reg .b64 %sp,%dp,%off;
ld.param.u64 %sp,[src];ld.param.u64 %dp,[dst];mov.u32 %a,%ctaid.x;mov.u32 %t,%tid.x;mad.lo.u32 %idx,%a,32,%t;
'''+body+'\nret;}'
 (art/'primitive.ptx').write_text(ptx);mod=c.c_void_p();ck(cu.cuModuleLoadData(c.byref(mod),c.c_char_p(ptx.encode())));fn=c.c_void_p();ck(cu.cuModuleGetFunction(c.byref(fn),mod,b'test'))
 src=c.c_uint64();dst=c.c_uint64();out=np.zeros(words,np.uint32)
 ck(cu.cuMemAlloc_v2(c.byref(src),c.c_size_t(inp.nbytes)));ck(cu.cuMemAlloc_v2(c.byref(dst),c.c_size_t(out.nbytes)));ck(cu.cuMemcpyHtoD_v2(src,c.c_void_p(inp.ctypes.data),c.c_size_t(inp.nbytes)))
 args=(c.c_void_p*2)(c.cast(c.byref(src),c.c_void_p),c.cast(c.byref(dst),c.c_void_p));ck(cu.cuLaunchKernel(fn,(threads or len(inp))//32,1,1,32,1,1,0,None,args,None));ck(cu.cuCtxSynchronize());ck(cu.cuMemcpyDtoH_v2(c.c_void_p(out.ctypes.data),dst,c.c_size_t(out.nbytes)));ck(cu.cuMemFree_v2(src));ck(cu.cuMemFree_v2(dst));ck(cu.cuModuleUnload(mod));return out
# All 65536 byte pairs in even and odd positions; other bytes deliberately differ.
i=np.arange(65536,dtype=np.uint32);lo=i&255;hi=i>>8
inp=lo|(hi<<16)|((255-lo)<<8)|((255-hi)<<24)
body='mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;ld.global.u32 %r0,[%sp];\n'+ '\n'.join(b.fast_fp8_conversion_declarations())+'\n.reg .b32 first,second;mov.b32 dlssnr_fp8_scale,0x5c005c00;\n'+'\n'.join(b.even_odd_decode_lines('%r0','first','second'))+'\nmul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{first,second};'
out=execute(body,inp,2*len(inp)).reshape(-1,2)
def half(v):
 ex=((v&127)>>3).astype(np.int32);ma=v&7;val=np.where(ex==0,ma*2.**-9,(1+ma/8)*2.**(ex-7));h=val.astype(np.float16).view(np.uint16).astype(np.uint32);return h|((v&128)<<8)
valid=((lo&127)!=127)&((hi&127)!=127)
for par in [0,1]:
 a=(inp>>(8*par))&255;z=(inp>>(16+8*par))&255;v=((a&127)!=127)&((z&127)!=127);expected=half(a)|(half(z)<<16);assert np.array_equal(out[v,par],expected[v]),par
# Coordinate proof: the new A and B slots use the identical permutation k_original=2*k16+parity.
slots=0
for lane in range(32):
 g,t=divmod(lane,4)
 for par in [0,1]:
  for reg in range(4):
   for e in range(2):
    orig=(g+8*(reg%2),4*t+2*e+par+16*(reg//2));native=(g+8*(reg%2),2*(2*t+e+8*(reg//2))+par);assert orig==native;slots+=1
  for reg in range(2):
   for e in range(2):assert (4*t+2*e+par+16*reg,g)==(2*(2*t+e+8*reg)+par,g);slots+=1
# All half lane labels exercise mapped PRMT pair selection, including signs/subnormals.
body='mul.wide.u32 %off,%idx,8;add.u64 %sp,%sp,%off;ld.global.v2.u32 {%r0,%r1},[%sp];prmt.b32 %r2,%r0,%r1,0x5410;prmt.b32 %r3,%r0,%r1,0x7632;mul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r2,%r3};'
mp=np.stack([i|((65535-i)<<16),((i^0x55aa)&65535)|(((i^0xaa55)&65535)<<16)],axis=1).reshape(-1);mo=execute(body,mp,len(mp),len(mp)//2).reshape(-1,2);mi=mp.reshape(-1,2)
assert np.array_equal(mo[:,0],(mi[:,0]&65535)|((mi[:,1]&65535)<<16));assert np.array_equal(mo[:,1],(mi[:,0]>>16)|(mi[:,1]&0xffff0000))
# Actual generated MMA against independent integer matrix products (exactly representable).
rng=np.random.default_rng(1616);nw=64
A=rng.integers(-2,3,(nw,16,32));B=rng.integers(-2,3,(nw,32,8));enc=np.array([0xc0,0xb8,0,0x38,0x40],np.uint32)
packed=np.zeros((nw,32,6),np.uint32)
for lane in range(32):
 g,t=divmod(lane,4)
 for reg in range(4):
  for by in range(4):packed[:,lane,reg]|=enc[A[:,g+8*(reg%2),4*t+by+16*(reg//2)]+2]<<(8*by)
 for reg in range(2):
  for by in range(4):packed[:,lane,4+reg]|=enc[B[:,4*t+by+16*reg,g]+2]<<(8*by)
raw='mma.sync.aligned.m16n8k32.row.col.f16.e4m3.e4m3.f16 {%r6,%r7}, {%r0,%r1,%r2,%r3}, {%r4,%r5}, {%r8,%r9};'
match=list(b.dp.FP8_MMA_PATTERN.finditer(raw));assert len(match)==1
b.dp.mapped_fp16_sources=b.forward_mapped_fp16_sources
lower=b.fast_render_fp8_mma_run(match,{})
assert 'shfl.' not in lower and 'prmt.' not in lower
body='mul.wide.u32 %off,%idx,24;add.u64 %sp,%sp,%off;'+''.join(f'ld.global.u32 %r{i},[%sp+{4*i}];' for i in range(6))+'mov.b32 %r8,0x38003800;mov.b32 %r9,0x38003800;'+lower+'mul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r6,%r7};'
mo=execute(body,packed.reshape(-1),nw*32*2,nw*32).reshape(nw,32,2);expected=np.matmul(A,B)+0.5
for lane in range(32):
 g,t=divmod(lane,4)
 for reg in range(2):
  vals=expected[:,g+8*reg,2*t:2*t+2].astype(np.float16).view(np.uint16).astype(np.uint32);words=vals[:,0]|(vals[:,1]<<16);assert np.array_equal(mo[:,lane,reg],words),(lane,reg)
(p/'primitives.json').write_text(json.dumps({'finite_pair_count_each_parity':int(valid.sum()),'byte_pairs_tested_each_parity':65536,'mismatches':0,'coordinate_slots':slots,'mapped_prmt_cases':65536,'actual_generated_MMA_matrix_cases':nw,'MMA_output_elements':nw*16*8,'scope':'finite E4M3 decode, all half-bit mapped permutation, exact K coordinate permutation; not legacy FP16 rounding equivalence'},indent=2)+'\n');print('PASS decode finite pairs, mapped PRMT,768 A/B coordinate slots')
ck(cu.cuCtxDestroy_v2(ctx))
