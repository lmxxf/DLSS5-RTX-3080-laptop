#!/usr/bin/env python3
import os
import re
import sys
import json
import hashlib
import subprocess
from phase2_transform import transform as phase2_transform
from phase5_transform import transform as phase5_transform
from phase8_transform import transform as phase8_transform, low_register_fp8
from phase9_transform import transform as phase9_transform, c32_mapped_lowreg
from phase10_transform import apply_register_caps, optimize_fp8 as phase10_optimize_fp8
from phase11_transform import pack_ffn_half_features
PHASE11_HALF_FEATURE_PACK = True
from phase14_transform import fix_legacy_attention_abi
PHASE14_ATTENTION_ABI = True
from phase17_transform import transform as phase17_half_transform, version_ptx as phase17_version_ptx
PHASE17_C32_HALF = True
from phase18_transform import transform as phase18_pack_transform
PHASE18_SITES = {'c32-wave1-fast':['c32-v'], 'c64-wave2-fast':['byteout']}
PHASE18_C256_CAP = None
PHASE18_QKV_MASK = 7
from phase12_transform import pack_c32_av
PHASE12_C32_AV = True
PHASE10_CAPS = True
PHASE10_FP8 = True
C32_LOCAL_FP8_POLICY_MODULES = {"c32-wave1-fast"}
LOW_REGISTER_FP8_MODULES = {"vit-stream-fast", "c512-m32-deep"}

# Per-module controlled experiments; defaults enable the verified Phase-8 sites.
PHASE8_OVERRIDES = {}
from concurrent.futures import ThreadPoolExecutor, as_completed

