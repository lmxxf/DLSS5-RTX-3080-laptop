from pathlib import Path
import subprocess,os,shutil,re,json,numpy as np
r=Path(__file__).resolve().parents[1];p=r/'phase14';src=p/'artifacts/host';out=p/'artifacts/geometry-host';out.mkdir(exist_ok=True)
for f in src.glob('*.h'):shutil.copy2(f,out/f.name)
s=(r/'Development/HIP/benchmark_cuda_nn.cpp').read_text();mark='CaseConfig cases[] = {';assert s.count(mark)==1;s=s.replace(mark,mark+'''
        {"0.5x_Small_512 (31-block,512x512)", "0.5", true, 512,512},
        {"0.5x_Small_1024 (31-block,1024x768)", "0.5", true, 1024,768},
''');(out/'benchmark_cuda_nn.cpp').write_text(s)
subprocess.run(['c++','-O3','-std=c++17',str(out/'benchmark_cuda_nn.cpp'),'-ldl','-o',str(out/'benchmark_cuda_nn')],check=True)
rows=[]
for w,h,tokens in [(512,512,64),(896,512,128),(1024,768,192)]:
 images={}
 for cap in [256,400]:
  variant=f'geometry-{w}-{cap}';env=os.environ.copy();env.update(DLSS5_BENCH_WIDTH=str(w),DLSS5_BENCH_GRAPH='0',DLSS5_AMPERE_WEIGHTS='1',DLSS5_BENCH_SMALL_ONLY='1',DLSS5_LAB_COMPACT_ALL='1',DLSS5_LAB_C256_SPLIT='0',DLSS5_LAB_ATTN400='0' if cap==256 else '1',DLSS5_BENCH_PROFILE='1',DLSS5_BENCH_DUMP=str(p/'artifacts/outputs'/variant))
  log=p/(variant+'.log')
  with log.open('w') as f:ret=subprocess.run([str(out/'benchmark_cuda_nn'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(p/'artifacts/selected/modules'),'0','1'],env=env,stdout=f,stderr=subprocess.STDOUT)
  assert ret.returncode==0,log;s=log.read_text();v=re.search(r'Validity : invalid=(\d+).*?bit_diff_first_last=(\d+)',s);assert v and int(v[1])==int(v[2])==0
  local=[]
  for line in s.splitlines():
   c=line.split()
   if len(c)==10 and c[1].isdigit():local.append(float(c[7]))
  assert len(local)==32 and all(x==0 for x in local)
  assert f'vit_attention_fused_{cap}_bytein_bout' in s
  images[cap]=np.fromfile(p/f'artifacts/outputs/{variant}-{w}.rgb32',np.uint32)
 assert np.array_equal(images[256],images[400]),w
 rows.append({'processing':[w,h],'Small31_tokens':tokens,'correct256_vs400_full_bitdiff':0,'invalid':0,'first_last_bitdiff':0,'active_kernels':32,'LMem_nonzero':0})
(p/'small-geometry-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
