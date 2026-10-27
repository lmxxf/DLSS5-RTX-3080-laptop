#!/usr/bin/env python3
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import ctypes
import os
import hashlib
from pathlib import Path
import re
import shutil
import struct
import sys
import time
import numpy as np

PATCHER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PATCHER_DIR))
import dlssnr_patcher as dp

src_code = (PATCHER_DIR / "dlssnr_patcher.py").read_text()
# Also patch fence.acquire.gpu -> fence.acq_rel.gpu in transform_ptx for 310.9.16.0 compatibility!
src_code = src_code.replace(
    'output = output.replace("fence.release.gpu;", "fence.acq_rel.gpu;")',
    'output = output.replace("fence.release.gpu;", "fence.acq_rel.gpu;")\n   '
    ' output = output.replace("fence.acquire.gpu;", "fence.acq_rel.gpu;")',
)
exec(compile(src_code, "dlssnr_patcher_fast.py", "exec"), dp.__dict__)

REG_TOKEN_RE = re.compile(r"%r[sd]?\d+")


def fast_lower_fp8_mma_entry(text: str) -> tuple[str, int]:
  matches = list(dp.FP8_MMA_PATTERN.finditer(text))
  if not matches:
    return text, 0
  runs = [[matches[0]]]
  for match in matches[1:]:
    if text[runs[-1][-1].end() : match.start()].strip():
      runs.append([match])
    else:
      runs[-1].append(match)
  packed_sources = dp.fp8_pack_sources(text)
  out = []
  last = 0
  for run in runs:
    out.append(text[last : run[0].start()])
    out.append(dp.render_fp8_mma_run(run, packed_sources))
    last = run[-1].end()
  out.append(text[last:])
  text = "".join(out)

  counts = Counter(REG_TOKEN_RE.findall(text))
  text = dp.FP8_PACK_PATTERN.sub(
      lambda m: "" if counts[m.group("destination")] == 1 else m.group(0),
      text,
  )
  counts = Counter(REG_TOKEN_RE.findall(text))
  text = dp.FP8_DOWN_PATTERN.sub(
      lambda m: "" if counts[m.group("destination")] == 1 else m.group(0),
      text,
  )
  return text, len(matches)


dp.lower_fp8_mma_entry = fast_lower_fp8_mma_entry

stock_fp8_decl = dp.fp8_conversion_declarations
stock_fp8_to_half = dp.fp8_pair_to_half_lines
stock_half_decl = dp.half_conversion_declarations
stock_half_to_fp8 = dp.half_pair_to_fp8_lines
stock_render_mma = dp.render_fp8_mma_run
stock_mapped_sources = dp.mapped_fp16_sources
stock_pack_sources = dp.fp8_pack_sources
stock_lower_conversions = dp.lower_fp8_conversions


def fast_fp8_conversion_declarations() -> list[str]:
  return [
      ".reg .b32 dlssnr_fp8_abs, dlssnr_fp8_sign, dlssnr_fp8_scale;",
  ]


def fast_fp8_pair_to_half_lines(source: str, destination: str) -> list[str]:
  return [
      f"prmt.b32 {destination}, {source}, 0, 0x1404;",
      f"and.b32 dlssnr_fp8_sign, {destination}, 0x80008000;",
      f"and.b32 dlssnr_fp8_abs, {destination}, 0x7f007f00;",
      "shr.u32 dlssnr_fp8_abs, dlssnr_fp8_abs, 1;",
      f"or.b32 {destination}, dlssnr_fp8_sign, dlssnr_fp8_abs;",
      "mov.b32 dlssnr_fp8_scale, 0x5c005c00;",
      f"mul.rn.f16x2 {destination}, {destination}, dlssnr_fp8_scale;",
  ]


