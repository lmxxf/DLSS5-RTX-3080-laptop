"""Diagnostic only: extra UAV argument; count executed FP8-MMA runs/loop headers."""
from pathlib import Path
import sys,os,json,re,hashlib
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from pe_fatbins import assemble
inv=json.loads((p/'natural-loops.json').read_text());names=sorted(inv);ids={n:i for i,n in enumerate(names)};assert len(ids)<=64;old_lower=b.fast_lower_fp8_mma_entry

def count_code(offset,value):
 return '{\n.reg .u32 vc_lane; .reg .pred vc_p; .reg .u64 vc_old;\nmov.u32 vc_lane,%laneid;\nsetp.eq.u32 vc_p,vc_lane,0;\n'+f'@vc_p atom.global.add.u64 vc_old,[v25_counter+{offset}],{value};\n'+'}\n'
def lower_entry(text):
 m=re.search(r'\.entry\s+(\w+)',text)
 if not m or m[1] not in ids:return old_lower(text)
 name=m[1];idx=ids[name];assert len(inv[name]['loops'])<=2;needle=re.search(r'(?s)(\.param\s+\.align\s+8\s+\.b8\s+\w+\[\d+\])\s*\)',text);assert needle
 text=text[:needle.start()]+needle[1]+',\n.param .u64 v25_counter_param\n)'+text[needle.end():]
 brace=text.index('{',text.index('.entry'));text=text[:brace+1]+'\n.reg .u64 v25_counter;\nld.param.u64 v25_counter,[v25_counter_param];\n'+text[brace+1:]
 for j,loop in enumerate(inv[name]['loops']):
  label=loop['header']+':';assert text.count(label)==1;text=text.replace(label,label+'\n'+count_code(idx*64+8*(j+1),1),1)
 text=re.sub(r'\bmma\.sync\.aligned\.m16n8k16\.row\.col\.f16\.f16\.f16\.f16\s+[^;]+;',lambda m:count_code(idx*64,1)+m[0],text)
 render=b.dp.render_fp8_mma_run
 def wrapped(matches,sources):
  code=render(matches,sources);ops=[line.strip().split()[0] for line in code.splitlines() if line.strip() and not line.strip().startswith(('{','}','.'))]
  prmt=sum(op.startswith('prmt.') for op in ops);integer=sum(op.startswith(('and.','or.','xor.','shl.','shr.','lop3.','mad.','mov.')) for op in ops);half=sum(op.startswith('mul.rn.f16x2') for op in ops);unmapped=code.count('0xb391;');mapped=code.count('0x5410;')
  weights={0:2*len(matches),3:prmt,4:integer,5:half,6:unmapped,7:mapped};return ''.join(count_code(idx*64+8*j,value) for j,value in weights.items() if value)+code
 b.dp.render_fp8_mma_run=wrapped
 try:return old_lower(text)
 finally:b.dp.render_fp8_mma_run=render
b.dp.lower_fp8_mma_entry=lower_entry
root=Path('/mnt/c/DLSS5-5090-dll');raw=(root/'nvngx_dlssnr.dll').read_bytes();locs=b.dp.find_fatbins(raw);base=(root/'nvngx_dlssnr_sm86_v24.dll').read_bytes();os.environ['DLSSNR_BUILD_CACHE']=str(p/'artifacts/counters');blobs={};log={}
for fb in [0,4,5]:
 loc=locs[fb];_,blob,msg=b.worker_compile_fatbin((fb,raw[loc.offset:loc.offset+loc.size],True,True,'multidef',False,'evenodd',255,'swar','mbarrier','prmt8',8));blobs[fb]=blob;log[str(fb)]=msg;print(msg,flush=True)
data,manifest=assemble(base,locs,blobs,b.dp);b.fast_update_pe_checksum(data);out=root/'nvngx_dlssnr_v25_counter_DIAGNOSTIC.dll';out.write_bytes(data);(p/'counter-build.json').write_text(json.dumps({'path':str(out),'sha256':hashlib.sha256(data).hexdigest(),'ids':ids,'counter_stride':64,'stats':log,'manifest':manifest,'bins':{'0':'executed HMMA.16816 semantic warp instructions','1/2':'natural compute-loop header warp visits','3':'MMA-decoder PTX PRMT warp operations','4':'MMA-decoder PTX integer and mov warp operations','5':'MMA-decoder f16x2 multiply warp operations','6':'unmapped operand-pair decode events','7':'mapped operand-pair forwarding events'},'diagnostic_only':True},indent=2)+'\n')
# Generated name-to-counter mapping consumed only by the diagnostic runner.
lines=['static int counter_id(const std::string&n){']+[f'if(n=="{name}")return {idx};' for name,idx in ids.items()]+['return -1;}'];(p/'counter_ids.h').write_text('\n'.join(lines)+'\n')
