# V2.7 factor, cap and conditional controls

Every process: 50 warmup / 80 iter; forward ABBA and reverse BAAB. Means of process GPU median/min. No clock lock; compare each candidate with its own bracketing control.

| Candidate | Width | V2.6 median ms | Candidate median ms | V2.6 min ms | Candidate min ms | Decrease | Forward / reverse |
|---|---:|---:|---:|---:|---:|---:|---:|
| a | 1280 | 6.04775 | 6.02750 | 5.97675 | 5.95075 | 0.335% | 0.275% / 0.393% |
| a | 1600 | 8.84550 | 8.80150 | 8.63525 | 8.63900 | 0.497% | 0.657% / 0.339% |
| a | 1920 | 11.58475 | 11.58000 | 11.29650 | 11.31875 | 0.041% | -0.134% / 0.215% |
| b | 1280 | 6.06500 | 6.06675 | 5.99025 | 5.97225 | -0.029% | -0.033% / -0.025% |
| b | 1600 | 8.81625 | 8.82875 | 8.62900 | 8.64075 | -0.142% | 0.085% / -0.368% |
| b | 1920 | 11.60750 | 11.66425 | 11.32975 | 11.32725 | -0.489% | -0.588% / -0.391% |
| ab | 1280 | 6.07725 | 6.03925 | 5.99175 | 5.96400 | 0.625% | 0.595% / 0.655% |
| ab | 1600 | 8.81275 | 8.78675 | 8.64600 | 8.59675 | 0.295% | -0.023% / 0.610% |
| ab | 1920 | 11.56700 | 11.58950 | 11.31425 | 11.26275 | -0.195% | -0.454% / 0.065% |
| cap0-168 | 1280 | 6.07900 | 6.02200 | 5.98875 | 5.95850 | 0.938% | 0.926% / 0.950% |
| cap0-168 | 1600 | 8.83875 | 8.77950 | 8.64550 | 8.57900 | 0.670% | 0.431% / 0.909% |
| cap0-168 | 1920 | 11.61700 | 11.50375 | 11.35225 | 11.20375 | 0.975% | 0.987% / 0.962% |
| cap1-192 | 1280 | 6.07525 | 6.10225 | 5.98750 | 6.01750 | -0.444% | -0.446% / -0.443% |
| cap1-192 | 1600 | 8.84050 | 8.87400 | 8.67625 | 8.71625 | -0.379% | -0.284% / -0.473% |
| cap1-192 | 1920 | 11.57775 | 11.63175 | 11.32625 | 11.41050 | -0.466% | -0.692% / -0.241% |

Conditional comparisons below use four-kernel cap168 as reference, not V2.6.

| Addition/change | Width | Four-kernel cap median | Candidate median | Decrease | Forward / reverse |
|---|---:|---:|---:|---:|---:|
| add-A | 1280 | 5.95050 | 5.94225 | 0.139% | 0.306% / -0.025% |
| add-A | 1600 | 8.66725 | 8.65025 | 0.196% | 0.232% / 0.161% |
| add-A | 1920 | 11.36325 | 11.35550 | 0.068% | -0.176% / 0.312% |
| prefix-only | 1280 | 6.02675 | 6.03850 | -0.195% | -0.141% / -0.249% |
| prefix-only | 1920 | 11.48850 | 11.51825 | -0.259% | -0.078% / -0.439% |

Recommendation: cap168 only for prefix, inpview, ds_wait, outview in FB00. Keep post/upsample and all other kernels unchanged. A/B and C64 raised caps are not selected; adding A to the winning cap configuration reverses sign at 720p/1080p. Prefix-only is slower than adjusting all four in both tested tiers/directions.
