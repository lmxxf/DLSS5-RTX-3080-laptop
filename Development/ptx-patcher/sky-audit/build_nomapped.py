"""Diagnostic build only; never replaces the installed fast DLL."""
from pathlib import Path
import sys, types, concurrent.futures
repo=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(repo))
m=types.ModuleType('sky_build');sys.modules[m.__name__]=m
m.__file__=str(repo/'build_sm86_dlls.py')
s=(repo/'build_sm86_dlls.py').read_text().replace('/tmp/dlssnr-310-9-16-sm86',str(repo))
exec(compile(s,str(repo/'build_sm86_dlls.py'),'exec'),m.__dict__)
m.dp.fp8_pack_sources=lambda text: {}
def work(task):
 return m.worker_compile_fatbin(task)
if __name__=='__main__':
 data=bytearray(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes())
 m.dp.strip_authenticode(data);locs=m.dp.find_fatbins(data)
 out=bytearray(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_fast.dll').read_bytes())
 tasks=[(i,bytes(data[l.offset:l.offset+l.size]),True) for i,l in enumerate(locs[:7])]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  for i,fb,msg in pool.map(work,tasks):
   l=locs[i];out[l.offset:l.offset+l.size]=fb+bytes(l.size-len(fb));print(i,msg,flush=True)
 m.fast_update_pe_checksum(out)
 Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_nomapped.dll').write_bytes(out)
