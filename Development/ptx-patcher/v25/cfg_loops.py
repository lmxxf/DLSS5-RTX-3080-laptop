from pathlib import Path
import re,bisect,json,sys,collections
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));from ptx_mapped import INS

def parse(text):
 clean=re.sub(r'/\*.*?\*/|//[^\n]*',lambda m:re.sub(r'[^\n]',' ',m[0]),text,flags=re.S);ins=[]
 for m in INS.finditer(clean):ins.append({'start':m.start(),'end':m.end(),'op':m['op'],'args':m['args'].strip(),'guard':(m['guard'] or '').strip(),'text':clean[m.start():m.end()].strip()})
 for m in re.finditer(r'(?m)^\s*(@!?%p\d+\s+)?(ret|exit)\s*;',clean):ins.append({'start':m.start(),'end':m.end(),'op':m[2],'args':'','guard':(m[1] or '').strip(),'text':m[0].strip()})
 ins.sort(key=lambda x:x['start'])
 starts=[x['start'] for x in ins];labels={m[1]:bisect.bisect_left(starts,m.end()) for m in re.finditer(r'(?m)^\s*(\$\w+):',clean)}
 return graph(ins,labels)

def graph(ins,labels):
 bounds=sorted({0,len(ins),*labels.values(),*(i+1 for i,x in enumerate(ins) if x['op'] in ['bra','bra.uni','ret','exit'])});blocks=[];index={}
 for start,end in zip(bounds,bounds[1:]):
  if start==end:continue
  n=len(blocks);index[start]=n;blocks.append({'start':start,'end':end,'label':next((l for l,k in labels.items() if k==start),f'block{n}'),'ins':ins[start:end],'succ':[]})
 for n,b in enumerate(blocks):
  x=b['ins'][-1]
  if x['op'] in ['bra','bra.uni']:
   target=re.search(r'\$\w+',x['args'])[0];b['succ'].append(index[labels[target]])
   if x['guard'] and n+1<len(blocks):b['succ'].append(n+1)
  elif (x['op'] not in ['ret','exit'] or x['guard']) and n+1<len(blocks):b['succ'].append(n+1)
 pred={n:set() for n in range(len(blocks))}
 for n,b in enumerate(blocks):
  for to in b['succ']:pred[to].add(n)
 reachable=set();todo=[0]
 while todo:
  n=todo.pop()
  if n in reachable:continue
  reachable.add(n);todo.extend(blocks[n]['succ'])
 dom={n:({0} if n==0 else set(reachable)) for n in reachable};changed=True
 while changed:
  changed=False
  for n in sorted(reachable-{0}):
   new={n}|set.intersection(*(dom[x] for x in pred[n]&reachable))
   if new!=dom[n]:dom[n]=new;changed=True
 loops=[]
 for n,b in enumerate(blocks):
  if n not in reachable:continue
  for header in b['succ']:
   if header not in dom[n]:continue
   nodes={header,n};todo=[n] if n!=header else []
   while todo:
    z=todo.pop()
    for prev in pred[z]:
     if prev not in nodes:nodes.add(prev);todo.append(prev)
   flat=[x for z in sorted(nodes) for x in blocks[z]['ins']];mma=[x for x in flat if x['op'].startswith('mma.sync')]
   loops.append({'header':blocks[header]['label'],'latch':b['label'],'guard':b['ins'][-1]['guard'],'nodes':sorted(nodes),'mma_sites':len(mma),'tail':[x['text'] for x in b['ins'][-8:]],'header_ins':[x['text'] for x in blocks[header]['ins'][:12]]})
 return ins,blocks,loops
if __name__=='__main__':
 active=json.loads((p.parent/'v24/sass-audit.json').read_text())['c'];out={}
 for fb in [0,4,5]:
  s=(p/f'artifacts/raw/fb{fb:02}.ptx').read_text()
  for entry in re.split(r'(?=\.visible \.entry )',s)[1:]:
   name=re.match(r'\.visible \.entry (\w+)',entry)[1]
   if name not in active:continue
   ins,blocks,loops=parse(entry);compute=[l for l in loops if l['mma_sites']];out[name]={'FB':fb,'raw_MMA_sites':sum(x['op'].startswith('mma.sync') for x in ins),'loops':compute,'sync_only_loops':len(loops)-len(compute)}
   print(name,'MMA',out[name]['raw_MMA_sites'])
   for l in compute:print(l['header'],l['mma_sites'],l['tail'])
 (p/'natural-loops.json').write_text(json.dumps(out,indent=2)+'\n')
