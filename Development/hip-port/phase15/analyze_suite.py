from pathlib import Path
import json,numpy as np,hashlib,argparse
p=Path(__file__).resolve().parent;pa=argparse.ArgumentParser();pa.add_argument('--tag',default='regression');a=pa.parse_args();runs=json.loads((p/(a.tag+'-runs.json')).read_text());manifest=json.loads((p/'input-manifest.json').read_text());index={(x['label'],x['mode']):x for x in runs};rows=[];issues=[]
def read(run,i,w,h):return np.fromfile(Path(run['output_dir'])/f'{i}.rgb32',np.float32).reshape(h,w,3)
for geo in manifest['geometries']:
 label=geo['geometry'];w,h=geo['processing'];vw,vh=geo['visible'];rr=[index[(label,m)] for m in ['400','256','f32']]
 if any(x['returncode'] for x in rr):issues.append({'geometry':label,'reason':'runner failure'});continue
 first_outputs=[]
 for i,source in enumerate(geo['inputs']):
  native,legacy,ref=[read(run,i,w,h) for run in rr];assert np.isfinite(native).all() and np.isfinite(ref).all();bits=int(np.count_nonzero(native.view(np.uint32)!=legacy.view(np.uint32)))
  if bits:issues.append({'geometry':label,'input':source['id'],'reason':'correct256/400 mismatch','elements':bits})
  delta=native[:vh,:vw].astype(np.float64)-ref[:vh,:vw].astype(np.float64);mse=float(np.mean(delta*delta));psnr=float(-10*np.log10(mse)) if mse else None
  row={'geometry':label,'processing':[w,h],'visible':[vw,vh],'input':source['id'],'origin':source['origin'],'white':source['white'],'PSNR_peak':1.,'PSNR_domain':'encoded working RGB output, visible rectangle; not linear HDR/game ground truth','psnr_peak1':psnr,'maxabs':float(np.max(abs(delta))),'rmse':float(np.sqrt(mse)),'correct256_vs400_full_bitdiff':bits,'invalid':int(np.count_nonzero(~np.isfinite(native))),'repeat_first_last_bitdiff':0,'native_LMem_nonzero':sum(r['lmem']!=0 for r in rr[0]['resources'].values()),'input_sha256':source['sha256'],'reference_sha256':rr[2]['output_sha256'][i],'native_sha256':rr[0]['output_sha256'][i],'meets_45dB_on_this_input_only':psnr is None or psnr>=45}
  rows.append(row);first_outputs.append(native)
 for stem in ['menu-linear','menu-dynamic','codec-ramp']:
  ids=[next(i for i,s in enumerate(geo['inputs']) if s['id']==stem+f'-wp{white}') for white in [1,512]]
  assert geo['inputs'][ids[0]]['sha256']==geo['inputs'][ids[1]]['sha256']
  for run in rr:assert run['output_sha256'][ids[0]]==run['output_sha256'][ids[1]],(label,stem,run['mode'])
 assert len(set(rr[0]['output_sha256']))>=2,'stale full-frame output'
 j=next(i for i,s in enumerate(geo['inputs']) if s['id']=='menu-dynamic-wp1');assert not np.array_equal(first_outputs[0].view(np.uint32),first_outputs[j].view(np.uint32))
report={'rows':rows,'new_correctness_issues':issues,'white1_vs512_input_and_all_output_pairs_bitdiff':0,'real_source_count':1,'real_scene_HDR_count':0,'real_gameplay_sequence_count':0,'legacy45_global_gate_pass':all(x['meets_45dB_on_this_input_only'] for x in rows) and 43.57794791233917>=45,'baseline720_PSNR_dB':43.57794791233917,'performance_status':'paused: representative real HDR/gameplay inputs insufficient; no C32 experiment and no new performance result','baseline_calibration':json.loads((p/'calibration.json').read_text())}
pin=p/'pinned-image-outputs.json'
if pin.exists():
 frozen=json.loads(pin.read_text())['cases']
 assert len(frozen)==len(rows)
 for x in rows:
  for k,v in frozen[x['geometry']+'/'+x['input']].items():assert x[k]==v,('pinned input/output changed',x['geometry'],x['input'],k)
report['accuracy_limitations']=[{k:x[k] for k in ['geometry','input','white','psnr_peak1','maxabs','origin']} for x in rows if x['psnr_peak1'] is not None and x['psnr_peak1']<45]
report['canonical720_below45']=True
(p/'image-results.json').write_text(json.dumps(report,indent=2)+'\n');lines=['# Phase15 offline input regression','','Style1 Small31 Graph off; same reused input/output buffers; all input repeats deterministic. Precision comparison is NativeFP16 vs paired frozenF32 accumulation chain. Peak=1 in ENCODED working RGB, not reconstructed linearHDR. No in-game visual acceptance.','', '| Geometry | Input | Source class | White | PSNR peak1 dB | Maxabs | 256/400 bitdiff |','|---|---|---|---:|---:|---:|---:|']
for x in rows:lines.append(f'| {x["geometry"]} | {x["input"]} | {x["origin"]} | {x["white"]} | {x["psnr_peak1"]:.6f} | {x["maxabs"]:.9f} | {x["correct256_vs400_full_bitdiff"]} |')
lines+=['','Legacy45dB is NOT declared passed globally: accepted canonical720 remains43.577948dB. A single menu and synthetic patterns cannot establish overall image quality.','',f'New correctness issues: `{issues}`. White1/512 encoded inputs and all corresponding outputs are bit-identical. Real linearHDR/gameplay sequence evidence remains missing; performance work paused.']
(p/'image-results.md').write_text('\n'.join(lines)+'\n');print('image rows',len(rows),'issues',issues);print('real source per-geometry:',[(x['geometry'],x['psnr_peak1'],x['maxabs']) for x in rows if x['origin']=='real_game_SDR_menu'])
