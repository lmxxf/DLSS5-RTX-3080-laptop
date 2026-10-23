param([string]$Assets='D:\DLSSNR-Lab\network-720p\DLSS5-AMD\native-game-tiled-assets',[string]$Output='D:\DLSSNR-Lab\hip-backend\split_fast_oracle.cso',[string]$CompilerRoot='D:\DLSSNR-Lab\matrix-probe\dxc-preview')
$ErrorActionPreference='Stop'
& "$CompilerRoot\bin\x64\dxc.exe" -I "$CompilerRoot\inc\hlsl" -I $Assets -T cs_6_10 -E main -HV 2021 -enable-16bit-types -O3 -D NATIVE_SPLIT_FFWD_WAVES4=1 -D NATIVE_SPLIT_FFWD_BLOCKED=1 -D NATIVE_FAST_ACCUMULATE=1 -D NATIVE_FAST_EPILOGUE=1 -D NATIVE_HW_H=1 -D NATIVE_SPLIT_FFWD_TILED=0 -D NATIVE_SPLIT_FFWD8=0 -D NATIVE_SPLIT_MAPPED=0 "$Assets\native_wave_split_ffwd_parallel.hlsl" -Fo $Output
if($LASTEXITCODE){throw "DXC failed $LASTEXITCODE"}
