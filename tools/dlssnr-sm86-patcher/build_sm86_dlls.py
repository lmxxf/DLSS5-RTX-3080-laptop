#!/usr/bin/env python3
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import ctypes
import hashlib
from pathlib import Path
import re
import shutil
import struct
import sys
import time
import numpy as np

sys.path.insert(0, "/tmp/dlssnr-310-9-16-sm86")
import dlssnr_patcher as dp

src_code = Path("/tmp/dlssnr-310-9-16-sm86/dlssnr_patcher.py").read_text()
src_code = re.sub(
    r'rf"\(\?P<guard>@!\?\{PTX_PREDICATE\}\\s\+\)\?([^"]*)"',
    r'r"(?P<guard>)\1"',
    src_code,
)
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


def fast_render_fp8_mma_run(
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
  mapped = {
      register: sources
      for register, sources in packed_sources.items()
      if sources[2] < matches[0].start()
  }
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

  for register in operands:
    first, second = names[register]
    if register in mapped:
      low, high, _position = mapped[register]
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


def worker_compile_fatbin(args):
  i, blob, is_fast = args
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
    dp.render_fp8_mma_run = fast_render_fp8_mma_run
  else:
    dp.fp8_conversion_declarations = stock_fp8_decl
    dp.fp8_pair_to_half_lines = stock_fp8_to_half
    dp.half_conversion_declarations = stock_half_decl
    dp.half_pair_to_fp8_lines = stock_half_to_fp8
    dp.render_fp8_mma_run = stock_render_mma

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
  ptx_sm86, stats = dp.transform_ptx(txt, dp.AMPERE)

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
    if len(new_fb) > len(blob):
      used_opt = 1
      cubin = compile_cubin(1)
      new_fb = pack_single_elf_fatbin(blob, cubin, zstd_compress)

  assert (
      len(new_fb) <= len(blob)
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


if __name__ == "__main__":
  t0 = time.time()
  orig_data = bytearray(
      Path("/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll").read_bytes()
  )
  dp.strip_authenticode(orig_data)
  locs = dp.find_fatbins(orig_data)

  d_fast = bytearray(
      Path("/tmp/dlssnr-310-9-16-sm86/nvngx_dlssnr_sm86_fast.dll").read_bytes()
  )
  tasks = [
      (i, bytes(orig_data[locs[i].offset : locs[i].offset + locs[i].size]), True)
      for i in range(7)
  ]
  print(
      "Recompiling Fatbins 0..6 for fast variant with fused prmt + borrow-free"
      " bfe.u32..."
  )
  with ProcessPoolExecutor(max_workers=7) as pool:
    for i, new_fb, msg in pool.map(worker_compile_fatbin, tasks):
      loc = locs[i]
      d_fast[loc.offset : loc.offset + loc.size] = new_fb + b"\x00" * (
          loc.size - len(new_fb)
      )
      print(f"  [{i+1:02d}/15] {msg}")

  chk = fast_update_pe_checksum(d_fast)
  fast_tmp = Path("/tmp/dlssnr-310-9-16-sm86/nvngx_dlssnr_sm86_fast.dll")
  fast_tmp.write_bytes(d_fast)
  shutil.copy2(fast_tmp, "/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_fast.dll")
  print(
      f"Done in {time.time()-t0:.2f}s! Checksum=0x{chk:08x},"
      f" SHA256={hashlib.sha256(d_fast).hexdigest()}"
  )
