# V3.8 serial paired results

Means of process GPU medians, forward ABBA / reverse BAAB; positive = lower latency.

|Round/candidate|Width|Base ms|Candidate ms|Gain %|Forward %|Reverse %|Quality pass|
|---|---:|---:|---:|---:|---:|---:|---|
|timed/async_pool_only|1280|5.72225|5.73200|-0.170|-0.140|-0.201|True|
|timed/async_pool_only|1600|8.37625|8.43725|-0.728|-0.777|-0.679|True|
|timed/async_pool_only|1920|11.07850|11.12800|-0.447|-0.420|-0.474|True|
|timed/fb3_inp_up_exact|1280|5.71800|5.71625|0.031|-0.096|0.157|True|
|timed/fb3_inp_up_exact|1600|8.39200|8.39800|-0.071|0.333|-0.477|True|
|timed/fb3_inp_up_exact|1920|11.04700|11.07500|-0.253|-0.163|-0.344|True|
|timed/fb3_inp_up_fast|1280|5.70450|5.70725|-0.048|0.079|-0.175|True|
|timed/fb3_inp_up_fast|1600|8.39875|8.40875|-0.119|-0.250|0.012|True|
|timed/fb3_inp_up_fast|1920|11.07775|11.06800|0.088|-0.203|0.379|True|
|timed/joint_zero_const_fb456_fb3_inp_up_fast|1280|5.75400|5.71400|0.695|1.034|0.356|True|
|timed/joint_zero_const_fb456_fb3_inp_up_fast|1600|8.40350|8.39700|0.077|0.006|0.148|True|
|timed/joint_zero_const_fb456_fb3_inp_up_fast|1920|11.08650|11.07975|0.061|0.050|0.072|True|
|timed/pack4_fb26_clean|1280|5.70225|5.67475|0.482|0.512|0.453|True|
|timed/pack4_fb26_clean|1600|8.37675|8.33875|0.454|0.417|0.491|True|
|timed/pack4_fb26_clean|1920|11.07550|11.08500|-0.086|-0.266|0.095|True|
|timed/pack4_pure36|1280|5.69050|5.67500|0.272|0.195|0.349|True|
|timed/pack4_pure36|1600|8.40075|8.39525|0.065|-0.424|0.552|True|
|timed/pack4_pure36|1920|11.07275|11.06775|0.045|0.045|0.045|True|
|timed/zero_const_fb26|1280|5.68425|5.66400|0.356|0.177|0.532|True|
|timed/zero_const_fb26|1600|8.37675|8.36725|0.113|0.602|-0.376|True|
|timed/zero_const_fb26|1920|11.07875|11.06650|0.111|0.068|0.153|True|
|timed/zero_const_fb456|1280|5.68000|5.66650|0.238|0.106|0.367|True|
|timed/zero_const_fb456|1600|8.41975|8.36475|0.653|0.594|0.712|True|
|timed/zero_const_fb456|1920|11.07375|11.05900|0.133|0.063|0.203|True|
|repeat/joint_zero_const_fb456_fb3_inp_up_fast|1280|5.74175|5.73050|0.196|0.026|0.365|True|
|repeat/joint_zero_const_fb456_fb3_inp_up_fast|1600|8.35700|8.44150|-1.011|-0.388|-1.637|True|
|repeat/joint_zero_const_fb456_fb3_inp_up_fast|1920|11.06525|11.09500|-0.269|-0.217|-0.321|True|
|repeat/zero_const_fb456|1280|5.73900|5.71850|0.357|0.348|0.366|True|
|repeat/zero_const_fb456|1600|8.42300|8.37050|0.623|0.184|1.062|True|
|repeat/zero_const_fb456|1920|11.08225|11.05300|0.264|0.320|0.208|True|
