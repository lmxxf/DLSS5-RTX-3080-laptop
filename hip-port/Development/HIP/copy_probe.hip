typedef unsigned uint;
extern "C" __attribute__((global)) void copy_probe(const uint*in,uint*out,uint n){
 uint i=__builtin_amdgcn_workgroup_id_x()*256+__builtin_amdgcn_workitem_id_x();if(i>=n)return;out[i]=in[i]+1u;
}
