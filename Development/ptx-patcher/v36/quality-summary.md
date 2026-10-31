# V3.6 输出质量汇总

三档固定输入、末帧对 V3.1_pack5；不推断未测输入或中间激活范围。经验 Pack4 继续按近似候选验收。

|候选|验收类型|次数|最大 bit-diff|最大绝对误差|非有限数最大值|全部质量门通过|
|---|---|---:|---:|---:|---:|---|
|baseline|精确|231|0|0.0|0|True|
|fb2_inplace|精确|15|0|0.0|0|True|
|fb3_inplace|精确|15|0|0.0|0|True|
|fb23_inplace|精确|15|0|0.0|0|True|
|fb23_fast_inplace|近似/实证|15|5302705|0.00927734375|0|True|
|pack_proven|精确|15|0|0.0|0|True|
|pack4_all|近似/实证|15|0|0.0|0|True|
|async_fb4|精确|15|0|0.0|0|True|
|async_fb5|精确|15|0|0.0|0|True|
|async_fb45|精确|15|0|0.0|0|True|
|pack4_fb0|近似/实证|15|0|0.0|0|True|
|pack4_fb1|近似/实证|15|0|0.0|0|True|
|pack4_fb2|近似/实证|15|0|0.0|0|True|
|pack4_fb3|近似/实证|15|0|0.0|0|True|
|pack4_fb4|近似/实证|15|0|0.0|0|True|
|pack4_fb5|近似/实证|15|0|0.0|0|True|
|pack4_fb6|近似/实证|15|0|0.0|0|True|
|fb3_selective_fast_inplace|近似/实证|15|5211625|0.0087890625|0|True|
|fb2_epoch_shadow|精确|15|0|0.0|0|True|
|fb2_epoch_fast_shadow|近似/实证|15|5152796|0.0078125|0|True|