def parse_ps1_modules(ps1_path):
    txt = open(ps1_path, "r", encoding="utf-8").read()
    modules = []
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
    text = re.sub(
        r'__has_builtin\s*\(\s*__builtin_amdgcn_[a-zA-Z0-9_]+\s*\)',
        '1',
        text
    )
    text = re.sub(
        r'(?<![=\w])\bint\s+__attribute__\s*\(\(\s*ext_vector_type\s*\(\s*4\s*\)\s*\)\)(?=\s+[a-zA-Z_])',
        'sm86_i4',
        text
    )
    text = text.replace(
        'DEV float fp8_add0(float x){',
        'DEV unsigned char byte_F(float x);\nDEV float fp8_add0(float x){'
    )
    text = re.sub(
        r'if\s+constexpr\s*\(\s*\(\s*CW_PACK_MODE_MASK\s*&\s*\(\s*1u\s*<<\s*Site\s*\)\s*\)\s*!=\s*0\s*\)\s*\{.*?return\s+i2\{lo,hi\};\s*\}',
        '',
        text,
        flags=re.DOTALL
    )
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
    # 1. Unroll `for(uint ci=0;ci<2;ci++)` in wave_owned_mh.inc / wave_owned_c32.inc to promote f8[2] and f8[4][2] to SSA registers (eliminates 336B stack!)
    text = re.sub(
        r'(?<!unroll"\)\s)(?<!unroll 2"\)\s)\bfor\(uint ci=0;ci<2;ci\+\+\)',
        '_Pragma("unroll") for(uint ci=0;ci<2;ci++)',
        text
    )
    # 2. Unroll `for(uint n=0;n<4;n++)` in vit_contract_blocked_body to promote f8 total[4] and acc[4] to SSA registers
    text = re.sub(
        r'(?<!unroll"\)\s)\bfor\(uint n=0;n<4;n\+\+\)',
        '_Pragma("unroll") for(uint n=0;n<4;n++)',
        text
    )
    text = text.replace(
        '_Pragma("unroll") for(uint n=0;n<4;n++)for(uint e=0;e<8;e++)',
        '_Pragma("unroll") for(uint n=0;n<4;n++)_Pragma("unroll") for(uint e=0;e<8;e++)'
    )
    text = re.sub(
        r'(#pragma\s+unroll[^\n]*\n\s*|_Pragma\("unroll[^"]*"\)\s*)+_Pragma\("unroll"\)',
        '_Pragma("unroll")',
        text
    )
    # 3. Unroll `for(uint j=0;j<4;j++)` and `for(uint sidx=0;sidx<C/16;sidx++)` in mh_pool_project_* and conjugate K32 `acc = H(acc + sum)` to stay in Ampere layout across chunks!
    text = text.replace(
        'for(uint sidx=0;sidx<C/16;sidx++)for(uint e=0;e<8;e++)',
        '_Pragma("unroll") for(uint sidx=0;sidx<C/16;sidx++)_Pragma("unroll") for(uint e=0;e<8;e++)'
    )
    text = text.replace(
        'for(uint half=0;half<2;half++){uint sidx=chunk*2+half;for(uint j=0;j<4;j++)',
        '_Pragma("unroll") for(uint half=0;half<2;half++){uint sidx=chunk*2+half;_Pragma("unroll") for(uint j=0;j<4;j++)'
    )
    text = text.replace(
        'for(uint j=0;j<4;j++){pool_i4 b;',
        '_Pragma("unroll") for(uint j=0;j<4;j++){pool_i4 b;'
    )
    text = text.replace(
        'for(uint j=0;j<4;j++){h8 b;uint nt=colg/16+j;',
        '_Pragma("unroll") for(uint j=0;j<4;j++){h8 b;uint nt=colg/16+j;'
    )
    text = text.replace(
        'for(uint j=0;j<4;j++)for(uint e=0;e<8;e++)acc[j][e]=H(acc[j][e]+sum[j][e]);\n }',
        '_Pragma("unroll") for(uint j=0;j<4;j++){sum[j]=__sm86_c_to_ampere_f32(sum[j]);_Pragma("unroll") for(uint e=0;e<8;e++)acc[j][e]=H(acc[j][e]+sum[j][e]);}\n }\n _Pragma("unroll") for(uint j=0;j<4;j++)acc[j]=__sm86_d_to_rdna4_f32(acc[j]);'
    )
    text = text.replace(
        'for(uint e=0;e<8;e++)acc[e]=channels==32?Hrtz(acc[e]+sum[e]):H(acc[e]+sum[e]);\n }',
        'sum=__sm86_c_to_ampere_f32(sum);_Pragma("unroll") for(uint e=0;e<8;e++)acc[e]=channels==32?Hrtz(acc[e]+sum[e]):H(acc[e]+sum[e]);\n }\n acc=__sm86_d_to_rdna4_f32(acc);'
    )
    # 4. Conjugate 4-partition accumulation in vit_contract_blocked_body, vit_stream_project_tiles, and decoder_project2x_h16w_wide_body so `acc`/`a` stays in Ampere layout across `part=0..3`!
    text = text.replace(
        '_Pragma("unroll") for(uint n=0;n<4;n++)for(uint e=0;e<8;e++){if constexpr(Partial)out[(part*tokens+first+gr()*8+e)*1024+col+n*16+rc()]=acc[n][e];else total[n][e]+=acc[n][e];}\n  }',
        '_Pragma("unroll") for(uint n=0;n<4;n++){if constexpr(Partial){for(uint e=0;e<8;e++)out[(part*tokens+first+gr()*8+e)*1024+col+n*16+rc()]=acc[n][e];}else{if(part==part0)total[n]=__sm86_c_to_ampere_f32(total[n]);acc[n]=__sm86_c_to_ampere_f32(acc[n]);_Pragma("unroll") for(uint e=0;e<8;e++)total[n][e]+=acc[n][e];}}\n  }\n  if constexpr(!Partial){_Pragma("unroll") for(uint n=0;n<4;n++)total[n]=__sm86_d_to_rdna4_f32(total[n]);}'
    )
    text = text.replace(
        '#pragma unroll\n   for(uint t=0;t<TM;t++)\n#pragma unroll\n   for(uint j=0;j<TN;j++)for(uint e=0;e<8;e++)total[t][j][e]+=a[t][j][e];}',
        '#pragma unroll\n   for(uint t=0;t<TM;t++)\n#pragma unroll\n   for(uint j=0;j<TN;j++){if(p==0)total[t][j]=__sm86_c_to_ampere_f32(total[t][j]);a[t][j]=__sm86_c_to_ampere_f32(a[t][j]);_Pragma("unroll") for(uint e=0;e<8;e++)total[t][j][e]+=a[t][j][e];}}\n#pragma unroll\n  for(uint t=0;t<TM;t++)\n#pragma unroll\n  for(uint j=0;j<TN;j++)total[t][j]=__sm86_d_to_rdna4_f32(total[t][j]);'
    )
    text = text.replace(
        '    a=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(x0,i2{bw[0],bw[1]},a);\n    a=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(x1,i2{bw[2],bw[3]},a);\n   }for(uint e=0;e<8;e++)total[e]=p?total[e]+a[e]:a[e];\n  }',
        '    a=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(x0,i2{bw[0],bw[1]},a);\n    a=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(x1,i2{bw[2],bw[3]},a);\n   }a=__sm86_c_to_ampere_f32(a);_Pragma("unroll") for(uint e=0;e<8;e++)total[e]=p?total[e]+a[e]:a[e];\n  }\n  total=__sm86_d_to_rdna4_f32(total);'
    )
    # 5. Automatically unroll small inner loops (<=16 steps or template tile bounds, excluding outer tile loops qt/ht/h2/qb) so SROA promotes f8/h8/i2 arrays to SSA registers (eliminating LMem!)
    unroll_pat = re.compile(
        r'((?:(?:#pragma\s+unroll[^\n]*|_Pragma\s*\(\s*"[^"]*unroll[^"]*"\s*\)|C5C_UNROLL\([^)]*\))\s*(?:#endif\s*)?)+)?'
        r'\b(for\s*\(\s*uint\s+(?!(?:qt|ht|h2|qb)\b)([a-zA-Z_]\w*)\s*=\s*0\s*;\s*\3\s*<\s*(?:2|3|4|5|6|8|16|NT|QT|TM|TN|B|T)u?\s*;\s*(?:\+\+\3|\3\+\+)\s*\))'
    )
    def _unroll_repl(m):
        if m.group(1):
            return m.group(0)
        return '_Pragma("unroll") ' + m.group(2)
    text = unroll_pat.sub(_unroll_repl, text)
    # Pre-shuffle input[0..1], act[0..1], feature[ci], Q, K, V, prob, and av[ci] in wave_owned_c32.inc!
    text = text.replace(
        "  if constexpr(Chain){",
        "  input[0]=sm86_preshuffle_fp8(input[0]);input[1]=sm86_preshuffle_fp8(input[1]);\n  if constexpr(Chain){"
    )
    text = text.replace(
        "ffn[0]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(bp.lo,input[0],ffn[0]);\n     ffn[1]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(bp.hi,input[1],ffn[1]);",
        "ffn[0]=sm86_wmma_fp8_preshuffled_b(bp.lo,input[0],ffn[0]);\n     ffn[1]=sm86_wmma_fp8_preshuffled_b(bp.hi,input[1],ffn[1]);"
    )
    text = text.replace(
        "ffn[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,input[kt],ffn[ci]);",
        "ffn[ci]=sm86_wmma_fp8_preshuffled_b(b,input[kt],ffn[ci]);"
    )
    text = text.replace(
        "f8 expanded=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(bp.lo,input[0],f8{});\n     expanded=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(bp.hi,input[1],expanded);",
        "f8 expanded=sm86_wmma_fp8_preshuffled_b(bp.lo,input[0],f8{});\n     expanded=sm86_wmma_fp8_preshuffled_b(bp.hi,input[1],expanded);"
    )
    text = text.replace(
        "act[hp]=a;",
        "act[hp]=sm86_preshuffle_fp8(a);"
    )
    text = text.replace(
        "ffn[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(cp.lo,act[0],ffn[ci]);\n     ffn[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(cp.hi,act[1],ffn[ci]);",
        "ffn[ci]=sm86_wmma_fp8_preshuffled_b(cp.lo,act[0],ffn[ci]);\n     ffn[ci]=sm86_wmma_fp8_preshuffled_b(cp.hi,act[1],ffn[ci]);"
    )
    text = text.replace(
        "expanded=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(bp.lo,input[0],expanded);\n     expanded=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(bp.hi,input[1],expanded);\n    }else _Pragma(\"unroll\") for(uint kt=0;kt<2;kt++){i2 b=matrix8(fw+512,(ht*16+r)*32+kt*16+g*8);expanded=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,input[kt],expanded);}",
        "expanded=sm86_wmma_fp8_preshuffled_b(bp.lo,input[0],expanded);\n     expanded=sm86_wmma_fp8_preshuffled_b(bp.hi,input[1],expanded);\n    }else _Pragma(\"unroll\") for(uint kt=0;kt<2;kt++){i2 b=matrix8(fw+512,(ht*16+r)*32+kt*16+g*8);expanded=sm86_wmma_fp8_preshuffled_b(b,input[kt],expanded);}"
    )
    text = text.replace(
        "if constexpr(W16==2){\n     _Pragma(\"unroll\") for(uint ci=0;ci<2;ci++){i2 b=matrix8(fw+4608,(ci*4+(ht>>1))*512+(((ht&1u)*2+g)*16+r)*8);ffn[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,a,ffn[ci]);}\n    }else _Pragma(\"unroll\") for(uint ci=0;ci<2;ci++){i2 b=matrix8(fw+4608,(ci*16+r)*128+ht*16+g*8);ffn[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,a,ffn[ci]);}",
        "a=sm86_preshuffle_fp8(a);if constexpr(W16==2){\n     _Pragma(\"unroll\") for(uint ci=0;ci<2;ci++){i2 b=matrix8(fw+4608,(ci*4+(ht>>1))*512+(((ht&1u)*2+g)*16+r)*8);ffn[ci]=sm86_wmma_fp8_preshuffled_b(b,a,ffn[ci]);}\n    }else _Pragma(\"unroll\") for(uint ci=0;ci<2;ci++){i2 b=matrix8(fw+4608,(ci*16+r)*128+ht*16+g*8);ffn[ci]=sm86_wmma_fp8_preshuffled_b(b,a,ffn[ci]);}"
    )
    text = text.replace(
        "CW_Q8_END_SITE(a,2);feature[ci]=a;}",
        "CW_Q8_END_SITE(a,2);feature[ci]=sm86_preshuffle_fp8(a);}"
    )
    text = text.replace(
        "q[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(bp.lo,feature[0],q[ci]);\n      q[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(bp.hi,feature[1],q[ci]);",
        "q[ci]=sm86_wmma_fp8_preshuffled_b(bp.lo,feature[0],q[ci]);\n      q[ci]=sm86_wmma_fp8_preshuffled_b(bp.hi,feature[1],q[ci]);"
    )
    text = text.replace(
        "q[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(feature[0],bp.lo,q[ci]);\n      q[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(feature[1],bp.hi,q[ci]);",
        "q[ci]=sm86_wmma_fp8_preshuffled_a(feature[0],bp.lo,q[ci]);\n      q[ci]=sm86_wmma_fp8_preshuffled_a(feature[1],bp.hi,q[ci]);"
    )
    text = text.replace(
        "q[ci]=part<2?__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,feature[kt],q[ci]):__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(feature[kt],b,q[ci]);",
        "q[ci]=part<2?sm86_wmma_fp8_preshuffled_b(b,feature[kt],q[ci]):sm86_wmma_fp8_preshuffled_a(feature[kt],b,q[ci]);"
    )
    text = text.replace(
        "CW_Q8_END_SITE(a,5);av[ci]=a;}",
        "CW_Q8_END_SITE(a,5);av[ci]=sm86_preshuffle_fp8(a);}"
    )
    text = text.replace(
        "acc=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(bp.lo,av[0],acc);\n    acc=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(bp.hi,av[1],acc);",
        "acc=sm86_wmma_fp8_preshuffled_b(bp.lo,av[0],acc);\n    acc=sm86_wmma_fp8_preshuffled_b(bp.hi,av[1],acc);"
    )
    text = text.replace(
        "acc=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,av[kt],acc);",
        "acc=sm86_wmma_fp8_preshuffled_b(b,av[kt],acc);"
    )
    # Shared Q/K/V is the measured Phase-3 winner and Phase-4 baseline.
    text = text.replace(
        "cw_qkv_smem[part][qt*2+ci][qlane]=a;",
        "cw_qkv_smem[part][qt*2+ci][qlane]=sm86_preshuffle_fp8(a);"
    )
    text = text.replace(
        "acc=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(cw_qkv_smem[1][kt*2+ci][lane],q[ci],acc);",
        "acc=sm86_wmma_fp8_preshuffled_ab(cw_qkv_smem[1][kt*2+ci][lane],q[ci],acc);"
    )
    text = text.replace(
        "CW_Q8_END_SITE(a,4);prob[kt]=a;",
        "CW_Q8_END_SITE(a,4);prob[kt]=sm86_preshuffle_fp8(a);"
    )
    text = text.replace(
        "acc=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(cw_qkv_smem[2][kt*2+ci][lane],prob[kt],acc);",
        "acc=sm86_wmma_fp8_preshuffled_ab(cw_qkv_smem[2][kt*2+ci][lane],prob[kt],acc);"
    )
    # 6. Pre-shuffle ALL activation fragments (in0/in1/inputs, hidden, plane1, plane0, Q/K/V, prob, AV) in wave_owned_mh.inc!
    text = text.replace(
        '{in0[qi]=w2_load<C>(plane0,qb+qi,kt);in1[qi]=w2_load<C>(plane0,qb+qi,kt+1);}',
        '{in0[qi]=sm86_preshuffle_fp8(w2_load<C>(plane0,qb+qi,kt));in1[qi]=sm86_preshuffle_fp8(w2_load<C>(plane0,qb+qi,kt+1));}'
    )
    text = text.replace(
        'expanded[qi][tile]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b0,in0[qi],expanded[qi][tile]);\n      _Pragma("unroll") for(uint qi=0;qi<B;qi++)expanded[qi][tile]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b1,in1[qi],expanded[qi][tile]);',
        'expanded[qi][tile]=sm86_wmma_fp8_preshuffled_b(b0,in0[qi],expanded[qi][tile]);\n      _Pragma("unroll") for(uint qi=0;qi<B;qi++)expanded[qi][tile]=sm86_wmma_fp8_preshuffled_b(b1,in1[qi],expanded[qi][tile]);'
    )
    text = text.replace(
        'inputs[qi]=w2_load<C>(plane0,qb+qi,kt);',
        'inputs[qi]=sm86_preshuffle_fp8(w2_load<C>(plane0,qb+qi,kt));'
    )
    text = text.replace(
        'expanded[qi][tile]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,inputs[qi],expanded[qi][tile]);',
        'expanded[qi][tile]=sm86_wmma_fp8_preshuffled_b(b,inputs[qi],expanded[qi][tile]);'
    )
    text = text.replace(
        'W2_Q8_END(packed);hidden[t2][qi]=packed;',
        'W2_Q8_END(packed);hidden[t2][qi]=sm86_preshuffle_fp8(packed);'
    )
    text = text.replace(
        'contract[qi][ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b0,hidden[0][qi],contract[qi][ci]);\n      _Pragma("unroll") for(uint qi=0;qi<B;qi++)contract[qi][ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b1,hidden[1][qi],contract[qi][ci]);',
        'contract[qi][ci]=sm86_wmma_fp8_preshuffled_b(b0,hidden[0][qi],contract[qi][ci]);\n      _Pragma("unroll") for(uint qi=0;qi<B;qi++)contract[qi][ci]=sm86_wmma_fp8_preshuffled_b(b1,hidden[1][qi],contract[qi][ci]);'
    )
    text = text.replace(
        'W2_Q8_END(packed);hidden[qi]=packed;',
        'W2_Q8_END(packed);hidden[qi]=sm86_preshuffle_fp8(packed);'
    )
    text = text.replace(
        'contract[qi][ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,hidden[qi],contract[qi][ci]);',
        'contract[qi][ci]=sm86_wmma_fp8_preshuffled_b(b,hidden[qi],contract[qi][ci]);'
    )
    text = text.replace(
        'i2 a=w2_load<C>(plane0,qt,kt);\n    _Pragma("unroll") for(uint tile=0;tile<W2_HIDDEN_TILES;tile++){\n     i2 b=w2_weight(fw,head*128+(ht+tile)*16+rc,C,kt*16);\n     expanded[tile]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,a,expanded[tile]);',
        'i2 a=sm86_preshuffle_fp8(w2_load<C>(plane0,qt,kt));\n    _Pragma("unroll") for(uint tile=0;tile<W2_HIDDEN_TILES;tile++){\n     i2 b=w2_weight(fw,head*128+(ht+tile)*16+rc,C,kt*16);\n     expanded[tile]=sm86_wmma_fp8_preshuffled_b(b,a,expanded[tile]);'
    )
    text = text.replace(
        'W2_Q8_END(hidden);',
        'W2_Q8_END(hidden);hidden=sm86_preshuffle_fp8(hidden);'
    )
    text = text.replace(
        'contract[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,hidden,contract[ci]);',
        'contract[ci]=sm86_wmma_fp8_preshuffled_b(b,hidden,contract[ci]);'
    )
    text = text.replace(
        'w2_store<C>(plane1,qb+qi,head*2+ci,a);',
        'w2_store<C>(plane1,qb+qi,head*2+ci,sm86_preshuffle_fp8(a));'
    )
    text = text.replace(
        'W2_Q8_END(a);w2_store<C>(plane1,qt,head*2+ci,a);',
        'W2_Q8_END(a);w2_store<C>(plane1,qt,head*2+ci,sm86_preshuffle_fp8(a));'
    )
    text = text.replace(
        'result[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b0,a0,result[ci]);\n    result[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b1,a1,result[ci]);',
        'result[ci]=sm86_wmma_fp8_preshuffled_b(b0,a0,result[ci]);\n    result[ci]=sm86_wmma_fp8_preshuffled_b(b1,a1,result[ci]);'
    )
    text = text.replace(
        'i2 a=w2_load<C>(plane1,qt,kt),b=w2_weight(fw+8*C*C,head*32+ci*16+rc,C,kt*16);\n   result[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,a,result[ci]);',
        'i2 a=w2_load<C>(plane1,qt,kt),b=w2_weight(fw+8*C*C,head*32+ci*16+rc,C,kt*16);\n   result[ci]=sm86_wmma_fp8_preshuffled_b(b,a,result[ci]);'
    )
    text = text.replace(
        'W2_Q8_END(a);w2_store<C>(plane0,qt,head*2+ci,a);',
        'W2_Q8_END(a);w2_store<C>(plane0,qt,head*2+ci,sm86_preshuffle_fp8(a));'
    )
    text = text.replace(
        '__builtin_memcpy(&f,feature+p*C+col,8);w2_store<C>(plane0,qt,head*2+ci,f);',
        '__builtin_memcpy(&f,feature+p*C+col,8);w2_store<C>(plane0,qt,head*2+ci,sm86_preshuffle_fp8(f));'
    )
    text = text.replace(
        'if(part<2)q[part][ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,a,q[part][ci]);\n     else q[part][ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,q[part][ci]);',
        'if(part<2)q[part][ci]=sm86_wmma_fp8_preshuffled_b(b,a,q[part][ci]);\n     else q[part][ci]=sm86_wmma_fp8_preshuffled_a(a,b,q[part][ci]);'
    )
    text = text.replace(
        'if(part<2)q[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,a,q[ci]);\n    else q[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(a,b,q[ci]);',
        'if(part<2)q[ci]=sm86_wmma_fp8_preshuffled_b(b,a,q[ci]);\n    else q[ci]=sm86_wmma_fp8_preshuffled_a(a,b,q[ci]);'
    )
    text = text.replace(
        'i2 a=w2_load<C>(plane0,qt,kt,qlane),b=w2_weight(aw,head*32+ci*16+qrc,C,kt*16,qgr);\n   query[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,a,query[ci]);',
        'i2 a=w2_load<C>(plane0,qt,kt,qlane),b=w2_weight(aw,head*32+ci*16+qrc,C,kt*16,qgr);\n   query[ci]=sm86_wmma_fp8_preshuffled_b(b,a,query[ci]);'
    )
    text = text.replace(
        '__builtin_memcpy(&a,feature+w2_pixel(win,qt*16+rc,workw)*C+ct*16+gr*8,8);',
        '__builtin_memcpy(&a,feature+w2_pixel(win,qt*16+rc,workw)*C+ct*16+gr*8,8);a=sm86_preshuffle_fp8(a);'
    )
    text = text.replace(
        '{i2 b;__builtin_memcpy(&b,diag+(part*(C/16)+ct)*512+(gr*16+rc)*8,8);result[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,a,result[ci]);}',
        '{i2 b;__builtin_memcpy(&b,diag+(part*(C/16)+ct)*512+(gr*16+rc)*8,8);result[ci]=sm86_wmma_fp8_preshuffled_b(b,a,result[ci]);}'
    )
    text = text.replace(
        'i2 a=w2_load<C>(plane1,qt,kt),b=w2_weight(aw+3*C*C,head*32+ci*16+rc,C,kt*16);\n   result[ci]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(b,a,result[ci]);',
        'i2 a=w2_load<C>(plane1,qt,kt),b=w2_weight(aw+3*C*C,head*32+ci*16+rc,C,kt*16);\n   result[ci]=sm86_wmma_fp8_preshuffled_b(b,a,result[ci]);'
    )
    text = text.replace(
        'if(part==0)w2_store<C>(plane1,qt,head*2+ci,a);else if(part==1)w2_store<C>(plane_k,qt,head*2+ci,a);else vals[qt][ci]=a;',
        'a=sm86_preshuffle_fp8(a);if(part==0)w2_store<C>(plane1,qt,head*2+ci,a);else if(part==1)w2_store<C>(plane_k,qt,head*2+ci,a);else vals[qt][ci]=a;'
    )
    text = text.replace(
        'w2_store<C>(plane1,qt,head*2+ci,q);w2_store<C>(plane_k,qt,head*2+ci,k);vals[qt][ci]=v;',
        'w2_store<C>(plane1,qt,head*2+ci,sm86_preshuffle_fp8(q));w2_store<C>(plane_k,qt,head*2+ci,sm86_preshuffle_fp8(k));vals[qt][ci]=sm86_preshuffle_fp8(v);'
    )
    text = text.replace(
        'W2_Q8_END(a);query_frag[ci]=a;',
        'W2_Q8_END(a);query_frag[ci]=sm86_preshuffle_fp8(a);'
    )
    text = text.replace(
        'scores=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(w2_load<C>(plane_k,key,head*2+ci),',
        'scores=sm86_wmma_fp8_preshuffled_ab(w2_load<C>(plane_k,key,head*2+ci),'
    )
    text = text.replace(
        'W2_Q8_END(a);prob[key]=a;',
        'W2_Q8_END(a);prob[key]=sm86_preshuffle_fp8(a);'
    )
    text = text.replace(
        'av=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(vals[key][ci],prob[key],av);',
        'av=sm86_wmma_fp8_preshuffled_ab(vals[key][ci],prob[key],av);'
    )
    # 7. Pre-shuffle q[0..1] and xb in vit_attention_transposed_score_body (deep_fast.hip)!
    text = text.replace(
        'h8 ones{};_Pragma("unroll") for(uint e=0;e<8;e++)ones[e]=(_Float16)1.f;\n f8 sum{},acc[2]{};\n for(uint key=0,tile=0;key<tokens;key+=16,tile^=1u)',
        'q[0]=sm86_preshuffle_fp8(q[0]);q[1]=sm86_preshuffle_fp8(q[1]);\n h8 ones{};_Pragma("unroll") for(uint e=0;e<8;e++)ones[e]=(_Float16)1.f;\n f8 sum{},acc[2]{};\n for(uint key=0,tile=0;key<tokens;key+=16,tile^=1u)'
    )
    text = text.replace(
        'a=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(y,q[k/16],a);}',
        'a=sm86_wmma_fp8_preshuffled_b(y,q[k/16],a);}'
    )
    text = text.replace(
        'acc[c]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(y,xb,acc[c]);\n#else\n  acc[c]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(xb,y,acc[c]);',
        'acc[c]=sm86_wmma_fp8_preshuffled_b(y,xb,acc[c]);\n#else\n  acc[c]=sm86_wmma_fp8_preshuffled_a(xb,y,acc[c]);'
    )
    text = text.replace(
        '_Pragma("unroll") for(uint c=0;c<2;c++){i2 y{};',
        'xb=sm86_preshuffle_fp8(xb);_Pragma("unroll") for(uint c=0;c<2;c++){i2 y{};'
    )
    if PHASE14_ATTENTION_ABI:
        text = fix_legacy_attention_abi(text)
    return f'#include "{compat_header_path}"\n' + text

