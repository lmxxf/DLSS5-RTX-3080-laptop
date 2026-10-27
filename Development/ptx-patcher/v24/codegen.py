"""Isolated V2.4 factors A=1, B-bias=2, B-quad=4, C-pool=8."""
import re,collections,bisect

def up(source,destination):
 return [f'prmt.b32 {destination}, {source}, {source}, 0x9180;',f'and.b32 {destination}, {destination}, 0x017f017f;',f'shl.b32 {destination}, {destination}, 7;','mov.b32 dlssnr_fp8_scale, 0x5c005c00;',f'mul.rn.f16x2 {destination}, {destination}, dlssnr_fp8_scale;']

def bias_pack(source,destination):
 from v22.codegen import pack
 lines=pack(source,destination)
 return [line.replace('0x003f003f','0x603f603f') for line in lines if line!='add.u32 dlssnr_v22_n, dlssnr_v22_n, 0x00c000c0;']

def quad(low,high,destination,bias=True):
 # Separate norm outputs keep the first result live without an extra mov.
 from v22.codegen import pack
 generate=bias_pack if bias else pack
 consts={'0x5f005f00':'vq_clamp','0x40004000':'vq_magic','0x24002400':'vq_threshold'}
 lines=['{','.reg .b32 vq_a,vq_sub,vq_t,vq_mask,vq_lo,vq_hi,vq_clamp,vq_magic,vq_threshold;']
 lines += [f'mov.b32 {name}, {value};' for value,name in consts.items()]
 for source,out in [(low,'vq_lo'),(high,'vq_hi')]:
  body=generate(source,'UNUSED')[:-2]
  for line in body:
   if line.startswith('mov.b32 dlssnr_v22_mask,'):continue
   for old,new in [('dlssnr_v22_a','vq_a'),('dlssnr_v22_sub','vq_sub'),('dlssnr_v22_t','vq_t'),('dlssnr_v22_n',out)]:line=line.replace(old,new)
   if line.startswith('min.f16x2'):line=line.replace('dlssnr_v22_mask','vq_clamp')
   elif line.startswith('add.rn.f16x2'):line=line.replace('dlssnr_v22_mask','vq_magic')
   elif line.startswith('set.lt.u32.f16x2'):line=line.replace('dlssnr_v22_mask, vq_a, dlssnr_v22_mask','vq_mask, vq_a, vq_threshold')
   else:line=line.replace('dlssnr_v22_mask','vq_mask')
   lines.append(line)
 lines += [f'prmt.b32 {destination}, vq_lo, vq_hi, 0x6420;','}']
 return lines


def fuse_quads(text,stats,bias,dp=None):
 if dp is None:
  import dlssnr_patcher as dp
 parts=re.split(r'(?=\.visible \.entry )',text);total=0
 for i,part in enumerate(parts):
  counts=collections.Counter(re.findall(r'%r[sd]?\d+',part));downs=collections.defaultdict(list)
  for m in dp.FP8_DOWN_PATTERN.finditer(part):downs[m['destination']].append(m)
  boundaries=sorted([m.start() for m in re.finditer(r'(?m)^\s*[\w$]+\s*:',part)]+[m.end() for m in re.finditer(r'\bbra(?:\.uni)?\s+[^;]+;|\b(?:ret|exit);',part)])
  braces=list(re.finditer(r'[{}]',part));bp=[m.start() for m in braces];depth=[0]
  for m in braces:depth.append(depth[-1]+(1 if m[0]=='{' else -1))
  replacements=[]
  for pack in dp.FP8_PACK_PATTERN.finditer(part):
   lo,hi=pack['low'],pack['high']
   if pack['guard'] or lo==hi or counts[lo]!=2 or counts[hi]!=2 or len(downs[lo])!=1 or len(downs[hi])!=1:continue
   a,z=downs[lo][0],downs[hi][0]
   if a['guard'] or z['guard'] or max(a.end(),z.end())>pack.start():continue
   points=[a.start(),z.start(),pack.start()]
   if len({bisect.bisect_right(boundaries,x) for x in points})!=1:continue
   # Function-root declarations allow nonadjacent cvts, without crossing
   # lexical scopes or moving either source read across intervening writes.
   if any(depth[bisect.bisect_left(bp,x)]!=1 for x in points):continue
   body=quad(a['source'],z['source'],pack['destination'],bias)
   body=[line.replace('vq_',f'vq{total}_') for line in body]
   core=(len(body)-7)//2
   assert 2*core+7==len(body)
   declaration='\n'.join(body[1:5])+'\n'
   alo='\n'.join(body[5:5+core]);zhi='\n'.join(body[5+core:-2])
   if a.start()<z.start():alo=declaration+alo
   else:zhi=declaration+zhi
   replacements += [(a.start(),a.end(),alo),(z.start(),z.end(),zhi),(pack.start(),pack.end(),body[-2])];total+=1
  for start,end,replacement in sorted(replacements,reverse=True):part=part[:start]+replacement+part[end:]
  parts[i]=part
 stats.add('fused_quad_pairs',total);stats.add('fp16_to_fp8',2*total)
 return ''.join(parts)

