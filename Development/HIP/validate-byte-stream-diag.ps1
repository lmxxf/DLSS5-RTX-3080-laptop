$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend';$m='mh-byte-stream-diag-modules'
$common='DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1'
foreach($i in 0..3){
 $flags=$common+';DLSS5_NETWORK_HEIGHT=900'
 if($i -in @(1,2)){$flags+=';DLSS5_HIP_MH_BYTE_STREAM=1'}
 & "$r\profile-1080.ps1" -Families none -Tag "streamdiag900-$i" -ExtraFlag $flags -Modules "$r\$m" -Runner benchmark_byte_diag.exe -TimingOnly
 $row=Import-Csv "$r\profile1080\streamdiag900-$i-summary.csv"
 if(!$i){$expected=$row.hash}elseif($row.hash -ne $expected){throw '900 output differs'}
}
$common+=';DLSS5_HIP_MH_BYTE_STREAM=1'
& "$r\validate-c32-register-ex.ps1" -Extended -Candidate $m -Baseline $m -Tag streamdiag -CandidateFlags $common -Runner benchmark_byte_diag.exe
& "$r\validate-c32-register-ex.ps1" -OnlyHeight 720 -Candidate $m -Baseline $m -Tag streamdiag720 -CandidateFlags $common -Runner benchmark_byte_diag.exe