def legacy_render_fp8_mma_run(
    matches,
    packed_sources: dict[str, tuple[str, str, int]],
) -> str:
  operands: list[str] = []
  for match in matches:
    for name in ("a0", "a1", "a2", "a3", "b0", "b1"):
      register = match.group(name)
      if register not in operands:
        operands.append(register)
  names = {
      register: (f"dlssnr_fp16_{index}_0", f"dlssnr_fp16_{index}_1")
      for index, register in enumerate(operands)
  }
  from ptx_mapped import mapped_at
  mapped = mapped_at(packed_sources, matches[0].start())
  quant_lines, quant_names = dp.mapped_fp16_sources(mapped, operands)
  has_encoded_operands = any(register not in mapped for register in operands)

  lines = ["{"]
  lines.extend([
      ".reg .u32 dlssnr_lane, dlssnr_group, dlssnr_pair;",
      ".reg .u32 dlssnr_source0, dlssnr_source1, dlssnr_parity;",
      ".reg .b32 dlssnr_shuffle0, dlssnr_shuffle1, dlssnr_prmt_sel;",
      ".reg .pred dlssnr_high;",
      ".reg .b32 "
      + ", ".join(name for pair in names.values() for name in pair)
      + ";",
  ])
  if has_encoded_operands:
    lines.extend(fast_fp8_conversion_declarations())
  lines.extend([
      "mov.u32 dlssnr_lane, %laneid;",
      "and.b32 dlssnr_group, dlssnr_lane, 0x1c;",
      "shr.u32 dlssnr_pair, dlssnr_lane, 1;",
      "and.b32 dlssnr_pair, dlssnr_pair, 1;",
      "add.u32 dlssnr_source0, dlssnr_group, dlssnr_pair;",
      "add.u32 dlssnr_source1, dlssnr_source0, 2;",
      "and.b32 dlssnr_parity, dlssnr_lane, 1;",
      "setp.ne.u32 dlssnr_high, dlssnr_parity, 0;",
  ])
  if has_encoded_operands:
    lines.extend([
        "selp.b32 dlssnr_prmt_sel, 0x3424, 0x1404, dlssnr_high;",
        "mov.b32 dlssnr_fp8_scale, 0x5c005c00;",
    ])

  lines.extend(quant_lines)
  for register in operands:
    first, second = names[register]
    if register in mapped:
      low, high, _position = mapped[register]
      low, high = quant_names[low], quant_names[high]
      for source_index, destination in (
          ("dlssnr_source0", first),
          ("dlssnr_source1", second),
      ):
        lines.extend([
            f"shfl.sync.idx.b32 dlssnr_shuffle0, {low}, {source_index}, 0x1f,"
            " 0xffffffff;",
            f"shfl.sync.idx.b32 dlssnr_shuffle1, {high}, {source_index}, 0x1f,"
            " 0xffffffff;",
            f"selp.b32 {destination}, dlssnr_shuffle1, dlssnr_shuffle0,"
            " dlssnr_high;",
        ])
    else:
      for source_index, destination in (
          ("dlssnr_source0", first),
          ("dlssnr_source1", second),
      ):
        lines.extend([
            f"shfl.sync.idx.b32 {destination}, {register}, {source_index},"
            " 0x1f, 0xffffffff;",
            f"prmt.b32 {destination}, {destination}, 0, dlssnr_prmt_sel;",
            f"and.b32 dlssnr_fp8_sign, {destination}, 0x80008000;",
            f"and.b32 dlssnr_fp8_abs, {destination}, 0x7f007f00;",
            "shr.u32 dlssnr_fp8_abs, dlssnr_fp8_abs, 1;",
            f"or.b32 {destination}, dlssnr_fp8_sign, dlssnr_fp8_abs;",
            f"mul.rn.f16x2 {destination}, {destination}, dlssnr_fp8_scale;",
        ])

  for match in matches:
    d0, d1 = match.group("d0"), match.group("d1")
    c0, c1 = match.group("c0"), match.group("c1")
    a0, a1 = names[match.group("a0")]
    a2, a3 = names[match.group("a1")]
    a4, a5 = names[match.group("a2")]
    a6, a7 = names[match.group("a3")]
    b0, b1 = names[match.group("b0")]
    b2, b3 = names[match.group("b1")]
    lines.extend([
        "mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16 "
        f"{{{d0}, {d1}}}, {{{a0}, {a2}, {a1}, {a3}}}, "
        f"{{{b0}, {b1}}}, {{{c0}, {c1}}};",
        "mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16 "
        f"{{{d0}, {d1}}}, {{{a4}, {a6}, {a5}, {a7}}}, "
        f"{{{b2}, {b3}}}, {{{d0}, {d1}}};",
    ])
  lines.append("}")
  return "\n".join(lines)


