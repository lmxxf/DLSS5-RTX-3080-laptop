$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-ffn-qkv-bn\multihead_fast_padded.hip")+"`n"
[IO.File]::WriteAllText("$r\ffn-qkv-bn.generated.hip",$src,$utf8)
& "$r\..\rtc_compile.exe" "$r\ffn-qkv-bn.hsaco" "$r\ffn-qkv-bn.generated.hip" comgr
if($LASTEXITCODE){throw 'COMGR failed'}
$m="$r\ffn-qkv-bn-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\vit-half-stream-modules\*.hsaco" $m -Force
Copy-Item "$r\ffn-qkv-bn.hsaco" "$m\multihead-fast-padded-wave-packed.hsaco" -Force
Write-Output ("module sha256 "+(Get-FileHash "$r\ffn-qkv-bn.hsaco").Hash)
Select-String -Path "$r\ffn-qkv-bn.hsaco.s" -Pattern '^\s+\.(vgpr_count|sgpr_count|group_segment_fixed_size|private_segment_fixed_size|name):' | ForEach-Object { $_.Line.Trim() } | Select-String -Pattern 'qkv_bn|c64_project_mapped_g128_qkv$|c128_project_mapped_g128_qkv$|vgpr|sgpr|group_segment|private' | Out-String -Width 200
