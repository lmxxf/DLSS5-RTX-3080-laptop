# V3.4 paired serial measurements

50 warmup / 80 iter, forward ABBA + reverse BAAB; positive = lower latency; means of process GPU medians.

|Round/candidate|Width|V3.1 ms|Candidate ms|Decrease %|Forward %|Reverse %|
|---|---:|---:|---:|---:|---:|---:|
|bench/quad_fb0145|1280|5.69825|5.69800|0.004|-0.106|0.113|
|bench/quad_fb0145|1600|8.39750|8.35500|0.506|0.625|0.387|
|bench/quad_fb0145|1920|11.04525|11.04175|0.032|-0.327|0.388|
|bench/quad_fb1|1280|5.68325|5.66900|0.251|0.267|0.235|
|bench/quad_fb1|1600|8.37125|8.35250|0.224|0.036|0.411|
|bench/quad_fb1|1920|11.05125|11.01350|0.342|0.222|0.461|
|bench/quad_fb1_shared|1280|5.72350|5.72450|-0.017|-0.184|0.148|
|bench/quad_fb1_shared|1600|8.36950|8.37500|-0.066|-0.770|0.629|
|bench/quad_fb1_shared|1920|11.05250|11.05000|0.023|-0.108|0.154|
|bench/quad_local|1280|5.68400|5.68700|-0.053|0.213|-0.315|
|bench/quad_local|1600|8.39100|8.36800|0.274|0.156|0.392|
|bench/quad_local|1920|11.00100|10.98175|0.175|0.345|0.005|
|bench/shared_forward|1280|5.72125|5.71025|0.192|0.114|0.269|
|bench/shared_forward|1600|8.40600|8.39875|0.086|0.048|0.125|
|bench/shared_forward|1920|11.04875|11.16375|-1.041|-1.552|-0.526|
|repeat/quad_fb1|1280|5.72625|5.73575|-0.166|-0.166|-0.166|
|repeat/quad_fb1|1600|8.40125|8.40075|0.006|0.178|-0.167|
|repeat/quad_fb1|1920|11.02800|11.04025|-0.111|-0.059|-0.163|