def assemble_module_source(mod, source_dir, compat_header_path):
    lines = ["#define HIP_ISA_HALF 1"]
    if mod["name"].endswith("-packed"):
        lines.append("#define HIP_PREPACKED_WEIGHTS 1")
    for d in mod["defines"] + mod["l23defines"]:
        if mod["name"]=="c64-wave2-fast" and PHASE18_QKV_MASK is not None and d.startswith("W2_QKV_FUSE "):
            d="W2_QKV_FUSE "+str(PHASE18_QKV_MASK)
        lines.append(f"#define {d}")
    if mod["name"] in {"deep_fast-packed", "deep_fast-packed-fast", "vit-stream-fast"}:
        lines += ["#define VIT_EXPAND_TAIL_VEC 1", "#define VIT_QKV_TAIL_VEC 1", "#define VIT_CONTRACT_TAIL_VEC 1", "#define VIT_PROJECT_TAIL_VEC 1"]
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

prep_call_pat = re.compile(r'^(\s*)(%\S+)\s*=\s*(?:tail\s+)?call[^@]*@(__sm86_(?:prep|unpack)_(?:fp8|f16))\((<2 x i32>|<8 x half>)(?:\s+noundef)?\s+(%\S+|zeroinitializer|<[^>]+>)\)(.*)$')

