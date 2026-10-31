from pathlib import Path
import sys,json,ctypes as c,numpy as np,re
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
import v31.codegen as pack;pack.MODE='pack5';import local_quad
src=(p.parent/'v2/check_primitives.py').read_text();exec(src[:src.index('# All 65536 byte pairs')]);b.dp.half_conversion_declarations=pack.declarations;b.dp.half_pair_to_fp8_lines=pack.pack
class Stats:
 def add(self,*a):pass
pair='cvt.rn.satfinite.e4m3x2.f16x2 %rs0,%r0;\ncvt.rn.satfinite.e4m3x2.f16x2 %rs1,%r1;\nmov.b32 %r2,{%rs0,%rs1};\n'
cases={'plain':pair,'reused_names':pair+'xor.b32 %r0,%r0,0x55555555;\n'+pair,'nested':'{\n'+pair+'\n}','live_out':pair+'cvt.u32.u16 %r5,%rs0;\nxor.b32 %r2,%r2,%r5;','overwrite_after':pair+'mov.b16 %rs0,0;\ncvt.u32.u16 %r5,%rs0;\nxor.b32 %r2,%r2,%r5;','conditional_overwrite':pair+'setp.ne.u32 %p0,%r0,0;\n@%p0 mov.b16 %rs0,0;\ncvt.u32.u16 %r5,%rs0;\nxor.b32 %r2,%r2,%r5;'}
rows=[];i=np.arange(65536,dtype=np.uint32);data=i|(np.uint32(0xa55a)<<16)
for name,code in cases.items():
 text='.visible .entry fixture(){\n.reg .b16 %rs<4>;\n.reg .pred %p0;\n'+code+'\nret;\n}'
 local_quad.AUDIT=[];fused=local_quad.fuse_quads(text,Stats(),False);count=local_quad.AUDIT[0]['fused'];old=b.dp.lower_fp8_conversions(text,Stats());new=b.dp.lower_fp8_conversions(fused,Stats())
 def inner(s):return s[s.index('{')+1:s.rfind('}')].rsplit('ret;',1)[0]
 init='ld.global.u32 %r0,[%sp];xor.b32 %r1,%r0,0x55aa3355;'
 body='.reg .b32 old;mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;'+init+'{'+inner(old)+'mov.b32 old,%r2;}'+init+'{'+inner(new)+'}mul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{old,%r2};'
 out=execute(body,data,len(data)*2).reshape(-1,2);bad=int(np.count_nonzero(out[:,0]!=out[:,1]));assert bad==0;rows.append({'case':name,'input_patterns':len(data),'fused_pairs':count,'bitdiff':bad});print(rows[-1],flush=True)
# Quantization is not identity: forwarding unquantized native half is unsafe.
body='mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;ld.global.u32 %r0,[%sp];'+ '\n'.join(pack.declarations()+b.fast_fp8_conversion_declarations()+['.reg .b16 packed;']+pack.pack('%r0','packed')+['cvt.u32.u16 %r2,packed;']+b.fast_fp8_pair_to_half_lines('%r2','%r1'))+'mul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r0,%r1};'
data=i|(i<<16);out=execute(body,data,len(data)*2).reshape(-1,2);sample=out[0x3c40];assert sample[0]!=sample[1]
quant={'half_patterns':65536,'changed_word_patterns':int(np.count_nonzero(out[:,0]!=out[:,1])),'example_original_word':hex(int(sample[0])),'example_expanded_word':hex(int(sample[1])),'original_half_value':float(np.array([0x3c40],np.uint16).view(np.float16)[0]),'expanded_half_value':float(np.array([sample[1]&65535],np.uint16).view(np.float16)[0]),'scope':'same pack5 and old UP as frozen baseline; demonstrates non-identity, not image quality metric'}
(p/'local-gpu-tests.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'quantization-counterexample.json').write_text(json.dumps(quant,indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx))
