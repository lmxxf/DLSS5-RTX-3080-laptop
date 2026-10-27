from pathlib import Path
import sys,ctypes as c,json,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from codegen import jit_render
from v23.decode import decode
src=(p.parent/'v2/check_primitives.py').read_text();exec(src[:src.index('# All 65536 byte pairs')]);b.dp.mapped_fp16_sources=b.forward_mapped_fp16_sources;b.even_odd_decode_lines=decode
raw='\n'.join('mma.sync.aligned.m16n8k32.row.col.f16.e4m3.e4m3.f16 {%r300,%r301}, {'+','.join(f'%r{200+4*(i//16)+j}' for j in range(4))+'}, {'+','.join(f'%r{216+2*(i%16)+j}' for j in range(2))+'}, {%r300,%r301};' for i in range(64));ms=list(b.dp.FP8_MMA_PATTERN.finditer(raw));assert len(ms)==64
rng=np.random.default_rng(2400);vals=np.array([0,0x30,0xb0,0x38,0xb8,0x40,0xc0],np.uint32);x=rng.choice(vals,size=(128*32,48,4));x=(x[:,:,0]|(x[:,:,1]<<8)|(x[:,:,2]<<16)|(x[:,:,3]<<24)).reshape(-1);rows=[]
for mapped in [{},{'%r204':('%r300','%r301',-1)}]:
 old=b.fast_render_fp8_mma_run(ms,mapped);new=jit_render(ms,mapped,builder=b)
 body='.reg .b32 '+','.join(f'%r{i}' for i in list(range(200,248))+[300,301])+';mul.wide.u32 %off,%idx,192;add.u64 %sp,%sp,%off;'+''.join(f'ld.global.u32 %r{200+j},[%sp+{4*j}];' for j in range(48))+'mov.b32 %r300,0x38003800;mov.b32 %r301,0x38003800;'+old+'mov.b32 %r0,%r300;mov.b32 %r1,%r301;mov.b32 %r300,0x38003800;mov.b32 %r301,0x38003800;'+new+'mul.wide.u32 %off,%idx,16;add.u64 %dp,%dp,%off;st.global.v4.u32 [%dp],{%r0,%r1,%r300,%r301};'
 r=execute(body,x,128*32*4,128*32).reshape(-1,4);diff=int(np.count_nonzero(r[:,:2]!=r[:,2:]));assert diff==0;rows.append({'mapped_accumulator_clobber_hazard':bool(mapped),'warps':128,'MMA_per_run':64,'word_bitdiff':diff})
(p/'pool-test.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows);ck(cu.cuCtxDestroy_v2(ctx))
