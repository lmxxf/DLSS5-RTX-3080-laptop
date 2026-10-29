from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent;read=lambda n:json.loads((p/n).read_text());a=read('bench.json');r=read('repeat.json');s=read('smoke.json');assert len(a)==72 and len(r)==48 and len(s)==4
for x in a+r+s:
 assert x['metrics']['nonfinite']==0
 if x['variant'] in ('baseline','pack8'):assert x['quality']['bitdiff']==0
for w in (1280,1600,1920):
 hashes={x['quality']['sha256'] for x in a+r if x['width']==w and x['variant'] in ('pack5','pack5_quad')};assert len(hashes)==1
prim=read('primitives.json');assert all(t['mismatch_pairs']==0 for k in ('pack8','pack5_quad') for t in prim[k]);assert all(t['varying_half_mismatch_values']==158 for t in prim['pack5'])
cs=read('candidates.json')
for c in cs.values():assert hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()==c['sha256'];assert Path(c['path']).stat().st_size==266414592 and len(c['manifest'])==15 and all(m[1]=='inline' for m in c['manifest'])
assert hashlib.sha256(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v29_fast.dll').read_bytes()).hexdigest()=='55b518762bbe4d43fbe71f838352e23584d719736d86dd45437f4f50fc135f5c'
summ=read('bench-summary.json');rep=read('repeat-summary.json');win=all(v['gain_percent']>0 and all(z['gain_percent']>0 for z in v['directions'].values()) for d in (summ['pack5'],rep['pack5']) for v in d.values())
out={'passed':True,'formal_runs':120,'smoke_runs':4,'all_nonfinite':0,'A_bitdiff':0,'B_C_output_sha_identical_all_tiers':True,'B_repeat_confirmed':win,'production_updated':False,'candidates':cs,'quality':{w:next(x['quality'] for x in a if x['width']==w and x['variant']=='pack5') for w in (1280,1600,1920)}};(p/'validation.json').write_text(json.dumps(out,indent=2)+'\n')
lines=['# PTX V3.1 Pack8 / Pack5 / Quad实验','','结论：'+('B pack5两轮三档全部双向净提速，作为非0bit胜出实验候选保留。' if win else 'B复测未满足两轮三档全方向收益，不晋升。')+' A收益不稳定；C首轮1080p回退。生产V2.9_fast及5处部署均不覆盖。','','## 原语与算法','','以SHA55b51876的V2.9_fast为基线。A仅将and清符号替换为abs.f16x2；B改为ties-toward-zero的简化舍入；C在B上沿用v24同基本块/无guard/唯一消费者/作用域检查，在原两条转换位置保留读取，并以PRMT7531拼接，同时启用up因子A。C是融合＋up联合候选，不能把全部收益归给融合。','','每候选两通道排列×65536 half位型×256对侧poison，共33,554,432对：A相对V29为0 mismatch；B每种排列105826对不符，单通道158个位型不同；C双输入quad相对两个B pack为0 mismatch。涵盖NaN/Inf/±0，但不是穷举全部2^32输入组合。符号对称的ties-toward-zero不等于对任意数据分布无偏。','','独立ptxas O4 core验证旧9/A8/B5条，abs折叠进HMNMX2绝对值修饰符。四元素小核两个B pack＋拼接为11条核心，quad为9条，PRMT从3→1。SASS原文和opcode列表均保留。','','## 三档配对与复测','','首轮72次（3候选×3档×正反各ABBA/BAAB），有收益的B及低分辨率获益的C补48次复测，另4次快验。每正式进程50warmup/80iter，720 sky、900/1080 scene，均值为四个进程GPU median的平均；未锁频、不剔除波动。候选分别对自己的括号基线。','','|轮次|候选|宽度|V29 ms|候选 ms|下降|正/反下降|','|---|---|---:|---:|---:|---:|---:|']
for label,data in [('first',summ),('repeat',rep)]:
 for v,ws in data.items():
  for w,z in ws.items():lines.append(f"|{label}|{v}|{w}|{z['baseline_median_ms']:.5f}|{z['candidate_median_ms']:.5f}|{z['gain_percent']:.3f}%|{z['directions']['forward']['gain_percent']:.3f}% / {z['directions']['reverse']['gain_percent']:.3f}%|")
lines+=['','## 质量与静态资源','','124次输出全部finite，A严格相对V29_fast 0bit。B/C三档输出SHA完全一致，相对V29_fast PSNR61.73767/60.82124/59.64497dB，maxabs0.00439453/0.00781250/0.00830078，720天空变号0、HF RMS0.0001053983。这是对已有近似版的新增数值差异，不是原生GPU/F32绝对质量，未做动态游戏视觉验收。','','|版本|38核SASS含NOP|不含NOP|PRMT|STL/LDL|','|---|---:|---:|---:|---:|']
res=read('resources.json')
for mode,rs in res.items():
 assert len(rs)==38
 lines.append(f"|{mode}|{sum(z['instructions'] for z in rs.values())}|{sum(z['instructions_nonop'] for z in rs.values())}|{sum(z['PRMT'] for z in rs.values())}|{sum(z['STL'] for z in rs.values())}/{sum(z['LDL'] for z in rs.values())}|")
lines+=['','所有版本HMMA13188不变。FB04/FB05全部活跃核REG/STACK均未进一步下降；FB01最大STACK仍104B，FB04仍88B，FB00仍16B，其他为0。少PTX临时变量和少静态指令并不保证物理REG更少；逐核完整资源见resources.json。C仅在FB01/02/03融合456/616/616对，共1688对（全导出静态PTX计数）。','','## 交付与复现','','三份DLL均266414592B，15/15 O4原槽位，无扩节。V27的base_caps/kernel_caps、multidef_nq、lowhigh/lowhigh8、mbarrier不变；A/B mask8，C mask13。']
for name,c in cs.items():lines.append(f"- {name}: `{c['path']}`；SHA256 `{c['sha256']}`")
lines+=['','顺序：check_primitives.py、isolated_sass.py、quad_sass.py、build.py、extract_modules.py、audit.py、run.py；复测repeat.py后analyze.py repeat。复现须使用新的输出目录或归档旧日志（脚本拒绝覆盖计时日志）。代码复用v24融合资格检查，未改变共享生产生成器默认。','','保留候选DLL、源码、日志、SASS小核与JSON；清理编译大缓存和RGB。未写本机生产目录、未改发布ZIP、未push。']
(p/'README.md').write_text('\n'.join(lines)+'\n')
removed=[]
for d in [p/'artifacts',Path('/mnt/c/DLSS5-5090-dll/ptx-v31-bench')]:
 if d.exists():removed.append({'path':str(d),'bytes':sum(f.stat().st_size for f in d.rglob('*') if f.is_file())});shutil.rmtree(d)
(p/'cleanup.json').write_text(json.dumps(removed,indent=2)+'\n');print('PASS',win)
