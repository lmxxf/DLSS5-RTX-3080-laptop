param([switch]$Restore)
$ErrorActionPreference='Stop'
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class MenuWindow {
 public delegate bool CB(IntPtr h,IntPtr p);
 [StructLayout(LayoutKind.Sequential)] public struct Rect {public int L,T,R,B;}
 [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr p);
 [DllImport("user32.dll")] public static extern bool EnumWindows(CB cb,IntPtr p);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out Rect r);
 [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h,IntPtr after,int x,int y,int w,int height,uint flags);
 public static IntPtr Find(uint pid){IntPtr found=IntPtr.Zero;EnumWindows((h,p)=>{uint id;GetWindowThreadProcessId(h,out id);if(id==pid&&IsWindowVisible(h))found=h;return true;},IntPtr.Zero);return found;}
}
'@
[void][MenuWindow]::SetProcessDpiAwarenessContext([IntPtr](-4))
$g=Get-Process SB-Win64-Shipping -ErrorAction Stop | Select-Object -First 1
$h=[MenuWindow]::Find($g.Id);if($h -eq [IntPtr]::Zero){throw 'Game window missing'}
$path='D:\DLSSNR-Lab\hip-backend\live-menu-window.json'
if($Restore){$r=Get-Content $path -Raw|ConvertFrom-Json;[void][MenuWindow]::SetWindowPos($h,[IntPtr]::Zero,$r.x,$r.y,$r.w,$r.h,0x14)}
else{$r=New-Object MenuWindow+Rect;[void][MenuWindow]::GetWindowRect($h,[ref]$r);@{x=$r.L;y=$r.T;w=$r.R-$r.L;h=$r.B-$r.T}|ConvertTo-Json|Set-Content $path;[void][MenuWindow]::SetWindowPos($h,[IntPtr]::Zero,0,0,$r.R-$r.L+16,$r.B-$r.T,0x16)}