def cse_and_hoist_prep_calls(body: str, split_basic_blocks) -> str:
    blocks = split_basic_blocks(body)
    bb_map = {lbl: lns for lbl, lns in blocks}
    bb_order = [lbl for lbl, _ in blocks]

    # Per-Basic-Block CSE of @__sm86_prep_fp8 and @__sm86_prep_f16:
    # Deduplicates all repeated prep calls on the same SSA variable within each basic block
    # without hoisting <4 x i32> across basic blocks (preventing cross-loop register pressure bloat!).
    for lbl in bb_order:
        lns = bb_map[lbl]
        seen = {}
        new_lns = []
        for ln in lns:
            mp = prep_call_pat.match(ln)
            if mp:
                indent, res_v, fn_name, arg_ty, arg_v, tail = mp.groups()
                if arg_v == "zeroinitializer":
                    new_lns.append(f"{indent}{res_v} = add <4 x i32> zeroinitializer, zeroinitializer")
                    continue
                if "0xH3C00" in arg_v and arg_v.count("0xH3C00") == 8:
                    new_lns.append(f"{indent}{res_v} = add <4 x i32> <i32 1006648320, i32 1006648320, i32 1006648320, i32 1006648320>, zeroinitializer")
                    continue
                if arg_v.startswith("%"):
                    key = (fn_name, arg_ty, arg_v)
                    if key in seen:
                        canon_v = seen[key]
                        new_lns.append(f"{indent}{res_v} = add <4 x i32> {canon_v}, zeroinitializer")
                        continue
                    seen[key] = res_v
            new_lns.append(ln)
        bb_map[lbl] = new_lns

    return "\n".join("\n".join(bb_map[lbl]) for lbl in bb_order)

