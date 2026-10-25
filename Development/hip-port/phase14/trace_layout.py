from pathlib import Path
import sys,json,numpy as np
from cuda_probe import CUDA
from reference import encode,decode
r=Path(__file__).resolve().parents[1];p=r/'phase14';sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
out=p/'artifacts/layout';out.mkdir(parents=True,exist_ok=True);mod=dict(name='layout',sources=['../phase14/layout_probe.hip'],defines=[],l23defines=[])
mod['defines']=['P14_LAYOUT_ABI 2']
res=b.compile_one_module(mod,str(r/'hip'),str(out),str(r/'hip/sm86_compat.h'),str(r/'hip/ptx2cubin'));assert res[1],res[2]
import ctypes as C
# Sweep every query/key coordinate, both V channel halves, and both independent ABI errors.
d=CUDA();m=d.load(out/'layout.hsaco');rows=[]
for query in range(16):
 for key in range(16):
  a=np.zeros((3,16,32),np.uint8);a[0,query,5]=0x38;a[1,key,5]=0x40;a[2,key,7]=0x38;a[2,key,23]=0x30
  x=d.alloc(a);ys={}
  for mode in [0,1,2,3,5,6,7]:
   y=np.zeros((32,48),np.float32);dev=d.alloc(y);d.run(m,'layout',[x,dev,C.c_uint(mode)],1);d.read(dev,y);ys[mode]=y;d.free(dev)
  assert np.array_equal(ys[2][:,24:32],ys[0][:,24:32]),'PV ABI error must not change denominator'
  for mode in [5,6,7]:assert np.array_equal(ys[0].view(np.uint32),ys[mode].view(np.uint32)),(query,key,mode)
  score=ys[0][:,:8];expected=np.zeros((32,8),np.float32)
  expected[:]=0;expected[(query//8)*16+key,query%8]=2;assert np.array_equal(score,expected)
  # Stored t[(g*8+e)*24+r] is [query,key]. Read t[r*24+g*8+e] is [query=r,key=g8+e].
  expected_prob=ys[0][:,8:16].reshape(2,16,8).transpose(0,2,1).reshape(16,16)
  read_prob=ys[0][:,16:24].reshape(2,16,8).transpose(1,0,2).reshape(16,16)
  assert np.array_equal(expected_prob,read_prob)
  denom=read_prob.astype(float).sum(axis=1).astype(np.float16).astype(np.float32)
  expected_sum=np.stack([denom[(lane//16)*8:lane//16*8+8] for lane in range(32)])
  assert np.array_equal(ys[0][:,24:32],expected_sum)
  expected_pv=np.zeros((32,16),np.float32);values=decode(encode(read_prob[:,key]))
  for lane in range(32):
   if lane%16==7:
    expected_pv[lane,:8]=values[(lane//16)*8:lane//16*8+8]
    expected_pv[lane,8:]=values[(lane//16)*8:lane//16*8+8]*.5
  assert np.array_equal(ys[0][:,32:],expected_pv)

  row={'query':query,'key':key,'badQ_score_diffs':int(np.count_nonzero(ys[1][:,:8]!=ys[0][:,:8])),'badP_score_diffs':int(np.count_nonzero(ys[2][:,:8]!=ys[0][:,:8])),'badP_PV_diffs':int(np.count_nonzero(ys[2][:,32:]!=ys[0][:,32:])),'fixed_all_u32_diff':0}
  if query==3 and key==11:(p/'coordinate-counterexample.json').write_text(json.dumps({'metadata':row,'reference':ys[0].tolist(),'doubleQ':ys[1].tolist(),'doubleP':ys[2].tolist(),'fixed':ys[7].tolist()},indent=2)+'\n')
  rows.append(row);d.free(x)
assert sum(x['badQ_score_diffs'] for x in rows)>0
assert sum(x['badP_PV_diffs'] for x in rows)>0
(p/'layout-results.json').write_text(json.dumps({'coordinate_cases':256,'fixed_u32_diff':0,'badQ_score_diffs':sum(x['badQ_score_diffs'] for x in rows),'badP_score_diffs':sum(x['badP_score_diffs'] for x in rows),'badP_PV_diffs':sum(x['badP_PV_diffs'] for x in rows),'LDS_transpose_and_denominator':'every coordinate verified independently','cases':rows},indent=2)+'\n');print('PASS: all256 coordinates, LDS transpose/denominator valid; two ABI errors independently reproduced and fixed')
