$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab\hip-backend'
foreach($i in 0..3){
 $flags='DLSS5_NETWORK_HEIGHT=900'
 if($i -in @(1,2)){$flags+=';DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1'}
 & "$r\profile-1080.ps1" -Families none -Tag "featurebyte900-$i" -ExtraFlag $flags -Modules "$r\mh-ex-production-modules" -TimingOnly
 $row=Import-Csv "$r\profile1080\featurebyte900-$i-summary.csv"
 if(!$i){$expected=$row.hash}elseif($row.hash -ne $expected){throw '900 output differs'}
}
& "$r\validate-c32-register-ex.ps1" -Extended -Candidate mh-ex-production-modules -Baseline mh-ex-production-modules -Tag featurebyte -CandidateFlags 'DLSS5_HIP_MH_FEATURE_BYTE=1;DLSS5_HIP_MH_PROJ_DIAG_FB=1'
