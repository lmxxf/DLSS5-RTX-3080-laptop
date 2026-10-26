# Route B V2 same-round DLL comparison

Preset2 / Style1; 50warmup/80iter, 720p sky /900p and1080p deterministic scene; default DVFS. forward old→new→V7, reverse V7→new→old. GPU hardware timestamps, wall kept separately.

| Round | Width | DLL | GPU min /median ms | Wall median | Sky sign changes /HF RMS |
|---|---:|---|---:|---:|---|
| forward | 1280 | new | 10.027 /10.187 | 10.622 | 0 /0.000101989 |
| forward | 1600 | new | 14.834 /15.266 | 15.594 | — |
| forward | 1920 | new | 19.986 /20.359 | 20.547 | — |
| forward | 1280 | old | 14.415 /15.877 | 16.450 | 0 /0.000103482 |
| forward | 1600 | old | 23.117 /24.514 | 25.069 | — |
| forward | 1920 | old | 29.937 /31.959 | 32.461 | — |
| forward | 1280 | v7 | 6.283 /6.417 | 6.951 | 0 /0.000093139 |
| forward | 1600 | v7 | 9.215 /9.328 | 9.948 | — |
| forward | 1920 | v7 | 12.085 /12.311 | 12.811 | — |
| reverse | 1280 | new | 10.040 /10.249 | 10.542 | 0 /0.000101989 |
| reverse | 1600 | new | 14.767 /15.280 | 15.573 | — |
| reverse | 1920 | new | 20.058 /20.333 | 20.897 | — |
| reverse | 1280 | old | 15.741 /15.956 | 16.508 | 0 /0.000103482 |
| reverse | 1600 | old | 20.758 /24.527 | 25.110 | — |
| reverse | 1920 | old | 28.081 /32.005 | 32.503 | — |
| reverse | 1280 | v7 | 6.412 /6.477 | 7.000 | 0 /0.000093139 |
| reverse | 1600 | v7 | 9.207 /9.319 | 9.943 | — |
| reverse | 1920 | v7 | 12.083 /12.305 | 12.695 | — |

PSNR peak=1 in bench output RGB. Pairwise distance is not absolute model quality; original DLL requires newer hardware and is not run on sm86.

| Pair | PSNR dB | maxabs | Bit differences |
|---|---:|---:|---:|
| forward-1280-old-vs-new | 62.544361 | 0.004394531 | 1967250 |
| forward-1280-old-vs-v7 | 48.123143 | 0.013671875 | 2662468 |
| forward-1280-new-vs-v7 | 47.913975 | 0.014160156 | 2661211 |
| reverse-1280-old-vs-new | 62.544361 | 0.004394531 | 1967250 |
| reverse-1280-old-vs-v7 | 48.123143 | 0.013671875 | 2662468 |
| reverse-1280-new-vs-v7 | 47.913975 | 0.014160156 | 2661211 |
| repeat-1280-old | 999.000000 | 0.000000000 | 0 |
| repeat-1280-new | 999.000000 | 0.000000000 | 0 |
| repeat-1280-v7 | 999.000000 | 0.000000000 | 0 |
| forward-1600-old-vs-new | 61.663517 | 0.006835938 | 3561139 |
| forward-1600-old-vs-v7 | 39.164901 | 0.099487305 | 4247750 |
| forward-1600-new-vs-v7 | 39.253644 | 0.096496582 | 4245611 |
| reverse-1600-old-vs-new | 61.663517 | 0.006835938 | 3561139 |
| reverse-1600-old-vs-v7 | 39.164901 | 0.099487305 | 4247750 |
| reverse-1600-new-vs-v7 | 39.253644 | 0.096496582 | 4245611 |
| repeat-1600-old | 999.000000 | 0.000000000 | 0 |
| repeat-1600-new | 999.000000 | 0.000000000 | 0 |
| repeat-1600-v7 | 999.000000 | 0.000000000 | 0 |
| forward-1920-old-vs-new | 58.495481 | 0.008544922 | 5457988 |
| forward-1920-old-vs-v7 | 38.884089 | 0.110107422 | 6118200 |
| forward-1920-new-vs-v7 | 38.541064 | 0.114990234 | 6125436 |
| reverse-1920-old-vs-new | 58.495481 | 0.008544922 | 5457988 |
| reverse-1920-old-vs-v7 | 38.884089 | 0.110107422 | 6118200 |
| reverse-1920-new-vs-v7 | 38.541064 | 0.114990234 | 6125436 |
| repeat-1920-old | 999.000000 | 0.000000000 | 0 |
| repeat-1920-new | 999.000000 | 0.000000000 | 0 |
| repeat-1920-v7 | 999.000000 | 0.000000000 | 0 |
