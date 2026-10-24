typedef unsigned uint;
extern "C" __attribute__((global)) void rtz_probe(const float*in,uint*out,uint n){
 uint i=__builtin_amdgcn_workgroup_id_x()*256+__builtin_amdgcn_workitem_id_x();if(i>=n)return;
 uint h;float x=in[i];asm("v_cvt_pkrtz_f16_f32 %0, %1, %1" : "=v"(h) : "v"(x));out[i]=h&65535u;
}
