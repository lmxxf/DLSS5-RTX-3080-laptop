# Phase17 paired controls

Small31/Style1,Graph off,defaultDVFS;50warmup/80iter for ABBA. PROFILE_TOTAL is an independent instrumented frame.

| Run | Width | GPU min /median ms | Wall median | PROFILE_TOTAL |
|---|---:|---:|---:|---:|
| baseline-a-nc-abba | 1280 | 13.797 /14.067 | 14.156 | 13.306880 |
| baseline-a-nc-abba | 1600 | 23.199 /23.581 | 23.667 | 21.999616 |
| baseline-a-nc-abba | 1920 | 31.018 /31.608 | 31.717 | 28.778496 |
| baseline-a2-nc-abba | 1280 | 13.898 /14.066 | 14.155 | 13.271040 |
| baseline-a2-nc-abba | 1600 | 23.218 /23.657 | 23.732 | 21.683200 |
| baseline-a2-nc-abba | 1920 | 31.263 /31.828 | 31.927 | 28.777472 |
| baseline-quick | 1280 | 14.181 /14.190 | 14.320 | 14.338048 |
| baseline-quick | 1600 | 23.107 /23.200 | 23.256 | 21.610496 |
| baseline-quick | 1920 | 30.631 /30.745 | 30.816 | 28.306528 |
| candidate-b-nc-abba | 1280 | 13.614 /13.785 | 13.865 | 12.987424 |
| candidate-b-nc-abba | 1600 | 22.762 /23.203 | 23.271 | 20.881408 |
| candidate-b-nc-abba | 1920 | 30.716 /31.094 | 31.169 | 27.372544 |
| candidate-b2-nc-abba | 1280 | 13.601 /13.812 | 13.904 | 13.456384 |
| candidate-b2-nc-abba | 1600 | 22.771 /23.215 | 23.309 | 20.911104 |
| candidate-b2-nc-abba | 1920 | 30.641 /31.131 | 31.260 | 27.361280 |
| candidate-quick | 1280 | 13.765 /13.774 | 13.851 | 12.961792 |
| candidate-quick | 1600 | 22.927 /23.087 | 23.191 | 21.128192 |
| candidate-quick | 1920 | 30.273 /30.904 | 31.030 | 27.768832 |
| nc-quick | 1280 | 13.715 /13.721 | 13.830 | 13.913088 |
| nc-quick | 1600 | 22.585 /22.702 | 22.801 | 20.950016 |
| nc-quick | 1920 | 30.113 /30.157 | 30.272 | 27.718656 |

## 1280 C32 profiles

| Run | Kernel | Total ms | Regs | LMem | Shared | OccW |
|---|---|---:|---:|---:|---:|---:|
| baseline-a-nc-abba | c32_wave1_finish_b8 | 0.485376 | 162 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_finish_dcrop_b8d | 0.498688 | 162 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_mapped_b8 | 0.490496 | 168 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_post_b8 | 1.982464 | 168 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_prefix_b8d | 2.032640 | 168 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_up_b8 | 0.556032 | 168 | 0 | 10240 | 9 |
| baseline-a2-nc-abba | c32_wave1_finish_b8 | 0.483328 | 162 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_finish_dcrop_b8d | 0.497664 | 162 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_mapped_b8 | 0.489472 | 168 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_post_b8 | 1.978368 | 168 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_prefix_b8d | 2.023424 | 168 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_up_b8 | 0.553984 | 168 | 0 | 10240 | 9 |
| baseline-quick | c32_wave1_finish_b8 | 0.523264 | 162 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_finish_dcrop_b8d | 0.539648 | 162 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_mapped_b8 | 0.531456 | 168 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_post_b8 | 2.147328 | 168 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_prefix_b8d | 2.194432 | 168 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_up_b8 | 0.601088 | 168 | 0 | 10240 | 9 |
| candidate-b-nc-abba | c32_wave1_finish_b8 | 0.437248 | 168 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_finish_dcrop_b8d | 0.448512 | 168 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_mapped_b8 | 0.441344 | 167 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_post_b8 | 1.847296 | 168 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_prefix_b8d | 1.934336 | 168 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_up_b8 | 0.530432 | 154 | 0 | 10240 | 9 |
| candidate-b2-nc-abba | c32_wave1_finish_b8 | 0.432128 | 168 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_finish_dcrop_b8d | 0.472064 | 168 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_mapped_b8 | 0.468992 | 167 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_post_b8 | 1.838080 | 168 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_prefix_b8d | 2.035712 | 168 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_up_b8 | 0.524288 | 154 | 0 | 10240 | 9 |
| candidate-quick | c32_wave1_finish_b8 | 0.441344 | 168 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_finish_dcrop_b8d | 0.468992 | 168 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_mapped_b8 | 0.443392 | 162 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_post_b8 | 1.857536 | 168 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_prefix_b8d | 1.958912 | 168 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_up_b8 | 0.537600 | 154 | 0 | 10240 | 9 |
| nc-quick | c32_wave1_finish_b8 | 0.468992 | 168 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_finish_dcrop_b8d | 0.481280 | 168 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_mapped_b8 | 0.472064 | 167 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_post_b8 | 1.994752 | 168 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_prefix_b8d | 2.075648 | 168 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_up_b8 | 0.567296 | 154 | 0 | 10240 | 9 |

## 1600 C32 profiles

