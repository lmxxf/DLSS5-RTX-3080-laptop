$ErrorActionPreference='Stop';$d='D:\DLSSNR-Lab\hip-backend\bridge-stages'
& "$d\compile-shaders.exe" "$d\new-shaders" > "$d\shaders.log"
if($LASTEXITCODE){throw 'Shader compile failed'}
Get-Content "$d\shaders.log"
