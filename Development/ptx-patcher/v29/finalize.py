from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent;read=lambda n:json.loads((p/n).read_text());a=read('bench.json');r=read('repeat.json');s=read('smoke.json');assert len(a)==len(r)==48 and len(s)==3
for x in a+r+s:
 assert x['metrics']['nonfinite']==0
 if x['variant']!='fast':assert x['quality']['bitdiff']==0
out={'formal_runs':96,'smoke_runs':3,'all_finite':True,'exact_all_bitdiff':0,'quality':{},'candidates':read('candidates.json'),'recommendation':'Keep V2.7 strict default; exact gains not stable across directions; fast is an optional non-bit-exact experimental variant.'}
for w in (1280,1600,1920):out['quality'][w]=next(x['quality'] for x in a if x['variant']=='fast' and x['width']==w)
for x in out['candidates'].values():assert hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256']
assert hashlib.sha256(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v27.dll').read_bytes()).hexdigest()=='28150da4ea554258b660b610bf23168a266caeda1eb68521d195d2276f0b2969'
(p/'validation.json').write_text(json.dumps(out,indent=2)+'\n')
lines=['# PTX V2.9 Unified Mul Pack 实验','','结论：保留V2.7严格默认。修正后的A原语及整网0bit，但两轮收益方向不稳定；B三档有收益，保留为明确非0bit的实验DLL，未覆盖生产或发布包。','','## 先修正用户给定算法的一个操作数顺序错误','','原式 `lop3 y,y,source,0x7f007f00,0xd8` 在掩码位选择source幅值，原语大面积不符（每种排列16,774,912/16,777,216对）。正确顺序为 `lop3 y,source,y,0x7f007f00,0xd8`，保留量化幅值和原符号。代码中两候选均使用修正式，原始失败留在primitives-original.json。','','## 原语与资源','','全部65536种half位型分别置于两个通道，另一通道遍历256种poison，共33,554,432对/候选，包含NaN/Inf和正负零。A全部0 mismatch；B每种排列10,240对差异。此测试不是穷举全部2^32通道组合。','','独立O4小核排除地址/常量装载等脚手架后，旧核心13条、A12条、B9条；A没有实现预期11条。SASS文本见baseline/exact/fast-pack.sass。全38活跃核统计含NOP等固定尾部，计数口径见audit.py：指令176431→174695(A)/164659(B)，HMMA均13188；LDL/STL 108/109→102/105(A)、104/109(B)。FB01最大STACK96→96(A)/104(B)，其他FB最大STACK不变。不能声称零spill。','','## 两轮未插桩配对结果','','每轮3档×2候选×8进程=48，50warmup/80iter，正向ABBA/反向BAAB。取进程GPU median均值；默认DVFS，保留所有波动，不剔除异常点。额外第二轮因第一轮A的1080p变号而启动，两轮分别报告。','','|轮次|候选|宽度|V27 ms|候选 ms|耗时下降|正/反下降|','|---|---|---:|---:|---:|---:|---:|']
for label,file in [('first','bench-summary.json'),('repeat','repeat-summary.json')]:
 for v,ws in read(file).items():
  for w,z in ws.items():lines.append(f"|{label}|{v}|{w}|{z['baseline_median_ms']:.5f}|{z['candidate_median_ms']:.5f}|{z['gain_percent']:.3f}%|{z['directions']['forward']['gain_percent']:.3f}% / {z['directions']['reverse']['gain_percent']:.3f}%|")
lines+=['','## 质量与交付','','共99次运行，全部finite；A及基线输出相对V27严格0bit。B相对V27（RGB peak=1）PSNR62.60892/62.11713/60.59469dB，maxabs0.00439453/0.00561523/0.00744629，天空0变号。高PSNR不等于逐位一致，也不是相对原厂或F32的绝对画质评价。','','两个DLL均266414592B、15/15 O4原槽位；构建保留V27四核cap168及原hot255，只替换SWAR pack生成器。']
for k,v in out['candidates'].items():lines+=['',f"- {k}: `{v['path']}`；SHA256 `{v['sha256']}`"]
lines+=['','复现：check_primitives.py → build.py → extract_modules.py → audit.py → run.py；复测repeat.py后analyze.py repeat。原语先验收再进入整网。源码与结果保留，临时PTX/cubin/RGB清理，两个候选DLL保留。未修改生产生成器默认，未部署、未push。']
(p/'README.md').write_text('\n'.join(lines)+'\n')
removed=[]
for directory in [p/'artifacts',Path('/mnt/c/DLSS5-5090-dll/ptx-v29-bench')]:
 if directory.exists():
  removed.append({'path':str(directory),'bytes':sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())});shutil.rmtree(directory)
(p/'cleanup.json').write_text(json.dumps(removed,indent=2)+'\n');print('PASS 99 runs; candidates retained')
