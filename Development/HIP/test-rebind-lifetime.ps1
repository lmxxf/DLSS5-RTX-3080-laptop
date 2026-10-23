$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$cases=@(
 @('colour-sync','queued_frame_old.exe',0,1,0,0),
 @('colour-old','queued_frame_old.exe',1,1,0,0),
 @('colour-fixed','queued_frame_fixed.exe',1,1,0,0),
 @('motion-sync','queued_frame_old.exe',0,0,2,0),
 @('motion-old','queued_frame_old.exe',1,0,2,0),
 @('motion-fixed','queued_frame_fixed.exe',1,0,2,0),
 @('both-sync','queued_frame_old.exe',0,1,2,0),
 @('both-fixed','queued_frame_fixed.exe',1,1,2,0),
 @('content-sync','queued_frame_old.exe',0,0,0,1),
 @('content-old','queued_frame_old.exe',1,0,0,1),
 @('content-fixed','queued_frame_fixed.exe',1,0,0,1)
)
$hashes=@{}
foreach($c in $cases){
 $name='rebind-'+$c[0]
 & "$r\run-queued-frame.ps1" -Runner $c[1] -Name $name -Async $c[2] -Rotate $c[3] -Temporal $c[4] -VaryContent $c[5] | Out-Null
 $hashes[$c[0]]=(Get-FileHash "$r\$name.f16").Hash
 Write-Output "CASE=$($c[0]) SHA=$($hashes[$c[0]])"
}
foreach($pair in @(@('colour-sync','colour-old',$false),@('colour-sync','colour-fixed',$true),@('motion-sync','motion-old',$false),@('motion-sync','motion-fixed',$true),@('both-sync','both-fixed',$true),@('content-sync','content-old',$true),@('content-sync','content-fixed',$true))){
 $equal=$hashes[$pair[0]] -eq $hashes[$pair[1]]
 if($equal -ne $pair[2]){throw "Unexpected comparison: $($pair[0]) / $($pair[1])"}
 Write-Output "PASS $($pair[0]) / $($pair[1]) equal=$equal"
}
