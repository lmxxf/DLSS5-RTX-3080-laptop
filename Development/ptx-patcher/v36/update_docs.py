from pathlib import Path
import json
p=Path(__file__).resolve().parent;dev=p.parent.parent;v=json.loads((p/'validation.json').read_text());sel=json.loads((p/'selected.json').read_text()) if (p/'selected.json').exists() else None
verdict=f'晋升{sel["variant"]}为独立V3.6 SHA{sel["sha256"]}，作为下一轮唯一1.00×，不覆盖生产。' if sel else '本轮无晋升，保持V3.1_pack5为唯一1.00×。';states='；'.join(f'分支{b} {r["state"]} n={r["n"]}/3' for b,r in v['branches'].items())
record=f'''\n\n## 2026-11-01：PTX V3.6，新分支5/6/7的首轮构造验证与串行实测（闇）

{verdict} {states}。分支1～4保持原有Pruned3/3，不用新分支首轮失败宣称全局物理上限。

分支5：对全部8944存活Pack做typed CFG范围、符号、NaN/负零与命名half作用域审计，证明680处可用pack3，其余保留通用或标记实证探索。Pack4/Pack3独立ptxas-O4核心数据依赖切片为4/3条，两个有界域各33554432对GPU原语零差异；不把地址LEA混入核心。pack_proven只用证明点；pack4_all/fbN实证候选的输出精度不当成所有中间值有界的证明。

分支6：构造全字节可逆逆编码，保留旧解码对7f/ff的±480再无夹断编码，全33554432对包括保留字节的测试零差异。由此实施FB02/03原位2×exact、组合与fast。资源查询后固定零新增STACK/STL/LDL且CTA不降的入口，精确精选复用FB03，fast单列；另选择FB02一个可精确配对的局部交换阶段构造exact/fast。

分支7：完成FB04/05全部Shared声明与发布周期审计，生产期均为异步或异步/回退混合，无独立纯Type-I周期。选定所有返回路径上的发布点，原cp.async及字节视图不变，等完成后CTA协作LDS+decode+STS+BAR生成独立half视图；FB04、FB05及组合完整模型实际测试，未证明的读取保留旧解码，超默认静态Shared48KiB入口未擅加Host opt-in。另用真实16B cp.async.cg跨warp原语完成构造性验证，不从微核推帧收益。

计数{v['counts']}，精确成功运行{v['exact_runs']}次末帧0bit/maxabs0/nonfinite0；近似运行{v['approximate_runs']}次按预先50dB/1/64/finite/sky0质量门检查。所有正式计时串行，首轮六方向全胜者补repeat。单次过程输出嵌入bench/repeat JSON，未生成或提交.log碎片。六个DLL路径与三个ZIP共九个保护路径SHA不变，不部署、不push。临时大产物清理，按代码/验证、汇总/硬件、文档/状态三小提交，无Co-Authored-By。

[回执](ptx-patcher/v36/README.md)、[数据](ptx-patcher/v36/timing-summary.md)、[验收](ptx-patcher/v36/validation.json)。
'''
f=dev/'DevHistory.md';s=f.read_text();assert '## 2026-11-01：PTX V3.6' not in s;f.write_text(s+record)
f=dev/'WorkingPlan.md';s=f.read_text();assert 'WorkingPlan — PTX V3.6' in s;lines=s.splitlines()
for j,line in enumerate(lines):
 for b,r in v['branches'].items():
  if line.startswith(f'| **分支 {b}** |'):
   a=line.split('|');a[2]=f' **`[{r["state"]}]`** ';a[3]=f' **`{r["n"]} / 3`** ';a[-2]+='；V3.6本轮结果见文末回执 ';lines[j]='|'.join(a)
s='\n'.join(lines)+'\n'
if sel:
 s=s.replace('- **当前唯一 `1.00×` 对比基线**：','- **V3.6输入 `1.00×` 基线（历史）**：',1);s=s.replace('### 候选分支调度表（`K = 3`）',f'**下一轮唯一1.00×：V3.6**，`{sel["path"]}`，SHA `{sel["sha256"]}`。原任务与本轮数据属于旧V3.1输入参考，后续在新基线重测。\n\n### 候选分支调度表（`K = 3`）',1)
s+=f'''\n### V3.6 执行回执（2026-11-01）

{verdict} {states}。本轮构造了范围特化、全字节原位、按入口/epoch精选及异步发布后协同解包，完整[回执](ptx-patcher/v36/README.md)、[配对](ptx-patcher/v36/timing-summary.md)、[验收](ptx-patcher/v36/validation.json)。

所有计时串行，首轮全档双向胜出才补repeat，质量门预先固定；精确{v['exact_runs']}次均末帧0bit，近似{v['approximate_runs']}次质量逐项保留。进程输出汇总进JSON，不留单次.log碎文件；九个生产/发布路径不变，清理临时大二进制，三个干净小提交，不加Co-Authored-By、不push。新分支按真实结果更新，不把未晋升首轮写作全空间收敛。
''';f.write_text(s);print(verdict,states)
