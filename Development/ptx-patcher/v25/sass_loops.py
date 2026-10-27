from pathlib import Path
import re,json,sys,subprocess,collections
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));from cfg_loops import graph

def parse_sass(text):
 ins=[];address={}
 for m in re.finditer(r'/\*([0-9a-f]+)\*/\s+(@!?(?:UP|P)(?:\d+|T)\s+)?([A-Z][\w.]*)([^;]*);',text):
  pc=int(m[1],16);op=m[3];args=m[4].strip();address[pc]=len(ins);ins.append({'start':pc,'end':pc+16,'op':('mma.sync.sass' if op.startswith('HMMA') else op.lower()),'sass_op':op,'args':args,'guard':(m[2] or '').strip(),'text':f'{pc:04x}: '+m[0].split('*/',1)[1].strip()})
 # Local NOINC calls in these kernels are non-returning structured exits.
 assert not any(x['sass_op'].startswith('RET') for x in ins),'Subroutine RET requires a call-aware CFG'
 for x in ins:
  if x['sass_op']=='CALL.REL.NOINC' and re.search(r'0x([0-9a-f]+)',x['args']):x['op']='bra'
 targets={int(re.search(r'0x([0-9a-f]+)',x['args'])[1],16) for x in ins if x['op']=='bra'}
 labels={f'$S_{pc:x}':i for pc,i in address.items() if pc in targets or i==0}
 for x in ins:
  if x['op']=='bra':x['args']=f'$S_{int(re.search(r"0x([0-9a-f]+)",x["args"])[1],16):x}'
 return graph(ins,labels)
if __name__=='__main__':
 raw=(p/'artifacts/fb05.sass').read_text();out={}
 for ch in raw.split('Function : ')[1:]:
  name=ch.splitlines()[0].strip()
  if name not in json.loads((p/'natural-loops.json').read_text()):continue
  ins,blocks,loops=parse_sass(ch);compute=[l for l in loops if l['mma_sites']];out[name]=compute
  if name in ['cc_vit_1d_ffn_expand_chained_fp8','cc_vit_1d_ffn_contract_chained_fp8','cc_vit_1d_qkv_chained_fp8']:
   print(name)
   for l in compute:print(l['header'],l['mma_sites'],l['tail'])
 (p/'sass-natural-loops.json').write_text(json.dumps(out,indent=2)+'\n')
