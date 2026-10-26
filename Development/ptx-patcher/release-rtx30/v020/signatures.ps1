[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$ErrorActionPreference = 'Stop'
$root = 'C:\DLSS5-5090-dll'
$names = @('OptiScaler-REFramework','OptiScaler','Magpie')
$files = @{
 'OptiScaler-REFramework' = 'C:\XboxGames\Onimusha- Way of the Sword\Content\nvngx_dlssnr.dll'
 'OptiScaler' = 'C:\Program Files (x86)\Steam\steamapps\common\StellarBlade\SB\Binaries\Win64\nvngx_dlssnr.dll'
 'Magpie' = 'C:\DLSS5-5090-dll\发布打包\Magpie-DLSS5-RTX30-0.2.0\nvngx_dlssnr.dll'
}
$results = @()
foreach ($name in $names) {
 $file = $files[$name]
 $sig = Get-AuthenticodeSignature -LiteralPath $file
 $hash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLower()
 if ($hash -ne 'c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed') { throw "SHA mismatch $file" }
 $results += [pscustomobject]@{Package=$name;SHA256=$hash;Authenticode=$sig.Status.ToString();Meaning='Patched DLL is unsigned; integrity SHA and NGX execution checked separately'}
}
$core = 'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll'
$sig = Get-AuthenticodeSignature -LiteralPath $core
$results += [pscustomobject]@{Package='NVIDIA driver NGX core';Path=$core;Authenticode=$sig.Status.ToString()}
$results | ConvertTo-Json -Depth 4
