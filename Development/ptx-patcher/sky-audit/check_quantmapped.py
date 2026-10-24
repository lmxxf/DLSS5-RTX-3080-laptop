import numpy as np
h=np.arange(65536,dtype=np.uint16);x=h.view(np.float16)
finite=np.isfinite(x);v=np.clip(x.astype(np.float32),-448,448).astype(np.float16)
b=v.view(np.uint16).astype(np.uint32)
normal=((b+63+((b>>7)&1))&0xff80).astype(np.uint16)
a=np.abs(v).astype(np.float16)
with np.errstate(over='ignore',invalid='ignore'):
 sub=((a+np.float16(2)).astype(np.float16)-np.float16(2)).astype(np.float16).view(np.uint16)|(b.astype(np.uint16)&0x8000)
q=np.where((b&0x7fff)<0x2400,sub,normal).astype(np.uint16)
# Independent E4M3 finite positive value table, nearest even on ties.
e=np.arange(127);exp=e>>3;man=e&7
grid=np.where(exp==0,man*2.**-9,(1+man/8)*2.**(exp-7))
y=np.minimum(np.abs(x.astype(np.float64)),448)
with np.errstate(invalid='ignore'):
 dist=np.abs(y[:,None]-grid);idx=dist.argmin(1);best=dist[np.arange(65536),idx]
 for off in [1,-1]:
  k=np.clip(idx+off,0,126);tie=(dist[np.arange(65536),k]==best)&((k&1)==0);idx=np.where(tie,k,idx)
ref=grid[idx].astype(np.float16).view(np.uint16)|(h&0x8000)
print('finite mismatches',np.count_nonzero(q[finite]!=ref[finite]),'/',finite.sum())
print('seven-instruction normal-only mismatches',np.count_nonzero(normal[finite]!=ref[finite]))
assert np.array_equal(q[finite],ref[finite])