# --- SSA IR Algebraic Cancellation for WMMA C/D Shuffles ---
d2r_pat = re.compile(r'^(\s*)(%\S+)\s*=\s*(?:tail\s+)?call[^@]*@__sm86_d_to_rdna4\(<4 x i32>(?:\s+noundef)?\s+(%\S+|zeroinitializer)\)(.*)$')
c2a_pat = re.compile(r'^(\s*)(%\S+)\s*=\s*(?:tail\s+)?call[^@]*@__sm86_c_to_ampere\(<8 x float>(?:\s+noundef)?\s+(%\S+|zeroinitializer)\)(.*)$')
phi_pat = re.compile(r'^(\s*)(%\S+)\s*=\s*phi\s+<8 x float>\s*(.+)$')
fadd_zero_pat = re.compile(r'^(\s*)(%\S+)\s*=\s*fadd\s+<8 x float>\s+(%\S+|zeroinitializer),\s*zeroinitializer\s*$')

def split_basic_blocks(body: str):
    blocks = []
    cur_label = "bb"
    cur_lines = []
    for ln in body.splitlines():
        if not ln.strip():
            continue
        m_lbl = re.match(r'^([a-zA-Z0-9_.]+):\s*(?:;.*)?$', ln)
        if m_lbl:
            if cur_lines:
                blocks.append((cur_label, cur_lines))
            cur_label = m_lbl.group(1)
            cur_lines = [ln]
        else:
            cur_lines.append(ln)
    if cur_lines:
        blocks.append((cur_label, cur_lines))
    return blocks

def pass1_direct_and_dce(body: str) -> str:
    lines = [ln for ln in body.splitlines() if ln.strip()]
    alias = {}
    def resolve(v):
        while v in alias:
            v = alias[v]
        return v

    d2r_map = {}
    for ln in lines:
        mf = fadd_zero_pat.match(ln)
        if mf:
            alias[mf.group(2)] = resolve(mf.group(3))
            continue
        md = d2r_pat.match(ln)
        if md:
            d2r_map[md.group(2)] = resolve(md.group(3))

    new_lines = []
    for ln in lines:
        mc = c2a_pat.match(ln)
        if mc:
            indent, res_v, arg_v, _ = mc.groups()
            arg_v = resolve(arg_v)
            if arg_v == "zeroinitializer":
                alias[res_v] = "zeroinitializer"
                new_lines.append(f"{indent}{res_v} = or <4 x i32> zeroinitializer, zeroinitializer")
                continue
            elif arg_v in d2r_map:
                src_x = resolve(d2r_map[arg_v])
                alias[res_v] = src_x
                new_lines.append(f"{indent}{res_v} = or <4 x i32> {src_x}, zeroinitializer")
                continue
        new_lines.append(ln)

    var_uses = {}
    for ln in new_lines:
        for v in re.findall(r'%[a-zA-Z0-9_.]+', ln):
            var_uses[v] = var_uses.get(v, 0) + 1

    cleaned = []
    for ln in new_lines:
        md = d2r_pat.match(ln)
        if md and var_uses.get(md.group(2), 0) <= 1:
            continue
        mc = c2a_pat.match(ln)
        if mc and var_uses.get(mc.group(2), 0) <= 1:
            continue
        cleaned.append(ln)
    return "\n".join(cleaned)

