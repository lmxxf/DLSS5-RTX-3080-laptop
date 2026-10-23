$ErrorActionPreference='Stop'
$root='D:\DLSSNR-Lab\hip-backend\compiler-versions-20260929'
if(Get-Process|Where-Object{$_.ProcessName -match 'Shipping|^re9$|^Onimusha|^SandFall|^benchmark|^rt_bench|^jobbench|^rtc_compile'}){throw 'GPU lab busy'}
$env:AMD_COMGR_EMIT_VERBOSE_LOGS='1'
$env:AMD_COMGR_REDIRECT_LOGS="$root\comgr2-verbose.log"
$env:AMD_COMGR_CACHE='0'
[IO.File]::WriteAllText("$root\probe.hip",'extern "C" __attribute__((global)) void probe(float* out) { out[__builtin_amdgcn_workitem_id_x()] = 1.0f; }')
& "$root\rtc_compile-comgr2.exe" "$root\comgr2-probe.hsaco" "$root\probe.hip" comgr gfx1201
if($LASTEXITCODE){throw 'COMGR2 probe failed'}
Get-Content "$root\comgr2-verbose.log"
Get-FileHash "$env:windir\System32\amd_comgr_2.dll"
