$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
$cases=@(
 @('colour',1,0,0,'411DF44CD72093504699AD1B19D1109988C25976F859F17B7181DB1DE90B7CD1'),
 @('both',1,2,0,'43712DDEE8EA04AD645BB2A1AEC55F60839F27C0C3E293A94DC2A5EC35399DFF'),
 @('content',0,0,1,'411DF44CD72093504699AD1B19D1109988C25976F859F17B7181DB1DE90B7CD1'),
 @('evict',2,0,0,'411DF44CD72093504699AD1B19D1109988C25976F859F17B7181DB1DE90B7CD1'),
 @('evict-motion',2,3,0,'43712DDEE8EA04AD645BB2A1AEC55F60839F27C0C3E293A94DC2A5EC35399DFF'))
foreach($c in $cases){
 & "$r\run-queued-frame.ps1" -Runner queued_frame_motion_cache.exe -Name ('cache-'+$c[0]) -Async 1 -Rotate $c[1] -Temporal $c[2] -VaryContent $c[3] | Out-Null
 if((Get-FileHash "$r\cache-$($c[0]).f16").Hash -ne $c[4]){throw "Mismatch $($c[0])"}
 Write-Output "PASS $($c[0])"
}
foreach($i in 0..7){
 $runner=if($i -in @(0,3,4,7)){'queued_frame_cache.exe'}else{'queued_frame_motion_cache.exe'}
 $name="motion-cache-abba-$i"
 & "$r\run-queued-frame.ps1" -Runner $runner -Name $name -Async 1 -Rotate 1 -Temporal 2 | Out-Null
 if((Get-FileHash "$r\$name.f16").Hash -ne $cases[1][4]){throw 'ABBA mismatch'}
 Write-Output "$runner $((Get-Content "$r\$name.log"|Select-String '^hot_ms_per_frame=').Line)"
}
