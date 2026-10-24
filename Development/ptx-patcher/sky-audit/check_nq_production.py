from pathlib import Path
import hashlib,json
from build_nq_controls import b,multidef_sources,no_quant
original=b.stock_pack_sources if hasattr(b,'stock_pack_sources') else b.dp.fp8_pack_sources

def setup():
 b.dp.fp8_conversion_declarations=b.fast_fp8_conversion_declarations
 b.dp.fp8_pair_to_half_lines=b.fast_fp8_pair_to_half_lines
 b.dp.half_conversion_declarations=b.fast_half_conversion_declarations
 b.dp.half_pair_to_fp8_lines=b.fast_half_pair_to_fp8_lines
 b.dp.render_fp8_mma_run=b.fast_render_fp8_mma_run
 b.dp.mapped_fp16_sources=no_quant
setup()
old={};new={}
for mode,result in [('control',old),('production',new)]:
 b.dp.fp8_pack_sources=multidef_sources if mode=='control' else lambda t:original(t,local_only=False)
 for i in range(7):
  t=Path(f'/tmp/dlss-sky-audit/fatbin{i:02d}.ptx').read_text();out,_=b.dp.transform_ptx(t,b.dp.AMPERE)
  result[i]=hashlib.sha256(out.encode()).hexdigest()
print('Control vs production PTX identical:',old==new)
assert old==new
Path(__file__).with_name('nq-production-ptx-hashes.json').write_text(json.dumps(old,indent=2))
