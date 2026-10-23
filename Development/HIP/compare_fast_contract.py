#!/usr/bin/env python3
"""Test whether final half RTZ alone explains the production MH contract delta."""
import argparse
import bisect
import math
import struct
from pathlib import Path


def load(path):
    b = Path(path).read_bytes()
    if not b or len(b) % 4:
        raise ValueError(path)
    return list(struct.unpack('<'+'f'*(len(b)//4), b))


def half(x, rtz):
    if not math.isfinite(x):
        return x
    if not rtz:
        try:
            return struct.unpack('<e', struct.pack('<e', x))[0]
        except OverflowError:
            return math.copysign(math.inf, x)
    u = struct.unpack('<I', struct.pack('<f', x))[0]
    a = abs(x)
    if a >= 65504:
        return math.copysign(65504.0, x)
    if a < 2**-14:
        return math.copysign(math.floor(a*2**24)*2**-24, x)
    return struct.unpack('<f', struct.pack('<I', u & 0xffffe000))[0]


VALUES = [(i % 8)/512 if i < 8 else math.ldexp(1+(i % 8)/8, i//8-7)
          for i in range(127)]


def quant(x):
    if not math.isfinite(x):
        raise ValueError('nonfinite prequantization value; inspect separately')
    a = abs(x)
    j = bisect.bisect_left(VALUES, a)
    candidates = range(max(0, j-1), min(126, j)+1)
    q = min(candidates, key=lambda i: (abs(a-VALUES[i]), i % 2))
    return -VALUES[q] if x < 0 else VALUES[q]


def differences(a, b):
    if len(a) != len(b):
        raise ValueError('count mismatch')
    return sum(struct.pack('<f', x) != struct.pack('<f', y) for x, y in zip(a, b))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('prefix', help='same output prefix passed to multihead_fast_validate')
    args = p.parse_args()
    bad = 0
    for pattern in range(2):
        base = args.prefix+f'-p{pattern}'
        raw = load(base+'-hip-contract-pre.f32')
        prod = load(base+'-production-contract.f32')
        rne_file = base+'-hip-contract-rne.f32'
        gpu_rne = load(rne_file if Path(rne_file).exists() else base+'-hip-contract.f32')
        gpu_rtz = load(base+'-hip-contract-rtz.f32')
        cpu_rne = [quant(half(x, False)) for x in raw]
        cpu_rtz = [quant(half(x, True)) for x in raw]
        checks = {'CPU_RNE_vs_HIP_RNE': differences(cpu_rne, gpu_rne),
                  'CPU_RTZ_vs_HIP_RTZ': differences(cpu_rtz, gpu_rtz),
                  'CPU_RTZ_vs_production': differences(cpu_rtz, prod)}
        bad += sum(checks.values())
        print(f'pattern={pattern} values={len(raw)} '+
              ' '.join(f'{k}={v}' for k, v in checks.items())+
              f' original_RNE_vs_production={differences(gpu_rne, prod)}')
    print('Final-half-RTZ-only hypothesis '+('PASS' if not bad else 'NOT ESTABLISHED'))
    return int(bool(bad))


if __name__ == '__main__':
    raise SystemExit(main())