def even_odd_decode_lines(register, first, second):
  """Decode lane-local bytes 0/2 and 1/3, with no lane exchange or PRMT."""
  return [
      f"and.b32 dlssnr_fp8_abs, {register}, 0x007f007f;",
      f"and.b32 dlssnr_fp8_sign, {register}, 0x00800080;",
      f"mad.lo.u32 {first}, dlssnr_fp8_sign, 2, dlssnr_fp8_abs;",
      f"shl.b32 {first}, {first}, 7;",
      f"mul.rn.f16x2 {first}, {first}, dlssnr_fp8_scale;",
      f"and.b32 dlssnr_fp8_abs, {register}, 0x7f007f00;",
      f"and.b32 dlssnr_fp8_sign, {register}, 0x80008000;",
      "shr.u32 dlssnr_fp8_abs, dlssnr_fp8_abs, 1;",
      f"or.b32 {second}, dlssnr_fp8_abs, dlssnr_fp8_sign;",
      f"mul.rn.f16x2 {second}, {second}, dlssnr_fp8_scale;",
  ]


stock_even_odd_decode_lines = even_odd_decode_lines

def fast_render_fp8_mma_run(matches, packed_sources):
  """Use the same K permutation for A/B; FP16 rounding order differs from legacy."""
  operands=list(dict.fromkeys(m.group(n) for m in matches for n in ("a0","a1","a2","a3","b0","b1")))
  names={r:(f"dlssnr_fp16_{i}_0",f"dlssnr_fp16_{i}_1") for i,r in enumerate(operands)}
  from ptx_mapped import mapped_at
  mapped=mapped_at(packed_sources,matches[0].start())
  quant_lines,quant_names=dp.mapped_fp16_sources(mapped,operands)
  encoded=any(r not in mapped for r in operands)
  lines=["{", ".reg .b32 "+", ".join(n for pair in names.values() for n in pair)+";"]
  if encoded:lines+=fast_fp8_conversion_declarations()+["mov.b32 dlssnr_fp8_scale, 0x5c005c00;"]
  lines+=quant_lines
  for r in operands:
    first,second=names[r]
    if r in mapped:
      low,high,_=mapped[r];low,high=quant_names[low],quant_names[high]
      lines += [f"prmt.b32 {first}, {low}, {high}, 0x5410;",f"prmt.b32 {second}, {low}, {high}, 0x7632;"]
    else:lines+=even_odd_decode_lines(r,first,second)
  for m in matches:
    d0,d1=m.group("d0"),m.group("d1");c0,c1=m.group("c0"),m.group("c1")
    for parity in [0,1]:
      aa=[names[m.group(n)][parity] for n in ("a0","a1","a2","a3")]
      bb=[names[m.group(n)][parity] for n in ("b0","b1")]
      cc=[c0,c1] if parity==0 else [d0,d1]
      lines.append(f"mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16 {{{d0}, {d1}}}, {{{', '.join(aa)}}}, {{{', '.join(bb)}}}, {{{', '.join(cc)}}};")
  return "\n".join(lines+["}"])


def fast_half_conversion_declarations() -> list[str]:
  return [
      ".reg .b32 dlssnr_f16_abs, dlssnr_f16_sign, dlssnr_f16_lsb;",
      ".reg .b32 dlssnr_f16_sub2, dlssnr_f16_norm2, dlssnr_f16_magic;",
      ".reg .b32 dlssnr_f16_lo, dlssnr_f16_hi;",
      ".reg .pred dlssnr_f16_denorm_lo, dlssnr_f16_denorm_hi;",
  ]


