$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$mh="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-mh-byte-stream\multihead_fast_padded.hip")+"`n"
[IO.File]::WriteAllText("$r\mh-byte-stream-padded.generated.hip",$mh,$utf8)
& "$r\..\rtc_compile.exe" "$r\mh-byte-stream-padded.hsaco" "$r\mh-byte-stream-padded.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed: padded'}
$fa="#define HIP_ISA_HALF 1`n"+[IO.File]::ReadAllText("$r\src-mh-byte-stream\multihead_fused_attention.hip")+"`n"
[IO.File]::WriteAllText("$r\mh-byte-stream-attention.generated.hip",$fa,$utf8)
& "$r\..\rtc_compile.exe" "$r\mh-byte-stream-attention.hsaco" "$r\mh-byte-stream-attention.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed: attention'}
$m="$r\mh-byte-stream-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\vit-qkv-fp8-modules\*.hsaco" $m -Force
Copy-Item "$r\mh-byte-stream-padded.hsaco" "$m\multihead-fast-padded-wave-packed.hsaco" -Force
Copy-Item "$r\mh-byte-stream-attention.hsaco" "$m\multihead_fused_attention.hsaco" -Force
Write-Output ("padded sha256 "+(Get-FileHash "$r\mh-byte-stream-padded.hsaco").Hash)
Write-Output ("attention sha256 "+(Get-FileHash "$r\mh-byte-stream-attention.hsaco").Hash)
