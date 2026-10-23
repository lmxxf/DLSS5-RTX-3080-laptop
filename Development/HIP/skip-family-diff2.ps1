# In-frame cost of the ViT family (both backends) and the C32 chains (HIP only; the HLSL harness cannot skip raw chain blocks)
# by skipping blocks (identity) and timing the frame. Timing only: skipped-frame output is not the network output.
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game running'}
$base=@(Get-Content "$r\vit-all-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_SKIP_BLOCKS='})
$sets=[ordered]@{
 'none'=@('42,43,46',$false);
 'vit'=@('31,32,33,34,35,36,37,38,42,43,46',$false);
 'c32front'=@('2,3,42,43,46',$false);
 'c32back'=@('67,68,42,43,46',$false);
 'c32all'=@('1,2,3,4,66,67,68,69,42,43,46',$false);
 'none2'=@('42,43,46',$true)
}
foreach($k in $sets.Keys){
 ($base+@("DLSS5_SKIP_BLOCKS=$($sets[$k][0])"))|Set-Content "$r\skip2-$k-flags.txt"
 $backends=if($sets[$k][1]){@('hlsl','hip')}else{@('hip')}
 foreach($b in $backends){
  $runner=if($b -eq 'hlsl'){'benchmark_hlsl_edges.exe'}else{'benchmark_vit_hstream.exe'}
  Write-Output "SET=$k backend=$b"
  & "$r\validate-hdr.ps1" -Runner $runner -Modules vit-half-stream-modules -Name "skip2-$b-$k" -Flags "skip2-$k-flags.txt" -EdgesOnly 1
  if(Get-Process SB-Win64-Shipping -ErrorAction SilentlyContinue){throw 'Game started'}
 }
}
