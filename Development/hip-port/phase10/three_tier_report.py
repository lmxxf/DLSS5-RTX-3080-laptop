"""Combine new 720p run with the previously frozen 900p/1080p selected run."""
from pathlib import Path
import re,json,hashlib
import numpy as np
phase=Path(__file__).resolve().parent;root=phase.parents[2]
text=(phase/'selected-720p-bench.log').read_text();assert 'ALL SELECTED MODEL/RESOLUTION BENCHMARKS PASSED!' in text
assert 'CUDA_KERNEL_TRACE' not in text
assert re.search(r'GRAPH_STATUS enabled=0 .*small=1 wave_owned=1 final_direct=1',text)
g=re.search(r'GPU  \(ms\):.*?median=([\d.]+).*?min=([\d.]+)',text);wall=re.search(r'Wall \(ms\):.*?median=([\d.]+)',text);total=re.search(r'PROFILE_TOTAL ([\d.]+) kernels=(\d+)',text)
v=re.search(r'Validity : invalid=(\d+).*bit_diff_first_last=(\d+) fnv1a64=(\w+)',text);assert v[1]==v[2]=='0'
rows=[line.split() for line in text.splitlines() if len(line.split())==10 and line.split()[1].isdigit()]
assert len(rows)==32 and all(int(r[7])==0 for r in rows)
assert any(r[0].startswith('c256_wave2') for r in rows)
a=np.fromfile(phase/'artifacts/outputs/selected-720p-1280.rgb32',np.uint32)
b=np.fromfile(phase/'artifacts/outputs/phase5-720p-reference-1280.rgb32',np.uint32)
assert a.size==b.size==1280*768*3 and np.array_equal(a,b)
new={'display':'720p','processing':'1280×768','gpu_min':float(g[2]),'gpu_median':float(g[1]),'wall_median':float(wall[1]),'kernel_total':float(total[1]),'invalid':int(v[1]),'first_last_bitdiff':int(v[2]),'hash':v[3],'active_kernels':32,'lmem_nonzero':0,'reference_bitdiff':0,'source':'selected-720p-bench.log','ptx_historical_median':15.83}
old=json.loads((phase/'results.json').read_text())['selected'];data=[new]
for w,name,shape,ptx in [('1600','900p','1600×1024',24.47),('1920','1080p','1920×1152',32.04)]:
 c=old[w];data.append({'display':name,'processing':shape,**{k:c[k] for k in ['gpu_min','gpu_median','wall_median','kernel_total']},'invalid':c['accuracy_vs_baseline']['invalid'],'lmem_nonzero':c['lmem_kernel_kinds'],'source':'selected-bench.log (previous final independent run)','ptx_historical_median':ptx})
lines=['| 档位（CUDA处理尺寸） | CUDA GPU min | CUDA GPU median | CUDA Wall median | CUDA PROFILE_TOTAL | invalid | PTX历史GPU median |','|---|---:|---:|---:|---:|---:|---:|']
for c in data:lines.append(f'| {c["display"]}（{c["processing"]}） | {c["gpu_min"]:.3f} | **{c["gpu_median"]:.3f}** | {c["wall_median"]:.3f} | {c["kernel_total"]:.6f} | {c["invalid"]} | {c["ptx_historical_median"]:.2f} |')
table='\n'.join(lines)
(phase/'three-tier-results.json').write_text(json.dumps({'warmup':50,'iterations':80,'graph':False,'rows':data,'ptx_note':'Historical rounded reference; input/processing geometry not unified in this supplement.'},indent=2)+'\n')
(phase/'three-tier-results.md').write_text('# Phase 10 三档完整对照\n\n'+table+'\n\n单位ms，Small31/Style1、Graph off、50 warmup/80 iter。720p本次补测，900p/1080p沿用上一轮最终selected独立复测，不混入其它轮次最小值。PROFILE_TOTAL为独立插桩帧。PTX列为历史标尺，本轮没有统一输入/处理尺寸重跑DLL。\n')
common='''单位均为ms。CUDA均使用Phase10最终selected模块、0.5x Small31、Style1、Graph off、50 warmup/80 iter；720p本次补测，900p/1080p沿用上一轮最终独立复测，未混入其它控制轮次的min或核累计。PROFILE_TOTAL是单独插桩帧。PTX列为历史GPU median标尺，本轮未统一输入/处理尺寸重跑DLL，不计算严格同条件加速比。
'''
notes='''720p首次触发旧C256分散核的CUDA_ERROR_MISALIGNED_ADDRESS；逐核同步定位为mh_ffn_fused_c256_frag_project_g128_qkv_bytein_fb。仅扩展Host的1280×768门控以使用现有c256_wave2，selected的40个模块字节不变。采用Phase5无对齐升级模块、关闭新720 C256门控跑旧分散路径，完整输出与本次720p逐位一致（0 bit-diff）。新路径首末帧0bit-diff、invalid0、32/32活跃核LMem0。同步诊断仅由DLSS5_BENCH_SYNC_KERNELS显式启用，正式计时未启用。

复测脚本：`bash Development/hip-port/phase10/bench_720p.sh`；[三档记录](hip-port/phase10/three-tier-results.md)，原日志`hip-port/phase10/selected-720p-bench.log`、故障定位及Phase5参考日志均保留。900p/1080p门控不变。
'''
updates=[(root/'Development/DevHistory.md','## 2026-10-25：Phase 10 720p补测与三档PTX历史标尺',common+'\n'+table+'\n\n'+notes),(root/'Development/WorkingPlan.md','### Phase 10 三档实测补齐（2026-10-25）',common+'\n'+table+'\n\n720p已补齐：首末帧0bit-diff、invalid0、32/32零LMem，与Phase5旧分散C256参考输出逐位一致。Host增加1280×768的C256 wave2门控解决旧分散核对齐错误，selected模块未改；900p/1080p沿用已归档最终轮次。详见[三档记录](hip-port/phase10/three-tier-results.md)。\n')]
for p,heading,content in updates:
 s=p.read_text();block='\n'+heading+'\n\n'+content
 if heading in s:
  start=s.index('\n'+heading);level=len(heading)-len(heading.lstrip('#'))
  rest=s[start+len('\n'+heading):];nxt=re.search(r'\n#{1,'+str(level)+r'} ',rest)
  end=start+len('\n'+heading)+nxt.start() if nxt else len(s)
  s=s[:start]+block+s[end:]
 else:s+=block
 p.write_text(s)
print(table)
