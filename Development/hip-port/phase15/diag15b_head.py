from diag15b_paths import ROOT
from pathlib import Path
import numpy as np,json
p=Path(__file__).resolve().parent;root=ROOT;rows={}
def rtz(x):
 h=x.astype(np.float16);b=h.view(np.uint16).copy();over=np.abs(h.astype(np.float32))>np.abs(x);b[over]-=1;return b.view(np.float16).astype(np.float32)
def head(features,weights,color):
 count=features.shape[0];out=np.empty((count,3),np.float32);dot=np.empty_like(out)
 for first in range(0,count,8192):
  f=features[first:first+8192].astype(np.float32);s=np.zeros((len(f),3),np.float32)
  for c in range(32):s+=f[:,c,None]*weights[:,c]
  dot[first:first+len(f)]=s;acc=s;center=(color[first:first+len(f),:3]*np.float32(.125)-np.float32(.0625)).astype(np.float32)
  v=((acc*np.float32(.03125)+center)*np.float32(8)+np.float32(.5)).astype(np.float32);out[first:first+len(f)]=np.clip(v,0,1)
 return out,dot
for case in json.loads((p/'diag15b-inputs.json').read_text()):
 name=case['case'];w,h=case['processing'];n=w*h;got={};row={}
 for mode in ['native','f32']:
  folder=root/'post'/name/mode;f=np.memmap(folder/'post-features.bin',np.float16,mode='r',shape=(n,32));assert np.isfinite(f).all();weight=np.fromfile(folder/'post-head-weights.bin',np.float32).reshape(3,32);color=np.fromfile(folder/'post-color.bin',np.float32).reshape(n,4)
  cpu,dot=head(f,weight,color);gpu=np.fromfile(folder/'post-replay-rgb.bin',np.float32).reshape(n,3);diff=int(np.count_nonzero(cpu.view(np.uint32)!=gpu.view(np.uint32)));assert diff==0,(name,mode,diff,np.max(abs(cpu-gpu)))
  row[mode+'_CPU_head_bitdiff']=diff;got[mode]=(f,weight,cpu,dot)
  if mode=='f32':
   cross=np.fromfile(folder/'post-cross-rgb.bin',np.float32).reshape(n,3);cf=np.memmap(folder/'post-cross-features.bin',np.float16,mode='r',shape=(n,32));cc,cd=head(cf,weight,color);assert np.array_equal(cc.view(np.uint32),cross.view(np.uint32))
   got['cross']=(cf,weight,cross,cd)
 a=got['native'][2].astype(float);b=got['f32'][2].astype(float);mid=got['cross'][2].astype(float);local=a-mid;upstream=mid-b;d=a-b;assert np.max(abs(local+upstream-d))==0
 vh=case['visible'][1];local=local.reshape(h,w,3)[:vh];upstream=upstream.reshape(h,w,3)[:vh];d=d.reshape(h,w,3)[:vh]
 low=np.fromfile(root/'post'/name/'f32/post-lowonly-rgb.bin',np.float32).reshape(n,3).astype(float);skip=np.fromfile(root/'post'/name/'f32/post-skiponly-rgb.bin',np.float32).reshape(n,3).astype(float);ref0=got['f32'][2].astype(float);cross0=got['cross'][2].astype(float)
 row['upstream_branch_replays']={'low_only_RGB_MSE':float(np.mean((low-ref0)**2)),'skip_only_RGB_MSE':float(np.mean((skip-ref0)**2)),'interaction_RMS':float(np.sqrt(np.mean((cross0-low-skip+ref0)**2))),'scope':'standalone F32 replays, nonlinear contributions not added as independent percentages'}
 row['final_RGB_error_decomposition']={'local_post_same_inputs_MSE':float(np.mean(local*local)),'upstream_input_MSE':float(np.mean(upstream*upstream)),'cross_term':float(2*np.mean(local*upstream)),'total_MSE':float(np.mean(d*d))}
 # Linear dot contribution (CW_FAST_NUM3: Hrtz at head is identity): signed covariance terms sum to dot-error MSE.
 fN=got['native'][0];fF=got['f32'][0];weights=got['native'][1];assert np.array_equal(weights,got['f32'][1]);deltaDot=np.zeros((n,3),float);featureRMS=[]
 for c in range(32):
  df=fN[:,c].astype(float)-fF[:,c].astype(float);deltaDot+=df[:,None]*weights[:,c];featureRMS.append(float(np.sqrt(np.mean(df*df))))
 contrib=[]
 for c in range(32):
  df=fN[:,c].astype(float)-fF[:,c].astype(float);v=np.mean(df[:,None]*weights[:,c]*deltaDot,axis=0);contrib.append({'feature':c,'signed_covariance_contribution':v.tolist(),'feature_error_RMS':featureRMS[c]})
 row['linear_head_feature_contributions']=sorted(contrib,key=lambda x:sum(x['signed_covariance_contribution']),reverse=True);row['head_dot_error_MSE']=float(np.mean(deltaDot*deltaDot));row['head_contributions_sum']=float(np.sum([x['signed_covariance_contribution'] for x in contrib])/3)
 row['feature_error_RMS_native_f32']=float(np.sqrt(np.mean((fN.astype(float)-fF.astype(float))**2)));row['feature_reference_RMS']=float(np.sqrt(np.mean(fF.astype(float)**2)))
 rows[name]=row;print(name,row['final_RGB_error_decomposition'],flush=True)
(p/'diag15b-head.json').write_text(json.dumps({'cases':rows,'scope':'isolated post kernel replay verified0bit; CPU head reconstructs outputs0bit; crossF32 uses COPIED Native low/skip, never injected into original network; MSE cross term retained'},indent=2)+'\n')
