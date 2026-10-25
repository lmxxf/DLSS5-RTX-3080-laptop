from pathlib import Path
import shutil,subprocess
r=Path(__file__).resolve().parents[1];p=r/'phase13';out=p/'artifacts/diagnostic-host';out.mkdir(exist_ok=True)
for f in (r/'Development/HIP').glob('*.h'):shutil.copy2(f,out/f.name)
s=(r/'Development/HIP/hip_reference_network.h').read_text().replace('"../../src/','"'+str((r/'src').resolve())+'/')
# Diagnostic only: directly tap Stage without installing observer/changing graph gates.
old='void Stage(const std::string&name,const Tensor&t){'
new='''void Stage(const std::string&name,const Tensor&t){
 if(const char*dir=std::getenv("DLSS5_PHASE13_TRACE")){
  static std::set<std::string> dumped;
  if(dumped.insert(name).second){Synchronize();std::vector<char>b(t->bytes);api.Check(api.hipMemcpy(b.data(),P(t),b.size(),2),"phase13 stage");std::ofstream f(std::string(dir)+"/"+name+".bin",std::ios::binary);f.write(b.data(),b.size());std::fprintf(stderr,"TRACE_STAGE %s %zu\\n",name.c_str(),b.size());}
 }
'''
assert s.count(old)==1;s=s.replace(old,new)
# Read instrumented module clocks after target launch, not from another process/context.
point='  if(opt.wall_profile){api.Check(api.hipStreamSynchronize(stream),"wall profile completion");'
hook='''  if(const char*dir=std::getenv("DLSS5_PHASE13_CLOCK")){if(module=="c32_wave1"&&(kernel.find("prefix")!=std::string::npos||kernel.find("post")!=std::string::npos)){
 static std::set<std::string> dumped;if(dumped.insert(kernel).second){Synchronize();void*ptr{};size_t bytes{};api.Check(api.hipModuleGetGlobal(&ptr,&bytes,modules.at(module),"sm86_phase13_clock"),"clock global");std::vector<char>b(bytes);api.Check(api.hipMemcpy(b.data(),ptr,bytes,2),"clock read");std::ofstream f(std::string(dir)+"/"+kernel+".clock",std::ios::binary);f.write(b.data(),bytes);}}
 }
'''
assert s.count(point)==1;s=s.replace(point,hook+point);(out/'hip_reference_network.h').write_text(s)
# Capture the actual first ViT QKV->attention producer/consumer buffers.
s=(out/'hip_reference_network.h').read_text()
point='  if(opt.wall_profile){api.Check(api.hipStreamSynchronize(stream),"wall profile completion");'
hook=r'''  if(const char*dir=std::getenv("DLSS5_PHASE13_ATTN_TAP")){if(kernel.rfind("vit_attention_fused_",0)==0){
 static bool done=false;if(!done){done=true;Synchronize();void*in{};void*outp{};U n{};std::memcpy(&in,argv[0],sizeof(in));std::memcpy(&outp,argv[1],sizeof(outp));std::memcpy(&n,argv[2],4);
 for(unsigned i=0;i<2;i++){size_t bytes=size_t(n)*1024*(i?1:3);std::vector<char>b(bytes);api.Check(api.hipMemcpy(b.data(),i?outp:in,bytes,2),"attn tap");std::ofstream f(std::string(dir)+(i?"/av.bin":"/qkv.bin"),std::ios::binary);f.write(b.data(),bytes);}std::fprintf(stderr,"ATTN_TAP %s n=%u\n",kernel.c_str(),n);}}
 }
'''
s=s.replace(point,hook+point)
s=s.replace('std::string fused=n<=256?', 'std::string fused=(n<=256&&!std::getenv("DLSS5_PHASE13_ATTN400"))?')
(out/'hip_reference_network.h').write_text(s)
shutil.copy2(r/'Development/HIP/benchmark_cuda_nn.cpp',out/'benchmark_cuda_nn.cpp')
subprocess.run(['c++','-O3','-std=c++17',str(out/'benchmark_cuda_nn.cpp'),'-ldl','-o',str(out/'benchmark_cuda_nn')],check=True)
