param([string]$Folder='D:\DLSSNR-Lab\hip-backend\c32-fast-oracle',[string]$DxcRoot='D:\DLSSNR-Lab\matrix-probe\dxc-preview',[switch]$Map3)
$ErrorActionPreference='Stop'
$Dxc=Join-Path $DxcRoot 'bin\x64\dxc.exe'
$Inc=Join-Path $DxcRoot 'inc\hlsl'
Set-Location $Folder
$Mapped=if($Map3){1}else{0}
$Output=if($Map3){'c32_fast_oracle_map3.cso'}else{'c32_fast_oracle.cso'}
& $Dxc -I $Inc -T cs_6_10 -E main -HV 2021 -enable-16bit-types -O3 -D NATIVE_C32_FFN_FAST2=1 -D NATIVE_C32_FFN_FP8=1 -D NATIVE_C32_FFN_FAST3=1 -D NATIVE_C32_PRECISE_CHAIN=1 -D NATIVE_C32_SAT_CAST=1 -D NATIVE_C32_TILED_WEIGHTS=0 -D "NATIVE_C32_MAPPED_INPUT=$Mapped" -D NATIVE_C32_HALF_STREAM=0 -D NATIVE_RAW_OUTPUT_STORE=1 -D NATIVE_STATIC_LENGTH=1 -D NATIVE_FAST_ACCUMULATE=1 -D NATIVE_FAST_EPILOGUE=1 -D NATIVE_FAST_F=1 native_wave_c32_ffn_blocked.hlsl -Fo $Output
if($LASTEXITCODE -ne 0){throw 'Production FAST3 oracle compilation failed'}
