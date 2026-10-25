from pathlib import Path
import subprocess,shutil,hashlib,json
p=Path(__file__).resolve().parent;r=p.parent;out=p/'artifacts/host';out.mkdir(exist_ok=True)
src=r/'Development/HIP/benchmark_cuda_nn.cpp';s=src.read_text().replace('#include "hip_reference_network.h"','#include "'+str((r/'Development/HIP/hip_reference_network.h').resolve())+'"')
helper='''
 static unsigned ResourceOnly(Network&net,void*in,void*out){
  net.opt.profile=true;net.EnqueueRaw(in,nullptr,out,0);net.Synchronize();
  struct R{Handle fn{};unsigned block{},calls{};};std::map<std::string,R>rows;
  for(auto&t:net.timings){auto&r=rows[t.name];r.fn=t.function;r.block=t.block;++r.calls;net.api.hipEventDestroy(t.begin);net.api.hipEventDestroy(t.end);}net.timings.clear();net.opt.profile=false;auto&drv=hip_probe::detail::Drv();
  for(auto&kv:rows){int regs=-1,local=-1,shared=-1;drv.cuFuncGetAttribute(&regs,4,kv.second.fn);drv.cuFuncGetAttribute(&local,3,kv.second.fn);drv.cuFuncGetAttribute(&shared,1,kv.second.fn);printf("RESOURCE %s %u %u %d %d %d\\n",kv.first.c_str(),kv.second.calls,kv.second.block,regs,local,shared);}
  return unsigned(rows.size());
 }
'''
mark='struct LayerBenchmark {';assert s.count(mark)==1;s=s.replace(mark,mark+helper);(out/'base_benchmark.cpp').write_text(s);shutil.copy2(p/'frame_runner.cpp',out/'frame_runner.cpp')
subprocess.run(['c++','-O3','-std=c++17',str(out/'frame_runner.cpp'),'-ldl','-o',str(out/'frame_runner')],check=True)
(p/'host-provenance.json').write_text(json.dumps({'production_benchmark_source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'wrapper_sha256':hashlib.sha256((p/'frame_runner.cpp').read_bytes()).hexdigest(),'runner_sha256':hashlib.sha256((out/'frame_runner').read_bytes()).hexdigest(),'scope':'same production MakeProductionOptions; resource-only friend emits no timing; no production source modified'},indent=2)+'\n')
