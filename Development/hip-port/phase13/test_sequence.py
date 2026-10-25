from pathlib import Path
import sys,json,numpy as np
from cuda_probe import CUDA
r=Path(__file__).resolve().parents[1];p=r/'phase13';sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
out=p/'artifacts/probe';out.mkdir(exist_ok=True)
m=dict(name='sequence',sources=['../phase13/sequence_probe.hip'],defines=[],l23defines=[]);res=b.compile_one_module(m,str(r/'hip'),str(out),str(r/'hip/sm86_compat.h'),str(r/'hip/ptx2cubin'));assert res[1],res[2]
rng=np.random.default_rng(13);a=rng.uniform(-4,4,(4096,4,32,48)).astype(np.float16).view(np.uint16)
for i,h in enumerate([0,0x8000,0x7c00,0xfc00,0x7e00,0xfe01,1,0x8001,0x7bff,0xfbff]):a[i*8:(i+1)*8]=h
# Also cover the entire half-bit domain in prepared fragment operands.
a[128:]=np.resize(np.arange(65536,dtype=np.uint16),a[128:].shape)
d=CUDA();mod=d.load(out/'sequence.hsaco');x=d.alloc(a.view(np.uint32));y=np.zeros((4096,32,16),np.uint32);dev=d.alloc(y);d.run(mod,'sequence',[x,dev],4096);d.read(dev,y);diff=int(np.count_nonzero(y[:,:,:8]!=y[:,:,8:]));assert diff==0
(p/'sequence-results.json').write_text(json.dumps({'warps':4096,'lane_count':32,'h2_iterations':4,'MMA_calls_per_chain':8,'half_patterns':65536,'raw_u32_diff':diff,'per_chain_order':'h0hp0,h0hp1,...,h3hp1 unchanged; only ci0/ci1 interleaving differs'},indent=2)+'\n');print('sequence raw u32 diff',diff)
