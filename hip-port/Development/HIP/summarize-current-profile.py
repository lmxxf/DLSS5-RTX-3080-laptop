#!/usr/bin/env python3
"""Summarize interleaved family measurements; these are marginal costs, not additive layer times."""
import argparse
import csv
import statistics
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('directory', nargs='?', type=Path,
                    default=Path(__file__).resolve().parent.parent / 'results/1080-20260919')
args = parser.parse_args()
root = args.directory

def read(name):
    with (root / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

labels = {
    'c32': 'C32 全族', 'vit': 'ViT 全族', 'post': '末端融合块（post/head）',
    'c64': 'C64 FFN/投影/QKV', 'c128': 'C128 FFN/投影/QKV',
    'c256': 'C256 FFN/投影/QKV（连续权重片段）', 'attn64': 'C64 注意力/投影',
    'attn128': 'C128 注意力/投影', 'attn256': 'C256 注意力/投影',
    'split': 'C512 FFN/mix/投影', 'qkv512': 'C512 QKV',
    'attn512': 'C512 注意力/投影', 'decoder': '上采样解码核', 'pool': '独立下采样核',
    'c32prefix': '入口融合（全分辨率，1次）', 'c32chain': 'C32 普通链块（半分辨率，4次）',
    'c32mapped': 'C32 映射入口块（半分辨率，2次）', 'c32finish': 'C32 链尾融合（半分辨率，2次）',
    'vitqkv': 'ViT QKV', 'vitattn': 'ViT 注意力', 'vitexpand': 'ViT FFN 展开',
    'vitcontract': 'ViT FFN 收缩', 'vitproj': 'ViT 投影',
    'vitpack': 'ViT 输入打包', 'vitgather': 'ViT gather',
}
lines = ['# HIP 最新基线耗时定位（2026-09-19）', '',
         '本机RX 9070 XT；基线：`c256-frag-production-modules` + `benchmark_c256frag_production.exe`，对应已实玩通过的 C256 权重片段优化。', '',
         '固定 1296×720 RGBA16F 捕获，强制 900/1080 网络档；seed=0、temporal=0、Graph关闭。每组160帧，舍去32帧预热，取余下128帧中位数。每个家族多执行一遍，前后各跑正常基线；差值=重复组中位数−前后基线均值。末帧hash按档位核对，首尾检查有限值。', '',
         '**表内是重复执行的边际耗时，含缓存和提交影响，不是精确层时间分解，不能直接相加或当作可节省的时间。** 单轮P10/P90记录在runs.csv中，表示帧耗时分布，不是置信区间。', '',
         '## 大类', '']

def table(rows):
    indexed = {(r['height'], r['family']): r for r in rows}
    families = sorted({r['family'] for r in rows},
                      key=lambda f: -float(indexed[('1080', f)]['marginal_ms']))
    out = ['| 部分 | 900档增加 ms | 1080档增加 ms |', '|---|---:|---:|']
    for family in families:
        out.append(f"| {labels.get(family, family)} | " + ' | '.join(
            f"{float(indexed[(h, family)]['marginal_ms']):.3f}" for h in ['900', '1080']) + ' |')
    return out

coarse = read('current-map-margins.csv')
detail = read('current-detail-margins.csv')
lines += table(coarse)
lines += ['', '基线稳定性：', '', '| 轮次/档位 | 正常帧中位数的中位数 ms | 正常组范围 ms | 最大相邻基线漂移 ms |', '|---|---:|---:|---:|']
for tag, margins in [('current-map', coarse), ('current-detail', detail)]:
    runs = read(tag + '-runs.csv')
    for height in ['900', '1080']:
        values = [float(r['median_ms']) for r in runs if r['height'] == height and r['family'] == 'none']
        drift = max(float(r['baseline_drift_ms']) for r in margins if r['height'] == height)
        lines.append(f'| {tag}/{height} | {statistics.median(values):.3f} | {min(values):.3f}–{max(values):.3f} | {drift:.3f} |')
lines += ['', '## C32 与 ViT 细分', ''] + table(detail)
lines += ['', '## 入口噪声诊断', '']
noise_file = root / 'prefix-noise-margins.csv'
if noise_file.exists():
    noise = read(noise_file.name)
    indexed = {(r['height'], r['variant']): r for r in noise}
    assert len(indexed) == 4, 'Noise diagnostic incomplete'
    lines += ['临时将三项噪声特征置零，诊断图像会改变；分别在原版和消融版中测入口重复执行的边际成本，再比较二者。该模块不用于部署。差值也包含编译布局/数据改变的影响，只用于判断是否值得进一步实现保持输出的缓存。', '',
              '| 档位 | 原入口 ms | 零噪声入口 ms | 边际成本减少 ms |', '|---|---:|---:|---:|']
    for h in ['900', '1080']:
        a = float(indexed[(h, 'base')]['prefix_marginal_ms'])
        b = float(indexed[(h, 'zero-noise')]['prefix_marginal_ms'])
        lines.append(f'| {h} | {a:.3f} | {b:.3f} | {a-b:.3f} |')
else:
    lines += ['尚未完成。']
lines += ['', '## 判断与下一步', '',
          'C32入口块在完整W×H上计算，普通链块在W/2×H/2上计算；入口的单次工作量本来更大。末端post/head也是全分辨率。下一步优先看这些高分辨率C32计算的共同主干，以及ViT注意力内部的评分、归一化和加权汇总。', '',
          '噪声消融只得到约0.02/0.03ms的变化，接近相邻基线漂移；当前证据不支持优先增加噪声缓存。ViT的pack/gather也属小项，暂不把它们当主攻方向。', '',
          '相近的小项不据单轮差值作精细排名；后续代码候选仍需同批正反对照和完整正确性验证。', '',
          '## 复现与范围', '',
          '- `profile-current-families.ps1`：默认14类×两档；细分通过Families指定，Tag=current-detail。',
          '- `measure-prefix-noise.ps1`：只用于诊断的入口消融，要求独立编译并隔离存放的噪声置零模块。',
          '- 原始完整帧数据位于9070的 `D:\\DLSSNR-Lab\\hip-backend\\profile1080`，本目录存分组汇总和边际差值。',
          '- 本轮为定位测量，生产DLL、内核、游戏安装与已发布包均未修改。', '']
out = root / 'current-profile.md'
out.write_text('\n'.join(lines), encoding='utf-8')
print(out)
