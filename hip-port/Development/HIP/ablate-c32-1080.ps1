# Diagnostic only: changes the computed image. Never deploy these modules.
param([string]$Source='c32_fused_ffn_attention.hip',[int[]]$Phases=@(1,2,3))
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$base='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets\HIP'
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
$source=[IO.File]::ReadAllText("$r\$Source")
foreach($k in $Phases){
 $m="$r\c32-1080-ablate$k";New-Item -ItemType Directory -Force $m|Out-Null
 Copy-Item "$base\*.hsaco" $m -Force
 $src="$m\input.hip"
 [IO.File]::WriteAllText($src,"#define HIP_ISA_HALF 1`n#define HIP_PREPACKED_WEIGHTS 1`n#define HIP_C32_ABLATE $k`n"+$source)
 & "$r\..\rtc_compile.exe" "$m\c32_fused_ffn_attention-packed.hsaco" $src comgr|Out-Null
 if($LASTEXITCODE){throw 'Compile failed'}
 "COMPILED_ABLATION=$k"
}
foreach($k in (@(0)+$Phases+@(0))){
 $m=if($k){"$r\c32-1080-ablate$k"}else{$base}
 "ABLATION=$k"
 & "$r\profile-1080.ps1" -Families none -Tag "ablate$k" -Modules $m -TimingOnly:([bool]$k)
}
