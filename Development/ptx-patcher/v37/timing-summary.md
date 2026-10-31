# V3.7 serial paired results

Means of process GPU medians, forward ABBA / reverse BAAB; positive = lower latency.

|Round/candidate|Width|Base ms|Candidate ms|Gain %|Forward %|Reverse %|Quality pass|
|---|---:|---:|---:|---:|---:|---:|---|
|timed/async_qkv_only|1280|5.67650|5.69850|-0.388|-0.839|0.052|True|
|timed/async_qkv_only|1600|8.43275|8.42025|0.148|0.125|0.172|True|
|timed/async_qkv_only|1920|11.06650|11.10625|-0.359|-0.298|-0.420|True|
|timed/async_qkv_unrolled|1280|5.68925|5.72075|-0.554|-0.602|-0.506|True|
|timed/async_qkv_unrolled|1600|8.39525|8.43150|-0.432|-0.640|-0.226|True|
|timed/async_qkv_unrolled|1920|11.05075|11.11600|-0.590|-0.848|-0.334|True|
|timed/fb3_ds_wait_fast_inplace|1280|5.70850|5.73225|-0.416|-0.386|-0.446|True|
|timed/fb3_ds_wait_fast_inplace|1600|8.39875|8.39100|0.092|-0.562|0.741|True|
|timed/fb3_ds_wait_fast_inplace|1920|11.07650|11.10400|-0.248|-0.027|-0.470|True|
|timed/fb3_inpview_fast_inplace|1280|5.71675|5.71525|0.026|-0.018|0.070|True|
|timed/fb3_inpview_fast_inplace|1600|8.40225|8.33300|0.824|0.679|0.969|True|
|timed/fb3_inpview_fast_inplace|1920|11.07550|11.06325|0.111|0.172|0.050|True|
|timed/fb3_noinp_fast_inplace|1280|5.72575|5.74300|-0.301|-0.271|-0.332|True|
|timed/fb3_noinp_fast_inplace|1600|8.39950|8.38225|0.205|-0.376|0.784|True|
|timed/fb3_noinp_fast_inplace|1920|11.07900|11.08650|-0.068|0.041|-0.176|True|
|timed/fb3_outview_fast_inplace|1280|5.71300|5.76425|-0.897|-0.928|-0.866|True|
|timed/fb3_outview_fast_inplace|1600|8.42500|8.37950|0.540|0.190|0.890|True|
|timed/fb3_outview_fast_inplace|1920|11.07475|11.06775|0.063|0.063|0.063|True|
|timed/fb3_regdown_fast_inplace|1280|5.72550|5.75275|-0.476|-0.436|-0.516|True|
|timed/fb3_regdown_fast_inplace|1600|8.41950|8.38900|0.362|0.196|0.529|True|
|timed/fb3_regdown_fast_inplace|1920|11.09225|11.08850|0.034|0.004|0.063|True|
|timed/fb3_upsample_fast_inplace|1280|5.72325|5.72100|0.039|0.271|-0.192|True|
|timed/fb3_upsample_fast_inplace|1600|8.39550|8.35850|0.441|0.717|0.166|True|
|timed/fb3_upsample_fast_inplace|1920|11.09250|11.07875|0.124|-0.018|0.266|True|
|timed/joint_noinp|1280|5.72075|5.74600|-0.441|-0.384|-0.499|True|
|timed/joint_noinp|1600|8.35850|8.39000|-0.377|-0.126|-0.626|True|
|timed/joint_noinp|1920|11.08100|11.08700|-0.054|-0.176|0.068|True|
|timed/joint_regdown|1280|5.71325|5.74900|-0.626|-0.560|-0.692|True|
|timed/joint_regdown|1600|8.40975|8.40775|0.024|-0.083|0.131|True|
|timed/joint_regdown|1920|11.08400|11.09050|-0.059|-0.036|-0.081|True|
|timed/pack4_clean2356|1280|5.69325|5.65050|0.751|0.909|0.594|True|
|timed/pack4_clean2356|1600|8.38775|8.36325|0.292|0.866|-0.288|True|
|timed/pack4_clean2356|1920|11.07850|11.04850|0.271|0.293|0.248|True|
|timed/pack4_clean36|1280|5.70375|5.66700|0.644|0.528|0.759|True|
|timed/pack4_clean36|1600|8.42075|8.37975|0.487|0.160|0.813|True|
|timed/pack4_clean36|1920|11.07625|11.03700|0.354|0.501|0.208|True|
|timed/pack_zero_const|1280|5.69000|5.66175|0.496|0.353|0.638|True|
|timed/pack_zero_const|1600|8.40175|8.39875|0.036|-0.256|0.327|True|
|timed/pack_zero_const|1920|11.07975|11.03625|0.393|0.645|0.140|True|
|repeat/pack4_clean36|1280|5.73500|5.71150|0.410|0.140|0.678|True|
|repeat/pack4_clean36|1600|8.33025|8.36500|-0.417|-0.437|-0.397|True|
|repeat/pack4_clean36|1920|11.07175|11.03500|0.332|0.275|0.389|True|
