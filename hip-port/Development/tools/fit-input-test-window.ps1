# Interactive task: size only our synthetic borderless test source in physical pixels.
param([int]$Width=1914,[int]$Height=1063)
$ErrorActionPreference='Stop'
Start-Transcript -Path 'D:\DLSSNR-Lab\fit-input\test-window.log' -Force | Out-Null
Add-Type @'
using System;using System.Runtime.InteropServices;
public static class FitWindow {
 [DllImport("user32.dll")]public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr value);
 [DllImport("user32.dll")]public static extern bool SetWindowPos(IntPtr h,IntPtr after,int x,int y,int w,int height,uint flags);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)]public static extern IntPtr FindWindow(string cls,string title);
}
'@
$old=[FitWindow]::SetThreadDpiAwarenessContext([IntPtr](-4))
try {
 $hwnd=[IntPtr]([long](Get-Content 'D:\DLSSNR-Lab\logs\anim-hwnd.txt'))
 if($hwnd -eq [IntPtr]::Zero){throw 'Synthetic test window missing'}
 if(![FitWindow]::SetWindowPos($hwnd,[IntPtr]::Zero,0,0,$Width,$Height,0x14)){throw 'SetWindowPos failed'}
} finally {[FitWindow]::SetThreadDpiAwarenessContext($old) | Out-Null}
