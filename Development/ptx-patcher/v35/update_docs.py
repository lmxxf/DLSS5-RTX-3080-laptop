from pathlib import Path
import json
p=Path(__file__).resolve().parent;dev=p.parent.parent;v=json.loads((p/'validation.json').read_text());sfile=p/'selected.json';selected=json.loads(sfile.read_text()) if sfile.exists() else None;verdict=f'晋升{selected["variant"]}为独立V3.5（SHA {selected["sha256"]}），下一轮唯一1.00×，不部署。' if selected else '无候选两轮三档全胜且过质量门，保留V3.1_pack5；分支4 Pruned3/3，四个预设分支Open=0。'
record=f'''\n\n## 2026-11-01：PTX V3.5，Shared 2× FP16耦合表示实测闭环（闇）

{verdict} 固定V3.1_pack5 SHA1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86，baseline全量重建同SHA；全部15/15 O4原槽位。

实际构建FB01/02/03精确独立shadow、FB123精确组合、FB01原位2×精确、FB01独立及原位fast共7候选。原字节i映射为扩展half的2i字节，旧u32对应低/高两个f16x2，Shared地址及宽度成对×2；原位精确对非MMA读取重建有限pack5字节，独立shadow保留原字节视图供异构消费者使用。FB01全部164个存储词均为可证明的有限pack来源；FB02/03含全局/混合来源，采用精确shadow。FB04/05异步别名保留原布局，没有单边改copy地址或绕过量化。fast显式近似，并在数据前固定PSNR≥50dB、maxabs≤1/64、finite与sky0门。

有限FP8往返32,774,128个有效字零差异；half夹断后重新pack5的33,554,432对零差异，pack5不发出保留7f/ff；Shared跨lane/warp镜像零差异。精确整网快验三档0bit；fast快验PSNR约60dB，仍逐过程按固定质量门检查。原语及逐核改写事件见v35验证JSON。

首轮{v['counts']['timed']}次、repeat{v['counts'].get('repeat',0)}次、快验{v['counts']['smoke']}次，所有计时严格串行，所有编译/原语/资源查询先完成；精确成功运行{v['exact_successful_runs']}次均末帧0bit/maxabs0/nonfinite0，近似运行{v['approximate_runs']}次的PSNR/maxabs/sky逐项保留。没有单次.log碎片入库：过程文本嵌入聚合JSON。硬件/API四表及数据验收独立核对后才写结论。

分支4结算为{v['branch4']['state']} n={v['branch4']['n']}/3；其他三支保持Pruned3/3。本轮闭环是给定预设分支与质量门下的有限搜索结论，不将静态SASS计数或K=3当作全局物理极限证明。主脑可据此撰写交接报告供审阅。生产五处、原DLL与三ZIP九路径SHA不变，不部署、不push。清理临时大二进制，按构造/原语、跑分/硬件表、文档/分支状态分三次小提交，无Co-Authored-By。

[回执](ptx-patcher/v35/README.md)、[配对汇总](ptx-patcher/v35/timing-summary.md)、[验收](ptx-patcher/v35/validation.json)。
'''
f=dev/'DevHistory.md';s=f.read_text();assert '## 2026-11-01：PTX V3.5' not in s;f.write_text(s+record)
f=dev/'WorkingPlan.md';s=f.read_text();assert 'WorkingPlan — PTX V3.5' in s;lines=s.splitlines()
for j,line in enumerate(lines):
 if line.startswith('| **分支 4** |'):
  a=line.split('|');a[2]=f' **`[{v["branch4"]["state"]}]`** ';a[3]=f' **`{v["branch4"]["n"]} / 3`** ';a[-2]=' V3.5已完成FB01～03精确shadow、FB01原位2×及fast耦合表示实测，结算见文末回执 ';lines[j]='|'.join(a)
s='\n'.join(lines)+'\n'
if selected:s=s.replace('- **当前唯一 `1.00×` 对比基线**：','- **V3.5本轮输入 `1.00×` 基线（历史）**：',1);s=s.replace('### 候选分支调度表（`K = 3`）',f'**下一轮唯一1.00×基线：PTX V3.5**，`{selected["path"]}`，SHA `{selected["sha256"]}`。本页原任务与探针对照属于V3.1输入参考。\n\n### 候选分支调度表（`K = 3`）',1)
s+=f'''\n### V3.5 执行回执（2026-11-01）

{verdict} 分支4 {v['branch4']['state']} n={v['branch4']['n']}/3，剩余Open={len(v['remaining_open_branches'])}。详见[回执](ptx-patcher/v35/README.md)、[数据](ptx-patcher/v35/timing-summary.md)、[验收](ptx-patcher/v35/validation.json)。

7个候选完成精确shadow/原位2×与近似夹断half耦合改写；首轮{v['counts']['timed']}、repeat{v['counts'].get('repeat',0)}、快验{v['counts']['smoke']}，串行执行。单次过程输出汇总进JSON后不保留.log碎文件。九个生产/发布路径SHA不变，临时大产物清理；按任务单拆成三个干净提交，不加Co-Authored-By、不push。有限分支全部Pruned时可移交本轮终局资料，但并非全局物理最优的数学证明。
''';f.write_text(s);print(verdict)
