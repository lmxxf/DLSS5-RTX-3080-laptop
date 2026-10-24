#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
static unsigned frame=0;
void Toggle(){HWND h=FindWindowExW(HWND_MESSAGE,nullptr,L"Magpie_Hotkey",nullptr);printf("HOTKEY_WINDOW=%p\n",h);if(h)PostMessageW(h,WM_HOTKEY,0,0);}

LRESULT CALLBACK Wnd(HWND h,UINT m,WPARAM w,LPARAM l){
 if(m==WM_TIMER){++frame;InvalidateRect(h,nullptr,FALSE);if(frame==120){keybd_event(VK_MENU,0,0,0);keybd_event(VK_MENU,0,KEYEVENTF_KEYUP,0);SetForegroundWindow(h);printf("FOREGROUND=%p TARGET=%p\n",GetForegroundWindow(),h);Toggle();puts("START_HOTKEY");fflush(stdout);}if(frame==1320){Toggle();puts("STOP_HOTKEY");fflush(stdout);}if(frame==1400)DestroyWindow(h);return 0;}
 if(m==WM_PAINT){PAINTSTRUCT p;auto dc=BeginPaint(h,&p);RECT r;GetClientRect(h,&r);for(int y=0;y<r.bottom;y+=16){RECT row{0,y,r.right,y+16};auto brush=CreateSolidBrush(RGB((frame*2+y)%255,70+y/6,150));FillRect(dc,&row,brush);DeleteObject(brush);}SetBkMode(dc,TRANSPARENT);SetTextColor(dc,RGB(255,255,255));TextOutW(dc,30,30,L"RTX30 CUDA Magpie 1280x720 animated smoke",42);EndPaint(h,&p);return 0;}
 if(m==WM_DESTROY){PostQuitMessage(0);return 0;}return DefWindowProcW(h,m,w,l);
}
int wmain(){auto u=GetModuleHandleW(L"user32.dll");auto setp=(BOOL(WINAPI*)(HANDLE))GetProcAddress(u,"SetProcessDpiAwarenessContext");auto sett=(HANDLE(WINAPI*)(HANDLE))GetProcAddress(u,"SetThreadDpiAwarenessContext");auto getdpi=(UINT(WINAPI*)(HWND))GetProcAddress(u,"GetDpiForWindow");if(setp)setp((HANDLE)-4);if(sett)sett((HANDLE)-4);setvbuf(stdout,nullptr,_IONBF,0);WNDCLASSW c{};c.lpfnWndProc=Wnd;c.hInstance=GetModuleHandleW(nullptr);c.lpszClassName=L"RTX30Smoke";RegisterClassW(&c);RECT r{0,0,1280,720};AdjustWindowRect(&r,WS_OVERLAPPEDWINDOW,FALSE);auto h=CreateWindowW(c.lpszClassName,L"RTX30 Magpie smoke",WS_OVERLAPPEDWINDOW,100,100,r.right-r.left,r.bottom-r.top,nullptr,nullptr,c.hInstance,nullptr);ShowWindow(h,SW_SHOW);RECT cr;GetClientRect(h,&cr);printf("CLIENT=%ldx%ld dpi=%u\n",cr.right,cr.bottom,getdpi?getdpi(h):0);SetForegroundWindow(h);SetTimer(h,1,16,nullptr);MSG m;while(GetMessageW(&m,nullptr,0,0)>0){TranslateMessage(&m);DispatchMessageW(&m);}return 0;}
