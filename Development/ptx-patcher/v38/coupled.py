"""Byte-isomorphic Shared expansion; no original quantization is skipped in exact modes."""
from pathlib import Path
import re,json,collections
from analysis_common import Origin,REG,split_args,b
from v26.codegen import decode
import v31.codegen as pack
p=Path(__file__).resolve().parent

def plan_kernel(name,entry,k):
 o=Origin(entry);prefix=collections.defaultdict(list);native_decls=set();word_ok={};half_ok={};finite_cache={};busy=set()
 def hn(r):return 'v35_n_'+r[1:]
 def wn(r,n):return 'v35_w_'+r[1:]+'_'+str(n)
 def half(r,point):
  key=('h',r,point)
  if key in finite_cache:return finite_cache[key]
  if key in busy:return False
  busy.add(key);ds=o.reach(r,point);ok=bool(ds)
  for j,rr in ds:
   if j<0:ok=False;continue
   x=o.ins[j];m=b.dp.FP8_DOWN_PATTERN.fullmatch(x['text'])
   if m and not m['guard']:
    dest=hn(r);native_decls.add(dest)
    prefix[j].append(('clamp',dest,m['source']))
   else:ok=False
  busy.remove(key);finite_cache[key]=ok;return ok
 def word(r,point):
  key=('w',r,point)
  if key in finite_cache:return finite_cache[key]
  if key in busy:return False
  busy.add(key);ds=o.reach(r,point);ok=bool(ds)
  for j,rr in ds:
   if j<0:ok=False;continue
   x=o.ins[j];m=b.dp.FP8_PACK_PATTERN.fullmatch(x['text'])
   if m and not m['guard']:
    good=half(m['low'],j) and half(m['high'],j);ok=ok and good
    if good:
     native_decls.update([wn(r,0),wn(r,1)]);prefix[j].extend([('mov',wn(r,0),hn(m['low'])),('mov',wn(r,1),hn(m['high']))])
   elif x['op']=='mov.b32' and len(x['argv'])==2 and REG.fullmatch(x['argv'][1]) and not x['guard']:
    source=x['argv'][1];good=word(source,j);ok=ok and good
    if good:
     native_decls.update([wn(r,0),wn(r,1)]);prefix[j].extend([('mov',wn(r,0),wn(source,0)),('mov',wn(r,1),wn(source,1))])
   else:ok=False
  busy.remove(key);finite_cache[key]=ok;return ok
 stores=[]
 for s in k['stores']:
  assert len(s['symbols'])==1 and len(s['sources']) in [1,2,4]
  native=[]
  for r in s['sources']:
   ok=word(r,s['index']);native.append([wn(r,0),wn(r,1)] if ok else None)
  stores.append(s|{'fast_native':native,'finite_pack_derived':all(x is not None for x in native)})
 all_loads=[]
 for l in k['all_loads']:
  assert len(l['destinations']) in [1,2,4]
  all_loads.append(l|{'native':[[f'v35_l{l["index"]}_{i}_0',f'v35_l{l["index"]}_{i}_1'] for i in range(len(l['destinations']))]})
 for l in all_loads:
  for pair in l['native']:native_decls.update(pair)
 prefix={str(j):[list(t) for t in dict.fromkeys(xs)] for j,xs in prefix.items()}
 return k|{'native_declarations':sorted(native_decls),'prefix':prefix,'stores':stores,'all_loads':all_loads,'inplace_finite_proved':all(s['finite_pack_derived'] for s in stores),'fast_word_coverage':sum(x is not None for s in stores for x in s['fast_native']),'store_word_count':sum(len(s['sources']) for s in stores)}

def make_plans():
 a=json.loads((p.parent/'v35/analysis.json').read_text());out={}
 for fb,ks in a['fatbins'].items():
  text=(p/f'artifacts/raw/fb{int(fb):02}.ptx').read_text();parts={re.match(r'\.visible \.entry (\w+)',part)[1]:part for part in re.split(r'(?=\.visible \.entry )',text)[1:]}
  for name,k in ks.items():
   if k['eligible_shadow']:out[name]=plan_kernel(name,parts[name],k)
 (p/'artifacts/plans-generated.json').write_text(json.dumps(out,indent=2)+'\n');print({n:(k['FB'],k['inplace_finite_proved'],k['fast_word_coverage'],k['store_word_count']) for n,k in out.items()})


