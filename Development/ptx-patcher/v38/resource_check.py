from pathlib import Path
import json
p=Path(__file__).resolve().parent;r=json.loads((p/'resources.json').read_text());qkv='cc_split_swin_16h_qkv_512_chained_fp8';pool='cc_split_swin_16h_proj_pool_512_chained_fp8';out={}
for n in ['zero_const_fb26','zero_const_fb456','pack4_pure36','pack4_fb26_clean','fb3_inp_up_fast','fb3_inp_up_exact','async_pool_only']:
 out[n]={'active_nonNOP_delta':sum(v['INSN_NONOP']-r['baseline'][k]['INSN_NONOP'] for k,v in r[n].items()),'resource_changes':{k:{f:[r['baseline'][k][f],v[f]] for f in ['REG','STACK','STL','LDL','SHARED','PRMT','INSN_NONOP','resident_CTA_per_SM'] if v[f]!=r['baseline'][k][f]} for k,v in r[n].items() if v!=r['baseline'][k]}}
for n in ['zero_const_fb26','zero_const_fb456']:
 assert all(v['STACK']<=r['baseline'][k]['STACK'] for k,v in r[n].items())
for n in ['zero_const_fb26','zero_const_fb456']:assert [r[n][qkv][f] for f in ['STL','LDL']]==[33,22]
assert r['async_pool_only'][pool]['REG']==208 and r['async_pool_only'][pool]['INSN_NONOP']==6042
(p/'resource-validation.json').write_text(json.dumps({'passed':True,'single_factor_deltas':out,'static_counts_are_not_dynamic_timing':True},indent=2)+'\n');print('resource checks PASS')
