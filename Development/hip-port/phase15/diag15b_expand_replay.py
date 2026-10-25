from diag15b_paths import ROOT
from pathlib import Path
import sys,numpy as np,ctypes as C,json,hashlib
from cuda_probe import CUDA
from reference import encode,decode
p=Path(__file__).resolve().parent;root=ROOT;d=CUDA();mods={k:d.load(root/'expand'/k/'expand-canonical.hsaco') for k in ['native','f32']}
wfile=Path('/home/lmxxf/work/dlss5-assets/native-game-tiled-assets/small/block31-expand.f16');wf=np.fromfile(wfile,np.float16).astype(np.float32).reshape(4096,1024);weight=encode(wf);assert np.array_equal(decode(weight).view(np.uint32),wf.view(np.uint32));wp=d.alloc(weight);rows={}
for case in json.loads((p/'diag15b-inputs.json').read_text()):
 name=case['case'];n=case['processing'][0]//64*(case['processing'][1]//64);got={}
 for kind,src in [('native','native'),('f32','native'),('f32','f32')]:
  key=kind+'-on-'+src;raw=np.fromfile(root/'traces'/name/src/'expand-0-in.bin',np.uint8).reshape(n,1024);x=d.alloc(raw);a=np.zeros((n,4096),np.float32);byte=np.zeros((n,4096),np.uint8);ap=d.alloc(a);bp=d.alloc(byte);d.run(mods[kind],'expand_canonical',[x,wp,ap,bp,C.c_uint(n)],n//16*256);d.read(ap,a);d.read(bp,byte);d.free(x,ap,bp);folder=root/'expand/results'/name;folder.mkdir(parents=True,exist_ok=True);a.tofile(folder/(key+'.acc32'));byte.tofile(folder/(key+'.u8'));got[key]=(a,byte)
  if kind==src:
   expected=np.fromfile(root/'traces'/name/src/'expand-0-out.bin',np.uint8).reshape(n,4096);diff=int(np.count_nonzero(expected!=byte));assert diff==0,(name,key,diff)
 y=decode(got['native-on-native'][1]).astype(float);f_same=decode(got['f32-on-native'][1]).astype(float);f_orig=decode(got['f32-on-f32'][1]).astype(float);local=y-f_same;prop=f_same-f_orig;total=y-f_orig;assert np.max(abs(local+prop-total))==0
 # Independent CPU sum of the captured raw row-major operands at worst/local and distributed positions.
 accN,accF=got['native-on-native'][0],got['f32-on-native'][0];err=abs(accN.astype(float)-accF.astype(float));worst=np.argsort(err.reshape(-1))[-8:];chosen=list(worst)+[0,n*4096//3,n*4096//2,n*4096-1];cpu=[];X=decode(np.fromfile(root/'traces'/name/'native/expand-0-in.bin',np.uint8).reshape(n,1024)).astype(float)
 for pos in chosen:
  t,c=divmod(int(pos),4096);terms=X[t]*wf[c].astype(float);exact=float(terms.sum());sumabs=float(abs(terms).sum());r16=np.float16(0);r8=np.float16(0)
  for k in range(0,1024,16):r16=np.float16(float(r16)+terms[k:k+16].sum())
  for k in range(0,1024,8):r8=np.float16(float(r8)+terms[k:k+8].sum())
  # Conservative forward error bound for128 half-roundedK8 groups; not an invented exact CPU TensorCore specification.
  u=2**-11;bound=(128*u/(1-128*u))*sumabs
  assert abs(float(accN[t,c])-exact)<=bound+1e-8
  cpu.append({'token':t,'column':c,'CPU_exact_f64_sum':exact,'GPU_F32':float(accF[t,c]),'GPU_F16':float(accN[t,c]),'CPU_RNE_K16':float(r16),'CPU_RNE_K8':float(r8),'sumabs':sumabs,'conservative_FP16_bound':bound,'RNE_K16_exact_match':float(r16)==float(accN[t,c]),'RNE_K8_exact_match':float(r8)==float(accN[t,c])})
 # Four complete token rows, not just cherry-picked scalars, using measured K8 half rounding.
 tokens=sorted(set([0,n//2,n-1,int(worst[-1])//4096]));A=X[tokens];c8=np.zeros((len(tokens),4096),np.float16)
 for k in range(0,1024,8):c8=(c8.astype(float)+A[:,k:k+8]@wf[:,k:k+8].astype(float).T).astype(np.float16)
 target=accN[tokens];point_row_diff=int(np.count_nonzero(c8.astype(np.float32).view(np.uint32)!=target.view(np.uint32)))
 cpu_rows={'tokens':tokens,'elements':target.size,'CPU_RNE_K8_bitdiff':point_row_diff,'maxabs':float(np.max(abs(c8.astype(np.float32)-target)))}
 rows[name]={'production_vs_canonical_byte_diff':0,'F32_production_vs_canonical_byte_diff':0,'local_precision_MSE':float(np.mean(local*local)),'propagated_input_MSE':float(np.mean(prop*prop)),'cross_term':float(2*np.mean(local*prop)),'total_MSE':float(np.mean(total*total)),'local_precision_byte_flips':int(np.count_nonzero(got['native-on-native'][1]!=got['f32-on-native'][1])),'bytes':n*4096,'raw_acc_invalid_N/F32':[int(np.count_nonzero(~np.isfinite(accN))),int(np.count_nonzero(~np.isfinite(accF)))],'CPU_points':cpu,'CPU_full_token_rows':cpu_rows}
 print(name,'local/prop/total',rows[name]['local_precision_MSE'],rows[name]['propagated_input_MSE'],rows[name]['total_MSE'],'CPU8matches',sum(x['RNE_K8_exact_match'] for x in cpu),'/12',flush=True)
(p/'diag15b-expand.json').write_text(json.dumps({'weight_file':str(wfile),'weight_sha256':hashlib.sha256(wfile.read_bytes()).hexdigest(),'scope':'independent raw-row-major operand loader; same input scratch replay; no writes into network; MSE decomposition includes cross term','cases':rows},indent=2)+'\n')
