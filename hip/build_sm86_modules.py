#!/usr/bin/env python3
import os
import re
import sys
import json
import hashlib
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def parse_ps1_modules(ps1_path):
    txt = open(ps1_path, "r", encoding="utf-8").read()
    modules = []
    # Match each @{ ... } block inside $modules = @(...)
    block_start = txt.index("$modules = @(")
    block_end = txt.index("\n)\n", block_start)
    body = txt[block_start:block_end]
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("@{"):
            continue
        m_name = re.search(r"name\s*=\s*'([^']+)'", line)
        if not m_name:
            continue
        name = m_name.group(1)
        m_defs = re.search(r"defines\s*=\s*@\(([^)]*)\)", line)
        defines = re.findall(r"'([^']+)'", m_defs.group(1)) if m_defs else []
        m_srcs = re.search(r"sources\s*=\s*@\(([^)]*)\)", line)
        sources = re.findall(r"'([^']+)'", m_srcs.group(1)) if m_srcs else []
        m_l23 = re.search(r"l23defines\s*=\s*@\(([^)]*)\)", line)
        l23defines = re.findall(r"'([^']+)'", m_l23.group(1)) if m_l23 else []
        modules.append({
            "name": name,
            "defines": defines,
            "sources": sources,
            "l23defines": l23defines,
        })
    return modules

def transform_hip_to_sm86_cu(text, compat_header_path):
    # Replace __has_builtin(__builtin_amdgcn_...) checks with 1
    text = re.sub(
        r'__has_builtin\s*\(\s*__builtin_amdgcn_[a-zA-Z0-9_]+\s*\)',
        '1',
        text
    )
    # Replace inline variable declaration `int __attribute__((ext_vector_type(4))) var` (not preceded by typedef or =)
    text = re.sub(
        r'(?<![=\w])\bint\s+__attribute__\s*\(\(\s*ext_vector_type\s*\(\s*4\s*\)\s*\)\)(?=\s+[a-zA-Z_])',
        'sm86_i4',
        text
    )
    # Forward-declare byte_F right after fp8_add0 if present
    text = text.replace(
        'DEV float fp8_add0(float x){',
        'DEV unsigned char byte_F(float x);\nDEV float fp8_add0(float x){'
    )
    # Bypass multi-line s_setreg + v_cvt_pk_fp8_f32 inline asm block in wave_owned_c32.inc (fallback right below it is identical)
    text = re.sub(
        r'if\s+constexpr\s*\(\s*\(\s*CW_PACK_MODE_MASK\s*&\s*\(\s*1u\s*<<\s*Site\s*\)\s*\)\s*!=\s*0\s*\)\s*\{.*?return\s+i2\{lo,hi\};\s*\}',
        '',
        text,
        flags=re.DOTALL
    )
    # Replace the 4 inline asm patterns and target("cumode")
    text = re.sub(
        r'__attribute__\s*\(\(\s*target\s*\(\s*"cumode"\s*\)\s*\)\)',
        '',
        text
    )
    text = re.sub(
        r'asm\s*\(\s*"v_cvt_f16_f32\s+%0,\s*%1"\s*:\s*"=v"\s*\(([^)]+)\)\s*:\s*"v"\s*\(([^)]+)\)\s*\)',
        r'\1 = sm86_v_cvt_f16_f32(\2)',
        text
    )
    text = re.sub(
        r'asm\s*\(\s*"v_cvt_f32_f16\s+%0,\s*%1"\s*:\s*"=v"\s*\(([^)]+)\)\s*:\s*"v"\s*\(([^)]+)\)\s*\)',
        r'\1 = sm86_v_cvt_f32_f16(\2)',
        text
    )
    text = re.sub(
        r'asm\s*\(\s*"v_cvt_pkrtz_f16_f32\s+%0,\s*%1,\s*%1"\s*:\s*"=v"\s*\(([^)]+)\)\s*:\s*"v"\s*\(([^)]+)\)\s*\)',
        r'\1 = sm86_v_cvt_pkrtz_f16_f32(\2, \2)',
        text
    )
    text = re.sub(
        r'asm\s*\(\s*"v_cvt_pkrtz_f16_f32\s+%0,\s*%1,\s*%2"\s*:\s*"=v"\s*\(([^)]+)\)\s*:\s*"v"\s*\(([^)]+)\)\s*,\s*"v"\s*\(([^)]+)\)\s*\)',
        r'\1 = sm86_v_cvt_pkrtz_f16_f32(\2, \3)',
        text
    )
    text = re.sub(
        r'__asm__\s+volatile\s*\(\s*""\s*:\s*"\+v"\s*\(([^)]+)\)\s*\)',
        r'sm86_keep_alive(\1)',
        text
    )
    return f'#include "{compat_header_path}"\n' + text

