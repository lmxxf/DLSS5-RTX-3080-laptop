$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\llvm-fork-20260929'
if(Get-Process|Where-Object{$_.ProcessName -match 'Shipping|^re9$|^Onimusha|^SandFall|^benchmark|^rt_bench|^jobbench|^rtc_compile'}){throw 'GPU lab busy'}
$env:AMD_COMGR_EMIT_VERBOSE_LOGS='1'
$env:AMD_COMGR_REDIRECT_LOGS="$root\comgr-verbose.log"
$env:AMD_COMGR_SAVE_TEMPS='1'
$env:AMD_COMGR_CACHE='0'
[IO.File]::WriteAllText("$root\probe.hip",'extern "C" __attribute__((global)) void probe(float* out) { out[__builtin_amdgcn_workitem_id_x()] = 1.0f; }')
& 'D:\DLSSNR-Lab\build-0927\rtc_compile.exe' "$root\probe.hsaco" "$root\probe.hip" comgr gfx1201
if($LASTEXITCODE){throw 'COMGR probe failed'}
Get-Content "$root\comgr-verbose.log"
