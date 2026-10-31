# V3.8 输出质量汇总

三档固定输入、末帧对V3.1_pack5；经验Pack4仍按实证候选标记，不推断未测中间激活范围。

|候选|类型|次数|最大bit-diff|最大绝对误差|最小非无限PSNR dB|最大非有限数|质量全过|
|---|---|---:|---:|---:|---:|---:|---|
|baseline|精确|123|0|0.0|∞|0|True|
|zero_const_fb26|精确|15|0|0.0|∞|0|True|
|zero_const_fb456|精确|27|0|0.0|∞|0|True|
|pack4_pure36|近似/实证|15|0|0.0|∞|0|True|
|pack4_fb26_clean|近似/实证|15|0|0.0|∞|0|True|
|fb3_inp_up_fast|近似/实证|15|5196349|0.007568359375|60.724936016200104|0|True|
|fb3_inp_up_exact|精确|15|0|0.0|∞|0|True|
|async_pool_only|精确|15|0|0.0|∞|0|True|
|joint_zero_const_fb26_fb3_inp_up_fast|近似/实证|3|5178773|0.00732421875|60.756025047306615|0|True|
|joint_zero_const_fb26_fb3_inp_up_exact|精确|3|0|0.0|∞|0|True|
|joint_zero_const_fb456_fb3_inp_up_fast|近似/实证|27|5196349|0.007568359375|60.724936016200104|0|True|
|joint_zero_const_fb456_fb3_inp_up_exact|精确|3|0|0.0|∞|0|True|
|joint_pack4_pure36_fb3_inp_up_fast|近似/实证|3|5178773|0.00732421875|60.756025047306615|0|True|
|joint_pack4_pure36_fb3_inp_up_exact|近似/实证|3|0|0.0|∞|0|True|
|joint_pack4_fb26_clean_fb3_inp_up_fast|近似/实证|3|5178773|0.00732421875|60.756025047306615|0|True|
|joint_pack4_fb26_clean_fb3_inp_up_exact|近似/实证|3|0|0.0|∞|0|True|
