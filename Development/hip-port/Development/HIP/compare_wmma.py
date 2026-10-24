#!/usr/bin/env python3
"""Compare saved HIP/HLSL hardware results, preserving FP32/FP16 bit identity."""
import argparse
import math
import struct
from pathlib import Path


def compare(label, a, b, width, required):
    if len(a) != len(b) or not a or len(a) % width:
        raise ValueError(f'{label}: invalid/different byte lengths {len(a)} {len(b)}')
    n = len(a) // width
    fmt = 'f' if width == 4 else 'e'
    av = struct.unpack('<' + fmt * n, a)
    bv = struct.unpack('<' + fmt * n, b)
    different = sum(a[i:i+width] != b[i:i+width] for i in range(0, len(a), width))
    zero_sign = sum(x == 0 and y == 0 and math.copysign(1, x) != math.copysign(1, y)
                    for x, y in zip(av, bv))
    finite_errors = [abs(x-y) for x, y in zip(av, bv) if math.isfinite(x) and math.isfinite(y)]
    class_diff = sum((math.isnan(x), math.isinf(x)) != (math.isnan(y), math.isinf(y))
                     for x, y in zip(av, bv))
    print(f'{label}: values={n} bitdiff={different} signed_zero_diff={zero_sign} '
          f'nonfinite_class_diff={class_diff} max_finite_abs_diff={max(finite_errors, default=0):.9g} '
          f'required_equal={int(required)}')
    return required and different != 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('release/HIP'))
    p.add_argument('--hip-prefix', default='wmma-validation-fp8')
    p.add_argument('--hlsl-prefix', default='hlsl-wmma')
    args = p.parse_args()
    read = lambda suffix: (args.root / suffix).read_bytes()
    hp, sp = args.hip_prefix, args.hlsl_prefix
    hd, hm, hh = read(hp+'-d.f32'), read(hp+'-partial.f32'), read(hp+'-d.f16')
    # HIP host did not save the K16 half result: round the recorded partial FP32
    # with Python's independent IEEE RNE half conversion for that comparison.
    vals = struct.unpack('<'+'f'*(len(hm)//4), hm)
    partial_half = bytearray()
    for x in vals:
        try:
            partial_half += struct.pack('<e', x)
        except OverflowError:
            partial_half += struct.pack('<e', math.copysign(math.inf, x))
    failed = False
    for tag, ref, h in [('k32', hd, hh), ('split', hd, hh), ('partial', hm, partial_half),
                        ('late-C', hd, hh)]:
        required = tag != 'late-C'
        failed |= compare('HIP/HLSL '+tag+' FP32', ref, read(sp+'-'+tag+'.f32'), 4, required)
        failed |= compare('HIP/HLSL '+tag+' FP16', h, read(sp+'-'+tag+'.f16'), 2, required)
    print('late-C is deliberately diagnostic: different C placement is not an equivalent kernel.')
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
