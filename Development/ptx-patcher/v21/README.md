# V2.1：只放宽 maxnreg，保留 V2 输出

基线066aed5 / V2 SHA `737af93c2843fe18462c39da36a0a482e4d410493bed0e178fecabf526880f74`。本轮只改现存PTX `.maxnreg` 数字，不改V2偶奇K16、multidef_nq、量化、FP8图、权重、kernel名选择或Host路径。8个编译控制的PTX与重新生成的V2 PTX，屏蔽maxnreg数字后文本及SHA完全一致，见ptx-controls.json。

## 推荐产物

采用 **FB00/03/04/05/06→255**；FB01/02保持V2。新推荐：

`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v21.dll`

- 266,414,592B，**15/15 O4、15/15原槽位、无扩节**。
- SHA256 **c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed**。
- 最终从原始310.9.16.0全量重编15个Fatbin并实际CUDA加载，DLL SHA与胜出控制组合逐字节相同。
- V2文件保持原SHA，未覆盖旧fast、正式ZIP或外部游戏/Magpie。新推荐通过专用入口构建；通用构建器无cap参数时仍复现V2，避免混淆基线。

## 分因素扫描与选择

先编译8个点：C256(FB03)168/255，以及FB00/01/02/04/05/06各255。全部O4且均能原槽位装入。用V2原DLL字节为基底，只替换对应Fatbin，生成各单FB、hot255、all255控制；另组合fb45。扫描1080p每次50warmup/80iter，中间穿插V2对照：

| 控制 | GPU median ms |
|---|---:|
|V2前/中/后|20.140 /20.328 /20.294 /20.379 /20.366|
|仅C256→168|20.315|
|仅C256→255|20.386|
|仅FB00→255|20.258|
|仅FB04→255|17.665|
|仅FB05→255|15.361|
|仅FB06→255|20.285|
|hot255|12.761|
|all255|12.876|

C256单点清spill没有直接变成帧收益；FB04/05是主要有效点。正式三档进一步对比V2、fb45、hot255、all255，正向顺序baseline→fb45→hot255→all255，反向相反；每档每组独立50/80。

hot255三档正/反均略优fb45，且额外消除FB00/03/06栈溢出，选hot255；不把它相对fb45约0～0.1ms的小差异包装成稳定独立贡献。额外把FB01/02也设255反而较慢：900p all255为9.897/9.910ms vs hot2559.697/9.761；1080p为13.074/13.054 vs12.784/12.776，故不选all255。不逐核穷举寄存器限额，不因清spill而强行推广全部255。

## 正式三档验收

| 档位 | V2 median正/反 ms | 推荐V2.1 median正/反 ms | 正/反速度比 |
|---|---:|---:|---:|
|720p天空|10.227 /10.209|**6.662 /6.668**|1.535 /1.531×|
|900p场景|15.221 /15.302|**9.697 /9.761**|1.570 /1.568×|
|1080p场景|20.378 /20.418|**12.784 /12.776**|1.594 /1.598×|

全部13次扫描+24次正式对比，共**37次**完整输出相对同档新跑V2 **0 bit-diff、invalid0**。三档所有候选的输出SHA一致；天空变号均0，HF RMS保持V2的0.000101989。不同于V2更换K分组的阶段，本轮没有引入新数值差异。

完整min/median/Wall成组见[final-results.md](final-results.md)，全部控制见[results.md](results.md)及原始日志。默认DVFS、未锁频/改功耗，GPU硬件timestamp；遥测按运行时窗归档，不宣称等频因果。未在本轮重跑V7，不把上轮V7成绩混入本轮严格对比。

## STACK / LDL / STL 真实变化

下表为全导出静态统计，包含未执行变体；不是动态访问次数：

| 推荐修改FB | V2 max STACK→V2.1 B | LDL旧→新 | STL旧→新 | 新最大REG |
|---|---:|---:|---:|---:|
|00|240→0|709→0|702→0|248|
|03|200→0|629→0|706→0|218|
|04|1032→80|2169→40|2201→78|255|
|05|480→8|1027→7|1017→5|255|
|06|168→0|117→0|110→0|252|

C256168控制为24B STACK、18/18 LDL/STL，255才归零。FB01/02全255控制同样可清到0，但因整帧选择保留V2设置。**推荐DLL仍非全网零STACK**：FB01保持原max120B；FB04两种qkv_512_fp8核仍80B；FB05三个attention_fp8核仍8B。原`.maxnreg`是上限，不是实际统一占255个寄存器；cap升高会改变占用率与调度，所以必须看整帧，不能从清spill直接推导速度。

[资源表](resources.md)、resources.json、resource-usage原始cuobjdump报告保存所有核REG/STACK/SHARED及LDL/STL计数。FB04/05残留及C256单点负/近零结果保留，不继续为零数字硬压。

## 构建、复测和清理

```bash
python3 Development/ptx-patcher/v21/build_recommended.py
```

该入口读取selected.json，给通用构建器传0/3/4/5/6:255，并核验重建SHA；全部15个Fatbin从原源编译，不依赖已清理的候选二进制。手动等价参数为`--maxnreg 0:255 --maxnreg 3:255 --maxnreg 4:255 --maxnreg 5:255 --maxnreg 6:255`，不传时仍是V2。

完整重做控制先运行build_controls.py、combine.py，然后用bench.py的新tag或修改run_compare.py的tag运行。已有tag拒绝覆盖。inspect_controls.py依赖候选构建生成的cubin；analyze.py/finalize.py在清理RGB前运行。原cap/新cap的规范化PTX证明见verify_ptx_control.py。8项mapped、1项MMA代码生成、1项cap仅修改数字回归均通过。

保留推荐DLL、V2基线、源码/原始日志/遥测/资源报告/每核计数/输出SHA/PE与构建清单。候选DLL、RGB、临时PTX/cubin在核验SHA后删除，见cleanup.json；不提交二进制，不push。本轮没有引入FP16图、离线权重预解码或IMMA，提速来自同一V2图上的寄存器上限控制。