def address(arg,symbol,new_symbol):
 m=re.fullmatch(r'\[\s*(%\w+)(?:\s*([+-])\s*(\d+))?\s*\]',arg);assert m,arg;r=m[1];offset=int(m[3] or 0)*(-1 if m[2]=='-' else 1)
 lines=['.reg .b32 a35,b35,c35;']
 lines += [f'cvt.u32.u64 a35,{r};' if r.startswith('%rd') else f'mov.b32 a35,{r};']
 if offset:lines.append(f'add.u32 a35,a35,{offset};')
 lines += [f'mov.u32 b35,{symbol};','sub.u32 a35,a35,b35;','shl.b32 a35,a35,1;',f'mov.u32 c35,{new_symbol};','add.u32 a35,a35,c35;']
 return lines

def native_memory(op,regs,addr='a35'):
 lines=[]
 for i in range(0,len(regs),4):
  group=regs[i:i+4];a=f'[{addr}'+(f'+{4*i}' if i else '')+']';suffix=f'.v{len(group)}.u32' if len(group)>1 else '.u32';v='{'+','.join(group)+'}' if len(group)>1 else group[0]
  lines.append(f'{op}{suffix} {v},{a};' if op.startswith('ld') else f'{op}{suffix} {a},{v};')
 return lines

def repack(lo,hi,dst):
 import pack_range as inverse
 return ['{','.reg .b16 sh35lo,sh35hi;']+inverse.declarations()+inverse.pack(lo,'sh35lo','pack4')+inverse.pack(hi,'sh35hi','pack4')+[f'mov.b32 {dst},{{sh35lo,sh35hi}};','}']

def apply_entry(entry,k,mode):
 inplace='inplace' in mode;fast='fast' in mode
 # Full-byte inverse codec covers reserved 7f/ff as decoded +/-480.
 o=Origin(entry);changes=[];rootdecl=['.reg .b32 '+','.join(k['native_declarations'])+';'];symbols=k['symbols'];newsyms={s:('v35_shared_ext'+str(i) if not inplace else s) for i,s in enumerate(symbols)}
 for s,d in symbols.items():
  if inplace:
   pattern=r'(\.shared\s+\.align\s+\d+\s+\.b8\s+'+re.escape(s)+r'\[)'+str(d['bytes'])+r'(\])';match=re.search(pattern,entry);assert match;changes.append((match.start(),match.end(),match[1]+str(d['bytes']*2)+match[2]))
  else:rootdecl.append(f'.shared .align 16 .b8 {newsyms[s]}[{d["bytes"]*2}];')
 if fast:
  for j,items in k['prefix'].items():
   lines=['{','.reg .b32 cl35;','mov.b32 cl35,0x5f005f00;']
   for kind,dst,src in items:
    if kind=='mov':lines.append(f'mov.b32 {dst},{src};')
    else:lines += [f'abs.f16x2 {dst},{src};',f'min.f16x2 {dst},{dst},cl35;',f'lop3.b32 {dst},{src},{dst},0x7fff7fff,0xd8;']
   lines+=['}'];at=o.ins[int(j)]['start'];changes.append((at,at,'\n'+'\n'.join(lines)+'\n'))
 for s in k['stores']:
  symbol=s['symbols'][0];lines=['{']+address(s['address'],symbol,newsyms[symbol]);tmp=[f's35_{i}' for i in range(2*len(s['sources']))];lines+=['.reg .b32 '+','.join(tmp)+',dlssnr_fp8_scale;','mov.b32 dlssnr_fp8_scale,0x5c005c00;']
  for i,r in enumerate(s['sources']):
   if fast and s['fast_native'][i]:lines += [f'mov.b32 {tmp[2*i]},{s["fast_native"][i][0]};',f'mov.b32 {tmp[2*i+1]},{s["fast_native"][i][1]};']
   else:lines+=decode(r,tmp[2*i],tmp[2*i+1])
  lines+=native_memory('st.shared',tmp)+['}'];x=o.ins[s['index']]
  if not inplace:lines=[x['text']]+lines
  changes.append((x['start'],x['end'],'\n'.join(lines)))
 mma_loads={l['index'] for l in k['MMA_loads']}
 for l in k['all_loads']:
  if not inplace and l['index'] not in mma_loads:continue
  lines=['{']+address(l['address'],l['symbol'],newsyms[l['symbol']]);flat=[r for pair in l['native'] for r in pair];lines+=native_memory('ld.shared',flat)+['}'];x=o.ins[l['index']]
  if inplace:
   for dst,(lo,hi) in zip(l['destinations'],l['native']):lines+=repack(lo,hi,dst)
  else:lines=[x['text']]+lines
  changes.append((x['start'],x['end'],'\n'.join(lines)))
 for begin,end,new in sorted(changes,key=lambda a:(a[0],a[1]),reverse=True):entry=entry[:begin]+new+entry[end:]
 at=entry.index('{')+1;entry=entry[:at]+'\n'+'\n'.join(rootdecl)+'\n'+entry[at:];return entry
if __name__=='__main__':make_plans()
