param([string]$Candidate='c32-register-ex-modules',[string]$Baseline='', [string]$Tag='regex900')
$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend';$expected=''
foreach($i in 0..3){
 $m=if($i -in @(1,2)){"$r\$Candidate"}else{if($Baseline){"$r\$Baseline"}else{''}}
 & "$r\profile-1080.ps1" -Families none -Tag "$Tag-$i" -ExtraFlag DLSS5_NETWORK_HEIGHT=900 -Modules $m -TimingOnly
 $row=Import-Csv "$r\profile1080\$Tag-$i-summary.csv"
 if(!$expected){$expected=$row.hash}elseif($expected -ne $row.hash){throw '900 output differs'}
}
