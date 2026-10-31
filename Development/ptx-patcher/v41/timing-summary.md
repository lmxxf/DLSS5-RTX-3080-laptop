# V4.1 serial paired results

Means of process GPU medians, forward ABBA / reverse BAAB; positive = lower latency.

|Round/candidate|Width|Base ms|Candidate ms|Gain %|Forward %|Reverse %|Quality pass|
|---|---:|---:|---:|---:|---:|---:|---|
|timed/joint_up_add_fb4pool_zero_pack4|1280|5.65625|5.65875|-0.044|-0.248|0.159|True|
|timed/joint_up_add_fb4pool_zero_pack4|1600|8.32775|8.30425|0.282|0.205|0.359|True|
|timed/joint_up_add_fb4pool_zero_pack4|1920|11.02125|11.01275|0.077|0.131|0.023|True|
|timed/pack4_add_fb4_nospill|1280|5.61900|5.62275|-0.067|0.018|-0.150|True|
|timed/pack4_add_fb4_nospill|1600|8.32875|8.32900|-0.003|0.366|-0.373|True|
|timed/pack4_add_fb4_nospill|1920|11.01100|11.01125|-0.002|0.091|-0.095|True|
|timed/up_add_fb4pool|1280|5.60975|5.61350|-0.067|-0.234|0.097|True|
|timed/up_add_fb4pool|1600|8.28700|8.28950|-0.030|-0.157|0.096|True|
|timed/up_add_fb4pool|1920|10.98150|11.00175|-0.184|-0.324|-0.045|True|
|timed/up_add_fb6|1280|5.58700|5.59175|-0.085|0.036|-0.204|True|
|timed/up_add_fb6|1600|8.29725|8.28325|0.169|-0.406|0.736|True|
|timed/up_add_fb6|1920|11.00350|10.99050|0.118|0.209|0.027|True|
|timed/up_occ_keep|1280|5.60125|5.59200|0.165|0.262|0.071|True|
|timed/up_occ_keep|1600|8.25775|8.27825|-0.248|-0.487|-0.012|True|
|timed/up_occ_keep|1920|10.97675|10.95350|0.212|0.698|-0.273|True|
|timed/zero_fb23456|1280|5.62375|5.60975|0.249|0.385|0.115|True|
|timed/zero_fb23456|1600|8.27375|8.32850|-0.662|-0.702|-0.621|True|
|timed/zero_fb23456|1920|11.00700|11.02125|-0.129|0.014|-0.272|True|