def fast_half_pair_to_fp8_lines(source: str, destination: str) -> list[str]:
  # 100% 0-mismatch bit-exact SWAR implementation using hardware add.rn.f16x2 0x40004000 for subnormals
  # and borrow-free bfe.u32 for normals!
  return [
      f"and.b32 dlssnr_f16_sign, {source}, 0x80008000;",
      "shr.u32 dlssnr_f16_sign, dlssnr_f16_sign, 8;",
      f"and.b32 dlssnr_f16_abs, {source}, 0x7fff7fff;",
      "and.b32 dlssnr_f16_sub2, dlssnr_f16_abs, 0x3fff3fff;",
      "mov.b32 dlssnr_f16_magic, 0x40004000;",
      "add.rn.f16x2 dlssnr_f16_sub2, dlssnr_f16_sub2, dlssnr_f16_magic;",
      "shr.u32 dlssnr_f16_lsb, dlssnr_f16_abs, 7;",
      "and.b32 dlssnr_f16_lsb, dlssnr_f16_lsb, 0x00010001;",
      "add.u32 dlssnr_f16_lsb, dlssnr_f16_lsb, 0x003f003f;",
      "add.u32 dlssnr_f16_norm2, dlssnr_f16_abs, dlssnr_f16_lsb;",
      "and.b32 dlssnr_f16_lo, dlssnr_f16_abs, 0xffff;",
      "shr.u32 dlssnr_f16_hi, dlssnr_f16_abs, 16;",
      "setp.lt.u32 dlssnr_f16_denorm_lo, dlssnr_f16_lo, 0x2400;",
      "setp.lt.u32 dlssnr_f16_denorm_hi, dlssnr_f16_hi, 0x2400;",
      "bfe.u32 dlssnr_f16_lo, dlssnr_f16_norm2, 7, 9;",
      "sub.u32 dlssnr_f16_lo, dlssnr_f16_lo, 0x40;",
      "min.u32 dlssnr_f16_lo, dlssnr_f16_lo, 0x7e;",
      "bfe.u32 dlssnr_f16_hi, dlssnr_f16_norm2, 23, 9;",
      "sub.u32 dlssnr_f16_hi, dlssnr_f16_hi, 0x40;",
      "min.u32 dlssnr_f16_hi, dlssnr_f16_hi, 0x7e;",
      (
          "selp.b32 dlssnr_f16_lo, dlssnr_f16_sub2, dlssnr_f16_lo,"
          " dlssnr_f16_denorm_lo;"
      ),
      "and.b32 dlssnr_f16_lo, dlssnr_f16_lo, 0xff;",
      "shr.u32 dlssnr_f16_sub2, dlssnr_f16_sub2, 16;",
      (
          "selp.b32 dlssnr_f16_hi, dlssnr_f16_sub2, dlssnr_f16_hi,"
          " dlssnr_f16_denorm_hi;"
      ),
      "and.b32 dlssnr_f16_hi, dlssnr_f16_hi, 0xff;",
      "prmt.b32 dlssnr_f16_lo, dlssnr_f16_lo, dlssnr_f16_hi, 0x4440;",
      "or.b32 dlssnr_f16_lo, dlssnr_f16_lo, dlssnr_f16_sign;",
      "prmt.b32 dlssnr_f16_lo, dlssnr_f16_lo, 0, 0x4420;",
      f"cvt.u16.u32 {destination}, dlssnr_f16_lo;",
  ]


def forward_mapped_fp16_sources(mapped, operands):
  # Preserve upstream FP16 forwarding; only eligibility filtering changes.
  return [], {s:s for r in operands if r in mapped for s in mapped[r][:2]}


def fast_mapped_fp16_sources(mapped, operands):
  sources = sorted({s for r in operands if r in mapped for s in mapped[r][:2]})
  if not sources:
    return [], {}
  names = {s: f"qm_q{i}" for i, s in enumerate(sources)}
  lines = [
      ".reg .b32 qm_min, qm_max, qm_two, qm_threshold, qm_lsb, qm_abs, qm_sub, qm_mask, qm_sign;",
      ".reg .b32 " + ", ".join(names.values()) + ";",
      "mov.b32 qm_min, 0xdf00df00;", "mov.b32 qm_max, 0x5f005f00;",
      "mov.b32 qm_two, 0x40004000;", "mov.b32 qm_threshold, 0x24002400;",
  ]
  for source, q in names.items():
    lines += [
        f"max.f16x2 {q}, {source}, qm_min;", f"min.f16x2 {q}, {q}, qm_max;",
        f"and.b32 qm_sign, {q}, 0x80008000;", f"and.b32 qm_abs, {q}, 0x7fff7fff;",
        "set.lt.u32.f16x2 qm_mask, qm_abs, qm_threshold;",
        "add.rn.f16x2 qm_sub, qm_abs, qm_two;", "sub.rn.f16x2 qm_sub, qm_sub, qm_two;",
        f"shr.u32 qm_lsb, {q}, 7;", "and.b32 qm_lsb, qm_lsb, 0x00010001;",
        "add.u32 qm_lsb, qm_lsb, 0x003f003f;", f"add.u32 {q}, {q}, qm_lsb;",
        f"and.b32 {q}, {q}, 0xff80ff80;", "or.b32 qm_sub, qm_sub, qm_sign;",
        f"lop3.b32 {q}, qm_mask, qm_sub, {q}, 0xca;",
    ]
  return lines, names


