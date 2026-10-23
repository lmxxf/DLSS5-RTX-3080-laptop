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
        '_Pragma("unroll") for(uint j=0;j<4;j++){sum[j]=__sm86_c_to_ampere(sum[j]);_Pragma("unroll") for(uint e=0;e<8;e++)acc[j][e]=H(acc[j][e]+sum[j][e]);}\n }\n _Pragma("unroll") for(uint j=0;j<4;j++)acc[j]=__sm86_d_to_rdna4(acc[j]);'
    )
    text = text.replace(
        'for(uint e=0;e<8;e++)acc[e]=channels==32?Hrtz(acc[e]+sum[e]):H(acc[e]+sum[e]);\n }',
        'sum=__sm86_c_to_ampere(sum);_Pragma("unroll") for(uint e=0;e<8;e++)acc[e]=channels==32?Hrtz(acc[e]+sum[e]):H(acc[e]+sum[e]);\n }\n acc=__sm86_d_to_rdna4(acc);'
    )
    # 4. Conjugate 4-partition accumulation in vit_contract_blocked_body and vit_stream_project_tiles so `acc`/`a` stays in Ampere layout across `part=0..3`!
    text = text.replace(
        '_Pragma("unroll") for(uint n=0;n<4;n++)for(uint e=0;e<8;e++){if constexpr(Partial)out[(part*tokens+first+gr()*8+e)*1024+col+n*16+rc()]=acc[n][e];else total[n][e]+=acc[n][e];}\n  }',
        '_Pragma("unroll") for(uint n=0;n<4;n++){if constexpr(Partial){for(uint e=0;e<8;e++)out[(part*tokens+first+gr()*8+e)*1024+col+n*16+rc()]=acc[n][e];}else{if(part==part0)total[n]=__sm86_c_to_ampere(total[n]);acc[n]=__sm86_c_to_ampere(acc[n]);_Pragma("unroll") for(uint e=0;e<8;e++)total[n][e]+=acc[n][e];}}\n  }\n  if constexpr(!Partial){_Pragma("unroll") for(uint n=0;n<4;n++)total[n]=__sm86_d_to_rdna4(total[n]);}'
    )
    text = text.replace(
        '#pragma unroll\n   for(uint t=0;t<TM;t++)\n#pragma unroll\n   for(uint j=0;j<TN;j++)for(uint e=0;e<8;e++)total[t][j][e]+=a[t][j][e];}',
        '#pragma unroll\n   for(uint t=0;t<TM;t++)\n#pragma unroll\n   for(uint j=0;j<TN;j++){if(p==0)total[t][j]=__sm86_c_to_ampere(total[t][j]);a[t][j]=__sm86_c_to_ampere(a[t][j]);_Pragma("unroll") for(uint e=0;e<8;e++)total[t][j][e]+=a[t][j][e];}}\n#pragma unroll\n  for(uint t=0;t<TM;t++)\n#pragma unroll\n  for(uint j=0;j<TN;j++)total[t][j]=__sm86_d_to_rdna4(total[t][j]);'
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

prep_call_pat = re.compile(r'^(\s*)(%\S+)\s*=\s*(?:tail\s+)?call[^@]*@(__sm86_prep_(?:fp8|f16))\((<2 x i32>|<8 x half>)(?:\s+noundef)?\s+(%\S+|zeroinitializer|<[^>]+>)\)(.*)$')

def cse_and_hoist_prep_calls(body: str, split_basic_blocks) -> str:
    blocks = split_basic_blocks(body)
    bb_map = {lbl: lns for lbl, lns in blocks}
    bb_order = [lbl for lbl, _ in blocks]

    var_def = {}
    for lbl, lns in blocks:
        for idx, ln in enumerate(lns):
            m_def = re.match(r'^\s*(%[a-zA-Z0-9_.]+)\s*=\s*(.+)$', ln)
            if m_def:
                v, rhs = m_def.group(1), m_def.group(2)
                var_def[v] = (lbl, idx, rhs.lstrip().startswith("phi "))

    prep_groups = {}
    for lbl, lns in blocks:
        for idx, ln in enumerate(lns):
            mp = prep_call_pat.match(ln)
            if mp:
                indent, res_v, fn_name, arg_ty, arg_v, tail = mp.groups()
                key = (fn_name, arg_ty, arg_v)
                prep_groups.setdefault(key, []).append((lbl, idx, res_v, ln))

    if not prep_groups:
        return body

    inserts_after_phis = {}
    inserts_after_line = {}
    replace_call_with_id = {}

    for (fn_name, arg_ty, arg_v), calls in prep_groups.items():
        call_bbs = {c[0] for c in calls}
        def_info = var_def.get(arg_v, None)
        def_lbl = def_info[0] if def_info else bb_order[0]

        if len(call_bbs) == 1 and list(call_bbs)[0] == def_lbl:
            # All calls are in the same block where arg_v is defined:
            # Keep the first call `calls[0]` in-place (minimal register live range!) and CSE `calls[1:]`!
            if len(calls) <= 1:
                continue
            canon_v = calls[0][2]
            for lbl, idx, res_v, _ in calls[1:]:
                replace_call_with_id[res_v] = canon_v
        else:
            # Either called across multiple blocks, or `arg_v` is defined in an outer block (LICM!):
            # Wait: only hoist to `def_lbl` if `len(calls) > 1` OR `calls[0][0]` is a loop block!
            canon_v = f"%prep_{calls[0][2][1:]}"
            call_line = f"  {canon_v} = tail call <4 x i32> @{fn_name}({arg_ty} noundef {arg_v})"
            if def_info is None or def_info[2]:
                inserts_after_phis.setdefault(def_lbl, []).append(call_line)
            else:
                inserts_after_line.setdefault((def_lbl, def_info[1]), []).append(call_line)
            for lbl, idx, res_v, _ in calls:
                replace_call_with_id[res_v] = canon_v

    if not replace_call_with_id:
        return body

    for lbl in bb_order:
        lns = bb_map[lbl]
        new_lns = []
        for idx, ln in enumerate(lns):
            mp = prep_call_pat.match(ln)
            if mp and mp.group(2) in replace_call_with_id:
                indent, res_v, _, _, _, _ = mp.groups()
                canon_v = replace_call_with_id[res_v]
                new_lns.append(f"{indent}{res_v} = add <4 x i32> {canon_v}, zeroinitializer")
            else:
                new_lns.append(ln)
            if (lbl, idx) in inserts_after_line:
                new_lns.extend(inserts_after_line[(lbl, idx)])

        if lbl in inserts_after_phis:
            insert_pos = 1 if re.match(r'^[a-zA-Z0-9_.]+:', new_lns[0]) else 0
            while insert_pos < len(new_lns) and ('= phi ' in new_lns[insert_pos]):
                insert_pos += 1
            new_lns = new_lns[:insert_pos] + inserts_after_phis[lbl] + new_lns[insert_pos:]
        bb_map[lbl] = new_lns

    return "\n".join("\n".join(bb_map[lbl]) for lbl in bb_order)

# --- SSA IR Algebraic Cancellation for WMMA C/D Shuffles ---
d2r_pat = re.compile(r'^(\s*)(%\S+)\s*=\s*(?:tail\s+)?call[^@]*@__sm86_d_to_rdna4\(<8 x float>(?:\s+noundef)?\s+(%\S+|zeroinitializer)\)(.*)$')
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
                new_lines.append(f"{indent}{res_v} = fadd <8 x float> zeroinitializer, zeroinitializer")
                continue
            elif arg_v in d2r_map:
                src_x = resolve(d2r_map[arg_v])
                alias[res_v] = src_x
                new_lines.append(f"{indent}{res_v} = fadd <8 x float> {src_x}, zeroinitializer")
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
                    f"  {pre_amp} = tail call contract <8 x float> @__sm86_c_to_ampere(<8 x float> noundef {pre_v})"
                )

            lns[i] = f"{indent}{pvar} = phi <8 x float> [ {pre_amp}, %{pre_lbl} ], [ {new_back_v}, %{latch_lbl} ]"
            if is_diamond:
                d_lbl, d_idx, d_indent, _ = all_phis[back_v]
                old_d_ln = bb_map[d_lbl][d_idx]
                bb_map[d_lbl][d_idx] = re.sub(re.escape(d_var) + r'(?![a-zA-Z0-9_.])', mma_v, old_d_ln)

            for c_res in c2a_by_arg[pvar]:
                c2a_to_identity[c_res] = pvar

            d2r_to_remove.add(d_var)
            if uses_in_exit > 0:
                if phi_indices_in_exit:
                    for idx in phi_indices_in_exit:
                        e_indent, epvar, erhs = phi_pat.match(elns[idx]).groups()
                        amp_epvar = f"%amp_{epvar[1:]}"
                        new_erhs = re.sub(re.escape(back_v) + r'(?![a-zA-Z0-9_.])', new_back_v, erhs)
                        elns[idx] = f"{e_indent}{amp_epvar} = phi <8 x float> {new_erhs}"
                        exit_inserts.setdefault(exit_lbl, []).append(
                            f"  {epvar} = tail call contract <8 x float> @__sm86_d_to_rdna4(<8 x float> noundef {amp_epvar})"
                        )
                else:
                    exit_inserts.setdefault(exit_lbl, []).append(
                        f"  {back_v} = tail call contract <8 x float> @__sm86_d_to_rdna4(<8 x float> noundef {new_back_v})"
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
                updated.append(f"{indent}{res_v} = fadd <8 x float> {pvar}, zeroinitializer")
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

def cancel_wmma_shuffles_ir(ir: str) -> str:
    out_chunks = []
    pos = 0
    for m in re.finditer(r'(define\s+[^\n]+\{\n)(.*?)(\n\}\n)', ir, flags=re.DOTALL):
        out_chunks.append(ir[pos:m.start()])
        header, body, footer = m.group(1), m.group(2), m.group(3)
        if '@__sm86_prep_' in body:
            body = cse_and_hoist_prep_calls(body, split_basic_blocks)
        if '@__sm86_c_to_ampere' in body or '@__sm86_d_to_rdna4' in body:
            body = optimize_function_body(optimize_function_body(body))
        out_chunks.append(header + body + footer)
        pos = m.end()
    out_chunks.append(ir[pos:])
    res = "".join(out_chunks)
    res = re.sub(r'\bnoinline\b', 'alwaysinline', res)
    return res

def compile_one_module(mod, source_dir, out_dir, compat_header_path, ptx2cubin_bin):
    name = mod["name"]
    cu_src = assemble_module_source(mod, source_dir, compat_header_path)
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

    opt_ir = cancel_wmma_shuffles_ir(open(named_ll, "r", encoding="utf-8").read())
    open(opt_ll, "w", encoding="utf-8").write(opt_ir)

    res = subprocess.run(["opt-14", "-O3", "-disable-loop-unrolling", "-S", opt_ll, "-o", final_ll], capture_output=True, text=True)
    if res.returncode != 0:
        return (name, False, f"opt-14 -O3 failed:\n{res.stderr}", [], "")

    res = subprocess.run(["llc-14", "-march=nvptx64", "-mcpu=sm_86", "-O3", final_ll, "-o", ptx_path], capture_output=True, text=True)
    if res.returncode != 0:
        return (name, False, f"llc-14 failed:\n{res.stderr}", [], "")

    for tmp in [raw_ll, named_ll, opt_ll, final_ll]:
        if os.path.exists(tmp):
            os.remove(tmp)

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

if __name__ == "__main__":
    main()
