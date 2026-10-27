# Diagnostic per-FB GPU intervals

1920×1080, 50 warmup / 20 measured frames, original 82 single-kernel NVAPI chains. D3D12 timestamps perturb scheduling. Values below are per-frame FB sums averaged over 20 frames; not ABBA and not dynamic stall counters. Full-frame decisions use results.md. Warmup trace rows were pruned, with original raw SHA retained in profile-controls.json.

| Variant | FB01 ms | FB02 ms | FB04 ms | FB05 ms |
|---|---:|---:|---:|---:|
| baseline | 1.163213 | 1.019904 | 0.946483 | 3.231386 |
| c | 1.168947 | 1.027226 | 0.950579 | 3.127962 |
| abc | 1.220864 | 1.040282 | 0.921702 | 3.206707 |
| d1-192 | 1.271552 | 0.982682 | 0.955750 | 3.131750 |
| d1-224 | 1.376410 | 1.042637 | 1.040691 | 3.489894 |
| d1-255 | 1.316045 | 0.997632 | 0.912230 | 3.204250 |
| d2-192 | 1.151744 | 1.106995 | 0.982170 | 3.247974 |
| d2-224 | 1.180058 | 1.092915 | 0.971520 | 3.212083 |
| d2-255 | 1.150208 | 1.105459 | 0.983398 | 3.130726 |
| d4-168 | 1.170534 | 1.019802 | 1.879654 | 3.200922 |
| d4-192 | 1.181030 | 0.976026 | 0.954624 | 3.198771 |
| d4-224 | 1.226752 | 0.984064 | 0.964966 | 3.277978 |
| d5-168 | 1.211392 | 1.004186 | 0.931738 | 3.575091 |
| d5-192 | 1.196698 | 0.984525 | 0.917811 | 3.245107 |
| d5-224 | 1.182771 | 0.978739 | 0.966707 | 3.210906 |
| abc-end | 1.217690 | 1.026918 | 0.949453 | 3.224832 |
