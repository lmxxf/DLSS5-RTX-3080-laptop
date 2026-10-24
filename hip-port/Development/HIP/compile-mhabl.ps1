# Ablation module sets for the C64 attention-project kernel: mhabl1/2/3-modules = ffnh2-modules with multihead_fused_attention.hsaco
# rebuilt from hip\multihead_fused_attention.hip with HIP_MH_ABLATE=1/2/3 (production defines HIP_ISA_HALF, HIP_PREPACKED_WEIGHTS, HIP_MH_RTZ_ISA).
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$utf8=New-Object Text.UTF8Encoding($false)
foreach($n in 1,2,3){
 $src="#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_MH_RTZ_ISA 1`n#define HIP_MH_ABLATE $n`n"+[IO.File]::ReadAllText('D:\DLSSNR-Lab\hip\multihead_fused_attention.hip')+"`n"
 [IO.File]::WriteAllText("$r\mhabl$n.generated.hip",$src,$utf8)
 & 'D:\DLSSNR-Lab\hip\rtc_compile.exe' "$r\mhabl$n.hsaco" "$r\mhabl$n.generated.hip" comgr | Out-Null
 if($LASTEXITCODE){throw "COMGR failed mhabl$n"}
 $m="$r\mhabl$n-modules";Remove-Item $m -Recurse -Force -ErrorAction SilentlyContinue;New-Item -ItemType Directory $m|Out-Null
 Copy-Item "$r\ffnh2-modules\*.hsaco" $m;Copy-Item "$r\mhabl$n.hsaco" "$m\multihead_fused_attention.hsaco" -Force
 Write-Output ("mhabl$n "+(Get-FileHash "$r\mhabl$n.hsaco").Hash.Substring(0,12))
}
