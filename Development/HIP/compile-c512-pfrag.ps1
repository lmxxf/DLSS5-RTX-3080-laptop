$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$utf8=New-Object Text.UTF8Encoding($false)
$m="$r\c512-pfrag-modules";New-Item -ItemType Directory -Force $m|Out-Null
Copy-Item "$r\c512-frag-modules\*.hsaco" $m -Force
foreach($pair in @(@('deep_fast.hip','deep_fast-packed'),@('multihead_fast_padded.hip','multihead-fast-padded-wave-packed'))){
 $src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n"+[IO.File]::ReadAllText("$r\src-c512-pfrag\$($pair[0])")+"`n"
 [IO.File]::WriteAllText("$r\c512-pfrag-$($pair[1]).generated.hip",$src,$utf8)
 & "$r\..\rtc_compile.exe" "$r\c512-pfrag-$($pair[1]).hsaco" "$r\c512-pfrag-$($pair[1]).generated.hip" comgr
 if($LASTEXITCODE){throw "COMGR failed $($pair[1])"}
 Copy-Item "$r\c512-pfrag-$($pair[1]).hsaco" "$m\$($pair[1]).hsaco" -Force
 Write-Output ("module sha256 "+$pair[1]+" "+(Get-FileHash "$r\c512-pfrag-$($pair[1]).hsaco").Hash)
}
$t=Get-Content "$r\c512-pfrag-multihead-fast-padded-wave-packed.hsaco.s";$i=[array]::IndexOf($t,($t|Where-Object{$_ -match '^\s+\.name:\s+mh_qkv_normalize_frag_c512$'}|Select-Object -First 1));$t[($i-40)..($i+12)]|Select-String 'vgpr_count|private_segment|group_segment'
