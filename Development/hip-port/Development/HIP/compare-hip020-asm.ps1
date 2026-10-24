$ErrorActionPreference='Stop'
$r='D:\DLSSNR-Lab\hip-backend'
# For the modules whose bytes differ from ffnh2-modules, compare the assembly ignoring the source-text-derived __hip_cuid symbol.
$pairs=@(
  @('c32_fused_ffn_attention',           "$r\opt-lane-release-modules\c32_fused_ffn_attention.hsaco.s"),
  @('c32_fused_ffn_attention-packed',    "$r\c32dg.hsaco.s"),
  @('multihead-fast-padded-wave',        "$r\opt-lane-release-modules\multihead-fast-padded-wave.hsaco.s"),
  @('multihead_fused_attention',         "$r\rtz.hsaco.s"),
  @('deep_fast',                         "$r\opt-lane-release-modules\deep_fast.hsaco.s"),
  @('deep_fast-packed',                  "$r\bfall-deep_fast.hsaco.s"),
  @('multihead-fast-padded-wave-packed', "$r\ffnh2.hsaco.s"))
foreach($p in $pairs){
  $new="$r\hip020-modules\$($p[0]).hsaco.s"
  if(-not (Test-Path $p[1])){Write-Output ("{0,-36} production .s missing: {1}" -f $p[0],$p[1]);continue}
  $a=Get-Content $p[1] | Where-Object {$_ -notmatch '__hip_cuid'}
  $b=Get-Content $new  | Where-Object {$_ -notmatch '__hip_cuid'}
  $d=Compare-Object $a $b
  Write-Output ("{0,-36} asm lines differing (cuid excluded): {1}" -f $p[0],@($d).Count)
}
