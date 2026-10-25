"""Explicitly labelled image fixtures; all generated files stay in phase15."""
from pathlib import Path
import numpy as np,json,hashlib,shutil
from PIL import Image
p=Path(__file__).resolve().parent;r=p.parent;out=p/'artifacts/inputs';out.mkdir(exist_ok=True)
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
real=Path('/mnt/c/Users/lmxxf/Videos/Captures/明末：渊虚之羽 2026_1_25 14_32_11.png');smoke=Path('/mnt/c/DLSS5-5090-dll/发布打包/验证记录/magpie-smoke-input.f16')
if (out/'source-menu.png').exists():real=out/'source-menu.png'
if (out/'source-smoke.f16').exists():smoke=out/'source-smoke.f16'
assert sha(real)=='a055f4e3e43ee2094ca76433b8c57587e35eb5a73a6013622f540a5d52d1d29a'
assert sha(smoke)=='8f32c03e17faf3267434c84ff4b7c071b09796a45d965b5ae5667298ae45eafb'
if real.resolve()!=(out/'source-menu.png').resolve():shutil.copy2(real,out/'source-menu.png')
if smoke.resolve()!=(out/'source-smoke.f16').resolve():shutil.copy2(smoke,out/'source-smoke.f16')
srgb=np.asarray(Image.open(real).convert('RGB'),np.float32)/np.float32(255)
linear=np.where(srgb<=.04045,srgb/np.float32(12.92),((srgb+np.float32(.055))/np.float32(1.055))**np.float32(2.4)).astype(np.float16).astype(np.float32)
y,x=np.mgrid[:linear.shape[0],:linear.shape[1]];gain=(.60+.25*x/max(1,x.shape[1]-1)).astype(np.float32)
dynamic=np.clip(np.roll(np.flip(linear,axis=0),37,axis=1)[:,:,[1,2,0]]*gain[:,:,None]+np.float32(.005),0,1).astype(np.float16).astype(np.float32)
# Existing d3d12_native_codec_test.cpp decode/proxy RGB half-bit recipe.
Y,X=np.mgrid[:720,:1296];pix=(Y*1296+X).astype(np.uint32);bits=np.stack([((pix*37+c*7919)%0x3c01).astype(np.uint16) for c in range(3)],2);ramp=bits.view(np.float16).astype(np.float32)
smoke_rgb=np.fromfile(smoke,np.float16).reshape(720,1296,4)[:,:,:3].astype(np.float32)
def resize(a,w,h):
 sy=np.clip((np.arange(h,dtype=np.float32)+.5)*np.float32(a.shape[0]/h)-.5,0,a.shape[0]-1);sx=np.clip((np.arange(w,dtype=np.float32)+.5)*np.float32(a.shape[1]/w)-.5,0,a.shape[1]-1)
 y0=np.floor(sy).astype(int);x0=np.floor(sx).astype(int);y1=np.minimum(y0+1,a.shape[0]-1);x1=np.minimum(x0+1,a.shape[1]-1);fy=(sy-y0).astype(np.float32)[:,None,None];fx=(sx-x0).astype(np.float32)[None,:,None]
 return ((a[y0[:,None],x0[None,:]]*(1-fx)+a[y0[:,None],x1[None,:]]*fx)*(1-fy)+(a[y1[:,None],x0[None,:]]*(1-fx)+a[y1[:,None],x1[None,:]]*fx)*fy).astype(np.float32)
def encode(a,white):
 # Manual white, exposure1, source shader mode1; CPU fixture preprocessing only.
 v=np.maximum(a,np.float32(0))/np.float32(white);shoulder=np.float32(.75)+np.float32(.25)*(1-np.exp(-np.float32(5.770780)*(v-np.float32(.75))))
 v=np.clip(np.where(v<=.75,v,shoulder),0,1);v=np.where(v<=.0031308,v*np.float32(12.92),np.float32(1.055)*np.power(v,np.float32(1/2.4))-np.float32(.055))
 return v.astype(np.float16).astype(np.float32)
