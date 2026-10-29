from pathlib import Path
import json,re
p=Path(__file__).resolve().parent;repo=p.parents[3];pk=json.loads((p/'packages.json').read_text());SHA='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'
rows='\n'.join(f"| `{r['name']}` | `{r['sha256']}` |" for r in pk)
intro='''**Current release: 0.3.0 (2026-10-29), PTX V3.1_pack5.** Three official ZIPs have been built and verified locally; a v0.3.0 public mirror has not been uploaded/verified in this release task. 31-block Small / Preset 2 / Style 1, 15/15 O4 in original slots, 266,414,592 bytes.

RTX 3080 Laptop model-only GPU medians (50 warmup / 80 iterations): **development paired rounds 5.75 / 8.42 / 11.35 ms** (1080p repeat: 11.12 ms); a separate cooler run measured **5.62 / 8.38 / 11.07 ms**. Historical v0.2.0: 6.66 / 9.70 / 12.78 ms. These are separate runs under DVFS, not game FPS or a new paired v0.2.0 speedup test. This release changes rounding: benchmark PSNR vs V2.9_fast is **61.738 / 60.821 / 59.645 dB**, not bit-exact. Default OptiScaler strengths remain **1.0/1.0**, with optional **1.5/1.1**. [Release receipt](Development/ptx-patcher/release-rtx30/v030/README.md).

### v0.3.0 checksums

`nvngx_dlssnr.dll` SHA256: `'''+SHA+'''`

| ZIP | SHA256 |
|---|---|
'''+rows+'\n\n'
f=repo/'README.md';t=f.read_text();start=t.index('**Current release:');end=t.index('\n---',start);t=t[:start]+intro+t[end:];t=t.replace('-DLSS5-RTX30-0.2.0.zip','-DLSS5-RTX30-0.3.0.zip');t=t.replace('**③ Current `ptx-patcher` (`v0.2.0 / V2.1`)**','**③ Historical `ptx-patcher` (`v0.2.0 / V2.1`)**')
needle='### 3. Build Commands';tech='''### Current v0.3.0 implementation

V2.2 added native `cp.async.mbarrier.arrive` completion and branchless SWAR pack. V2.3 introduced the 8-instruction even/odd PRMT decode; V2.6 switched to Low/High selectors **0x9180/0xb3a2** and direct mapped halves (21,712 generated mapped PRMT sites removed). V2.4 introduced just-in-time decode and dead temporary reuse. V2.7 caps only four C32 kernels at168 to increase theoretical residency from8 to12 warps/SM. V2.9→V3.1 unifies normal/subnormal alignment with half2 ×2^-8, folds abs into HMNMX2, and uses LEA rounding toward zero at ties: pair pack core13→9→5 SASS. The 38-active-kernel non-NOP total is152,076 (V2.9_fast163,944). This is a static count, not executed instructions per frame; remaining spill is not zero.

Release-specific source and commands: [V3.1](Development/ptx-patcher/v31/README.md), [v0.3.0 packaging](Development/ptx-patcher/release-rtx30/v030/README.md). Generic commands below reproduce historical stages and do not implicitly select the current release.

''';t=t.replace(needle,tech+needle)
needle='| **`0.2.0`** |';i=t.index(needle);t=t[:i]+'| **`0.3.0`** | 2026-10-29 | PTX V3.1_pack5; Low/High mapped forwarding, asynchronous completion, pooled decoding, four C32 caps, 5-SASS approximate pack. Local three-package validation complete. | Model medians **5.75 / 8.42 / 11.35 ms**, separate cooler run5.62/8.38/11.07. [Receipt](Development/ptx-patcher/release-rtx30/v030/README.md) |\n'+t[i:];f.write_text(t)
f=repo/'Development/ptx-patcher/README.md';t=f.read_text().replace('### 2026-10-26：当前推荐 V2.1','### 2026-10-26：历史推荐 V2.1').replace('当前默认：','历史通用生成器默认（并非v0.3.0选择）：',1);t=t.replace('# RTX 3080 Laptop PTX 修补\n','# RTX 3080 Laptop PTX 修补\n\n当前正式本机包 **v0.3.0 / PTX V3.1_pack5**，核心SHA256 `'+SHA+'`。模型GPU耗时研发标尺5.75/8.42/11.35ms，另轮低温5.62/8.38/11.07ms；非0bit升级，默认1.0/1.0及增强INI保留。[发布回执](release-rtx30/v030/README.md)。后文V2/V2.1为历史记录，通用构建命令不会自动选当前pack5。\n',1);f.write_text(t)
f=p.parent/'发布回执.txt';t=f.read_text();f.write_text('当前正式本机版本：v0.3.0 / PTX V3.1_pack5（2026-10-29）。研发5.75/8.42/11.35ms，另轮5.62/8.38/11.07ms。三包SHA、Windows smoke及部署元数据见v030/README.md、v030/packages.json。未上传新的公网镜像；旧链接只代表历史版本。\n\n以下为历史回执：\n'+t)
text='''# v0.3.0 正式三包与本机同步回执

2026-10-29，核心PTX V3.1_pack5，266414592B，15/15 O4原槽位。SHA256 `'''+SHA+'''`。

## 包与校验

目录 `/mnt/c/DLSS5-5090-dll/发布打包/`。

| ZIP | SHA256 |
|---|---|
'''+rows+'''

每包附.sha256；包内SHA256SUMS覆盖全部文件（清单自身除外）。三个包全部CRC及逐文件SHA验证通过。旧0.2.0 ZIP/.sha256/release JSON及旧顶层清单归档archive/v0.2.0，archive/v0.1.0未动。保留未变ZIP压缩条目，仅重新压缩新核心/元数据。

## 实测与技术说明

模型GPU median，50warmup/80iter，RTX3080 Laptop：研发两轮进程median均值5.75/8.42/11.35ms（1080 repeat11.12）；另一低温评估5.62/8.38/11.07ms。v0.2.0历史6.66/9.70/12.78ms，非同轮配对，不将跨轮比值当严格因果速度比。

V2.2异步mbarrier绑定及SWAR、V2.3 PRMT8、V2.4按需解码/回收、V2.6 Low/High 9180/b3a2＋mapped零拷贝、V2.7四C32 cap168、V2.9→V3.1半精度乘2^-8＋abs折叠＋LEA ties-toward-zero，使pair pack核心13→9→5SASS。21,712是V2.6生成路径mapped PRMT削减；本版38活跃核非NOP152,076。183,651是此前V2.3基线/V2.4比较中的计数，不冒标为V2.2。本版对V29_fast PSNR61.738/60.821/59.645dB，非0bit，不能宣称原生无损或全部潜能已榨干。

## 验证与本机状态

三包各NGX Feature18创建/执行、两个OptiScaler完整FFX→NGX→NR组合，共5项Windows smoke均nonfinite0。默认1.0/1.0组合日志已确认。Windows核验核心SHA相同；修补NR为NotSigned（预期），驱动NGX core为Valid，不把SHA校验说成恢复厂商签名。

除NR及指定元数据外，stage与0.2.0逐文件SHA一致，含dxgi、转发桥、Magpie.exe、默认及增强INI。主fast、鬼武者根/_storage_、剑星、Magpie五处NR已为新SHA，核验后同步说明/manifest/校验清单；Magpie目录改为0.3.0。保留本机各原INI和运行组件，元数据备份在backups/20261029-v030-metadata。

源码执行顺序stage.py → smoke.py → signatures.ps1 → package.py → live.py → release_check.py → docs.py。脚本拒绝覆盖既有stage/ZIP/备份；重做先建立独立输出目录，不直接重跑已有部署。smoke复用v020已验证Windows工具；原始日志、manifest、逐包SHA和验收JSON保留。临时stage与release-v030-tools清理，三ZIP及本机目录保留。未上传公网镜像、不push；实机观感由Zero先前确认，本次只做程序验证。
''';(p/'README.md').write_text(text)
