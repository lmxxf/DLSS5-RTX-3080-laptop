from pathlib import Path
import sys,struct,json,hashlib,ctypes as c,subprocess,re
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import dlssnr_patcher as d
root=Path('/mnt/c/DLSS5-5090-dll');z=c.CDLL('libzstd.so.1');z.ZSTD_decompress.restype=c.c_size_t;rows={};tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump'
rows['baseline']=json.loads((p.parent/'v23/resources.json').read_text())['decode']
for tag in ['a','bias','b','c','abc']:
 rows[tag]={}
 for i in range(15):
  path=p/f'artifacts/{tag}/fatbin{i:02d}.cubin';res=subprocess.run([tool,'-res-usage',str(path)],capture_output=True,text=True,check=True).stdout;sass=subprocess.run([tool,'-sass',str(path)],capture_output=True,text=True,check=True).stdout;kernels={}
  for ch in sass.split('Function : ')[1:]:
   name=ch.splitlines()[0].strip();kernels[name]={k:len(re.findall(r'\b'+k+r'\b',ch)) for k in ['SHFL','HMMA','LDL','STL','LDGSTS','LDGDEPBAR','DEPBAR']}
  for m in re.finditer(r'Function\s+(\S+):\s*(.*)',res):
   if m[1] in kernels:kernels[m[1]]['resources']={a:int(b) for a,b in re.findall(r'(REG|STACK|LOCAL|SHARED):(\d+)',m[2])}
  assert kernels
  rows[tag][str(i)]={'kernels':kernels,'totals':{k:sum(r[k] for r in kernels.values()) for k in ['SHFL','HMMA','LDL','STL','LDGSTS','LDGDEPBAR','DEPBAR']},'max_stack':max(r.get('resources',{}).get('STACK',0) for r in kernels.values()),'cubin_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  print(tag,i,'STACK',rows[tag][str(i)]['max_stack'],'LDL/STL',rows[tag][str(i)]['totals']['LDL'],rows[tag][str(i)]['totals']['STL'],flush=True)
(p/'resources.json').write_text(json.dumps(rows,indent=2)+'\n')