def jit_render(matches,packed_sources,*,builder):
 b=builder
 from ptx_mapped import mapped_at
 operands=list(dict.fromkeys(m[n] for m in matches for n in ('a0','a1','a2','a3','b0','b1')))
 mapped=mapped_at(packed_sources,matches[0].start());quant_lines,quant_names=b.dp.mapped_fp16_sources(mapped,operands)
 first={r:min(i for i,m in enumerate(matches) if r in [m[n] for n in ('a0','a1','a2','a3','b0','b1')]) for r in operands}
 last={r:max(i for i,m in enumerate(matches) if r in [m[n] for n in ('a0','a1','a2','a3','b0','b1')]) for r in operands}
 # Upfront decoding reads run-entry values. Delayed reads must precede ANY
 # earlier MMA write of the source or its mapped FP16 alias.
 when={}
 for r in operands:
  refs=[quant_names[x] for x in mapped[r][:2]] if r in mapped else [r]
  clobbers=[i for i,m in enumerate(matches) if m['d0'] in refs or m['d1'] in refs]
  when[r]=min([first[r]]+clobbers)
 names={};free=[];size=0;body=[]
 for i,m in enumerate(matches):
  for r in operands:
   if when[r]!=i:continue
   if free:pair=free.pop()
   else:pair=(f'vp_{size}_0',f'vp_{size}_1');size+=1
   names[r]=pair;lo,hi=pair
   if r in mapped:
    a,z,_=mapped[r];body += [f'prmt.b32 {lo}, {quant_names[a]}, {quant_names[z]}, 0x5410;',f'prmt.b32 {hi}, {quant_names[a]}, {quant_names[z]}, 0x7632;']
   else:body+=b.even_odd_decode_lines(r,lo,hi)
  for parity in [0,1]:
   aa=[names[m[n]][parity] for n in ('a0','a1','a2','a3')];bb=[names[m[n]][parity] for n in ('b0','b1')];cc=[m['c0'],m['c1']] if parity==0 else [m['d0'],m['d1']]
   body.append(f'mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16 {{{m["d0"]}, {m["d1"]}}}, {{{", ".join(aa)}}}, {{{", ".join(bb)}}}, {{{", ".join(cc)}}};')
  for r in operands:
   if last[r]==i:free.append(names.pop(r))
 lines=['{','.reg .b32 '+', '.join(f'vp_{i}_{j}' for i in range(size) for j in [0,1])+';']
 if any(r not in mapped for r in operands):lines+=b.fast_fp8_conversion_declarations()+['mov.b32 dlssnr_fp8_scale, 0x5c005c00;']
 return '\n'.join(lines+quant_lines+body+['}'])

def apply(b,mask):
 if mask&1:
  b.dp.fp8_pair_to_half_lines=up;b.dp.fp8_conversion_declarations=lambda:['.reg .b32 dlssnr_fp8_scale;']
 if mask&2:b.dp.half_pair_to_fp8_lines=bias_pack
 if mask&4:
  old=b.stock_lower_conversions
  def convert(text,stats):return old(fuse_quads(text,stats,bool(mask&2),b.dp),stats)
  b.dp.lower_fp8_conversions=convert
 if mask&8:
  from functools import partial
  b.dp.render_fp8_mma_run=partial(jit_render,builder=b)