| Run | Kernel | Total ms | Regs | LMem | Shared | OccW |
|---|---|---:|---:|---:|---:|---:|
| baseline-a-nc-abba | c32_wave1_finish_b8 | 0.795648 | 162 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_finish_dcrop_b8d | 0.813056 | 162 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_mapped_b8 | 0.801792 | 168 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_post_b8 | 3.271680 | 168 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_prefix_b8d | 3.362816 | 168 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_up_b8 | 0.903168 | 168 | 0 | 10240 | 9 |
| baseline-a2-nc-abba | c32_wave1_finish_b8 | 0.793600 | 162 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_finish_dcrop_b8d | 0.820224 | 162 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_mapped_b8 | 0.797696 | 168 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_post_b8 | 3.272704 | 168 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_prefix_b8d | 3.363808 | 168 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_up_b8 | 0.904192 | 168 | 0 | 10240 | 9 |
| baseline-quick | c32_wave1_finish_b8 | 0.792576 | 162 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_finish_dcrop_b8d | 0.809984 | 162 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_mapped_b8 | 0.796672 | 168 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_post_b8 | 3.269632 | 168 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_prefix_b8d | 3.365888 | 168 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_up_b8 | 0.904192 | 168 | 0 | 10240 | 9 |
| candidate-b-nc-abba | c32_wave1_finish_b8 | 0.702464 | 168 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_finish_dcrop_b8d | 0.719872 | 168 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_mapped_b8 | 0.712704 | 167 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_post_b8 | 3.043328 | 168 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_prefix_b8d | 3.175424 | 168 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_up_b8 | 0.850944 | 154 | 0 | 10240 | 9 |
| candidate-b2-nc-abba | c32_wave1_finish_b8 | 0.702464 | 168 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_finish_dcrop_b8d | 0.720896 | 168 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_mapped_b8 | 0.712704 | 167 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_post_b8 | 3.044352 | 168 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_prefix_b8d | 3.179520 | 168 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_up_b8 | 0.850944 | 154 | 0 | 10240 | 9 |
| candidate-quick | c32_wave1_finish_b8 | 0.712704 | 168 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_finish_dcrop_b8d | 0.733184 | 168 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_mapped_b8 | 0.720896 | 162 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_post_b8 | 3.063808 | 168 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_prefix_b8d | 3.243008 | 168 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_up_b8 | 0.869376 | 154 | 0 | 10240 | 9 |
| nc-quick | c32_wave1_finish_b8 | 0.698368 | 168 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_finish_dcrop_b8d | 0.720896 | 168 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_mapped_b8 | 0.709632 | 167 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_post_b8 | 3.039232 | 168 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_prefix_b8d | 3.182592 | 168 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_up_b8 | 0.850944 | 154 | 0 | 10240 | 9 |

## 1920 C32 profiles

| Run | Kernel | Total ms | Regs | LMem | Shared | OccW |
|---|---|---:|---:|---:|---:|---:|
| baseline-a-nc-abba | c32_wave1_finish_b8 | 1.065984 | 162 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_finish_dcrop_b8d | 1.086464 | 162 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_mapped_b8 | 1.070080 | 168 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_post_b8 | 4.874240 | 168 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_prefix_b8d | 4.533248 | 168 | 0 | 8192 | 11 |
| baseline-a-nc-abba | c32_wave1_up_b8 | 1.219584 | 168 | 0 | 10240 | 9 |
| baseline-a2-nc-abba | c32_wave1_finish_b8 | 1.059840 | 162 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_finish_dcrop_b8d | 1.087488 | 162 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_mapped_b8 | 1.071104 | 168 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_post_b8 | 4.533248 | 168 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_prefix_b8d | 4.554752 | 168 | 0 | 8192 | 11 |
| baseline-a2-nc-abba | c32_wave1_up_b8 | 1.212416 | 168 | 0 | 10240 | 9 |
| baseline-quick | c32_wave1_finish_b8 | 1.056768 | 162 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_finish_dcrop_b8d | 1.083392 | 162 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_mapped_b8 | 1.067008 | 168 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_post_b8 | 4.406272 | 168 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_prefix_b8d | 4.532224 | 168 | 0 | 8192 | 11 |
| baseline-quick | c32_wave1_up_b8 | 1.211392 | 168 | 0 | 10240 | 9 |
| candidate-b-nc-abba | c32_wave1_finish_b8 | 0.937984 | 168 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_finish_dcrop_b8d | 0.963584 | 168 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_mapped_b8 | 0.951296 | 167 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_post_b8 | 4.098048 | 168 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_prefix_b8d | 4.289536 | 168 | 0 | 8192 | 11 |
| candidate-b-nc-abba | c32_wave1_up_b8 | 1.138688 | 154 | 0 | 10240 | 9 |
| candidate-b2-nc-abba | c32_wave1_finish_b8 | 0.937984 | 168 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_finish_dcrop_b8d | 0.962560 | 168 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_mapped_b8 | 0.950272 | 167 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_post_b8 | 4.100096 | 168 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_prefix_b8d | 4.288512 | 168 | 0 | 8192 | 11 |
| candidate-b2-nc-abba | c32_wave1_up_b8 | 1.139712 | 154 | 0 | 10240 | 9 |
| candidate-quick | c32_wave1_finish_b8 | 0.946176 | 168 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_finish_dcrop_b8d | 0.975872 | 168 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_mapped_b8 | 0.961536 | 162 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_post_b8 | 4.412416 | 168 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_prefix_b8d | 4.367360 | 168 | 0 | 8192 | 11 |
| candidate-quick | c32_wave1_up_b8 | 1.160192 | 154 | 0 | 10240 | 9 |
| nc-quick | c32_wave1_finish_b8 | 0.937984 | 168 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_finish_dcrop_b8d | 0.958464 | 168 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_mapped_b8 | 0.946176 | 167 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_post_b8 | 4.523008 | 168 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_prefix_b8d | 4.281344 | 168 | 0 | 8192 | 11 |
| nc-quick | c32_wave1_up_b8 | 1.137664 | 154 | 0 | 10240 | 9 |
