[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$ErrorActionPreference='Stop'
$results=@()
$f='C:\DLSS5-5090-dll\发布打包\.stage-v0.3.0\OptiScaler-REFramework-DLSS5-RTX30-0.3.0\nvngx_dlssnr.dll'
$h=(Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash.ToLower()
if($h -ne '1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'){throw 'SHA mismatch'}
$results += [pscustomobject]@{Package='OptiScaler-REFramework';SHA256=$h;Authenticode=(Get-AuthenticodeSignature -LiteralPath $f).Status.ToString()}
$f='C:\DLSS5-5090-dll\发布打包\.stage-v0.3.0\OptiScaler-DLSS5-RTX30-0.3.0\nvngx_dlssnr.dll'
$h=(Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash.ToLower()
if($h -ne '1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'){throw 'SHA mismatch'}
$results += [pscustomobject]@{Package='OptiScaler';SHA256=$h;Authenticode=(Get-AuthenticodeSignature -LiteralPath $f).Status.ToString()}
$f='C:\DLSS5-5090-dll\发布打包\.stage-v0.3.0\Magpie-DLSS5-RTX30-0.3.0\nvngx_dlssnr.dll'
$h=(Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash.ToLower()
if($h -ne '1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'){throw 'SHA mismatch'}
$results += [pscustomobject]@{Package='Magpie';SHA256=$h;Authenticode=(Get-AuthenticodeSignature -LiteralPath $f).Status.ToString()}
$results += [pscustomobject]@{Package='driver NGX core';Authenticode=(Get-AuthenticodeSignature -LiteralPath 'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll').Status.ToString()}
$results | ConvertTo-Json -Depth 4
