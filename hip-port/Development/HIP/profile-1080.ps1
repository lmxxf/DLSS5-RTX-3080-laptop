param([string]$Families='none',[int]$Frames=40,[string]$Tag='map',[string]$ExtraFlag='', [string]$Modules='', [switch]$TimingOnly,[string]$Runner='benchmark1080.exe',[int]$WarmupFrames=8)
$ErrorActionPreference='Stop'
if($WarmupFrames -lt 0 -or $Frames -lt $WarmupFrames+8){throw 'Need at least 8 measured frames after warmup'}
$r='D:\DLSSNR-Lab\hip-backend'
$base='D:\DLSSNR-Lab\Magpie-DLSS5-AMD-0.23\DLSS5-AMD'
$work="$r\profile1080";New-Item -ItemType Directory -Force $work|Out-Null
$flags=@(Get-Content "$base\native-game-flags.txt"|Where-Object{$_ -notmatch '^DLSS5_(NETWORK_HEIGHT|HIP_DUP_PREFIX|HIP_DUP_COUNT|SHOW_FPS|PRE_UPSCALE)='})+@('DLSS5_NETWORK_HEIGHT=1080','DLSS5_SHOW_FPS=0','DLSS5_PRE_UPSCALE=0')
$map=@{none='';c32='c32_fast_ffn_attention';c64='mh_ffn_fused_c64';c128='mh_ffn_fused_c128';c256='mh_ffn_fused_c256';attn64='c64_attention_project';attn128='c128_attention_project';attn256='c256_attention_project';vit='vit_';split='split_';qkv512='mh_qkv_normalize_frag_c512';attn512='mh_attention_project_frag_c512';post='c32_post_merge_head_half';decoder='decoder_project2x';pool='mh_pool';vitqkv='vit_qkv';vitattn='vit_attention';vitexpand='vit_expand';vitcontract='vit_contract';vitproj='vit_project';vitpack='vit_pack_input';vitgather='vit_gather';splitmix='split_mix';splitffn='split_ffn';splitproj='split_projection';c32prefix='c32_fast_ffn_attention_fused_half_prefix_finish_main8$';c32chain='c32_fast_ffn_attention_fused_half_chain$';c32mapped='c32_fast_ffn_attention_fused_half_mapped$';c32finish='c32_fast_ffn_attention_fused_half_chain_finish'}
if($ExtraFlag){$flags+=@($ExtraFlag.Split(';'))}
if(!$Modules){$Modules="$base\native-game-tiled-assets\HIP"}
$rows=@();$i=0
foreach($family in $Families.Split(',')){
 if(!$map.ContainsKey($family)){throw "Unknown family $family"}
 if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie running'}
 $prefix="$work\$Tag-$i-$family";$f="$work\flags.txt"
 [IO.File]::WriteAllLines($f,($flags+@("DLSS5_HIP_DUP_PREFIX=$($map[$family])",'DLSS5_HIP_DUP_COUNT=2')))
 & "$r\$Runner" "$base\native-game-tiled-assets" $f "$r\live-menu-before.f16" $prefix $Frames 0 $Modules 0 1 > "$prefix.log"
 if($LASTEXITCODE){throw "Benchmark failed $family"}
 if(Get-Process SB-Win64-Shipping,Magpie -ErrorAction SilentlyContinue){throw 'Game/Magpie started; discard timings'}
 $csv=@(Import-Csv "$prefix.csv");if($csv.Count -ne $Frames){throw 'Missing frames'}
 foreach($v in @($csv|Where-Object{$_.checked -eq '1'})){if([int]$v.invalid){throw 'Nonfinite output'}}
 $hash=(Get-FileHash "$prefix.f16").Hash
 if($family -eq 'none' -and !(Test-Path "$work\golden.sha256")){$hash|Set-Content "$work\golden.sha256"}
 if(!$TimingOnly -and $hash -ne (Get-Content "$work\golden.sha256" -Raw).Trim()){throw 'Output differs from baseline'}
 $t=@($csv|Where-Object{[int]$_.frame -ge $WarmupFrames}|ForEach-Object{[double]::Parse($_.wall_ms,[Globalization.CultureInfo]::InvariantCulture)}|Sort-Object)
 $median=($t[[int][Math]::Floor(($t.Count-1)/2)]+$t[[int][Math]::Floor($t.Count/2)])/2
 $row=[pscustomobject]@{family=$family;median_ms=$median;p10_ms=$t[[int][Math]::Floor(($t.Count-1)*0.1)];p90_ms=$t[[int][Math]::Floor(($t.Count-1)*0.9)];measured_frames=$t.Count;warmup_frames=$WarmupFrames;hash=$hash};$rows+=$row;$row|ConvertTo-Json -Compress
 $i++
}
$rows|Export-Csv "$work\$Tag-summary.csv" -NoTypeInformation
