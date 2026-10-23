"""Audit the actual residual-scale packing, preserving f32 remainder updates."""
from pathlib import Path
import argparse
import json
import numpy as np

def pieces(scale, clamp_subnormal):
    remaining = np.float32(scale)
    result, clamps = [], []
    for part in range(3):
        magnitude = abs(float(remaining))
        if magnitude < 0.015625:
            q = int(np.rint(np.float32(magnitude) * np.float32(512)))
            if clamp_subnormal and q > 7:
                clamps.append(part)
                q = 7
            decoded = np.float32(q / 512)
        else:
            if magnitude >= 448:
                raise ValueError('NativePreblockRuntime rejects scales >=448')
            exponent = int(np.floor(np.log2(magnitude)))
            step = 2.0 ** (exponent - 3)
            q = int(np.rint(np.float32(magnitude) / np.float32(step)))
            decoded = np.float32(q * step)
        decoded = np.copysign(decoded, remaining)
        result.append(float(decoded))
        remaining = np.float32(remaining - decoded)
    return result, clamps

def main():
    p = argparse.ArgumentParser()
    p.add_argument('assets', type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    report = []
    for block in (2, 3, 4, 67, 68, 69):
        weights = np.fromfile(args.assets / f'block{block}-ffn.f32', '<f4')
        assert weights.size == 8736
        changed, clamp_events, sum_changes = [], 0, 0
        for channel, scale in enumerate(weights[8704:8736]):
            old, _ = pieces(scale, False)
            new, clamps = pieces(scale, True)
            clamp_events += len(clamps)
            if old != new:
                changed.append(dict(channel=channel, scale=float(scale), old=old,
                                    new=new, clamped_parts=clamps,
                                    old_sum=sum(old), new_sum=sum(new)))
                sum_changes += sum(old) != sum(new)
        item = dict(block=block, channels=32, changed_channels=len(changed),
                    clamp_events=clamp_events, changed_sum_channels=sum_changes,
                    details=changed)
        report.append(item)
        print(f'block={block} changed_channels={len(changed)} clamp_events={clamp_events} changed_sum_channels={sum_changes}')
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + '\n')

if __name__ == '__main__':
    main()
