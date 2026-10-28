# V2.9 paired controls

50 warmup / 80 iter, forward ABBA and reverse BAAB; mean of process GPU medians, paired V2.7 reference.

|Candidate|Width|Baseline ms|Candidate ms|Decrease|Forward / reverse|
|---|---:|---:|---:|---:|---:|
|exact|1280|6.08775|5.94150|2.402%|0.880% / 3.837%|
|exact|1600|8.86450|8.76900|1.077%|0.638% / 1.508%|
|exact|1920|11.58825|11.49325|0.820%|-0.976% / 2.565%|
|fast|1280|6.02850|5.87400|2.563%|2.229% / 2.883%|
|fast|1600|8.83450|8.58125|2.867%|2.527% / 3.197%|
|fast|1920|11.64550|11.28750|3.074%|1.714% / 4.399%|
