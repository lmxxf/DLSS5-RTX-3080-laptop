from pathlib import Path
import sys,concurrent.futures,importlib.util
repo=Path(__file__).resolve().parents[1];sys.path.insert(0,str(repo))
spec=importlib.util.spec_from_file_location('safe_build',repo/'build_sm86_dlls.py');b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b)
def work(task):return b.worker_compile_fatbin(task)
if __name__=='__main__':
 data=bytearray(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes());b.dp.strip_authenticode(data);locs=b.dp.find_fatbins(data)
 out=bytearray(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_fast.dll').read_bytes());oversize=[]
 tasks=[(i,bytes(data[l.offset:l.offset+l.size]),True,True) for i,l in enumerate(locs)]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  futures=[pool.submit(work,t) for t in tasks]
  for f in concurrent.futures.as_completed(futures):
   i,fb,msg=f.result();l=locs[i];print(i,msg,flush=True)
   if len(fb)>l.size:oversize.append(i)
   else:out[l.offset:l.offset+l.size]=fb+bytes(l.size-len(fb))
 print('oversize',sorted(oversize),flush=True)
 if not oversize:
  b.fast_update_pe_checksum(out);Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_safe.dll').write_bytes(out)
