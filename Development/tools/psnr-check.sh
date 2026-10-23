#!/bin/bash
# usage: psnr-check.sh <candidate> [golden-candidate=ffnh2]
# Fetches the three validate-psnr.ps1 outputs of <candidate> from amd9070 and prints PSNR / max abs error / exact-match
# fraction against the bit-exact golden outputs (<golden>-full.f16, <golden>-reset.f16, <golden>-history-check.f32).
set -e
c=$1; g=${2:-ffnh2}
d=$(dirname "$0")/../../release/HIP/psnr; mkdir -p "$d"
for f in "$c-p-full.f16" "$c-p-reset.f16" "$c-p-history.f32" "$g-full.f16" "$g-reset.f16" "$g-history-check.f32"; do
  [ -f "$d/$f" ] && [[ "$f" == $g-* ]] || scp -q "amd9070:D:/DLSSNR-Lab/hip-backend/$f" "$d/$f"
done
python3 - "$d" "$c" "$g" <<'EOF'
import sys,numpy as np
d,c,g=sys.argv[1:]
def load(p):return np.fromfile(p,dtype=np.float16 if p.endswith('.f16') else np.float32).astype(np.float64)
for a,b in [(f"{c}-p-full.f16",f"{g}-full.f16"),(f"{c}-p-reset.f16",f"{g}-reset.f16"),(f"{c}-p-history.f32",f"{g}-history-check.f32")]:
    x,y=load(f"{d}/{a}"),load(f"{d}/{b}")
    assert x.shape==y.shape,(a,x.shape,y.shape)
    m=np.isfinite(x)&np.isfinite(y);nonfinite=int((~np.isfinite(x)).sum())
    e=x[m]-y[m];mse=float((e*e).mean());peak=float(np.abs(y[m]).max())
    psnr=float('inf') if mse==0 else 20*np.log10(peak)-10*np.log10(mse)
    print(f"{a:32s} psnr={psnr:7.2f} dB  maxabs={np.abs(e).max():.3e}  exact={float((e==0).mean())*100:6.2f}%  nonfinite={nonfinite}  peak={peak:.3f}")
EOF
