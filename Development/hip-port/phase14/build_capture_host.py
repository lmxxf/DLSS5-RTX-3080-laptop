from pathlib import Path
import shutil,subprocess
r=Path(__file__).resolve().parents[1];p=r/'phase14';src=p/'artifacts/host';out=p/'artifacts/capture-host';out.mkdir(exist_ok=True)
for f in src.glob('*'):
 if f.suffix in ['.h','.cpp']:shutil.copy2(f,out/f.name)
s=(src/'hip_reference_network.h').read_text();point='  if(opt.wall_profile){api.Check(api.hipStreamSynchronize(stream),"wall profile completion");'
hook=r'''  if(const char*dir=std::getenv("DLSS5_PHASE14_CAPTURE_ATTN")){if(kernel.rfind("vit_attention_fused_",0)==0){
 static unsigned i=0;if(i<8){unsigned id=i++;Synchronize();void*in{};void*outp{};U n{};std::memcpy(&in,argv[0],sizeof(in));std::memcpy(&outp,argv[1],sizeof(outp));std::memcpy(&n,argv[2],4);
 for(unsigned which=0;which<2;which++){size_t bytes=size_t(n)*1024*(which?1:3);std::vector<char>b(bytes);api.Check(api.hipMemcpy(b.data(),which?outp:in,bytes,2),"phase14 capture");std::ofstream f(std::string(dir)+"/"+std::to_string(id)+(which?"-av.bin":"-qkv.bin"),std::ios::binary);f.write(b.data(),bytes);}std::fprintf(stderr,"P14_ATTN %u %s n=%u\n",id,kernel.c_str(),n);}}
 }
'''
assert s.count(point)==1;s=s.replace(point,hook+point);(out/'hip_reference_network.h').write_text(s)
subprocess.run(['c++','-O3','-std=c++17',str(out/'benchmark_cuda_nn.cpp'),'-ldl','-o',str(out/'benchmark_cuda_nn')],check=True)