geometries=[('512',512,512,512,512),('480-fit',896,512,854,480),('1024',1024,768,1024,768),('640',640,640,640,640),('1152',1152,640,1152,640),('720',1280,768,1280,720),('1024-square',1024,1024,1024,1024)]
records=[]
for label,w,h,vw,vh in geometries:
 rows=[]
 for name,base,kind,direct in [('menu-sdr',srgb,'real_game_SDR_menu',True),('menu-linear',linear,'derived_display_linear_NOT_scene_HDR',False),('menu-dynamic',dynamic,'synthetic_whole_frame_transform_of_real_menu',False),('codec-ramp',ramp,'existing_codec_synthetic_RGB_recipe',False),('smoke',smoke_rgb,'existing_synthetic_gradient',True)]:
  whites=[1] if direct else [1,512]
  previous=None
  for white in whites:
   # Float16 source textures; power-of-two white pairing preserves source codes.
   source=(base*np.float32(white)).astype(np.float16).astype(np.float32)
   resized=resize(source,vw,vh);working=resized.astype(np.float16).astype(np.float32) if direct else encode(resized,white)
   yy=np.arange(h);xx=np.arange(w);yy=np.where(yy<vh,yy,2*vh-2-yy);xx=np.where(xx<vw,xx,2*vw-2-xx)
   padded=working[yy[:,None],xx[None,:]];rgba=np.ones((h,w,4),np.float32);rgba[:,:,:3]=padded;assert np.isfinite(rgba).all() and rgba[:,:,:3].min()>=0 and rgba[:,:,:3].max()<=1
   case=name+f'-wp{white}';file=out/f'{label}-{case}.rgba32';rgba.tofile(file)
   row={'id':case,'origin':kind,'source_kind':'sRGB8' if direct else 'derived/synthetic_linear_FP16','white':white,'linear_source_min':float(source.min()),'linear_source_max':float(source.max()),'processing':[w,h],'visible':[vw,vh],'file':str(file),'sha256':sha(file),'working_min':float(padded.min()),'working_max':float(padded.max()),'peak_for_PSNR':1.,'codec':'sRGB_IO pass-through' if direct else 'CPU shader-formula soft-knee/sRGB thenFP16; NOT D3D12 shader acceptance'}
   if previous is not None:assert np.array_equal(previous.view(np.uint32),rgba.view(np.uint32)),(label,name);row['wp1_vs_wp512_input_bitdiff']=0
   previous=rgba;rows.append(row)
 # Inputs used to prove dense change are direct-menu and its whole-frame derivative.
 a=np.fromfile(rows[0]['file'],np.float32).reshape(h,w,4);b=np.fromfile(next(t['file'] for t in rows if t['id']=='menu-dynamic-wp1'),np.float32).reshape(h,w,4)
 changed=float(np.mean(np.any(a[:,:,:3].view(np.uint32)!=b[:,:,:3].view(np.uint32),axis=2)));assert changed>.5
 records.append({'geometry':label,'processing':[w,h],'visible':[vw,vh],'dynamic_changed_pixel_fraction':changed,'inputs':rows})
# Canonical Phase14 patterns are identity fixtures, separate from image quality tests.
for w,h in [(1280,768),(1600,1024),(1920,1152)]:
 yy,xx=np.mgrid[:h,:w];a=np.ones((h,w,4),np.float32)
 for c,(vx,vy,offset) in enumerate([(17,31,0),(23,13,100),(7,41,200)]):a[:,:,c]=((xx*vx+yy*vy+offset)%1024).astype(np.float32)/np.float32(1024)
 f=out/f'baseline-{w}.rgba32';a.tofile(f)
(p/'input-manifest.json').write_text(json.dumps({'source_PNG_SHA256':sha(real),'source_smoke_SHA256':sha(smoke),'source_codec_recipe_SHA256':sha(r/'Development/d3d12_native_codec_test.cpp'),'source_encode_shader_SHA256':sha(r/'shaders/native_codec_encode.hlsl'),'fixture_generator_SHA256':sha(Path(__file__)),'geometry_mapping':'bilinear resize to visible; top-left reflection without repeated edge into processing extent','true_scene_HDR_sources':0,'geometries':records},indent=2)+'\n');print('Prepared',sum(len(t['inputs']) for t in records),'labelled images,7 geometries,baseline3; all white pairs0bit')
