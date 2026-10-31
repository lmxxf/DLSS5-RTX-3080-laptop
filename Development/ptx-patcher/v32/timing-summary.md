# V3.2 data-first paired timing audit

50 warmup / 80 iter. Means of independent process GPU medians; default DVFS. Positive means lower latency. Entire excluded screening round remains in excluded-timing.json, complete replacements in first.json.

|Candidate|Width|Base ms|Candidate ms|Decrease %|Forward %|Reverse %|
|---|---:|---:|---:|---:|---:|---:|
|first/split|1280|5.71050|5.71175|-0.022|-0.026|-0.017|
|first/split|1600|8.39800|8.39450|0.042|0.688|-0.609|
|first/split|1920|11.07100|11.11450|-0.393|-0.628|-0.158|
|first/split_up|1280|5.72675|5.70475|0.384|0.412|0.356|
|first/split_up|1600|8.40250|8.37900|0.280|0.233|0.326|
|first/split_up|1920|11.07575|11.06700|0.079|0.018|0.140|
|first/up|1280|5.70675|5.70025|0.114|0.300|-0.070|
|first/up|1600|8.40525|8.38700|0.217|0.547|-0.113|
|first/up|1920|11.07025|11.05350|0.151|-0.217|0.519|
|caps/split_up_contract|1280|5.72400|5.77575|-0.904|-0.464|-1.343|
|caps/split_up_contract|1600|8.40975|8.39225|0.208|-0.042|0.457|
|caps/split_up_contract|1920|11.16075|11.13825|0.202|0.292|0.112|
|caps/split_up_expand|1280|5.75550|5.85275|-1.690|-1.858|-1.523|
|caps/split_up_expand|1600|8.41925|8.53600|-1.387|-1.695|-1.079|
|caps/split_up_expand|1920|11.20300|11.39550|-1.718|-2.174|-1.265|
|caps/split_up_head|1280|5.74525|5.75000|-0.083|-0.210|0.043|
|caps/split_up_head|1600|8.40575|8.43800|-0.384|-0.411|-0.357|
|caps/split_up_head|1920|11.17500|11.20250|-0.246|0.013|-0.506|
|caps/split_up_pool|1280|5.75675|5.74475|0.208|-0.026|0.442|
|caps/split_up_pool|1600|8.42525|8.42900|-0.045|0.290|-0.381|
|caps/split_up_pool|1920|11.16550|11.09750|0.609|0.237|0.982|
|caps/split_up_proj|1280|5.76275|5.75175|0.191|0.113|0.268|
|caps/split_up_proj|1600|8.43675|8.43175|0.059|-0.077|0.195|
|caps/split_up_proj|1920|11.12475|11.14775|-0.207|-0.247|-0.167|
|caps/split_up_publish|1280|5.71700|5.71800|-0.017|-0.088|0.052|
|caps/split_up_publish|1600|8.41625|8.40325|0.154|0.089|0.220|
|caps/split_up_publish|1920|11.16225|11.12825|0.305|0.072|0.534|
|arithmetic/shift|1280|5.67375|5.66225|0.203|0.160|0.245|
|arithmetic/shift|1600|8.32500|8.31050|0.174|-0.036|0.382|
|arithmetic/shift|1920|10.99450|11.01925|-0.225|-0.255|-0.195|
|arithmetic/split_up_shift|1280|5.68250|5.69275|-0.180|0.053|-0.411|
|arithmetic/split_up_shift|1600|8.29800|8.33400|-0.434|-0.211|-0.656|
|arithmetic/split_up_shift|1920|11.02425|11.02100|0.029|-0.145|0.204|
|repeat/split_up|1280|5.75750|5.74650|0.191|0.113|0.269|
|repeat/split_up|1600|8.40450|8.41800|-0.161|-0.316|-0.006|
|repeat/split_up|1920|11.09150|11.03950|0.469|0.199|0.738|
