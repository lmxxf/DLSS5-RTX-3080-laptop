// Offline GPU-pointer API verification; input upload and output readback stay outside timing.
#include "hip_reference_network.h"
#include <chrono>
using namespace hip_reference;
int main(int argc,char**argv){try{
 if(argc!=6&&argc!=7){puts("device_network ASSETS MODULES INPUT_RGBA_F32 NOISE_F32 OUTPUT_RGB_F32 [900]");return 2;}
 Options o;o.assets=argv[1];o.modules=argv[2];o.wmma=o.wave=o.pooled=true;if(argc==7){if(std::string(argv[6])!="900")throw std::runtime_error("geometry");o.width=1600;o.height=1024;o.post_shift=3;o.fast_vit=true;}
 auto bytes=ReadBytes(argv[3]),noiseBytes=ReadBytes(argv[4]);if(bytes.size()!=size_t(o.width)*o.height*16||noiseBytes.size()!=50331648ull*4)throw std::runtime_error("input sizes");std::vector<float>noise(noiseBytes.size()/4);memcpy(noise.data(),noiseBytes.data(),noiseBytes.size());
 Network net(o);net.SetNoise(noise);auto&api=net.Runtime();void*in{},*out{};api.Check(api.hipMalloc(&in,bytes.size()),"input");api.Check(api.hipMalloc(&out,size_t(o.width)*o.height*12),"output");api.Check(api.hipMemcpy(in,bytes.data(),bytes.size(),1),"upload");
 for(unsigned i=0;i<3;i++){auto start=std::chrono::steady_clock::now();net.Enqueue(in,nullptr,out,0);net.Synchronize();printf("device_iteration=%u wall_ms=%.6f\n",i,std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count());}
 std::vector<char>result(size_t(o.width)*o.height*12);api.Check(api.hipMemcpy(result.data(),out,result.size(),2),"readback");std::ofstream f(argv[5],std::ios::binary);if(!f.write(result.data(),result.size()))throw std::runtime_error("output write");api.hipFree(in);api.hipFree(out);return 0;
 }catch(const std::exception&e){fprintf(stderr,"device network failed: %s\n",e.what());return 1;}}
