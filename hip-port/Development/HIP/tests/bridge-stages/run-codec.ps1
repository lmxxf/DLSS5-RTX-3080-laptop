$ErrorActionPreference='Stop';$d='D:\DLSSNR-Lab\hip-backend\bridge-stages'
if(Get-Process LOP-Win64-Shipping,SB-Win64-Shipping,OnimushaWotS,re9,Magpie -ErrorAction SilentlyContinue){throw 'Game running'}
foreach($case in @(@(1080,0),@(720,0),@(720,1))){
 & "$d\codec.exe" "$d\old-shaders" "$d\new-shaders" $case[0] $case[1] > "$d\codec-$($case[0])-$($case[1]).log"
 if($LASTEXITCODE){Get-Content "$d\codec-$($case[0])-$($case[1]).log";throw 'Codec test failed'}
 Get-Content "$d\codec-$($case[0])-$($case[1]).log"
}
