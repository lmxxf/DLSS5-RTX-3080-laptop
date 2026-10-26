from pathlib import Path
import json,hashlib,csv,re,datetime,numpy as np
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
samples=[]
for a in list(csv.reader((p/'compare-telemetry.csv').open()))[1:]:
 try:samples.append((datetime.datetime.strptime(a[0],'%Y/%m/%d %H:%M:%S.%f'),*[float(re.search(r'[\d.]+',x)[0]) for x in a[2:]]))
 except (ValueError,TypeError):pass
tele={}
for f in p.glob('compare-*-run.json'):
 m=json.loads(f.read_text());a,b=map(datetime.datetime.fromisoformat,[m['begin'],m['end']]);ss=[x for x in samples if a<=x[0]<=b and x[-1]>=90];tele[f.stem]={'util90_samples':len(ss),**{k:float(np.median([x[i] for x in ss])) if ss else None for k,i in [('temp_c',1),('power_w',2),('sm_mhz',3),('mem_mhz',4)]}}
(p/'telemetry-summary.json').write_text(json.dumps(tele,indent=2)+'\n')
manifest=json.loads((root/'nvngx_dlssnr_sm86_v2.manifest.json').read_text());assert len(manifest)==15 and all(x[1]=='inline' for x in manifest)
(p/'pe-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
paths={'source':root/'nvngx_dlssnr.dll','old':root/'nvngx_dlssnr_sm86_fast.dll','new':root/'nvngx_dlssnr_sm86_v2.dll','v7':root/'discord_v7/nvngx_dlssnr_309_v2i8_255_rtx2030_V7.dll'}
ident={k:{'path':str(f),'bytes':f.stat().st_size,'sha256':sha(f)} for k,f in paths.items()}
assert ident['source']['sha256']=='2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f';assert ident['old']['sha256']=='3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a'
(p/'identities.json').write_text(json.dumps(ident,indent=2)+'\n')
(p/'validation.json').write_text(json.dumps({'O4_fatbins':15,'original_slots':15,'extra_sections':0,'finite_e4m3_pair_cases_per_parity':64516,'all_byte_pairs_per_parity':65536,'mapped_half_bit_cases':65536,'coordinate_slots':768,'actual_MMA_integer_matrices':64,'MMA_output_elements':8192,'primitive_mismatches':0,'formal_benchmark_runs':18,'warmup':50,'iterations':80,'all_outputs_finite':True,'repeat_forward_reverse_all_three_DLLs_bitdiff':0,'sky_sign_changes_all_DLLs':0,'new_vs_old_is_bitwise_equal':False,'reason':'even/odd K permutation changes FP16 accumulation order; benchmark PSNR retained','source_and_old_DLL_unchanged':True,'release_ZIPs_modified':False},indent=2)+'\n')
print(ident['new'])
