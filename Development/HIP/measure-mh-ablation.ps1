# Diagnostic only: changes network output, never a deployment configuration.
param([ValidateSet('HIP','HLSL')][string]$Backend='HIP',[ValidateSet('all','baseline-after')][string]$CaseName='all')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$cases=@(
 @{name='baseline-before';extra=@()},
 @{name='without-c64';extra=@(5..8)+@(62..65)},
 @{name='without-c128';extra=@(9..14)+@(56..61)},
 @{name='without-c256';extra=@(15..22)+@(48..55)},
 @{name='without-c512';extra=@(23..30)+@(40..47)},
 @{name='baseline-after';extra=@()})
$runner=if($Backend -eq 'HIP'){'benchmark_vit_qkv_fused.exe'}else{'benchmark_hlsl_edges.exe'}
$golden=if($Backend -eq 'HIP'){'FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58'}else{'C7C2F49D3F637F7EA50E3236510677E06574067CC707CE03275EDF4609CAF30B'}
foreach($case in $cases){
 if($CaseName -ne 'all' -and $case.name -ne $CaseName){continue}
 if($Backend -eq 'HLSL' -and $case.name -eq 'without-c512'){Write-Output 'UNSUPPORTED HLSL C512 ablation: block23 input/output layouts differ';continue}
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
 $flags=@(Get-Content "$r\vit-qkv-validation-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_SKIP_BLOCKS='})
 $skip=@(@(42,43,46)+$case.extra|Sort-Object -Unique)
 $flags+='DLSS5_SKIP_BLOCKS='+($skip -join ',')
 $flags|Set-Content "$r\mh-ablation-flags.txt"
 $expected=if($case.extra.Count){''}else{$golden}
 & "$r\validate-hdr.ps1" -Runner $runner -Modules c32-global-ffn-release-modules -Name ('ablation-'+$Backend+'-'+$case.name) -Flags mh-ablation-flags.txt -EdgesOnly 1 -ExpectedHash $expected
 if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
}
