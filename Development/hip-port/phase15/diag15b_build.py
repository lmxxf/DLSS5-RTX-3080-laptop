from diag15b_paths import ROOT
from pathlib import Path
import shutil,subprocess,hashlib,json
p=Path(__file__).resolve().parent;r=p.parent;out=ROOT/'host';out.mkdir(exist_ok=True)
# Copy only headers; all mutations are in the ignored diagnostic copy.
for f in (r/'Development/HIP').glob('*.h'):shutil.copy2(f,out/f.name)
s=(r/'Development/HIP/hip_reference_network.h').read_text().replace('"../../src/','"'+str((r/'src').resolve())+'/')
mark='void Stage(const std::string&name,const Tensor&t){';assert s.count(mark)==1
hook=r'''void Stage(const std::string&name,const Tensor&t){
 if(!std::getenv("DLSS5_DIAG15B_ARMED")&&name=="head")if(const char*dir=std::getenv("DLSS5_DIAG15B_TRACE")){static bool once=false;if(!once){once=true;Synchronize();std::vector<char>b(t->bytes);api.Check(api.hipMemcpy(b.data(),P(t),b.size(),2),"15B cold-head proof");std::ofstream f(std::string(dir)+"/prepare-head.bin",std::ios::binary);f.write(b.data(),b.size());}}

 if(!std::getenv("DLSS5_DIAG15B_POST_ONLY"))if(std::getenv("DLSS5_DIAG15B_ARMED"))if(const char*dir=std::getenv("DLSS5_DIAG15B_TRACE")){static std::set<std::string> done;if(done.insert(name).second){Synchronize();std::vector<char>b(t->bytes);api.Check(api.hipMemcpy(b.data(),P(t),b.size(),2),"15B read-only tap");std::ofstream f(std::string(dir)+"/"+name+".bin",std::ios::binary);f.write(b.data(),b.size());std::fprintf(stderr,"15B_STAGE %s %zu\n",name.c_str(),b.size());}}
'''
s=s.replace(mark,hook)
point='  if(opt.wall_profile){api.Check(api.hipStreamSynchronize(stream),"wall profile completion");'
node=r'''  if(const char*dir=std::getenv("DLSS5_DIAG15B_TRACE")){
  bool armed=std::getenv("DLSS5_DIAG15B_ARMED")!=nullptr;
  auto save=[&](const std::string&name,void*ptr,size_t size){Synchronize();std::vector<char>b(size);api.Check(api.hipMemcpy(b.data(),ptr,size,2),"15B actual-input/node read");std::ofstream f(std::string(dir)+"/"+name+".bin",std::ios::binary);f.write(b.data(),size);};
  if(module=="c32_wave1"&&kernel.rfind("c32_wave1_prefix",0)==0){
   static bool cold=false,actual=false;void*ptr{};std::memcpy(&ptr,argv[0],sizeof(ptr));
   if(!armed&&!cold){cold=true;Synchronize();std::vector<char>b(size_t(W)*H*16);api.Check(api.hipMemcpy(b.data(),ptr,b.size(),2),"15B cold input check");bool zero=std::all_of(b.begin(),b.end(),[](char c){return c==0;});std::fprintf(stderr,"15B_PREPARE_INPUT all_zero=%u bytes=%zu\n",unsigned(zero),b.size());}
   if(armed&&!actual){actual=true;save("working-input",ptr,size_t(W)*H*16);}
  }

  if constexpr(sizeof...(A)>=4){if(!armed&&kernel.rfind("vit_stream_qkv_frag_",0)==0){static bool once=false;if(!once){once=true;void*dst{};unsigned nn{};std::memcpy(&dst,argv[2],sizeof(dst));std::memcpy(&nn,argv[3],4);save("prepare-qkv",dst,size_t(nn)*3072);}}}
  if(armed&&!std::getenv("DLSS5_DIAG15B_POST_ONLY")){static std::map<std::string,unsigned>next;std::string category;unsigned n{};void*src{};void*dst{};
   if constexpr(sizeof...(A)>=4){if(kernel.rfind("vit_expand_blocked_fp8",0)==0){category="expand";std::memcpy(&src,argv[0],sizeof(src));std::memcpy(&dst,argv[2],sizeof(dst));std::memcpy(&n,argv[3],4);}}
   if constexpr(sizeof...(A)>=5){if(kernel.rfind("vit_stream_contract_frag",0)==0){category="contract";std::memcpy(&src,argv[0],sizeof(src));std::memcpy(&dst,argv[3],sizeof(dst));std::memcpy(&n,argv[4],4);}}
   if constexpr(sizeof...(A)>=4){if(kernel.rfind("vit_stream_qkv_frag_",0)==0){category="qkv";std::memcpy(&src,argv[0],sizeof(src));std::memcpy(&dst,argv[2],sizeof(dst));std::memcpy(&n,argv[3],4);}}
   if constexpr(sizeof...(A)>=3){if(kernel.rfind("vit_attention_fused_",0)==0){category="attention";std::memcpy(&src,argv[0],sizeof(src));std::memcpy(&dst,argv[1],sizeof(dst));std::memcpy(&n,argv[2],4);}}
   if(!category.empty()&&next[category]<8){unsigned i=next[category]++;size_t ib=category=="expand"?size_t(n)*1024:category=="contract"?size_t(n)*4096:category=="qkv"?size_t(n)*1024:size_t(n)*3072;size_t ob=category=="expand"?size_t(n)*4096:category=="qkv"?size_t(n)*3072:size_t(n)*1024;
    save(category+"-"+std::to_string(i)+"-in",src,ib);save(category+"-"+std::to_string(i)+"-out",dst,ob);std::fprintf(stderr,"15B_NODE %s %u %s n=%u\n",category.c_str(),i,kernel.c_str(),n);}
  }
 }
'''
node+=(p/'diag15b_wave.inc').read_text()+(p/'diag15b_post.inc').read_text()
assert s.count(point)==1;s=s.replace(point,node+point);(out/'hip_reference_network.h').write_text(s)
# Phase15 wrapper contains resource-only instrumentation, no elapsed-time calls.
base=(p/'artifacts/host/base_benchmark.cpp').read_text();base=base.replace('"'+str((r/'Development/HIP/hip_reference_network.h').resolve())+'"','"hip_reference_network.h"');(out/'base_benchmark.cpp').write_text(base);runner=(p/'frame_runner.cpp').read_text().replace('hip_reference::Network net(opt);','unsetenv("DLSS5_DIAG15B_ARMED");hip_reference::Network net(opt);').replace('net.PrepareForExternalInput(false);','net.PrepareForExternalInput(false);setenv("DLSS5_DIAG15B_ARMED","1",1);');(out/'frame_runner.cpp').write_text(runner)
subprocess.run(['c++','-O3','-std=c++17',str(out/'frame_runner.cpp'),'-ldl','-o',str(out/'frame_runner')],check=True)
(p/'diag15b-host.json').write_text(json.dumps({'source_header_sha256':hashlib.sha256((r/'Development/HIP/hip_reference_network.h').read_bytes()).hexdigest(),'diagnostic_header_sha256':hashlib.sha256(s.encode()).hexdigest(),'runner_sha256':hashlib.sha256((out/'frame_runner').read_bytes()).hexdigest(),'scope':'read-only Stage copies; no observer/dump_dir, no graph-gate or production change'},indent=2)+'\n')
