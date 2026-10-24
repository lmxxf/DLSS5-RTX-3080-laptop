from pathlib import Path
import subprocess
root=Path('/mnt/c/DLSS5-5090-dll')
args=[str(root/'nvngx.dll_runner/bench_sky.exe'),r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll',r'C:\DLSS5-5090-dll\nvngx_dlssnr_sm86_nomapped.dll','1280','720','2','2','3',r'C:\DLSS5-5090-dll\sky_nomapped.rgb32','sky']
with (Path(__file__).parent/'nomapped-run.log').open('w') as f:
 subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)
