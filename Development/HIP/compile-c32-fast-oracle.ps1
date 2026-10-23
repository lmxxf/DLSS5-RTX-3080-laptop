param([string]$Assets='D:\DLSSNR-Lab\network-720p\DLSS5-AMD\native-game-tiled-assets',[string]$Output='D:\DLSSNR-Lab\hip-backend\c32_fast_attention_oracle.cso',[string]$CompilerRoot='D:\DLSSNR-Lab\matrix-probe\dxc-preview')
$ErrorActionPreference='Stop'
$defines=@('PASS=2','NATIVE_HW_H=1','NATIVE_C32_FUSED=1','NATIVE_C32_FP8_QKV=1','NATIVE_FAST_ATTENTION=1','NATIVE_FAST_ACCUMULATE=1','NATIVE_C32_ATTN_FAST2=1','NATIVE_C32_ATTN_FAST3=1','NATIVE_C32_ATTN_FAST4=1','NATIVE_C32_PRECISE_CHAIN=1','NATIVE_C32_SAT_CAST=1','NATIVE_C32_TWO_PASS_SOFTMAX=0','NATIVE_C32_FUSED_FFN=0','NATIVE_C32_EPILOGUE=0','NATIVE_C32_HALF_STREAM=0')
$args=@('-I',"$CompilerRoot\inc\hlsl",'-I',$Assets,'-T','cs_6_10','-E','attention','-HV','2021','-enable-16bit-types','-O3')
foreach($d in $defines){$args+=@('-D',$d)}
& "$CompilerRoot\bin\x64\dxc.exe" @args "$PSScriptRoot\c32_fast_attention_oracle.hlsl" -Fo $Output
if($LASTEXITCODE){throw "DXC failed $LASTEXITCODE"}
