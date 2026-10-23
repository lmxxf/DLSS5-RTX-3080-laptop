param([string]$Candidate='sparse',[string]$Runner='benchmark_sparse.exe',[string]$Reference='reference_sparse.exe',[string]$Modules='ffnh2-modules')
# Three checks with DLSS5_HIP_SPARSE_WEIGHTS=1 (+ the memory report), then compares the output hashes with the bit-exact references.
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
& "$r\validate-psnr.ps1" -Candidate $Candidate -Runner $Runner -Modules $Modules -Extra 'DLSS5_HIP_SPARSE_WEIGHTS=1;DLSS5_HIP_MEMORY=1' -RefFlags '--sparse-weights' -Reference $Reference
$full=(Get-FileHash "$r\$Candidate-p-full.f16").Hash;$reset=(Get-FileHash "$r\$Candidate-p-reset.f16").Hash;$hist=(Get-FileHash "$r\$Candidate-p-history.f32").Hash
Write-Output ("full    "+$(if($full -eq 'FEEA9EF3A8FCBF0692DCE7A506B5CA877F6DAEF7E942292F9B9D85A3523D0E58'){'OK'}else{'MISMATCH '+$full}))
Write-Output ("reset   "+$(if($reset -eq '22C171FCE0AA2DF325D3CEB65A7A1C3FFEFB56821B65A0834680506E9D05AFC8'){'OK'}else{'MISMATCH '+$reset}))
Write-Output ("history "+$(if($hist -eq '75B62D2F36B6861B1536EC06B087C3DDB8850F4CDF810E734E16E2BC0223C3F8'){'OK'}else{'MISMATCH '+$hist}))
Get-Content "$r\..\logs\native-hip.txt" | Select-String 'device_free_before|owned_MiB|sparse_weights granularity' | Select-Object -Last 3