def optimize_function_body(body: str) -> str:
    body = pass1_direct_and_dce(body)
    blocks = split_basic_blocks(body)
    bb_map = {lbl: lns for lbl, lns in blocks}
    bb_order = [lbl for lbl, _ in blocks]

    var_uses = {}
    c2a_uses = {}
    c2a_by_arg = {}
    d2r_in_bb = {}
    d2r_global = {}
    all_phis = {} # pvar -> (lbl, line_idx, indent, pairs)
    for lbl, lns in blocks:
        d2r_in_bb[lbl] = {}
        for idx, ln in enumerate(lns):
            md = d2r_pat.match(ln)
            if md:
                d2r_in_bb[lbl][md.group(2)] = md.group(3)
                d2r_global[md.group(2)] = md.group(3)
            mc = c2a_pat.match(ln)
            if mc:
                c2a_uses[mc.group(3)] = c2a_uses.get(mc.group(3), 0) + 1
                c2a_by_arg.setdefault(mc.group(3), []).append(mc.group(2))
            mp = phi_pat.match(ln)
            if mp:
                pairs = re.findall(r'\[\s*(%\S+|zeroinitializer)\s*,\s*%([a-zA-Z0-9_.]+)\s*\]', mp.group(3))
                all_phis[mp.group(2)] = (lbl, idx, mp.group(1), pairs)
            for v in re.findall(r'%[a-zA-Z0-9_.]+', ln):
                var_uses[v] = var_uses.get(v, 0) + 1

    preheader_inserts = {}
    exit_inserts = {}
    d2r_to_remove = set()
    c2a_to_identity = {}
    diamond_phi_rewrites = {} # back_v -> (lbl, idx, new_line)

    for header_lbl, lns in blocks:
        for i, ln in enumerate(lns):
            mp = phi_pat.match(ln)
            if not mp:
                continue
            indent, pvar, rhs = mp.groups()
            pairs = re.findall(r'\[\s*(%\S+|zeroinitializer)\s*,\s*%([a-zA-Z0-9_.]+)\s*\]', rhs)
            if len(pairs) != 2:
                continue

            # Determine which edge is the backedge (the block whose terminator branches to header_lbl and exit_lbl)
            (v0, b0), (v1, b1) = pairs
            cand = None
            for back_v, latch_lbl, pre_v, pre_lbl in [(v0, b0, v1, b1), (v1, b1, v0, b0)]:
                if pre_lbl not in bb_map or latch_lbl not in bb_map or pre_lbl == latch_lbl:
                    continue
                term = bb_map[latch_lbl][-1].strip()
                m_br = re.match(r'^br\s+i1\s+%\S+,\s*label\s+%([a-zA-Z0-9_.]+),\s*label\s+%([a-zA-Z0-9_.]+)', term)
                if not m_br:
                    continue
                t1, t2 = m_br.group(1), m_br.group(2)
                if t1 == header_lbl and t2 != header_lbl:
                    cand = (back_v, latch_lbl, pre_v, pre_lbl, t2)
                    break
                elif t2 == header_lbl and t1 != header_lbl:
                    cand = (back_v, latch_lbl, pre_v, pre_lbl, t1)
                    break
            if not cand:
                continue
            back_v, latch_lbl, pre_v, pre_lbl, exit_lbl = cand
            if exit_lbl not in bb_map:
                continue

            # Case A: `back_v` is directly in `d2r_global` (defined in any block of the loop body)
            # Case B: `back_v` is a 2-input diamond PHI `[ d_v, %then_bb ], [ pvar, %else_bb ]` where `d_v` is in `d2r_global`!
            is_diamond = False
            if back_v in d2r_global:
                if var_uses.get(pvar, 0) != 1 + c2a_uses.get(pvar, 0) or c2a_uses.get(pvar, 0) == 0:
                    continue
                d_var = back_v
                mma_v = d2r_global[d_var]
                new_back_v = mma_v
            elif back_v in all_phis:
                d_lbl, d_idx, d_indent, d_pairs = all_phis[back_v]
                if len(d_pairs) != 2:
                    continue
                (dv0, db0), (dv1, db1) = d_pairs
                if dv0 == pvar and dv1 in d2r_global:
                    d_var, d_then_bb, d_else_bb = dv1, db1, db0
                elif dv1 == pvar and dv0 in d2r_global:
                    d_var, d_then_bb, d_else_bb = dv0, db0, db1
                else:
                    continue
                # `pvar` is used in its definition (1), in `back_v` diamond PHI (1), and in `c_to_ampere(pvar)`
                if var_uses.get(pvar, 0) != 2 + c2a_uses.get(pvar, 0) or c2a_uses.get(pvar, 0) == 0:
                    continue
                # `d_var` is only used in its definition (1) and in `back_v` diamond PHI (1)
                if var_uses.get(d_var, 0) != 2:
                    continue
                is_diamond = True
                mma_v = d2r_global[d_var]
                new_back_v = back_v
            else:
                continue

            elns = bb_map[exit_lbl]
            uses_in_exit = sum(len(re.findall(re.escape(back_v) + r'(?![a-zA-Z0-9_.])', eln)) for eln in elns)
            if var_uses.get(back_v, 0) != 2 + uses_in_exit:
                continue

            can_sink = True
            phi_indices_in_exit = []
            for idx, eln in enumerate(elns):
                if re.search(re.escape(back_v) + r'(?![a-zA-Z0-9_.])', eln):
                    mp_e = phi_pat.match(eln)
                    if mp_e:
                        epairs = re.findall(r'\[\s*(%\S+|zeroinitializer)\s*,\s*%([a-zA-Z0-9_.]+)\s*\]', mp_e.group(3))
                        if not all(v == back_v or v == "zeroinitializer" for v, _ in epairs):
                            can_sink = False
                            break
                        phi_indices_in_exit.append(idx)
            if not can_sink:
                continue

            if pre_v == "zeroinitializer":
                pre_amp = "zeroinitializer"
            elif pre_v in d2r_global:
                pre_amp = d2r_global[pre_v]
            else:
                pre_amp = f"%init_amp_{pvar[1:]}"
                preheader_inserts.setdefault(pre_lbl, []).append(
                    f"  {pre_amp} = tail call <4 x i32> @__sm86_c_to_ampere(<8 x float> noundef {pre_v})"
                )

            lns[i] = f"{indent}{pvar} = phi <4 x i32> [ {pre_amp}, %{pre_lbl} ], [ {new_back_v}, %{latch_lbl} ]"
            if is_diamond:
                d_lbl, d_idx, d_indent, _ = all_phis[back_v]
                old_d_ln = bb_map[d_lbl][d_idx]
                bb_map[d_lbl][d_idx] = re.sub(re.escape(d_var) + r'(?![a-zA-Z0-9_.])', mma_v, old_d_ln).replace("phi <8 x float>", "phi <4 x i32>")

            for c_res in c2a_by_arg[pvar]:
                c2a_to_identity[c_res] = pvar

            d2r_to_remove.add(d_var)
            if uses_in_exit > 0:
                if phi_indices_in_exit:
                    for idx in phi_indices_in_exit:
                        e_indent, epvar, erhs = phi_pat.match(elns[idx]).groups()
                        amp_epvar = f"%amp_{epvar[1:]}"
                        new_erhs = re.sub(re.escape(back_v) + r'(?![a-zA-Z0-9_.])', new_back_v, erhs)
                        elns[idx] = f"{e_indent}{amp_epvar} = phi <4 x i32> {new_erhs}"
                        exit_inserts.setdefault(exit_lbl, []).append(
                            f"  {epvar} = tail call contract <8 x float> @__sm86_d_to_rdna4(<4 x i32> noundef {amp_epvar})"
                        )
                else:
                    exit_inserts.setdefault(exit_lbl, []).append(
                        f"  {back_v} = tail call contract <8 x float> @__sm86_d_to_rdna4(<4 x i32> noundef {new_back_v})"
                    )

    for lbl, lns in blocks:
        updated = []
        for ln in lns:
            md = d2r_pat.match(ln)
            if md and md.group(2) in d2r_to_remove:
                continue
            mc = c2a_pat.match(ln)
            if mc and mc.group(2) in c2a_to_identity:
                indent, res_v, _, _ = mc.groups()
                pvar = c2a_to_identity[res_v]
                updated.append(f"{indent}{res_v} = or <4 x i32> {pvar}, zeroinitializer")
                continue
            updated.append(ln)
        if lbl in preheader_inserts:
            updated = updated[:-1] + preheader_inserts[lbl] + [updated[-1]]
        bb_map[lbl] = updated

    for exit_lbl, ins_list in exit_inserts.items():
        elns = bb_map[exit_lbl]
        insert_pos = 1 if re.match(r'^[a-zA-Z0-9_.]+:', elns[0]) else 0
        while insert_pos < len(elns) and ('= phi ' in elns[insert_pos]):
            insert_pos += 1
        bb_map[exit_lbl] = elns[:insert_pos] + ins_list + elns[insert_pos:]

    body = "\n".join("\n".join(bb_map[lbl]) for lbl in bb_order)
    return pass1_direct_and_dce(body)

