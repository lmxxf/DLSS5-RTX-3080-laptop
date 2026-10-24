#!/usr/bin/env python3
"""Static instruction/resource summaries for kernels in both current traces.

Unique active kernel bodies are summed once per family, not multiplied by
launches/windows/loop iterations. These are not executed instruction counts.
"""
import argparse,collections,csv,importlib.util,json
from pathlib import Path

p=argparse.ArgumentParser(__doc__);p.add_argument('--comparison',action='append',required=True,help='L20=/path/to/comparison');p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('stats',repo/'Development/results/aco-isa-20260927/tools/isa_stats.py');stats=importlib.util.module_from_spec(spec);spec.loader.exec_module(stats)
mods={'c32_wave1':'c32-wave1','c64_wave2':'c64-wave2','c512_m32_deep':'c512-m32-deep','c512_m32_mh':'c512-m32-mh','deep':'deep_reference','deep_fast':'deep_fast-packed','mh_fast':'multihead-fast-padded-wave-packed','vit_stream':'vit-stream','mh':'multihead-reference'}
active={}
for height in (900,1080):
    rows=list(csv.reader((repo/f'Development/results/kernel-map-20260929/topology-{height}.csv').open()))
    for _,module,kernel,groups,_,threads in rows:
        key=mods[module]+'.hsaco',kernel
        r=active.setdefault(key,dict(calls900=0,calls1080=0))
        r['calls'+str(height)]+=1

def family(k):
    for c in (32,64,128,256):
        if k.startswith(f'c{c}_'):return f'C{c}'
    if k.startswith('mh_ffn_fused_c256'):return 'C256'
    if k.startswith('vit_'):return 'ViT'
    if k.startswith(('split_','c512_','mh_attention_project','mh_shift_pack')):return 'C512'
    return 'Boundary/head'

classes=['VALU','VOPD','WMMA','VMEM','SALU','WAIT','DS','SMEM']
meta=['vgpr_count','sgpr_count','group_segment_fixed_size','private_segment_fixed_size','vgpr_spill_count','sgpr_spill_count']
all_rows=[];summary=[]
for entry in a.comparison:
    version,path=entry.split('=',1);d=json.loads((Path(path)/'kernel-details.json').read_text())
    local=[]
    for arch in ['gfx1201','gfx1200']:
        for (module,k),calls in sorted(active.items()):
            item=d[arch+'/'+module];row=dict(version=version,arch=arch,family=family(k),module=module,kernel=k,**calls)
            for side in ['baseline','candidate']:
                v=item[side][k];c=collections.Counter()
                for op,n in v['opcodes'].items():c[stats.classify(op) or 'other']+=n
                assert not c['other'],(module,k,c)
                for cls in classes:row[side+'_'+cls]=c[cls]
                row[side+'_instructions']=v['instructions']
                for key in meta:row[side+'_'+key]=v['metadata'].get('.'+key,0)
                ops=v['opcodes']
                row[side+'_maxnum']=sum(n for op,n in ops.items() if op.startswith('v_max_num'))
                row[side+'_med3']=sum(n for op,n in ops.items() if op.startswith('v_med3'))
                row[side+'_half_conversions']=sum(n for op,n in ops.items() if op.startswith(('v_cvt_f32_f16','v_cvt_f16_f32','v_cvt_pkrtz_f16','v_cvt_pk_rtz_f16')))
                row[side+'_div_helpers']=sum(n for op,n in ops.items() if op.startswith(('v_div_scale','v_div_fmas','v_div_fixup')))
                row[side+'_setreg_writes']=sum(n for op,n in ops.items() if op.startswith('s_setreg'))
            local.append(row)
        for fam in sorted({family(k) for m,k in active}):
            subset=[r for r in local if r['arch']==arch and r['family']==fam]
            row=dict(version=version,arch=arch,family=fam,kernels=len(subset),calls900=sum(r['calls900'] for r in subset),calls1080=sum(r['calls1080'] for r in subset))
            for side in ['baseline','candidate']:
                for cls in classes+['instructions','maxnum','med3','half_conversions','div_helpers','setreg_writes']:
                    row[side+'_'+cls]=sum(r[side+'_'+cls] for r in subset)
                for key in meta:
                    row[side+'_'+key+'_min']=min(r[side+'_'+key] for r in subset)
                    row[side+'_'+key+'_max']=max(r[side+'_'+key] for r in subset)
            summary.append(row)
    all_rows+=local
for name,rows in [('active-kernels.csv',all_rows),('family-static.csv',summary)]:
    with (a.out/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
print(len(active),'unique active kernel/module pairs; summaries',len(summary))
