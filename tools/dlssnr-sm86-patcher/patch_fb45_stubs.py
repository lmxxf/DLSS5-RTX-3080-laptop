#!/usr/bin/env python3
import ctypes
import hashlib
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, "/tmp/dlssnr-310-9-16-sm86")
import build_sm86_dlls as b
import dlssnr_patcher as dp

libzstd = ctypes.CDLL("libzstd.so.1")
libzstd.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
libzstd.ZSTD_decompress.restype = ctypes.c_size_t
libzstd.ZSTD_compress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
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

libcuda = ctypes.CDLL("/usr/lib/wsl/lib/libcuda.so.1")
assert libcuda.cuInit(0) == 0
dev = ctypes.c_int()
assert libcuda.cuDeviceGet(ctypes.byref(dev), 0) == 0
ctx = ctypes.c_void_p()
assert libcuda.cuCtxCreate_v2(ctypes.byref(ctx), 0, dev.value) == 0

def make_stub_ptx(orig_ptx: str) -> str:
    # Extract all .visible .entry name ( .param ... ) headers and emit stub { ret; } bodies
    lines = [".version 8.0", ".target sm_86", ".address_size 64", ""]
    for m in re.finditer(r"(\.visible\s+\.entry\s+[A-Za-z0-9_$]+\s*\([^)]*\))", orig_ptx, re.DOTALL):
        lines.append(m.group(1) + "\n{\n    ret;\n}\n")
    return "\n".join(lines)

def compile_cubin(ptx_str: str) -> bytes:
    ptx_bytes = ptx_str.encode("utf-8")
    err_log = ctypes.create_string_buffer(16384)
    opts = (ctypes.c_int * 4)(5, 6, 7, 9)
    vals = (ctypes.c_void_p * 4)(
        ctypes.cast(err_log, ctypes.c_void_p),
        ctypes.c_void_p(16384),
        ctypes.c_void_p(4),
        ctypes.c_void_p(86),
    )
    state = ctypes.c_void_p()
    assert libcuda.cuLinkCreate_v2(4, opts, vals, ctypes.byref(state)) == 0
    res = libcuda.cuLinkAddData_v2(state, 1, ptx_bytes, len(ptx_bytes), b"stub.ptx", 0, None, None)
    if res != 0:
        raise RuntimeError(err_log.value.decode("utf-8", "replace"))
    cubin_ptr = ctypes.c_void_p()
    cubin_sz = ctypes.c_size_t()
    assert libcuda.cuLinkComplete(state, ctypes.byref(cubin_ptr), ctypes.byref(cubin_sz)) == 0
    cubin = ctypes.string_at(cubin_ptr.value, cubin_sz.value)
    libcuda.cuLinkDestroy(state)
    return cubin

orig_dll = Path("/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll").read_bytes()
orig_data = bytearray(orig_dll)
dp.strip_authenticode(orig_data)
locs = dp.find_fatbins(orig_data)

stub_fatbins = {}
for idx in (4, 5):
    loc = locs[idx]
    blob = bytes(orig_data[loc.offset : loc.offset + loc.size])
    recs = dp.parse_fatbin_records(blob)
    ptx_rec = [r for r in recs if r.kind == 1][0]
    hdr = blob[ptx_rec.offset : ptx_rec.offset + ptx_rec.header_size]
    kind, ver, hdr_sz, pad_sz, comp_sz, min_sz, code_ver, arch, fn_off, fn_len, flags, zero, uncomp_sz = struct.unpack_from("<HHIQIIIIIIQQQ", hdr[:64])
    payload = blob[ptx_rec.offset + hdr_sz : ptx_rec.offset + hdr_sz + (comp_sz if comp_sz else pad_sz)]
    txt = zstd_decompress(payload, uncomp_sz).decode("utf-8").rstrip("\x00")
    stub_ptx = make_stub_ptx(txt)
    cubin = compile_cubin(stub_ptx)
    new_fb = b.pack_single_elf_fatbin(blob, cubin, zstd_compress)
    mod = ctypes.c_void_p()
    assert libcuda.cuModuleLoadData(ctypes.byref(mod), new_fb) == 0
    for m in re.finditer(r"\.visible\s+\.entry\s+([A-Za-z0-9_$]+)", txt):
        fn = ctypes.c_void_p()
        assert libcuda.cuModuleGetFunction(ctypes.byref(fn), mod, m.group(1).encode("utf-8")) == 0
    libcuda.cuModuleUnload(mod)
    stub_fatbins[idx] = new_fb
    print(f"Prepared Fatbin {idx} ELF stub: {len(new_fb)} bytes")

for p_str in sys.argv[1:]:
    p = Path(p_str)
    if not p.is_file():
        continue
    d = bytearray(p.read_bytes())
    for idx, new_fb in stub_fatbins.items():
        loc = locs[idx]
        d[loc.offset : loc.offset + loc.size] = new_fb + b"\x00" * (loc.size - len(new_fb))
    chk = dp.update_pe_checksum(d)
    p.write_bytes(d)
    print(f"Updated {p}: checksum=0x{chk:08x}, sha256={hashlib.sha256(d).hexdigest()}")
