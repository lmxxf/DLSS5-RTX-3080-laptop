from pathlib import Path
import sys,re,collections
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dlssnr_patcher as d
for i in range(7):
 txt=Path('/tmp/dlss-sky-audit/fatbin%02d.ptx'%i).read_text(); entries=re.split(r'(?m)^\s*(?:\.visible\s+)?\.entry\b',txt)[1:]
 used=0;examples=[]
 for e in entries:
  mapping=d.fp8_pack_sources(e)
  writes=collections.defaultdict(list)
  for w in re.finditer(r'(?m)^\s*(?:@!?[\w%]+\s+)?[\w.]+\s+(\{[^}]+\}|%r\d+)\s*,',e):
   for reg in re.findall(r'%r\d+',w[1]):writes[reg].append(w.start())
  for mma in d.FP8_MMA_PATTERN.finditer(e):
   for k in ['a0','a1','a2','a3','b0','b1']:
    reg=mma[k]
    if reg not in mapping:continue
    lo,hi,pos=mapping[reg]
    if pos>=mma.start():continue
    used+=1
    for source in [reg]:
     start=pos
     mid=[p for p in writes[source] if start<p<mma.start()]
     # Exclude the original pack's own starting indentation.
     mid=[p for p in mid if p>e.find(';',pos)]
     if mid and len(examples)<2:
      examples.append((reg,source,e[mid[0]:e.find('\n',mid[0])],e[mma.start():e.find('\n',mma.start())]))
 print(i,'mapped operand uses',used,'overwrite examples',examples)
