from pathlib import Path
import sys,json,ctypes as c,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
import codegen as gen
src=(p.parent/'v2/check_primitives.py').read_text();exec(src[:src.index('# All 65536 byte pairs')])
refsrc=(p/'check_alias.py').read_text();ns={'decode':gen.decode};exec(refsrc[refsrc.index('def reference'):refsrc.index('rng=np.random')],ns);reference=ns['reference']
rng=np.random.default_rng(3300);val=np.array([0,0x30,0xb0,0x38,0xb8,0x40,0xc0],np.uint32);x=rng.choice(val,(128*32,48,4));data=(x[:,:,0]|(x[:,:,1]<<8)|(x[:,:,2]<<16)|(x[:,:,3]<<24)).reshape(-1);rows=[]
for mode in ['phase_pass','remat']:
 gen.MODE=mode
 for dependent in [False,True]:
  lines=[]
  for layer in range(4):
   for chain in range(4):
    d=300+2*chain;c0=d-2 if dependent and chain else d;c1=c0+1
    lines.append('mma.sync.aligned.m16n8k32.row.col.f16.e4m3.e4m3.f16 {'+f'%r{d},%r{d+1}'+'}, {'+','.join(f'%r{200+4*layer+j}' for j in range(4))+'}, {'+f'%r{232+2*chain},%r{233+2*chain}'+'}, {'+f'%r{c0},%r{c1}'+'};')
  ms=list(b.dp.FP8_MMA_PATTERN.finditer('\n'.join(lines)));a=[];candidate=gen.render(ms,{},builder=b,audit=a)
  if mode=='phase_pass':assert a[0]['decoded_half_events']==a[0]['original_decoded_half_events']
  init=''.join(f'ld.global.u32 %r{200+i},[%sp+{4*i}];' for i in range(48))+''.join(f'mov.b32 %r{i},0x38003800;' for i in range(300,308))
  body='.reg .b32 '+','.join([f'%r{i}' for i in list(range(200,248))+list(range(300,308))]+[f'old{i}' for i in range(8)])+';mul.wide.u32 %off,%idx,192;add.u64 %sp,%sp,%off;'+init+reference(ms,{})+''.join(f'mov.b32 old{i},%r{300+i};' for i in range(8))+init+candidate+'mul.wide.u32 %off,%idx,64;add.u64 %dp,%dp,%off;'
  for offset,regs in [(0,[f'old{i}' for i in range(4)]),(16,[f'old{i}' for i in range(4,8)]),(32,[f'%r{i}' for i in range(300,304)]),(48,[f'%r{i}' for i in range(304,308)])]:body+=f'st.global.v4.u32 [%dp+{offset}],{{'+','.join(regs)+'};'
  out=execute(body,data,128*32*16,128*32).reshape(-1,16);bad=int(np.count_nonzero(out[:,:8]!=out[:,8:]));assert bad==0;rows.append({'mode':mode,'dependent_accumulators':dependent,'word_bitdiff':bad,'audit':a[0]});print(mode,dependent,'PASS',a[0]['temporary_b32_peak'],flush=True)
(p/'layer-tests.json').write_text(json.dumps(rows,indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx))
