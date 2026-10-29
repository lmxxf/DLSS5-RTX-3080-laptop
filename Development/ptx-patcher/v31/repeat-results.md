# V3.1 paired controls

50 warmup / 80 iter, forward ABBA and reverse BAAB; mean of process GPU medians, paired V2.9_fast reference.

|Candidate|Width|Baseline ms|Candidate ms|Decrease|Forward / reverse|
|---|---:|---:|---:|---:|---:|
|pack5|1280|5.87675|5.77950|1.655%|1.753% / 1.557%|
|pack5|1600|8.64600|8.46125|2.137%|1.785% / 2.482%|
|pack5|1920|11.27500|11.12300|1.348%|1.373% / 1.324%|
|pack5_quad|1280|5.89600|5.73950|2.654%|2.700% / 2.609%|
|pack5_quad|1600|8.63650|8.48150|1.795%|2.019% / 1.573%|
|pack5_quad|1920|11.29075|11.33675|-0.407%|-2.524% / 1.702%|
