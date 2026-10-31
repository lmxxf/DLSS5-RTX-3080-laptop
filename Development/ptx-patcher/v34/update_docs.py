from pathlib import Path
import json
p=Path(__file__).resolve().parent;dev=p.parent.parent;v=json.loads((p/'validation.json').read_text());assert v['data_checks_pass'];verdict='V3.4无晋升候选，保留V3.1_pack5 SHA1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86为唯一1.00×。';assert not v['winners']
record=f'''\n\n## 2026-11-01：PTX V3.4，FB01独立Quad、Local Quad与Shared闭环前提反证（闇，10月31日晚启动）

{verdict} 首轮120次正式配对中仅quad_fb1三档六方向全胜；repeat24次的720/1080均值回退0.166%/0.111%，900均值虽快0.006%但正反变号，按预先门槛否决。另三档18次快验，共{v['strict_successful_runs']}次成功运行末帧对同配置V3.1严格0bit/maxabs0/nonfinite0。计时全部串行，所有构建/GPU原语/资源查询先完成，无排除样本。最终独立核验原始SUMMARY、输出SHA与时序；修正shared_forward名称被旧子串汇总器误作forward方向的问题，原始数据与晋升裁决不变。

FB01独立纯Quad仅mask12，其余14个cubin逐字节不变。实现寄存器声明绑定、同基本块最近定义及全CFG路径dead-after检查；14项结构/作用域/谓词/回边测试、6×65536 GPU融合/拒绝控制通过。Local仍只融合456/616/616共1688对，新增0：大量剩余mov是已编码字的拆分/反序拼接（如mov.b32{{%rs380,%rs381}},%r2099），或当前块没有两个cvt定义，并非全局计数/深度限制遗漏了大量量化对。按REG/STACK下降且无回退选出的Local模块只有FB01，等价于已测quad_fb0145，未制造重复精选候选。

36项pack_multidef逐项CFG审计全部为两条可达定义，唯一可达pack为0，保留行号/定义集/前驱分支反证，不放宽生产mapped。

Shared库存覆盖2320解码事件（FB01～05为2304，FB06附16），输出全部Shared符号、st/ld/cp.async、地址DAG、写端来源、跨线程见证和未解析发布epoch。另发现9入口36个非MMA同线程向量返读，通过store支配、各到达路径源词不变、TID-only地址、别名/内存写入检查，构建shared_forward及quad_fb1_shared；只转发已量化整数词，保留store/barrier与FP8量化，其他block形状走原LDS。快路/两个回退形状GPU逐位一致，正式首轮均未全档胜。直接转发量化前half不安全：GPU反例1.0625经pack5+UP为1.0。

**容量反证：设备Shared为102400B/SM、默认49152B/block、opt-in101376B/block，驱动每block保留1024B。早期把101376B写作SM总量不准确。** 对实际baseline cubin加入等于payload大小的dynamic Shared并设置必要opt-in，官方Occupancy API显示FB01～05全部保持当前CTA/SM（FB01 4096→8192B仍6CTA；FB05静态24600B额外24576B仍2CTA）。这只是原REG/线程数下的容量反事实，不是已实现FP16布局改写或性能收益；但足以否定“扩容必然降驻留”。

因此分支2按K=3结算Pruned3/3，分支1与3维持Pruned3/3；**分支4仍Open2/3**（本批次一次未晋升），完整耦合的保留量化FP16 Shared表示/读写/异步拷贝方向未被排除，任务单“无剩余静态路径”的终局条件未成立。不能把Open强推到0，也不移交“物理极限”终局报告。生产五处、原DLL与三ZIP九个保护路径SHA不变；清理临时大二进制，保留文本证据，立即独立commit，无Co-Authored-By，不push。

[完整回执](ptx-patcher/v34/README.md)、[逐方向计时](ptx-patcher/v34/timing-summary.md)、[36项CFG](ptx-patcher/v34/multidef36-audit.json)、[Shared布局](ptx-patcher/v34/shared-layout-audit.json)、[容量API](ptx-patcher/v34/shared-capacity-api.json)、[验收](ptx-patcher/v34/validation.json)。
'''
f=dev/'DevHistory.md';s=f.read_text();assert '## 2026-11-01：PTX V3.4' not in s;s=s.replace('101,376 B Shared Memory/SM','102,400 B Shared Memory/SM（block opt-in 101,376 B；驱动每 CTA 保留 1,024 B）',1);f.write_text(s+record)
f=dev/'WorkingPlan.md';s=f.read_text();assert 'WorkingPlan — PTX V3.4' in s;lines=s.splitlines()
for j,line in enumerate(lines):
 if line.startswith('| **分支 2** |'):
  a=line.split('|');a[2]=' **`[Pruned]`** ';a[3]=' **`3 / 3`** ';a[-2]=' V3.4 FB01独立Quad首轮全胜，repeat720/1080回退、900变号；Local精确规则新增0对；本分支K=3剪枝 ';lines[j]='|'.join(a)
 if line.startswith('| **分支 4** |'):
  a=line.split('|');a[2]=' **`[Open]`** ';a[3]=' **`2 / 3`** ';a[-2]=' V3.4全部36项均双可达定义；Shared payload翻倍官方API仍保持当前驻留，容量否定前提不成立；36向量编码词返读候选已测未晋升，耦合FP16表示路径未排除，不能终局剪枝 ';lines[j]='|'.join(a)
s='\n'.join(lines)+'\n';s+=f'''\n### V3.4 执行回执（2026-11-01，10月31日晚启动）

{verdict} 分支2 Pruned3/3；分支1/3保持Pruned3/3；**分支4保持Open2/3，剩余Open=1，终局交接条件不成立。** [完整回执](ptx-patcher/v34/README.md)、[验收](ptx-patcher/v34/validation.json)。

5个严格候选首轮120次，仅quad_fb1全档双向胜出，补24次repeat未通过；加18快验共{v['strict_successful_runs']}次末帧0bit/maxabs0/nonfinite0，所有计时串行。Local规则真正实现并通过结构/GPU控制，但新增融合对0；36项multidef均两条可达定义。完整Shared库存另解锁36个编码词返读（9入口），保留量化与形状回退，独立及FB01 Quad组合均实测。

**新事实推翻闭环前提：102400B/SM与101376B/block opt-in不可混同。实际baseline cubin加倍payload后，FB01～05官方API均保持当前CTA/SM。** 不能用容量证明所有剩余改写不可兑现。保留量化边界并成对改写Shared生产者/消费者及异步拷贝布局的方向仍未排除，不能将两项审计机械计作两次失败而强迫分支4变成Pruned3/3。

本轮已完成规定单因素、Local实现、CFG与Shared容量/布局审计及安全局部候选实测；没有编造“全部闭环”或物理极限结论。生产部署/ZIP不覆盖；清理临时大产物并立即独立commit，不push，无Co-Authored-By。
''';f.write_text(s);(p/'branches.json').write_text(json.dumps({f'branch{i}':v[f'branch{i}'] for i in range(1,5)},indent=2)+'\n');print(verdict,'branch4 Open2/3; no terminal handoff')
