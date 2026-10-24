param([switch]$FullStream)
$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend'
$a='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD\native-game-tiled-assets'
$extra=@('DLSS5_HIP_MH_FEATURE_BYTE=1','DLSS5_HIP_MH_PROJ_DIAG_FB=1');$refargs=@('--mh-feature-byte','--mh-proj-diag-fb')
$m='decoder-tail-modules';$runner='benchmark_production.exe';$reference='reference_production.exe';$tag='featurebyte-golden'
if($FullStream){$extra+='DLSS5_HIP_MH_BYTE_STREAM=1';$refargs+='--mh-byte-stream';$m='full-byte-modules';$runner='benchmark_full_byte.exe';$reference='reference_full_byte.exe';$tag='streamdiag-golden'}
@(Get-Content "$r\vitcf-on-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_NETWORK_HEIGHT='})+@('DLSS5_NETWORK_HEIGHT=900w')+$extra|Set-Content "$r\$tag-flags.txt"
if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
& "$r\validate-modules.ps1" -Candidate $tag -Assets $a -Modules $m -Flags "$tag-flags.txt" -Runner $runner -Reference $reference -ReferenceArgs $refargs
& "$r\validate-modules-960.ps1" -Candidate "$tag-960" -Assets $a -Modules $m -Runner $runner -Reference $reference -ExtraFlags $extra -ReferenceArgs $refargs
