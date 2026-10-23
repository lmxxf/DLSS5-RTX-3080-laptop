# In-frame cost of each MH channel family on both backends by skipping the family (identity copy) and timing the frame.
# Timing only: skipped-frame output is not the network output. Same flags file for both runners (HLSL ignores DLSS5_HIP_*).
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-qkv-fp8-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_SKIP_BLOCKS='})
$sets=[ordered]@{
 'none'='42,43,46';
 'c64'='5,6,7,8,62,63,64,65,42,43,46';
 'c128'='9,10,11,12,13,14,56,57,58,59,60,61,42,43,46';
 'c256'='15,16,17,18,19,20,21,22,48,49,50,51,52,53,54,55,42,43,46';
 'c512'='23,24,25,26,27,28,29,30,40,41,42,43,44,45,46,47';
 'mh-all'='5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65'
}
foreach($k in $sets.Keys){
 ($base+@("DLSS5_SKIP_BLOCKS=$($sets[$k])"))|Set-Content "$r\skip-$k-flags.txt"
 foreach($b in @('hlsl','hip')){
  $runner=if($b -eq 'hlsl'){'benchmark_hlsl_edges.exe'}else{'benchmark_vit_qkv_fp8.exe'}
  Write-Output "SET=$k backend=$b"
  & "$r\validate-hdr.ps1" -Runner $runner -Modules vit-qkv-fp8-modules -Name "skip-$b-$k" -Flags "skip-$k-flags.txt" -EdgesOnly 1
  if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
 }
}
