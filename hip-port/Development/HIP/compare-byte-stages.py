"""Compare raw float stage dumps against float or E4M3 byte stage dumps."""
import json
import re
import sys
from pathlib import Path
import numpy as np

base, candidate = map(Path, sys.argv[1:3])
rows = []
for path in sorted(base.glob('block*.bin'), key=lambda p: (int(re.match(r'block(\d+)', p.stem)[1]), {'input': 0, 'ffn': 1, 'norm': 2}.get(p.stem.split('-')[-1], 3))):
    other = candidate / path.name
    block = int(re.match(r'block(\d+)', path.stem)[1])
    if path.stem.endswith(('-ffn', '-norm')):
        a, b = np.fromfile(path, dtype=np.uint8), np.fromfile(other, dtype=np.uint8)
        if a.size != b.size:
            raise ValueError('This diagnostic expects byte features in both runs')
        mask = a != b
        rows.append(dict(stage=path.stem, block=block, unit='byte', elements=int(a.size), bitdiff=int(np.count_nonzero(mask)), first_indices=np.flatnonzero(mask)[:8].tolist()))
        continue
    a = np.fromfile(path, dtype='<f4')
    if other.stat().st_size == a.size:
        raw = np.fromfile(other, dtype=np.uint8)
        exponent, mantissa = (raw >> 3) & 15, raw & 7
        b = np.where(exponent == 0, mantissa.astype(np.float32) / 512,
                     np.ldexp(1 + mantissa.astype(np.float32) / 8, exponent.astype(np.int32) - 7)).astype(np.float32)
        b = np.where(raw & 128, -b, b)
        b[(raw & 127) == 127] = np.nan
    elif other.stat().st_size == a.nbytes:
        b = np.fromfile(other, dtype='<f4')
    else:
        raise ValueError(f'Unexpected sizes: {path.name}')
    different = a.view(np.uint32) != b.view(np.uint32)
    rows.append(dict(stage=path.stem, block=block, unit='float', elements=int(a.size),
                     bitdiff=int(np.count_nonzero(different)),
                     numericdiff=int(np.count_nonzero(a != b)),
                     invalid=int(np.count_nonzero(~np.isfinite(a) | ~np.isfinite(b))),
                     maxabs=float(np.max(np.abs(a - b))),
                     first_indices=np.flatnonzero(different)[:8].tolist()))
print(json.dumps(rows, indent=2))
