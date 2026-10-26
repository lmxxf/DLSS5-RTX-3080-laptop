from pathlib import Path
import re,json,subprocess,hashlib,shutil
p=Path(__file__).resolve().parent;r=p.parent;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';names=['c32_wave1_prefix_b8d_w16','c32_wave1_post_b8_w16','c32_wave1_mapped_b8_w16','c32_wave1_finish_b8_w16','c32_wave1_finish_dcrop_b8d_w16','c32_wave1_up_b8_w16'];rows={}
for tag,base in [('baseline',r/'phase16/artifacts/tail/modules'),('candidate',p/'artifacts/candidate/modules')]:
 f=base/'c32-wave1-fast.hsaco';ptx=(base/'c32-wave1-fast.ptx').read_text();res=subprocess.run([tool,'-res-usage',str(f)],capture_output=True,text=True,check=True).stdout;(p/(tag+'-resources.txt')).write_text(res);sass=subprocess.run([tool,'-sass',str(f)],capture_output=True,text=True,check=True).stdout
 rows[tag]={'module_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'sass_sha256':hashlib.sha256(sass.encode()).hexdigest(),'kernels':{}}
 for n in names:
  physical=('v3_' if tag=='candidate' else '')+n;match=re.search(r'\.visible\s+\.entry\s+'+physical+r'\(',ptx);a=ptx.index('{',match.start());z=ptx.index('\n}',a);body=ptx[a:z];chunk=sass.split('Function : '+physical+'\n')[1].split('Function : ')[0]
  rows[tag]['kernels'][n]={'ptx_ld_global_nc_v4_u32':len(re.findall(r'ld\.global\.nc\.v4\.u32',body)),'SASS_LDG128':len(re.findall(r'\bLDG(?:\.\w+)*\.128\b',chunk)),'SASS_HMUL2':len(re.findall(r'\bHMUL2\b',chunk)),'SASS_PRMT':len(re.findall(r'\bPRMT\b',chunk)),'SASS_SHFL':len(re.findall(r'\bSHFL\b',chunk)),'SASS_LDL':len(re.findall(r'\bLDL\b',chunk)),'SASS_STL':len(re.findall(r'\bSTL\b',chunk))}
(p/'isa.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'counter-availability.json').write_text(json.dumps({'ncu':shutil.which('ncu'),'cache_counter_measurements':'not collected; no L1/L2 hit-rate or DRAM-traffic claims; static code is not dynamic instruction count'},indent=2)+'\n')
print(json.dumps(rows,indent=2))
