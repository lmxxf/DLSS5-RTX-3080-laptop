"""Emit the two opt-in production modules from canonical HIP sources."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/wave-owned-production');OUT.mkdir(parents=True,exist_ok=True)
read=lambda name:(ROOT/'hip'/name).read_text()
c32='#define CW_ROLL_HIDDEN 1\n#define CW_ROLL_WINDOW 1\n#define CW_VEC_INPUT 1\n#define CW_PREFIX_SPLIT 1\n#define HIP_ISA_HALF 1\n#define HIP_PREPACKED_WEIGHTS 1\n'+read('c32_fused_ffn_attention.hip')+'\n'+read('wave_owned_c32.inc')
core=read('wave_owned_mh.inc');attention=core[core.index(' // One wave owns all keys'):core.index('#define W2_KERNEL')]
a='i2 a=w2_load<C>(plane0,qt,ct);';assert attention.count(a)==1
attention=attention.replace(a,'''i2 a;
#if W2_DIRECT_FEATURE
   __builtin_memcpy(&a,feature+w2_pixel(win,qt*16+rc,workw)*C+ct*16+gr*8,8);
#else
   a=w2_load<C>(plane0,qt,ct);
#endif
''')
mh='#define W2_FRAGMENT_WEIGHTS 1\n#define W2_LAUNDER_QKV 1\n#define W2_SCHED_FENCE 1\n#define W2_ROLL_QUERY 1\n#define W2_HIDDEN_TILES 2\n#define HIP_ISA_HALF 1\n#define HIP_PREPACKED_WEIGHTS 1\n#define HIP_FFN_HOIST_RES 2\n#define HIP_PDL_KERNELS 0\n'+read('multihead_fast_padded.hip')+'\n'+core+'\n#if !W2_DEFER_Q\n'+read('wave_owned_attention_setup.inc')+attention+'\n'+read('wave_owned_attention_exports.inc')+'\n#endif\n'
manifest={}
for name,source in [('c32-wave1',c32),('c64-wave2',mh)]:
 (OUT/(name+'.hip')).write_text(source);manifest[name]=hashlib.sha256(source.encode()).hexdigest()
(OUT/'sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(OUT)