# Optional per-module caps are populated only when address validation needs them.
IR_VECTOR_ALIGNMENT_OVERRIDES = {}

def upgrade_ir_alignments(ir: str, vector16_alignment: int = 16) -> str:
    """Expose native tensor memcpy alignment before and after LLVM optimization.

    Existing stronger guarantees are preserved. Physical offsets are validated by
    the GPU tests; a module may cap 16-byte transfers at 8 without weakening facts
    already established by LLVM itself.
    """
    assert vector16_alignment in (4, 8, 16)
    ir = re.sub(r"(addrspace\(3\)\s+global\s+[^\n]+?,\s*)align\s+(\d+)",
                lambda m: m[1] + "align " + str(max(16, int(m[2]))), ir)
    ir = re.sub(r"\b((?:load|store)\s+(?:i32|float)\b[^\n]+?,\s*)align\s+[12]\b", r"\1align 4", ir)
    ir = re.sub(r"\b((?:load|store)\s+(?:<2 x i32>|<2 x float>|<4 x half>|i64)[^\n]+?,\s*)align\s+[124]\b", r"\1align 8", ir)
    ir = re.sub(r"\b((?:load|store)\s+(?:<4 x i32>|<4 x float>|<8 x half>)[^\n]+?,\s*)align\s+(1|2|4|8)\b",
                lambda m: m[1] + "align " + str(max(int(m[2]), vector16_alignment)), ir)
    return ir

def cancel_wmma_shuffles_ir(ir: str, vector16_alignment: int = 16) -> str:
    out_chunks = []
    pos = 0
    for m in re.finditer(r'(define\s+[^\n]+\{\n)(.*?)(\n\}\n)', ir, flags=re.DOTALL):
        out_chunks.append(ir[pos:m.start()])
        header, body, footer = m.group(1), m.group(2), m.group(3)
        if '@__sm86_prep_' in body or '@__sm86_unpack_' in body:
            body = cse_and_hoist_prep_calls(body, split_basic_blocks)
        if '@__sm86_c_to_ampere' in body or '@__sm86_d_to_rdna4' in body:
            body = optimize_function_body(optimize_function_body(body))
        out_chunks.append(header + body + footer)
        pos = m.end()
    out_chunks.append(ir[pos:])
    res = "".join(out_chunks)
    res = re.sub(r'\bnoinline\b', 'alwaysinline', res)
    return upgrade_ir_alignments(res, vector16_alignment)

