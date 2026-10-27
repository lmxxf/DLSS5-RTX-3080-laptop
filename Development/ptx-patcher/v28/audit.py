from pathlib import Path
import json,re,math,hashlib,subprocess
p=Path(__file__).resolve().parent
read=lambda f:json.loads(f.read_text())
report=p.parents[1]/'doc/性能评估20261028-0335.md';text=report.read_text();profiles=read(p.parent/'v27/profile-summary.json');checks=[]
for line in text.splitlines():
 if not line.startswith('| **720p') and not line.startswith('| **1080p'):continue
 if '(ms)' in line or not ('FB' in line or '核区间合计' in line):continue
 w='1280' if '720p' in line else '1920';fb=re.search(r'FB(\d\d)',line)
 keys=['6','13','14'] if 'FB06+' in line else ([str(int(fb[1]))] if fb else [str(i) for i in [0,1,2,3,4,5,6,13,14]])
 exp=[sum(profiles[w][k][v] for k in keys) for v in ['v22','v24','v26']];exp +=[exp[0]-exp[2],exp[1]-exp[2]]
 cells=line.split('|')[3:8];nums=[float(re.search(r'`([+-]?[\d.]+)`',c)[1]) for c in cells];err=[abs(a-b) for a,b in zip(nums,exp)];checks.append({'width':w,'FBs':keys,'reported':nums,'exact':exp,'max_rounding_error':max(err),'within_rounding':max(err)<0.00000051})
assert len(checks)==16
base=read(p/'occupancy-baseline.json');caps=read(p/'occupancy-caps.json');candidates=read(p/'candidates.json');oldprof=read(p.parent/'v23/profile.json');targets=[]
for tag,item in candidates.items():
 for n,cap in item['caps'].items():
  b=base['cases'][f"baseline-fb{item['FB']}"]['kernels'][n];a=caps['cases'][f"{tag}-fb{item['FB']}"]['kernels'][n];launches={}
  for w,prof in oldprof.items():
   ls=[r for r in prof['calls'] if r['name']==n];assert all(r['dynamic_shared']==0 for r in ls)
   launches[w]={'calls':len(ls),'CTA_grids':sorted({math.prod(r['grid']) for r in ls}),'dynamic_shared':sorted({r['dynamic_shared'] for r in ls}),'ideal_capacity_waves_before':sorted({math.ceil(math.prod(r['grid'])/(48*b['resident_CTA_per_SM'])) for r in ls}),'ideal_capacity_waves_after':sorted({math.ceil(math.prod(r['grid'])/(48*a['resident_CTA_per_SM'])) for r in ls})}
  targets.append({'case':tag,'kernel':n,'cap':cap,'baseline':b,'candidate':a,'launches':launches})
# SASS counts per kernel; exact unchanged instruction bodies for protected entries.
tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump'
def sass(path):
 raw=subprocess.check_output([tool,'-sass',str(path)],text=True);out={}
 for part in re.split(r'Function : ',raw)[1:]:
  name=part.splitlines()[0].strip();inst=re.findall(r'/\*[0-9a-f]+\*/\s+([^\n]*?);',part);out[name]={'instruction_count':len(inst),'LDL':sum(bool(re.search(r'\bLDL\b',s)) for s in inst),'STL':sum(bool(re.search(r'\bSTL\b',s)) for s in inst),'instruction_sha256':hashlib.sha256('\n'.join(inst).encode()).hexdigest()}
 return out
ss={};bs={fb:sass(p/f'artifacts/baseline/fatbin{fb:02}.cubin') for fb in (0,4,5)}
for tag,item in candidates.items():
 fb=item['FB'];a=sass(p/f'artifacts/{tag}/fatbin{fb:02}.cubin');protected=['cc_split_swin_16h_qkv_512_chained_fp8','cc_split_swin_16h_ffwd_512_chained_fp8'] if fb==4 else (['cc_vit_1d_attention_chained_fp8','cc_vit_1d_projection_chained_fp8'] if fb==5 else ['cc_tinlayout_fused_post_block_swin_1h_32_fp8']);assert all(a[n]==bs[fb][n] for n in protected);ss[tag]={'targets':{n:{'before':bs[fb][n],'after':a[n]} for n in item['caps']},'protected_SASS_identical':protected}
(p/'sass-audit.json').write_text(json.dumps(ss,indent=2)+'\n')
r={'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),'profile_table_rows_checked':checks,'V27_performance':read(p.parent/'v27/selected.json')['performance'],'all_v23_launches_dynamic_shared_zero':all(r['dynamic_shared']==0 for d in oldprof.values() for r in d['calls']),'target_checks':targets,'scope':'Occupancy API maximum, not achieved concurrency; capacity waves are independent homogeneous grid idealization, not chained scheduler simulation.'}
records=[]
for f in (p.parent/'v27').glob('profile-*-v26-*.csv'):
 lines=[s.split(',') for s in f.read_text().splitlines() if s.startswith('KERNEL,')];vals=sorted({int(s[11]) for s in lines});assert vals==[0];records.append({'path':str(f),'kernel_rows':len(lines),'dynamic_shared_values':vals})
r['fresh_V26_capture_dynamic_shared_check']=records
r['historical_spill_scope']='V24 ABC whole-FB controls, not V27; several lightweight kernels spilled as well'
(p/'audit.json').write_text(json.dumps(r,indent=2)+'\n');(report.with_name(report.stem+'-审核核验.json')).write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n');print('CHECKED 16 timing rows; exceptions',sum(not r['within_rounding'] for r in checks),'target occupancy/grid and protected SASS passed')
lines=['# V2.8 resource controls','','|Case|Kernel|REG before→after|STACK before→after B|Warps/SM before→after|LDL/STL after|','|---|---|---:|---:|---:|---:|']
for t in targets:
 a=t['candidate'];b=t['baseline'];s=ss[t['case']]['targets'][t['kernel']]['after'];lines.append(f"|{t['case']}|{t['kernel']}|{b['REG']}→{a['REG']}|{b['STACK']}→{a['STACK']}|{b['resident_warps_per_SM']}→{a['resident_warps_per_SM']}|{s['LDL']}/{s['STL']}|")
(p/'resources.md').write_text('\n'.join(lines)+'\n')
