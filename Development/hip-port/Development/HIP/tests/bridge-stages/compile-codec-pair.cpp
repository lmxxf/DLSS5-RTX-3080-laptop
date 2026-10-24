#include <windows.h>
#include <d3dcompiler.h>
#include <cstdio>
int wmain(int argc,wchar_t**argv){if(argc!=5)return 2;for(int i=0;i<2;i++){ID3DBlob*b{},*e{};auto hr=D3DCompileFromFile(argv[1+i*2],nullptr,D3D_COMPILE_STANDARD_FILE_INCLUDE,"main","cs_5_1",D3DCOMPILE_OPTIMIZATION_LEVEL3,0,&b,&e);if(e){fwrite(e->GetBufferPointer(),1,e->GetBufferSize(),stderr);e->Release();}if(FAILED(hr))return 1;FILE*f=_wfopen(argv[2+i*2],L"wb");if(!f)return 1;bool ok=fwrite(b->GetBufferPointer(),1,b->GetBufferSize(),f)==b->GetBufferSize();fclose(f);b->Release();if(!ok)return 1;}return 0;}
