$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-vit-attn-fused\deep_fast.hip")+"`n"
[IO.File]::WriteAllText("$r\vit-attn-fused.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\vit-attn-fused.hsaco" "$r\vit-attn-fused.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\vit-attn-fused-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\ffn-qkv-round-byte-release-modules\*.hsaco" $m -Force
Copy-Item "$r\vit-attn-fused.hsaco" "$m\deep_fast-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\vit-attn-fused.hsaco").Hash)
