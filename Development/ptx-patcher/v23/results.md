# V2.3 decode control

Each process: 50 warmup / 80 measured iterations. Primary forward ABBA and reverse BAAB at all three tiers; additional 1080p forward/reverse block retained in full. Values are means of process medians/minima, not pooled-frame medians.

| Group | Width | V2.2 median ms | PRMT8 median ms | V2.2 min ms | PRMT8 min ms | Time decrease |
|---|---:|---:|---:|---:|---:|---:|
| primary | 1280 | 6.24950 | 6.12575 | 6.10150 | 5.98025 | 1.980% |
| primary | 1600 | 9.12125 | 8.92525 | 8.86075 | 8.72350 | 2.149% |
| primary | 1920 | 11.87775 | 11.80750 | 11.54325 | 11.36075 | 0.591% |
| confirm1080 | 1920 | 11.73375 | 11.55650 | 11.48250 | 11.28700 | 1.511% |
| combined | 1280 | 6.24950 | 6.12575 | 6.10150 | 5.98025 | 1.980% |
| combined | 1600 | 9.12125 | 8.92525 | 8.86075 | 8.72350 | 2.149% |
| combined | 1920 | 11.80575 | 11.68200 | 11.51288 | 11.32387 | 1.048% |
Primary 1080p forward includes one 12.144 ms candidate run and is slower in that direction; the reverse block wins. The concern motivated one complete independent confirmation block, whose two directions both win. No sample was dropped. Combined 1080p contains eight runs per version.

All 6 smoke and 32 timed outputs are bit identical to same-configuration V2.2 gold (maxabs=0 / PSNR=infinite / invalid=0).
