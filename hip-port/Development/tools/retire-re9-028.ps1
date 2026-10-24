$ErrorActionPreference='Stop'
$out='D:\給網友打包';$lab='D:\DLSSNR-Lab\release-0281'
$new=Get-Content "$lab\results.json" -Raw|ConvertFrom-Json
if($new.name -ne 'OptiScaler-REFramework-DLSS5-AMD-0.28.1' -or !$new.verified){throw 'Verified replacement missing'}
$zip=Join-Path $out ($new.name+'.zip')
if((Get-FileHash $zip).Hash -ne $new.sha256){throw 'Replacement ZIP changed'}
$preserve=@{}
foreach($base in @($out,"$out\history")){foreach($name in @('Magpie-DLSS5-AMD-0.28.zip','OptiScaler-DLSS5-AMD-0.28.zip')){$p=Join-Path $base $name;if(Test-Path $p){$preserve[$p]=(Get-FileHash $p).Hash}}}
$removed=@()
foreach($base in @($out,"$out\history")){
 foreach($suffix in @('.zip','.zip.sha256','')){
  $p=Join-Path $base ('OptiScaler-REFramework-DLSS5-AMD-0.28'+$suffix)
  if(Test-Path -LiteralPath $p){$item=Get-Item -LiteralPath $p;$h=if(!$item.PSIsContainer){(Get-FileHash -LiteralPath $p).Hash}else{$null};$removed += [pscustomobject]@{path=$p;directory=$item.PSIsContainer;sha256=$h};Remove-Item -LiteralPath $p -Recurse -Force;if(Test-Path -LiteralPath $p){throw 'Old artifact still exists'}}
 }
}
foreach($p in $preserve.Keys){if((Get-FileHash -LiteralPath $p).Hash -ne $preserve[$p]){throw 'Unrelated package changed'}}
[pscustomobject]@{replacement=$zip;removed=$removed;preserved=$preserve}|ConvertTo-Json -Depth 5|Set-Content "$lab\retired-028.json" -Encoding UTF8
"Removed $($removed.Count) old RE9 artifacts; preserved $($preserve.Count) regular 0.28 ZIPs"