def pack_single_elf_fatbin(
    source_fatbin: bytes, cubin_bytes: bytes, zstd_compress_fn
) -> bytes:
  recs = dp.parse_fatbin_records(source_fatbin)
  elf_rec = [r for r in recs if r.kind == 2][0]
  orig_hdr = bytearray(
      source_fatbin[elf_rec.offset : elf_rec.offset + elf_rec.header_size]
  )

  comp = zstd_compress_fn(cubin_bytes, 22)
  comp_sz = len(comp)
  pad_sz = (comp_sz + 7) & ~7
  padded_payload = comp + b"\x00" * (pad_sz - comp_sz)

  flags = struct.unpack_from("<Q", orig_hdr, 0x28)[0] | 0x8000
  struct.pack_into("<Q", orig_hdr, 0x08, pad_sz)
  struct.pack_into("<I", orig_hdr, 0x10, comp_sz)
  struct.pack_into("<I", orig_hdr, 0x1C, 86)
  struct.pack_into("<Q", orig_hdr, 0x28, flags)
  struct.pack_into("<Q", orig_hdr, 0x38, len(cubin_bytes))

  body = bytes(orig_hdr) + padded_payload
  fat_hdr = struct.pack("<IHHQ", dp.FATBIN_MAGIC, 1, 16, len(body))
  return fat_hdr + body


def fast_update_pe_checksum(data: bytearray) -> int:
  pe_offset = dp.pe_header_offset(data)
  checksum_offset = pe_offset + 24 + 64
  struct.pack_into("<I", data, checksum_offset, 0)
  arr = np.frombuffer(data, dtype=np.uint32)
  s = int(arr.sum(dtype=np.uint64))
  while s >> 16:
    s = (s & 0xFFFF) + (s >> 16)
  chk = (s & 0xFFFF) + len(data)
  struct.pack_into("<I", data, checksum_offset, chk)
  return chk


def override_maxnreg(text: str, limit: int | None) -> tuple[str, int]:
  """Only change existing PTX caps; leave launch bounds and instruction order intact."""
  if limit is None:
    return text, 0
  if not 1 <= limit <= 255:
    raise ValueError("maxnreg must be in 1..255")
  return re.subn(r"(?m)^(\s*\.maxnreg\s+)\d+", lambda m: m[1]+str(limit), text)