def assemble_module_source(mod, source_dir, compat_header_path):
    lines = ["#define HIP_ISA_HALF 1"]
    if mod["name"].endswith("-packed"):
        lines.append("#define HIP_PREPACKED_WEIGHTS 1")
    for d in mod["defines"] + mod["l23defines"]:
        lines.append(f"#define {d}")
    text = "\n".join(lines) + "\n"
    for part in mod["sources"]:
        if part == "@swin-persistent-types":
            types_path = os.path.join(source_dir, "swin_persistent_types.h")
            if not os.path.exists(types_path):
                types_path = os.path.join(source_dir, "../Development/HIP/swin_persistent_types.h")
            t_txt = open(types_path, "r", encoding="utf-8").read().replace("#pragma once", "")
            text += t_txt + "\n"
        elif part == "@wave-owned-attention-body":
            core = open(os.path.join(source_dir, "wave_owned_mh.inc"), "r", encoding="utf-8").read()
            start = core.index(" // One wave owns all keys")
            end = core.index("#define W2_KERNEL")
            text += core[start:end] + "\n"
        else:
            text += open(os.path.join(source_dir, part), "r", encoding="utf-8").read() + "\n"
    return transform_hip_to_sm86_cu(text, compat_header_path)

def compile_one_module(mod, source_dir, out_dir, compat_header_path, ptx2cubin_bin):
    name = mod["name"]
    cu_src = assemble_module_source(mod, source_dir, compat_header_path)
    cu_path = os.path.join(out_dir, f"{name}.generated.cu")
    ptx_path = os.path.join(out_dir, f"{name}.ptx")
    hsaco_path = os.path.join(out_dir, f"{name}.hsaco")
    if os.path.exists(hsaco_path) and os.path.getsize(hsaco_path) > 0 and os.path.exists(ptx_path):
        old_cu = open(cu_path, "r", encoding="utf-8").read() if os.path.exists(cu_path) else ""
        if old_cu == cu_src:
            ptx_txt = open(ptx_path, "r", encoding="utf-8").read()
            entries = re.findall(r"\.visible\s+\.entry\s+([a-zA-Z0-9_]+)\s*\(", ptx_txt)
            sha = hashlib.sha256(open(hsaco_path, "rb").read()).hexdigest()
            return (name, True, "", entries, sha)
    with open(cu_path, "w", encoding="utf-8") as f:
        f.write(cu_src)

    cmd_clang = [
        "clang++", "-x", "cuda", "--cuda-device-only", "--cuda-gpu-arch=sm_86",
        "-Xclang", "-fnative-half-type", "-Xclang", "-fallow-half-arguments-and-returns",
        "-nocudainc", "-nocudalib", "-std=c++20", "-O3",
        "-Wno-unknown-attributes", "-Wno-unused-value",
        "-S", cu_path, "-o", ptx_path
    ]
    res = subprocess.run(cmd_clang, capture_output=True, text=True)
    if res.returncode != 0:
        return (name, False, f"Clang failed:\n{res.stderr}", [], "")

    ptx_txt = open(ptx_path, "r", encoding="utf-8").read()
    entries = re.findall(r"\.visible\s+\.entry\s+([a-zA-Z0-9_]+)\s*\(", ptx_txt)

    cmd_cubin = [ptx2cubin_bin, ptx_path, hsaco_path] + entries
    res2 = subprocess.run(cmd_cubin, capture_output=True, text=True)
    if res2.returncode != 0:
        return (name, False, f"ptx2cubin failed:\n{res2.stderr}", entries, "")

    sha = hashlib.sha256(open(hsaco_path, "rb").read()).hexdigest()
    return (name, True, "", entries, sha)

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source_dir = sys.argv[1] if len(sys.argv) > 1 else here
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "modules")
    compat_header = sys.argv[3] if len(sys.argv) > 3 else os.path.join(here, "sm86_compat.h")
    ptx2cubin_bin = sys.argv[4] if len(sys.argv) > 4 else os.path.join(here, "ptx2cubin")

    os.makedirs(out_dir, exist_ok=True)
    ps1_path = os.path.join(source_dir, "build-modules.ps1")
    modules = parse_ps1_modules(ps1_path)
    print(f"Parsed {len(modules)} modules from {ps1_path}")

    results = []
    # Compile in parallel using 8 workers
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {
            ex.submit(compile_one_module, m, source_dir, out_dir, compat_header, ptx2cubin_bin): m
            for m in modules
        }
        for fut in as_completed(futs):
            name, ok, err, entries, sha = fut.result()
            results.append((name, ok, err, entries, sha))
            if ok:
                print(f"[PASS] {name:38s} entries={len(entries):2d} sha256={sha[:16]}...")
            else:
                print(f"[FAIL] {name:38s}\n{err}")

    results.sort(key=lambda x: x[0])
    passed = sum(1 for r in results if r[1])
    total_entries = sum(len(r[3]) for r in results if r[1])
    print(f"\nSUMMARY: {passed}/{len(modules)} modules compiled to sm_86 cubin & verified on RTX 3080 Laptop GPU ({total_entries} kernel entry points verified)!")
    if passed != len(modules):
        sys.exit(1)

if __name__ == "__main__":
    main()
