from pathlib import Path
import sys,ctypes as c,json,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from codegen import decode,render
import codegen;codegen.MODE=__import__('os').environ.get('V33_MODE','phase_pass')
src=(p.parent/'v2/check_primitives.py').read_text();snippet=src[:src.index('# All 65536 byte pairs')]
if codegen.MODE=='remat_call':snippet=snippet.replace(" (art/'primitive.ptx').write_text(ptx)"," ptx=ptx.replace('.visible .entry test',codegen.helper_functions()+'.visible .entry test');(art/'primitive.ptx').write_text(ptx)")
exec(snippet)
def reference(ms,mapped):
 rs=list(dict.fromkeys(m[n] for m in ms for n in ('a0','a1','a2','a3','b0','b1')));names={r:(f'ref{i}_0',f'ref{i}_1') for i,r in enumerate(rs)}
 lines=['{','.reg .b32 '+','.join(x for pair in names.values() for x in pair)+';','.reg .b32 dlssnr_fp8_scale;mov.b32 dlssnr_fp8_scale,0x5c005c00;']
 for r in rs:
  if r in mapped:lines += [f'mov.b32 {names[r][j]}, {mapped[r][j]};' for j in [0,1]]
  else:lines+=decode(r,*names[r])
 for m in ms:
  for ph in [0,1]:
   a=[names[m[n]][ph] for n in ('a0','a1','a2','a3')];bb=[names[m[n]][ph] for n in ('b0','b1')];cc=[m['c0'],m['c1']] if ph==0 else [m['d0'],m['d1']]
   lines.append(f'mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16 {{{m["d0"]},{m["d1"]}}}, {{{",".join(a)}}}, {{{",".join(bb)}}}, {{{",".join(cc)}}};')
 return '\n'.join(lines+['}'])
rng=np.random.default_rng(2601);vals=np.array([0,0x30,0xb0,0x38,0xb8,0x40,0xc0],np.uint32);x=rng.choice(vals,(128*32,48,4));data=(x[:,:,0]|(x[:,:,1]<<8)|(x[:,:,2]<<16)|(x[:,:,3]<<24)).reshape(-1);rows=[]
cases=[('same_K32_second_half',1,{'%r200':('%r300','%r301',-1)},300,1),('late_shared_sources',64,{'%r204':('%r300','%r301',-1),'%r205':('%r300','%r301',-1)},300,2),('same_low_high_source',64,{'%r204':('%r300','%r300',-1)},300,1),('late_encoded_clobber',64,{},204,0),('encoded_same_half_clobber',1,{},200,0),('encoded_before_first_use',64,{},220,0),('all_mapped_no_clobber',64,{f'%r{i}':('%r400','%r401',-1) for i in range(200,248)},300,0)]
for name,n,mapping,d0,copies in cases:
 raw='\n'.join('mma.sync.aligned.m16n8k32.row.col.f16.e4m3.e4m3.f16 {'+f'%r{d0},%r301'+'}, {'+','.join(f'%r{200+4*(i//16)+j}' for j in range(4))+'}, {'+','.join(f'%r{216+2*(i%16)+j}' for j in range(2))+'}, {'+f'%r{d0},%r301'+'};' for i in range(n));ms=list(b.dp.FP8_MMA_PATTERN.finditer(raw));audit=[];candidate=render(ms,mapping,builder=b,audit=audit);assert audit[0]['backup_moves']>=0
 if name=='all_mapped_no_clobber':assert audit[0]['temporary_b32_peak']==0 and 'prmt.' not in candidate
 init=''.join(f'ld.global.u32 %r{200+i},[%sp+{4*i}];' for i in range(48))+'mov.b32 %r300,0x38003800;mov.b32 %r301,0x38003800;mov.b32 %r400,0x38003800;mov.b32 %r401,0x38003800;'
 body='.reg .b32 '+','.join(f'%r{i}' for i in list(range(200,248))+[300,301,400,401])+';mul.wide.u32 %off,%idx,192;add.u64 %sp,%sp,%off;'+init+reference(ms,mapping)+f'mov.b32 %r0,%r{d0};mov.b32 %r1,%r301;'+init+candidate+'mul.wide.u32 %off,%idx,16;add.u64 %dp,%dp,%off;st.global.v4.u32 [%dp],{'+f'%r0,%r1,%r{d0},%r301'+'};'
 out=execute(body,data,128*32*4,128*32).reshape(-1,4);bad=int(np.count_nonzero(out[:,:2]!=out[:,2:]));assert bad==0,(name,bad);rows.append({'case':name,'warps':128,'K32_MMA_per_run':n,'word_bitdiff_against_independent_upfront_lowhigh':bad,'codegen':audit[0]});print(name,'PASS',flush=True)
(p/('alias-'+(__import__('os').environ.get('V33_MODE','phase_pass'))+'.json')).write_text(json.dumps(rows,indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx))
