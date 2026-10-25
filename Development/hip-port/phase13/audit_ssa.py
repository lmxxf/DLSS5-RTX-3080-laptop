from pathlib import Path
import sys,subprocess,re,json
r=Path(__file__).resolve().parents[1];p=r/'phase13';sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
out=p/'artifacts/ssa';out.mkdir(exist_ok=True);rows={}
for variant in ['baseline','prefix','post']:
 src=r/'phase12/artifacts/selected/modules/c32-wave1-fast.generated.cu' if variant=='baseline' else p/f'artifacts/{variant}/modules/c32-wave1-fast.generated.cu'
 raw=out/(variant+'.raw.ll');named=out/(variant+'.named.ll')
 cmd=['clang++','-x','cuda','--cuda-device-only','--cuda-gpu-arch=sm_86','-Xclang','-fnative-half-type','-Xclang','-fallow-half-arguments-and-returns','-nocudainc','-nocudalib','-std=c++20','-O3','-Wno-unknown-attributes','-Wno-unused-value','-S','-emit-llvm',str(src),'-o',str(raw)]
 subprocess.run(cmd,check=True);subprocess.run(['opt-14','-instnamer','-loop-simplify','-lcssa','-S',str(raw),'-o',str(named)],check=True)
 text=b.cancel_wmma_shuffles_ir(named.read_text());(out/(variant+'.ssa.ll')).write_text(text);stats={}
 for name in ['c32_wave1_prefix_b8d_w16','c32_wave1_post_b8_w16']:
  m=re.search(r'define[^\n]*@'+name+r'\(',text);assert m
  end=text.index('\n}',m.start());body=text[m.start():end];stats[name]={'phi_u4':len(re.findall(r'phi <4 x i32>',body)),'phi_f8':len(re.findall(r'phi <8 x float>',body)),'remaining_C_layout_calls':len(re.findall(r'call[^\n]*@__sm86_c_to_ampere\(',body)),'remaining_D_layout_calls':len(re.findall(r'call[^\n]*@__sm86_d_to_rdna4\(',body))}
 rows[variant]=stats
(p/'ssa-audit.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
