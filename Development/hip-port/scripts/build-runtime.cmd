@echo off
setlocal
cd /d "%~dp0.."
if not defined LMXXF_GXX set "LMXXF_GXX=C:\msys64\ucrt64\bin\g++.exe"
if not exist "%LMXXF_GXX%" (
  set "LMXXF_GXX=x86_64-w64-mingw32-g++.exe"
)
set "PATH=C:\msys64\ucrt64\bin;%PATH%"
set "OUT=%~1"
if not defined OUT set "OUT=bin"
if not exist "%OUT%" mkdir "%OUT%"
"%LMXXF_GXX%" -std=c++17 -O2 -shared -static -static-libgcc -static-libstdc++ -D_WIN32_WINNT=0x0A00 -DLMXXF_NR_RUNTIME_EXPORTS -I include -I src -I Development/HIP src/LmxxfNrRuntime.cpp -o "%OUT%\LmxxfNrRuntime.dll" -Wl,--out-implib,"%OUT%\LmxxfNrRuntime.dll.a" -ld3d12 -ldxgi -ld3dcompiler -ldxguid
if not %errorlevel%==0 (
  echo FAIL: Compilation failed
  exit /b 1
)
echo BUILD_OK %OUT%\LmxxfNrRuntime.dll
exit /b 0