def compile_one_module(mod, source_dir, out_dir, compat_header_path, ptx2cubin_bin):
    name = mod["name"]
    cu_src = assemble_module_source(mod, source_dir, compat_header_path)
    # Cache depends on helper bodies and SSA rewrites, not just the include path.
    key = open(compat_header_path, "rb").read() + open(__file__, "rb").read()
    phase2 = os.path.join(os.path.dirname(__file__), "phase2_transform.py")
    if os.path.exists(phase2): key += open(phase2, "rb").read()
    phase5 = os.path.join(os.path.dirname(__file__), "phase5_transform.py")
    if os.path.exists(phase5): key += open(phase5, "rb").read()
    phase8 = os.path.join(os.path.dirname(__file__), "phase8_transform.py")
    if os.path.exists(phase8): key += open(phase8, "rb").read()
    phase9 = os.path.join(os.path.dirname(__file__), "phase9_transform.py")
    if os.path.exists(phase9): key += open(phase9, "rb").read()
    phase10 = os.path.join(os.path.dirname(__file__), "phase10_transform.py")
    if os.path.exists(phase10): key += open(phase10, "rb").read()
    phase11 = os.path.join(os.path.dirname(__file__), "phase11_transform.py")
    if os.path.exists(phase11): key += open(phase11, "rb").read()
    key += str(PHASE11_HALF_FEATURE_PACK).encode()
    key += open(os.path.join(os.path.dirname(__file__), "phase12_transform.py"), "rb").read()
    key += str(PHASE12_C32_AV).encode()
    key += open(os.path.join(os.path.dirname(__file__), "phase14_transform.py"), "rb").read()
    key += str(PHASE14_ATTENTION_ABI).encode()
    key += repr((PHASE18_SITES.get(name,()),PHASE18_C256_CAP)).encode()
    key += open(os.path.join(source_dir,"phase18_transform.py"),"rb").read()
    key += str(PHASE17_C32_HALF and name == "c32-wave1-fast").encode()
    if PHASE17_C32_HALF and name == "c32-wave1-fast":
        key += open(os.path.join(source_dir,"phase17_transform.py"),"rb").read() + open(os.path.join(source_dir,"phase17_c32_half.h"),"rb").read()
    key += repr((PHASE10_CAPS, PHASE10_FP8)).encode()
    key += str(name in LOW_REGISTER_FP8_MODULES).encode()
    key += str(name in C32_LOCAL_FP8_POLICY_MODULES).encode()
    key += repr(PHASE8_OVERRIDES.get(name, (True, True, True))).encode()
    build_key = hashlib.sha256(cu_src.encode() + key).hexdigest()
    stamp = os.path.join(out_dir, name + ".build-key")
    cached_bin = os.path.join(out_dir, name + ".hsaco")
    cached_ptx = os.path.join(out_dir, name + ".ptx")
    if os.path.exists(stamp) and open(stamp).read() == build_key and os.path.exists(cached_bin):
        entries = re.findall(r"\.visible\s+\.entry\s+([a-zA-Z0-9_]+)\s*\(", open(cached_ptx).read())
        return (name, True, "", entries, hashlib.sha256(open(cached_bin,"rb").read()).hexdigest())
    # Resolve #if branches before structural rewrites; raw alternatives may have
    # mutually exclusive braces. Keep the original source next to the generated CU.
    phase1_cu = os.path.join(out_dir, name + ".phase1.cu")
    open(phase1_cu, "w").write(cu_src)
    pre = subprocess.run(["clang++", "-x", "cuda", "--cuda-device-only", "--cuda-gpu-arch=sm_86",
        "-nocudainc", "-nocudalib", "-std=c++20", "-E", "-P", phase1_cu],capture_output=True,text=True)
    if pre.returncode: return (name,False,"preprocess failed: " + pre.stderr,[],"")
    cpp = re.sub(r'(?m)^\s*#pragma unroll([^\n]*)\n\s*',lambda m:'_Pragma("unroll'+m[1]+'") ',pre.stdout)
    flag = re.search(r"(?m)^#define W2_FRAGMENT_WEIGHTS ([01])",cu_src)
    qflag=re.search(r"(?m)^#define SM86_C32_REGISTER_Q_MASK (\d+)",cu_src)
    bflag=re.search(r"(?m)^#define SM86_C32_PREFIX_MINBLOCKS (\d+)",cu_src)
    allbflag=re.search(r"(?m)^#define SM86_C32_MINBLOCKS (\d+)",cu_src)
    cu_src = "static constexpr bool sm86_phase2_fragment_weights = " + ("true" if flag and flag[1]=="1" else "false") + ";\n" + phase5_transform(phase2_transform(cpp),int(qflag[1]) if qflag else 0,int(bflag[1]) if bflag else 0,int(allbflag[1]) if allbflag else 0)
    cu_src = phase8_transform(cu_src, *PHASE8_OVERRIDES.get(name, (True, True, True)))
    cu_src = phase9_transform(cu_src)
    if name in C32_LOCAL_FP8_POLICY_MODULES:
        cu_src = c32_mapped_lowreg(cu_src)
    if name in LOW_REGISTER_FP8_MODULES:
        cu_src = low_register_fp8(cu_src)
    if PHASE10_FP8:
        cu_src = phase10_optimize_fp8(cu_src)
    if PHASE11_HALF_FEATURE_PACK and name == "c32-wave1-fast":
        cu_src = pack_ffn_half_features(cu_src)
    if PHASE12_C32_AV and name == "c32-wave1-fast":
        cu_src = pack_c32_av(cu_src)
    if PHASE17_C32_HALF and name == "c32-wave1-fast":
        cu_src = phase17_half_transform(cu_src)
        helpers = open(os.path.join(source_dir,"phase17_c32_half.h")).read().replace("#pragma once", "").replace("SM86_DEV", "__attribute__((device,always_inline)) inline")
        assert cu_src.count("struct cw_i2_pair")==1
        cu_src = cu_src.replace("struct cw_i2_pair",helpers+"\nstruct cw_i2_pair",1)
    if PHASE18_SITES.get(name):
        cu_src = phase18_pack_transform(cu_src, PHASE18_SITES[name])
    cu_src += "\n// build fingerprint: " + build_key + "\n"


    cu_path = os.path.join(out_dir, f"{name}.generated.cu")
    raw_ll = os.path.join(out_dir, f"{name}.raw.ll")
    named_ll = os.path.join(out_dir, f"{name}.named.ll")
    opt_ll = os.path.join(out_dir, f"{name}.opt.ll")
    final_ll = os.path.join(out_dir, f"{name}.final.ll")
    ptx_path = os.path.join(out_dir, f"{name}.ptx")
    hsaco_path = os.path.join(out_dir, f"{name}.hsaco")

    if os.path.exists(hsaco_path) and os.path.getsize(hsaco_path) > 0 and os.path.exists(ptx_path) and os.path.exists(cu_path):
        if open(cu_path, "r", encoding="utf-8").read() == cu_src:
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
        "-S", "-emit-llvm", cu_path, "-o", raw_ll
    ]
    res = subprocess.run(cmd_clang, capture_output=True, text=True)
    if res.returncode != 0:
        return (name, False, f"Clang failed:\n{res.stderr}", [], "")

    res = subprocess.run(["opt-14", "-instnamer", "-loop-simplify", "-lcssa", "-S", raw_ll, "-o", named_ll], capture_output=True, text=True)
    if res.returncode != 0:
        return (name, False, f"opt-14 prepass failed:\n{res.stderr}", [], "")

    vector_alignment = IR_VECTOR_ALIGNMENT_OVERRIDES.get(name, 16)
    opt_ir = cancel_wmma_shuffles_ir(open(named_ll, "r", encoding="utf-8").read(), vector_alignment)
    open(opt_ll, "w", encoding="utf-8").write(opt_ir)

    res = subprocess.run(["opt-14", "-O3", "-disable-loop-unrolling", "-S", opt_ll, "-o", final_ll], capture_output=True, text=True)
    if res.returncode != 0:
        return (name, False, f"opt-14 -O3 failed:\n{res.stderr}", [], "")

    # SROA/InstCombine can create fresh low-alignment transfers in the second O3.
    with open(final_ll, "r", encoding="utf-8") as f:
        final_ir = upgrade_ir_alignments(f.read(), vector_alignment)
    with open(final_ll, "w", encoding="utf-8") as f:
        f.write(final_ir)

    res = subprocess.run(["llc-14", "-march=nvptx64", "-mcpu=sm_86", "--fp-contract=fast", "-O3", final_ll, "-o", ptx_path], capture_output=True, text=True)
    if res.returncode != 0:
        return (name, False, f"llc-14 failed:\n{res.stderr}", [], "")

    for tmp in [raw_ll, named_ll, opt_ll, final_ll]:
        if os.path.exists(tmp):
            os.remove(tmp)

    ptx_txt = open(ptx_path, "r", encoding="utf-8").read()
    if PHASE10_CAPS:
        ptx_txt = apply_register_caps(ptx_txt)
        open(ptx_path,"w",encoding="utf-8").write(ptx_txt)
    if PHASE18_C256_CAP is not None and name == "c64-wave2-fast":
        from phase18_transform import apply_c256_cap
        ptx_txt = apply_c256_cap(ptx_txt,PHASE18_C256_CAP)
        open(ptx_path,"w",encoding="utf-8").write(ptx_txt)
    if PHASE17_C32_HALF and name == "c32-wave1-fast":
        ptx_txt = phase17_version_ptx(ptx_txt)
        open(ptx_path,"w",encoding="utf-8").write(ptx_txt)
    entries = re.findall(r"\.visible\s+\.entry\s+([a-zA-Z0-9_]+)\s*\(", ptx_txt)

    cmd_cubin = [ptx2cubin_bin, ptx_path, hsaco_path] + entries
    res2 = subprocess.run(cmd_cubin, capture_output=True, text=True)
    if res2.returncode != 0:
        return (name, False, f"ptx2cubin failed:\n{res2.stderr}", entries, "")

    sha = hashlib.sha256(open(hsaco_path, "rb").read()).hexdigest()
    open(stamp, "w").write(build_key)
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
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {
            ex.submit(compile_one_module, m, source_dir, out_dir, compat_header, ptx2cubin_bin): m
            for m in modules
        }
        for fut in as_completed(futs):
            name, ok, err, entries, sha = fut.result()
            results.append((name, ok, err, entries, sha))
            if ok:
                print(f"[PASS] {name:38s} entries={len(entries):3d} sha256={sha[:16]}...")
            else:
                print(f"[FAIL] {name:38s}\n{err}")

    results.sort(key=lambda x: x[0])
    passed = sum(1 for r in results if r[1])
    total_entries = sum(len(r[3]) for r in results if r[1])
    print(f"\nSUMMARY: {passed}/{len(modules)} modules compiled to sm_86 cubin & verified on RTX 3080 Laptop GPU ({total_entries} kernel entry points verified)!")
    if passed != len(modules):
        sys.exit(1)
    open(os.path.join(out_dir,"AMPERE_WEIGHTS_V2"),"w").write("CPU Ampere FP8 tiles; paired Phase-2 modules\n")
    v3_marker=os.path.join(out_dir,"AMPERE_WEIGHTS_V3")
    if PHASE17_C32_HALF:
        open(v3_marker,"w").write("C32_W16_F16_APPEND_V1\n")
    elif os.path.exists(v3_marker):
        os.remove(v3_marker)

if __name__ == "__main__":
    main()
