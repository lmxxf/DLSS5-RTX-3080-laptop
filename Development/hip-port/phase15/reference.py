import numpy as np
def decode(u):
 a=u&127
 return (np.where(u&128,-1.,1.)*np.where(a<8,a.astype(float)*2**-9,(1+(a&7).astype(float)/8)*np.exp2((a>>3).astype(float)-7))).astype(np.float32)
def encode(x):
 x=np.asarray(x,np.float32);b=x.view(np.uint32);s=(b>>24)&128;a=np.minimum(np.abs(x),np.float32(448)).astype(np.float32).view(np.uint32)
 sub=(a.view(np.float32)+np.float32(16384)).view(np.uint32)&255
 norm=((a+((a>>20)&1)+0x7ffff)>>20)-960
 return (s|np.where(a<0x3c800000,sub,norm)).astype(np.uint8)

def attention(raw):
 n=raw.size//(3*1024)
 q,k,v=decode(raw).reshape(3,n,32,32).transpose(0,2,1,3)
 score=np.matmul(q.astype(float),k.astype(float).transpose(0,2,1)).astype(np.float32)
 scale=np.array([0x2dbb],np.uint16).view(np.float16)[0]
 af=np.fmin(np.fmax((score.astype(float)*float(scale)+1.708984375).astype(np.float32),1.439453125),1.9775390625)
 hb=(af.view(np.uint32)>>13)-0x1c000;u=(((hb<<4)+0x4000)&65535).astype(np.uint16)
 prob=u.view(np.float16).astype(np.float32);prob8=decode(encode(prob))
 numerator=np.matmul(prob8.astype(float),v.astype(float));denom=prob.astype(float).sum(axis=2,keepdims=True)
 return encode((numerator/denom).astype(np.float32)).transpose(1,0,2).reshape(n,1024)
