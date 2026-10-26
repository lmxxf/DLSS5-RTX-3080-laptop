from pathlib import Path
import os,sys,json,subprocess
p=Path(__file__).resolve().parent;r=p.parent;base=r/'phase16/artifacts/tail/modules';new=p/'artifacts/candidate/modules';rows=[]
for name,src,marker,extra,oldhost in [('v2_with_v3_marker',base,True,{},False),('v3_without_marker',new,False,{},False),('v3_reject_w16h',new,True,{'NR_C32_W16':'2'},False),('v3_old_host',new,True,{},True)]:
 out=p/'artifacts/abi'/name;out.mkdir(parents=True,exist_ok=True)
 for f in src.iterdir():
  if f.suffix=='.hsaco' or f.name=='AMPERE_WEIGHTS_V2':
   dst=out/f.name
   if not dst.exists():dst.symlink_to(f)
 if marker:(out/'AMPERE_WEIGHTS_V3').write_text('C32_W16_F16_APPEND_V1\n')
 else:(out/'AMPERE_WEIGHTS_V3').unlink(missing_ok=True)
 env=os.environ.copy();env.update(DLSS5_BENCH_WIDTH='1280',DLSS5_BENCH_GRAPH='0',DLSS5_AMPERE_WEIGHTS='1',DLSS5_BENCH_SMALL_ONLY='1',DLSS5_LAB_COMPACT_ALL='1',DLSS5_LAB_C256_SPLIT='0',**extra);env.pop('DLSS5_AMPERE_C32_F16',None)
 host=r/'phase16/artifacts/benchmark_cuda_nn' if oldhost else p/'artifacts/benchmark_cuda_nn';res=subprocess.run([str(host),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(out),'0','1'],env=env,capture_output=True,text=True);(p/(name+'.log')).write_text(res.stdout+res.stderr);assert res.returncode!=0,name
 assert any(x in res.stdout+res.stderr for x in ['V3','500','not found','function','GetFunction']),res.stdout+res.stderr
 rows.append({'case':name,'returncode':res.returncode,'rejected':True,'old_host':oldhost})
(p/'abi-results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS four ABI/mode mismatch controls rejected')
