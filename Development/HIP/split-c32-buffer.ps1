$ErrorActionPreference='Stop';$r='D:\DLSSNR-Lab'
foreach($variant in 'read','write'){
 $sourceDir="$r\c32-buffer-$variant-src";New-Item -ItemType Directory -Force $sourceDir|Out-Null
 $macro=if($variant -eq 'read'){'HIP_C32_BUFFER_OUTPUT'}else{'HIP_C32_BUFFER_INPUT'}
 [IO.File]::WriteAllText("$sourceDir\c32_fused_ffn_attention.hip",("#define $macro 0`n"+[IO.File]::ReadAllText("$r\c32-buffer-src\c32_fused_ffn_attention.hip")))
 & "$r\c32-buffer-src\build-modules.ps1" -SourceDir "$r\c32-buffer-$variant-src" -OutputDir "$r\c32-buffer-$variant-build" -Compiler "$r\dual-arch-src\rtc_compile.exe" -Only c32_fused_ffn_attention-packed
}
foreach($variant in 'read','write'){
 & "$r\hip-backend\test-c32-buffer.ps1" -Timing -Recheck -Variant $variant
}
