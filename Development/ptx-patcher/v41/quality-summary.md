# V4.1 输出质量汇总

三档固定输入、末帧对V4.0；经验Pack4仍按实证候选标记，不推断未测中间激活范围。

|候选|类型|次数|最大bit-diff|最大绝对误差|最小非无限PSNR dB|最大非有限数|质量全过|
|---|---|---:|---:|---:|---:|---:|---|
|baseline|精确|75|0|0.0|∞|0|True|
|up_occ_keep|精确|15|0|0.0|∞|0|True|
|up_add_fb6|精确|15|0|0.0|∞|0|True|
|up_add_fb4pool|精确|15|0|0.0|∞|0|True|
|zero_fb23456|精确|15|0|0.0|∞|0|True|
|pack4_add_fb4_nospill|近似/实证|15|0|0.0|∞|0|True|
|joint_up_occ_keep_zero_pack4|近似/实证|3|0|0.0|∞|0|True|
|joint_up_add_fb6_zero_pack4|近似/实证|3|0|0.0|∞|0|True|
|joint_up_add_fb4pool_zero_pack4|近似/实证|15|0|0.0|∞|0|True|
