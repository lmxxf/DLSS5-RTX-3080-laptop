from phase2_transform import masked,end_at
HELPER=r'''
extern "C" __attribute__((device)) unsigned long long sm86_phase13_clock[2*1024*64]={};
template<bool Enabled,bool Prefix> __attribute__((device,always_inline)) inline void phase13_mark(unsigned win,unsigned slot){
 if constexpr(Enabled){if((win&63u)==0 && (win>>6)<1024){
 unsigned long long now;asm volatile("bar.warp.sync 0xffffffff; mov.u64 %0,%%clock64;":"=l"(now)::"memory");
 if(sm86_lane_id()==0)sm86_phase13_clock[((Prefix?1u:0u)*1024+(win>>6))*64+slot]=now;
 }}
}
'''
def instrument(s):
 m=masked(s);a=m.index('{',m.index('void cw_body('));z=end_at(m,a,'{','}');b=s[a+1:z]
 mark=lambda n:f'phase13_mark<(Prefix||Post),Prefix>(win,{n});'
 # Locate the actual two qt loops; mutations are performed from right to left.
 import re
 loops=list(re.finditer(r'for\(uint qt=0;qt<4;qt\+\+\)\{',masked(b)));assert len(loops)==2
 edits=[]
 for i,x in enumerate(loops):
  start=x.end();finish=end_at(masked(b),start-1,'{','}')
  edits.extend([(start,mark('qt*8+'+str(i*4))),(finish,mark('qt*8+'+str(i*4+3)))])
  if i==0:
   q=b.index('if constexpr(W16==1){',start,finish);edits.append((q,mark('qt*8+1')))
   q=b.index('i2 feature[2];',start,finish);edits.append((q,mark('qt*8+2')))
  else:
   q=b.index('i2 av[2];',start,finish);edits.append((q,mark('qt*8+5')))
   q=b.index('_Pragma("unroll") for(uint ci=0;ci<2;ci++){',q)
   # First ci loop is AV itself; find the projection loop following it.
   q=b.index('_Pragma("unroll") for(uint ci=0;ci<2;ci++){',q+1);edits.append((q,mark('qt*8+6')))
   edits.append((finish+1,mark('32')))
 edits.append((len(b),mark('33')))
 for at,new in sorted(edits,reverse=True):b=b[:at]+new+b[at:]
 return s[:a+1]+b+s[z:]
