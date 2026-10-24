#pragma clang fp contract(off)
#pragma clang fp reassociate(off)
extern "C" __attribute__((global)) void compare_rcp(unsigned*diff,unsigned begin,unsigned n){
 unsigned i=__builtin_amdgcn_workgroup_id_x()*256+__builtin_amdgcn_workitem_id_x();if(i>=n)return;
 float x=__builtin_bit_cast(float,begin+i);
 float r=__builtin_amdgcn_rcpf(x);r=__builtin_fmaf(r,__builtin_fmaf(-x,r,1.f),r);r=__builtin_fmaf(r,__builtin_fmaf(-x,r,1.f),r);
 float reference=1.f/x;diff[i]=__builtin_bit_cast(unsigned,r)^__builtin_bit_cast(unsigned,reference);
}
