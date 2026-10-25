from pathlib import Path
import hashlib,json,numpy as np
from PIL import Image
p=Path(__file__).resolve().parent;r=p.parent
paths=[Path('/mnt/c/Users/lmxxf/Videos/Captures/明末：渊虚之羽 2026_1_25 14_32_11.png'),Path('/mnt/c/Users/lmxxf/AppData/Local/Temp/dlss5_frame_test/input.f16'),Path('/mnt/c/DLSS5-5090-dll/发布打包/验证记录/magpie-smoke-input.f16')];rows=[]
for f in paths:
 row={'path':str(f),'exists':f.exists()}
 if f.exists():
  row.update(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest())
  if f.suffix=='.png':
   im=Image.open(f);row.update(size=list(im.size),mode=im.mode,srgb_chunk='srgb' in im.info,GameDVR_title=im.info.get('Microsoft.GameDVR.Title'),classification='real game SDR menu screenshot; visually inspected; not scene-linear HDR or gameplay sequence',metadata_keys=list(im.info))
  else:
   a=np.fromfile(f,np.float16).reshape(720,1296,4).astype(np.float32);rgb=a[:,:,:3];row.update(shape=[720,1296,4],rgb_min=float(rgb.min()),rgb_max=float(rgb.max()),rgb_unique=int(np.unique(rgb).size),invalid=int(np.count_nonzero(~np.isfinite(a))),classification='zero buffer, not usable image' if np.all(a==0) else 'synthetic smooth gradient smoke fixture; not game capture')
 rows.append(row)
missing=[{'path':'/mnt/d/DLSSNR-Lab/hip-backend/live-menu-before.f16','exists':Path('/mnt/d/DLSSNR-Lab/hip-backend/live-menu-before.f16').exists(),'source_document':'Development/HIP/benchmark-live-capture.md; originalD: frozen capture is unavailable on this machine'}]
result={'inputs':rows,'missing_documented_inputs':missing,'search_scope':['repo including ignored artifacts','/home/lmxxf/work/dlss5-assets excluding model weights','/mnt/c/DLSS5-5090-dll incl package zip listings','known Temp/dlss5_frame_test','Steam userdata screenshot roots','Videos/Captures','Pictures/Screenshots'],'usable_real_game_sdr_frames':1,'usable_real_scene_HDR_frames':0,'independent_real_gameplay_sequence_frames':0,'performance_experiment':'paused per user condition: one SDR menu is insufficient for representative HDR/gameplay quality','not_claimed':'No live capture, no game integration/visual acceptance, no claim of reaching legacy45dB threshold'}
(p/'input-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
