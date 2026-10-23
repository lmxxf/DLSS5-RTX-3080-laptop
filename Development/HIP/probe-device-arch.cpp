#include "hip_api.h"
#include <cstdio>
#include <cstddef>
int main(){try{hip_probe::Api a;a.Check(a.hipInit(0),"init");int n=0;a.Check(a.hipGetDeviceCount(&n),"count");printf("R0600_size=%zu arch_offset=%zu devices=%d\n",sizeof(hip_probe::DevicePropertiesR0600),offsetof(hip_probe::DevicePropertiesR0600,gcnArchName),n);for(int i=0;i<n;i++){auto p=a.Properties(i);printf("device=%d name=%s arch=%s\n",i,p.name,p.gcnArchName);}return 0;}catch(const std::exception&e){fprintf(stderr,"%s\n",e.what());return 1;}}
