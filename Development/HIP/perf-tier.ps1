param([string]$Blocks='12,28,41,42,43,44,46,52,53',[string]$Tag='skip9',[string]$Modules='ffnh2-modules',[string]$Runner='benchmark_pinline.exe',[string]$Reference='reference_vitcf.exe')
# Performance tier: ABBA timing of DLSS5_SKIP_BLOCKS=$Blocks against the production {42,43,46}, then the three PSNR outputs for psnr-check.sh.
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
& "$r\test-flag-ab.ps1" -Modules $Modules -Runner $Runner -Extra "DLSS5_SKIP_BLOCKS=$Blocks" -Tag $Tag -CheckHash 0
& "$r\validate-psnr.ps1" -Candidate $Tag -Runner $Runner -Modules $Modules -Extra "DLSS5_SKIP_BLOCKS=$Blocks" -RefFlags "--skip-blocks $Blocks" -Reference $Reference
