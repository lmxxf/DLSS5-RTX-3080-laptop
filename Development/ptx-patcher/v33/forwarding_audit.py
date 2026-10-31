"""Instruction-level read-only provenance / mixed-definition audit."""
from pathlib import Path
import sys,json,re,bisect,collections,struct,ctypes as c
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));sys.path.insert(0,str(p.parent/'v25'))
import build_sm86_dlls as b,ptx_mapped,cfg_loops
src=(p.parent/'v27/source_audit.py').read_text();namespace=dict(re=re,bisect=bisect,collections=collections,REG=re.compile(r'%[A-Za-z_]+\d+'),parse=cfg_loops.parse)
exec(src[src.index('def split_args'):src.index('\nresult={};all_peaks={}')],namespace);Origin=namespace['Origin']
def decompress(payload,size):
 z=c.CDLL('libzstd.so.1');z.ZSTD_decompress.restype=c.c_size_t;out=c.create_string_buffer(size);assert z.ZSTD_decompress(out,c.c_size_t(size),payload,c.c_size_t(len(payload)))==size;return out.raw
old=json.loads((p.parent/'v27/source-audit.json').read_text());raw=Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes();out={'mixed_records':[],'may_origin_counts':{},'pure_local_pack_alias_candidates':[]};counts=collections.Counter();rejected=collections.Counter();files=[]
for fb,loc in enumerate(b.dp.find_fatbins(raw)[:7]):
 blob=raw[loc.offset:loc.offset+loc.size];rec=next(r for r in b.dp.parse_fatbin_records(blob) if r.kind==1);h=blob[rec.offset:rec.offset+rec.header_size];vals=struct.unpack_from('<HHIQIIIIIIQQQ',h);size,compressed,flags,unc=vals[2],vals[4],vals[10],vals[12];payload=blob[rec.offset+size:rec.offset+size+(compressed or vals[3])];txt=(decompress(payload,unc) if flags&0x8000 else payload).decode().rstrip('\0')
 for entry in re.split(r'(?=\.visible \.entry )',txt)[1:]:
  name=re.match(r'\.visible \.entry (\w+)',entry)[1]
  if name not in old['fatbins'][str(fb)]:continue
  data=old['fatbins'][str(fb)][name];o=Origin(entry);ms=list(b.dp.FP8_MMA_PATTERN.finditer(entry));groups=[]
  for m in ms:
   if not groups or entry[groups[-1][-1].end():m.start()].strip():groups.append([m])
   else:groups[-1].append(m)
  for record in data['records']:
   point=bisect.bisect_right(o.starts,groups[record['run']][0].start())-1;definitions=o.reach(record['register'],point);leaves=sorted(o.leaves(definitions));assert leaves==record['leaf_categories'],(name,record,leaves);counts['+'.join(leaves)]+=1;rejected[record['reason']]+=1
   if 'global_load' in leaves and 'local_FP8_quantization' in leaves:
    proofs=[]
    for j,r in sorted(definitions):
     assert j>=0;x=o.ins[j];bid=o.owner[j];block=o.blocks[bid];lo=max(0,j-3);hi=min(len(o.ins),j+4)
     proofs.append({'definition_register':r,'instruction_index':j,'op':x['op'],'guard':x['guard'],'text':x['text'],'block':bid,'predecessors':sorted(o.preds[bid]),'block_successors':block['succ'],'context':[{'index':k,'text':o.ins[k]['text']} for k in range(lo,hi)]})
    out['mixed_records'].append({'FB':fb,'kernel':name,'register':record['register'],'run':record['run'],'consumer_instruction':point,'consumer_text':o.ins[point]['text'],'consumer_block':o.owner[point],'leaf_categories':leaves,'definitions':proofs,'decision':'reject unconditional half forwarding: both memory data and fallback quantization may reach this use'})
   if leaves==['local_FP8_quantization']:out['pure_local_pack_alias_candidates'].append({'kernel':name,'register':record['register'],'run':record['run']})
out['may_origin_counts']=dict(counts);out['eligibility_reasons']=dict(rejected);assert sum(counts.values())==5848 and len(out['mixed_records'])==144
out['scope']='Recomputed CFG may-reaching definitions on original PTX, matched all 5848 archived events; not actual dynamic path frequencies. A pure pack leaf alone would still require exact quantization preservation before widening.'
(p/'forwarding-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(counts,'mixed',len(out['mixed_records']),'pure pack',len(out['pure_local_pack_alias_candidates']))