def worker_compile_fatbin(args):
  i, blob, is_fast, *build_options = args
  allow_grow = bool(build_options and build_options[0])
  mapped_mode = build_options[1] if len(build_options)>1 else "multidef"
  quantize_mapped = bool(build_options[2]) if len(build_options)>2 else False
  mma_layout = build_options[3] if len(build_options)>3 else "evenodd"
  maxnreg = build_options[4] if len(build_options)>4 else None
  half_pack = build_options[5] if len(build_options)>5 else "legacy"
  bulk_completion = build_options[6] if len(build_options)>6 else "immediate"
  fp8_decode = build_options[7] if len(build_options)>7 else "legacy"
  v24_mask = build_options[8] if len(build_options)>8 else 0
  global even_odd_decode_lines
  even_odd_decode_lines = stock_even_odd_decode_lines
  if fp8_decode == "prmt8":
    from v23.decode import decode
    even_odd_decode_lines = decode
  elif fp8_decode == "lowhigh8":
    from v26.codegen import decode
    even_odd_decode_lines = decode
  elif fp8_decode == "hybrid8":
    from v25.decode import decode
    even_odd_decode_lines = decode
  t0 = time.time()
  libzstd = ctypes.CDLL("libzstd.so.1")
  libzstd.ZSTD_decompress.argtypes = [
      ctypes.c_void_p,
      ctypes.c_size_t,
      ctypes.c_void_p,
      ctypes.c_size_t,
  ]
  libzstd.ZSTD_decompress.restype = ctypes.c_size_t
  libzstd.ZSTD_compress.argtypes = [
      ctypes.c_void_p,
      ctypes.c_size_t,
      ctypes.c_void_p,
      ctypes.c_size_t,
      ctypes.c_int,
  ]
  libzstd.ZSTD_compress.restype = ctypes.c_size_t
  libzstd.ZSTD_compressBound.argtypes = [ctypes.c_size_t]
  libzstd.ZSTD_compressBound.restype = ctypes.c_size_t

  def zstd_decompress(src: bytes, uncomp_sz: int) -> bytes:
    dst = ctypes.create_string_buffer(uncomp_sz)
    ret = libzstd.ZSTD_decompress(dst, uncomp_sz, src, len(src))
    assert ret == uncomp_sz
    return dst.raw

  def zstd_compress(src: bytes, level: int = 22) -> bytes:
    bound = libzstd.ZSTD_compressBound(len(src))
    dst = ctypes.create_string_buffer(bound)
    ret = libzstd.ZSTD_compress(dst, bound, src, len(src), level)
    return dst.raw[:ret]

  if is_fast:
    dp.fp8_conversion_declarations = fast_fp8_conversion_declarations
    dp.fp8_pair_to_half_lines = fast_fp8_pair_to_half_lines
    dp.half_conversion_declarations = fast_half_conversion_declarations
    dp.half_pair_to_fp8_lines = fast_half_pair_to_fp8_lines
    dp.render_fp8_mma_run = legacy_render_fp8_mma_run if mma_layout=="legacy" else fast_render_fp8_mma_run
    from functools import partial
    dp.fp8_pack_sources = partial(stock_pack_sources, local_only=mapped_mode=="strict")
    dp.mapped_fp16_sources = fast_mapped_fp16_sources if quantize_mapped else forward_mapped_fp16_sources
  else:
    dp.fp8_conversion_declarations = stock_fp8_decl
    dp.fp8_pair_to_half_lines = stock_fp8_to_half
    dp.half_conversion_declarations = stock_half_decl
    dp.half_pair_to_fp8_lines = stock_half_to_fp8
    dp.render_fp8_mma_run = stock_render_mma
    dp.mapped_fp16_sources = stock_mapped_sources
    dp.fp8_pack_sources = stock_pack_sources

  if half_pack == "swar":
    from v22.codegen import declarations, pack
    dp.half_conversion_declarations = declarations
    dp.half_pair_to_fp8_lines = pack
  dp.lower_fp8_conversions = stock_lower_conversions
  if v24_mask:
    from v24.codegen import apply
    apply(sys.modules[__name__], v24_mask)
  if mma_layout == "lowhigh":
    if quantize_mapped:
      raise ValueError("Low/high direct mapped rendering requires quantize_mapped=False")
    from functools import partial
    from v26.codegen import render
    dp.render_fp8_mma_run = partial(render, builder=sys.modules[__name__])
  recs = dp.parse_fatbin_records(blob)
  ptx_rec = [r for r in recs if r.kind == 1][0]
  hdr = blob[ptx_rec.offset : ptx_rec.offset + ptx_rec.header_size]
  (
      kind,
      ver,
      hdr_sz,
      pad_sz,
      comp_sz,
      min_sz,
      code_ver,
      arch,
      fn_off,
      fn_len,
      flags,
      zero,
      uncomp_sz,
  ) = struct.unpack_from("<HHIQIIIIIIQQQ", hdr[:64])
  payload = blob[
      ptx_rec.offset
      + hdr_sz : ptx_rec.offset
      + hdr_sz
      + (comp_sz if comp_sz else pad_sz)
  ]
  raw_ptx = zstd_decompress(payload, uncomp_sz) if (flags & 0x8000) else payload
  txt = raw_ptx.decode("utf-8").rstrip("\x00")
  ptx_sm86, stats = dp.transform_ptx(txt, dp.AMPERE, bulk_completion=bulk_completion)
  ptx_sm86, cap_count = override_maxnreg(ptx_sm86, maxnreg)
  if maxnreg is not None:
    assert cap_count, f"Fatbin {i}: no existing .maxnreg to override"
    stats.add("maxnreg_override", cap_count)

  libcuda = ctypes.CDLL("/usr/lib/wsl/lib/libcuda.so.1")
  assert libcuda.cuInit(0) == 0
  dev = ctypes.c_int()
  assert libcuda.cuDeviceGet(ctypes.byref(dev), 0) == 0
  ctx = ctypes.c_void_p()
  assert libcuda.cuCtxCreate_v2(ctypes.byref(ctx), 0, dev.value) == 0

  def compile_cubin(opt_level: int) -> bytes:
    ptx_bytes = ptx_sm86.encode("utf-8")
    err_log = ctypes.create_string_buffer(16384)
    opts = (ctypes.c_int * 4)(5, 6, 7, 9)
    vals = (ctypes.c_void_p * 4)(
        ctypes.cast(err_log, ctypes.c_void_p),
        ctypes.c_void_p(16384),
        ctypes.c_void_p(opt_level),
        ctypes.c_void_p(86),
    )
    state = ctypes.c_void_p()
    assert libcuda.cuLinkCreate_v2(4, opts, vals, ctypes.byref(state)) == 0
    res = libcuda.cuLinkAddData_v2(
        state, 1, ptx_bytes, len(ptx_bytes), b"in.ptx", 0, None, None
    )
    if res != 0:
      raise RuntimeError(
          f"Fatbin {i} cuLinkAddData failed ({res}):"
          f" {err_log.value.decode('utf-8', 'replace')}"
      )
    cubin_ptr = ctypes.c_void_p()
    cubin_sz = ctypes.c_size_t()
    res = libcuda.cuLinkComplete(
        state, ctypes.byref(cubin_ptr), ctypes.byref(cubin_sz)
    )
    if res != 0:
      raise RuntimeError(
          f"Fatbin {i} cuLinkComplete failed ({res}):"
          f" {err_log.value.decode('utf-8', 'replace')}"
      )
    cubin = ctypes.string_at(cubin_ptr.value, cubin_sz.value)
    libcuda.cuLinkDestroy(state)
    return cubin

  if not is_fast and i <= 6:
    used_opt = 1
    cubin = compile_cubin(1)
    new_fb = pack_single_elf_fatbin(blob, cubin, zstd_compress)
  else:
    used_opt = 4
    cubin = compile_cubin(4)
    new_fb = pack_single_elf_fatbin(blob, cubin, zstd_compress)
    if is_fast:
      cache = Path(os.environ.get("DLSSNR_BUILD_CACHE", "/tmp/dlss-sky-audit/safe-o4")); cache.mkdir(parents=True, exist_ok=True)
      (cache / f"fatbin{i:02d}.cubin").write_bytes(cubin)
      (cache / f"fatbin{i:02d}.ptx").write_text(ptx_sm86)
      (cache / f"fatbin{i:02d}.bin").write_bytes(new_fb)
    if len(new_fb) > len(blob) and not allow_grow:
      used_opt = 1
      cubin = compile_cubin(1)
      new_fb = pack_single_elf_fatbin(blob, cubin, zstd_compress)

  assert (
      allow_grow or len(new_fb) <= len(blob)
  ), f"Fatbin {i} {len(new_fb)} > {len(blob)} even at O{used_opt}"
  mod = ctypes.c_void_p()
  assert libcuda.cuModuleLoadData(ctypes.byref(mod), new_fb) == 0
  libcuda.cuModuleUnload(mod)
  libcuda.cuCtxDestroy_v2(ctx)
  return (
      i,
      new_fb,
      (
          f"ELF O{used_opt} (cubin={len(cubin):7d} B -> fatbin={len(new_fb):6d}"
          f" / {len(blob):6d} B) in {time.time()-t0:.2f}s | {stats.summary()}"
      ),
  )


