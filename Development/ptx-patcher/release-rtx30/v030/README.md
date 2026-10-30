# v0.3.0 正式三包与本机同步回执

2026-10-29，核心PTX V3.1_pack5，266414592B，15/15 O4原槽位。SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`。

## 包与校验

目录 `/mnt/c/DLSS5-5090-dll/发布打包/`（已上传至夸克网盘：`https://pan.quark.cn/s/1ace87045701` · Gofile 镜像：`https://gofile.io/d/oR1ZAEvO`）。

| ZIP | SHA256 |
|---|---|
| `OptiScaler-REFramework-DLSS5-RTX30-0.3.0.zip` | `5cd5b76df4287ab7a8c52a81f45fd701fcb053d81bc4b8c4a044afcb43cab470` |
| `OptiScaler-DLSS5-RTX30-0.3.0.zip` | `cb36b3ebd4a4f5413ea814a3138302e5a71ddf4259dbdc0ff8b23f092f0ea573` |
| `Magpie-DLSS5-RTX30-0.3.0.zip` | `46aff5aa9b64ec588779ac52aa7133acfd920a1f2656b786265344598abbb46e` |

每包附.sha256；包内SHA256SUMS覆盖全部文件（清单自身除外）。三个包全部CRC及逐文件SHA验证通过。旧0.2.0 ZIP/.sha256/release JSON及旧顶层清单归档archive/v0.2.0，archive/v0.1.0未动。保留未变ZIP压缩条目，仅重新压缩新核心/元数据。

## 实测与技术说明

模型GPU median，50warmup/80iter，RTX3080 Laptop：研发两轮进程median均值5.75/8.42/11.35ms（1080 repeat11.12）；另一低温评估5.62/8.38/11.07ms。v0.2.0历史6.66/9.70/12.78ms，非同轮配对，不将跨轮比值当严格因果速度比。

V2.2异步mbarrier绑定及SWAR、V2.3 PRMT8、V2.4按需解码/回收、V2.6 Low/High 9180/b3a2＋mapped零拷贝、V2.7四C32 cap168、V2.9→V3.1半精度乘2^-8＋abs折叠＋LEA ties-toward-zero，使pair pack核心13→9→5SASS。21,712是V2.6生成路径mapped PRMT削减；本版38活跃核非NOP152,076。183,651是此前V2.3基线/V2.4比较中的计数，不冒标为V2.2。本版对V29_fast PSNR61.738/60.821/59.645dB，非0bit，不能宣称原生无损或全部潜能已榨干。

## 验证与本机状态

三包各NGX Feature18创建/执行、两个OptiScaler完整FFX→NGX→NR组合，共5项Windows smoke均nonfinite0。默认1.0/1.0组合日志已确认。Windows核验核心SHA相同；修补NR为NotSigned（预期），驱动NGX core为Valid，不把SHA校验说成恢复厂商签名。

除NR及指定元数据外，stage与0.2.0逐文件SHA一致，含dxgi、转发桥、Magpie.exe、默认及增强INI。主fast、鬼武者根/_storage_、剑星、Magpie五处NR已为新SHA，核验后同步说明/manifest/校验清单；Magpie目录改为0.3.0。保留本机各原INI和运行组件，元数据备份在backups/20261029-v030-metadata。

源码执行顺序stage.py → smoke.py → signatures.ps1 → package.py → live.py → release_check.py → docs.py。脚本拒绝覆盖既有stage/ZIP/备份；重做先建立独立输出目录，不直接重跑已有部署。smoke复用v020已验证Windows工具；原始日志、manifest、逐包SHA和验收JSON保留。临时stage与release-v030-tools清理，三ZIP及本机目录保留。未上传公网镜像、不push；实机观感由Zero先前确认，本次只做程序验证。
