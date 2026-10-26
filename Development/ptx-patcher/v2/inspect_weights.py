from pathlib import Path
import sys,struct,json,hashlib,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import dlssnr_patcher as d
files={'source':Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll'),'v7':Path('/mnt/c/DLSS5-5090-dll/discord_v7/nvngx_dlssnr_309_v2i8_255_rtx2030_V7.dll')};allrows={};payloads={}
for tag,f in files.items():
 b=f.read_bytes();pe=d.pe_header_offset(b);opt=pe+24;rsrva,rssize=struct.unpack_from('<II',b,opt+112+16);secs=d.read_pe_sections(b)
 def off(rva):
  for s in secs:
   if s.virtual_address<=rva<s.virtual_address+max(s.raw_size,s.virtual_size):return s.raw_offset+rva-s.virtual_address
  raise ValueError(rva)
 base=off(rsrva);rows={};payloads[tag]={}
 def walk(at,path):
  nn,ni=struct.unpack_from('<HH',b,base+at+12)
  for i in range(nn+ni):
   name,sub=struct.unpack_from('<II',b,base+at+16+8*i)
   if name&0x80000000:
    q=base+(name&0x7fffffff);n=struct.unpack_from('<H',b,q)[0];name=b[q+2:q+2+2*n].decode('utf-16le')
   key=path+[str(name)]
   if sub&0x80000000:walk(sub&0x7fffffff,key)
   else:
    rva,size,cp,_=struct.unpack_from('<IIII',b,base+sub);data=b[off(rva):off(rva)+size];k='/'.join(key);rows[k]={'rva':rva,'bytes':size,'sha256':hashlib.sha256(data).hexdigest(),'prefix_hex':data[:32].hex()};payloads[tag][k]=data
 walk(0,[]);allrows[tag]=rows
comparison={}
for k,a in allrows['source'].items():
 if k not in allrows['v7']:continue
 bb=allrows['v7'][k];comparison[k]={'source_bytes':a['bytes'],'v7_bytes':bb['bytes'],'identical':a['sha256']==bb['sha256']}
(p/'weights.json').write_text(json.dumps({'resources':allrows,'comparison':comparison},indent=2)+'\n')
print('leaves:',{k:len(v) for k,v in allrows.items()})
for k,row in comparison.items():
 if not row['identical']:print(k,row,'prefix',allrows['source'][k]['prefix_hex'],allrows['v7'][k]['prefix_hex'])
sys.path.insert(0,str(p.parents[1]/'hip-port/Development'))
from parse_weights_archive import parse_archive
record_rows={}
idx=np.arange(256,dtype=np.int32);e=(idx&127)>>3;m=idx&7
values=np.where(e==0,m*2.**-9,(1+m/8)*2.**(e-7)).astype(np.float16);table=values.view(np.uint16)|((idx&128)<<8).astype(np.uint16)
for key in comparison:
 if 'WEIGHTS' not in key:continue
 aa,bb=payloads['source'][key],payloads['v7'][key];ar,br=parse_archive(aa),parse_archive(bb);assert [r['name'] for r in ar]==[r['name'] for r in br]
 rr=[]
 for a,b in zip(ar,br):
  x=aa[a['payload_offset']:a['payload_offset']+a['payload_size']];y=bb[b['payload_offset']:b['payload_offset']+b['payload_size']]
  row={'name':a['name'],'old_bytes':len(x),'new_bytes':len(y),'old_dtype':a['dtype_code'],'new_dtype':b['dtype_code'],'unchanged':x==y}
  if len(y)==2*len(x):
   ix=np.frombuffer(x,np.uint8);actual=np.frombuffer(y,np.uint16);valid=(ix&127)!=127;expected=table[ix];row.update(finite_elements=int(valid.sum()),linear_fp8_to_f16_bitdiff=int(np.count_nonzero(actual[valid]!=expected[valid])),old_reserved_bytes=int((~valid).sum()))
  rr.append(row)
 record_rows[key]=rr
 print(key,'records',len(rr),'unchanged',sum(x['unchanged'] for x in rr),'doubled',sum('linear_fp8_to_f16_bitdiff' in x for x in rr),'all expanded finite bitdiff',sum(x.get('linear_fp8_to_f16_bitdiff',0) for x in rr))
(p/'weight-records.json').write_text(json.dumps(record_rows,indent=2)+'\n')
# Representative pure-matrix record: inspect expansion order and value multiset.
key='10/WEIGHTS_CC_SMALL_FP8/1033';aa=payloads['source'][key];bb=payloads['v7'][key];ar=parse_archive(aa);br=parse_archive(bb);samples=[]
for a,b in zip(ar,br):
 if b['payload_size']!=2*a['payload_size']:continue
 x=np.frombuffer(aa[a['payload_offset']:a['payload_offset']+a['payload_size']],np.uint8);y=np.frombuffer(bb[b['payload_offset']:b['payload_offset']+b['payload_size']],np.uint16);expect=table[x]
 row={'name':a['name'],'fp8_first32':x[:32].tolist(),'half_first32_hex':[hex(int(v)) for v in y[:32]],'expected_first32_hex':[hex(int(v)) for v in expect[:32]],'same_f16_multiset':bool(np.array_equal(np.sort(y),np.sort(expect)))}
 # Common 16x16 packed tile: interleave groups of two half fragments.
 for tile in [8,16,32,64,128,256,512,1024]:
  if len(y)%tile==0:row['tile'+str(tile)+'_same_multiset_fraction']=float(np.mean(np.all(np.sort(y.reshape(-1,tile),axis=1)==np.sort(expect.reshape(-1,tile),axis=1),axis=1)))
 samples.append(row)
(p/'weight-expansion-samples.json').write_text(json.dumps(samples,indent=2)+'\n');print('pure-matrix expansion samples',[(r['name'],r['same_f16_multiset']) for r in samples])
permutations=[]
for a,b in zip(ar,br):
 if b['payload_size']!=2*a['payload_size']:continue
 x=np.frombuffer(aa[a['payload_offset']:a['payload_offset']+a['payload_size']],np.uint8);y=np.frombuffer(bb[b['payload_offset']:b['payload_offset']+b['payload_size']],np.uint16);expected=table[x];inds=np.arange(len(x));counts={}
 for bit in range(3,int(np.log2(len(x)))):
  ix=(inds&3)|((inds&((1<<bit)-4))<<1)|((inds>>bit&1)<<2)|(inds&~((1<<(bit+1))-1));counts[str(bit)]=int(np.count_nonzero(expected[ix]!=y))
 permutations.append({'name':a['name'],'move_source_bit2_to_destination_bit_candidates':counts})
(p/'weight-permutation.json').write_text(json.dumps(permutations,indent=2)+'\n');print('bit move exact candidates',[(r['name'],[k for k,v in r['move_source_bit2_to_destination_bit_candidates'].items() if v==0]) for r in permutations])