def main():
  import argparse
  from concurrent.futures import as_completed
  from pe_fatbins import assemble
  parser = argparse.ArgumentParser(description="Build all 15 sm_86 O4 fatbins with multi-definition-filtered mapped operands")
  parser.add_argument("--input", type=Path, default=Path("/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll"))
  parser.add_argument("--output", type=Path, default=None)
  parser.add_argument("--mma-layout", choices=("evenodd", "legacy", "lowhigh"), default="evenodd", help="Legacy layout is a diagnostic control")
  parser.add_argument("--maxnreg", action="append", default=[], metavar="FB:LIMIT", help="Diagnostic per-fatbin existing .maxnreg override; e.g. 3:255")
  parser.add_argument("--workers", type=int, default=3)
  parser.add_argument("--mapped-mode", choices=("strict", "multidef"), default="multidef")
  parser.add_argument("--quantize-mapped", action="store_true", help="Diagnostic: restore explicit E4M3 quantization on mapped sources")
  parser.add_argument("--half-pack", choices=("legacy", "swar"), default="legacy")
  parser.add_argument("--bulk-completion", choices=("immediate", "mbarrier"), default="immediate")
  parser.add_argument("--fp8-decode", choices=("legacy", "prmt8", "hybrid8", "lowhigh8"), default="legacy")
  parser.add_argument("--v24-mask", type=int, default=0, help="Isolated factors: A=1, bias=2, quad=4, JIT pool=8")
  args = parser.parse_args()
  assert 0 <= args.v24_mask <= 15
  if (args.mma_layout == "lowhigh") != (args.fp8_decode == "lowhigh8"):
    parser.error("lowhigh layout and lowhigh8 decoding must be selected together")
  if args.mma_layout == "lowhigh" and (args.v24_mask != 8 or args.quantize_mapped or args.half_pack != "swar"):
    parser.error("V2.6 requires mask8, SWAR and non-quantized mapped sources")
  if args.v24_mask and (args.half_pack != "swar" or args.fp8_decode not in ("prmt8", "hybrid8", "lowhigh8") or args.mma_layout not in ("evenodd", "lowhigh") or args.quantize_mapped):
    parser.error("V2.4 factors require SWAR, PRMT8, evenodd and non-quantized mapped sources")
  if (args.half_pack != "legacy" or args.bulk_completion != "immediate" or args.fp8_decode != "legacy" or args.v24_mask) and args.output is None:
    parser.error("Experimental factors require an explicit --output path")
  caps = {}
  for spec in args.maxnreg:
    fb, limit = map(int, spec.split(":"))
    assert 0 <= fb < 15 and 1 <= limit <= 255, spec
    assert fb not in caps, f"Duplicate maxnreg override for FB{fb}"
    caps[fb] = limit
  if args.output is None:
    args.output = Path("/mnt/c/DLSS5-5090-dll/" + ("nvngx_dlssnr_sm86_v21.dll" if caps else "nvngx_dlssnr_sm86_v2.dll"))
  t0 = time.time()
  data = bytearray(args.input.read_bytes())
  expected_sha256 = "2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f"
  assert hashlib.sha256(data).hexdigest() == expected_sha256, "Unsupported original DLL SHA-256; expected 310.9.16.0 source"
  dp.strip_authenticode(data)
  locs = dp.find_fatbins(data)
  assert len(locs) == 15, f"Expected 15 fatbins, found {len(locs)}"
  dp.apply_host_patches(data, (dp.AMPERE,))
  tasks = [(i, bytes(data[l.offset:l.offset+l.size]), True, True, args.mapped_mode, args.quantize_mapped, args.mma_layout, caps.get(i), args.half_pack, args.bulk_completion, args.fp8_decode, args.v24_mask) for i, l in enumerate(locs)]
  blobs = {}
  with ProcessPoolExecutor(max_workers=args.workers) as pool:
    futures = [pool.submit(worker_compile_fatbin, task) for task in tasks]
    for future in as_completed(futures):
      i, blob, message = future.result()
      assert "ELF O4" in message, message
      blobs[i] = blob
      print(f"[{i:02d}/14] {message}", flush=True)
  data, manifest = assemble(data, locs, blobs, dp)
  fast_update_pe_checksum(data)
  args.output.parent.mkdir(parents=True, exist_ok=True)
  temporary = args.output.with_suffix(args.output.suffix + ".tmp")
  temporary.write_bytes(data)
  temporary.replace(args.output)
  import json
  args.output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))
  print(f"Done: 15/15 O4, {time.time()-t0:.2f}s, SHA256={hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
  main()
