from pathlib import Path
import re,json,subprocess
p=Path(__file__).resolve().parent;r=p.parent
names={'deep_fast-packed-fast':['vit_expand_blocked_fp8_frag_bytein_w16'],'vit-stream-fast':['vit_stream_contract_frag_bstream_bout_compactw_w16','vit_stream_project_n64_bb_bout_compactw_w16','vit_stream_qkv_frag_bin_w5f8']}
rows={};dis=Path('/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump')
for tag,base in [('baseline',r/'phase14/artifacts/selected/modules'),('tail',p/'artifacts/tail/modules')]:
 rows[tag]={}
 for mod,kernels in names.items():
  s=(base/(mod+'.ptx')).read_text();sass=subprocess.run([str(dis),'--dump-sass',str(base/(mod+'.hsaco'))],text=True,capture_output=True,check=True).stdout
  for n in kernels:
   match=re.search(r'\.visible\s+\.entry\s+'+n+r'\(',s);start=s.index('{',match.start());end=s.index('\n}',start);body=s[start:end]
   ss=sass.split('Function : '+n+'\n')[1].split('Function : ')[0]
   rows[tag][n]={'global_u8_stores':len(re.findall(r'st\.global(?:\.\w+)*\.u8\b',body)),'global_v4_stores':len(re.findall(r'st\.global(?:\.\w+)*\.v4\.u32\b',body)),'sass_STG128':len(re.findall(r'\bSTG(?:\.\w+)*\.128\b',ss)),'sass_STGU8':len(re.findall(r'\bSTG(?:\.\w+)*\.U8\b',ss)),'sass_instructions':len(re.findall(r'/\*[0-9a-f]+\*/',ss))}
(p/'isa.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
