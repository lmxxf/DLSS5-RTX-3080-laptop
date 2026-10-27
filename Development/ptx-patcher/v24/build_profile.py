from pathlib import Path
import subprocess,json
p=Path(__file__).resolve().parent;src=(p.parent/'bench_nvngx.dll.cpp').read_text();src=src.replace('static void ck(', '#include "profile_hook.h"\n\nstatic void ck(',1);src=src.replace('    // Load _nvngx.dll', '    ID3D12Resource* prof_rb = make_buffer(4096*8, D3D12_HEAP_TYPE_READBACK);\n    profile_init(qheap,prof_rb,ts_freq);\n    // Load _nvngx.dll',1);src=src.replace('        volatile auto er = snip_eval', '        profile_frame_begin(i);\n        volatile auto er = snip_eval',1);src=src.replace('        l->Close();\n        q->ExecuteCommandLists', '        profile_resolve(l);\n        l->Close();\n        q->ExecuteCommandLists');src=src.replace('    qhd.Count = 2;', '    qhd.Count = 4096;');src=src.replace('        double wall_ms =', '        profile_frame_end();\n        double wall_ms =',1)
out=p/'artifacts/profile_runner.cpp';out.parent.mkdir(exist_ok=True);out.write_text(src);mh=p/'artifacts/minhook'
if not mh.exists():
 subprocess.run(['git','clone','https://github.com/TsudaKageyu/minhook.git',str(mh)],check=True)
 subprocess.run(['git','-C',str(mh),'checkout','8af6b4acae5a9388fd742b56fa79ece89d96f823'],check=True)
files=['buffer.c','hook.c','trampoline.c','hde/hde64.c'];objs=[]
for f in files:
 obj=p/'artifacts'/Path(f).with_suffix('.o').name;subprocess.run(['x86_64-w64-mingw32-gcc','-O2','-c',str(mh/'src'/f),'-o',str(obj)],check=True);objs.append(str(obj))
exe=Path('/mnt/c/DLSS5-5090-dll/nvngx.dll_runner/bench_profile.exe');subprocess.run(['x86_64-w64-mingw32-g++','-O2','-std=c++17','-municode','-static',str(out),'-I'+str(p),'-I'+str(mh/'include'),*objs,'-ld3d12','-ldxgi','-ldxguid','-o',str(exe)],check=True)
(p/'profile-build.json').write_text(json.dumps({'minhook_commit':subprocess.check_output(['git','-C',str(mh),'rev-parse','HEAD'],text=True).strip(),'exe':str(exe)},indent=2)+'\n');print(exe)
