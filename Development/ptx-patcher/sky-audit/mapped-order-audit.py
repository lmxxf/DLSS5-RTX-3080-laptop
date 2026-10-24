from pathlib import Path
import sys,re,collections
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dlssnr_patcher as d
for i in range(7):
 txt=Path('/tmp/dlss-sky-audit/fatbin%02d.ptx'%i).read_text();count=0;examples=[]
 for e in re.split(r'(?m)^\s*(?:\.visible\s+)?\.entry\b',txt)[1:]:
  downs={v['destination']:v for v in d.FP8_DOWN_PATTERN.finditer(e)}
  packs={v['destination']:v for v in d.FP8_PACK_PATTERN.finditer(e)}
  mapping=d.fp8_pack_sources(e)
  for mma in d.FP8_MMA_PATTERN.finditer(e):
   for k in ['a0','a1','a2','a3','b0','b1']:
    reg=mma[k]
    if reg not in mapping or mapping[reg][2]>=mma.start():continue
    p=packs[reg]
    for side in ['low','high']:
     cv=downs[p[side]]
     if cv.start()>p.start():
      count+=1
      if len(examples)<2:examples.append((reg,p[side],cv['source'],p.start(),mma.start(),cv.start()))
 print(i,'down conversion textually after pack, mapped uses',count,'examples',examples)
