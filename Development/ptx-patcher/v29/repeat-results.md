# V2.9 paired controls

50 warmup / 80 iter, forward ABBA and reverse BAAB; mean of process GPU medians, paired V2.7 reference.

|Candidate|Width|Baseline ms|Candidate ms|Decrease|Forward / reverse|
|---|---:|---:|---:|---:|---:|
|exact|1280|6.04775|6.01100|0.608%|0.342% / 0.869%|
|exact|1600|8.78125|8.79350|-0.140%|-0.189% / -0.091%|
|exact|1920|11.67950|11.71675|-0.319%|0.158% / -0.797%|
|fast|1280|6.05300|5.89575|2.598%|2.843% / 2.354%|
|fast|1600|8.90400|8.72575|2.002%|2.138% / 1.865%|
|fast|1920|11.59850|11.39450|1.759%|1.468% / 2.047%|
