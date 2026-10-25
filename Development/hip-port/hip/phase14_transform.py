"""Match the operand ABI after preshuffling the legacy ViT attention Q/P.

The broad preshuffle insertion also reaches vit_attention_fused_body. Its QK/PV
operands are on the A side; unlike transposed_score_body they were never matched
by the old B-side substitutions. Only this function's two consumers change.
"""
import re
from phase2_transform import masked,end_at

def fix_legacy_attention_abi(text):
 mask=masked(text);m=re.search(r'\bvoid\s+vit_attention_fused_body\s*\(',mask)
 if not m:return text
 a=mask.index('{',end_at(mask,m.end()-1));z=end_at(mask,a,'{','}');body=text[a+1:z]
 assert body.count('q[0]=sm86_preshuffle_fp8(q[0]);q[1]=sm86_preshuffle_fp8(q[1]);')==1,'Q producer ABI changed'
 assert body.count('xb=sm86_preshuffle_fp8(xb);')==1,'P producer ABI changed'
 for old,new in [
  ('a=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(q[k/16],y,a);','a=sm86_wmma_fp8_preshuffled_a(q[k/16],y,a);'),
  ('acc[c]=__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(xb,y,acc[c]);','acc[c]=sm86_wmma_fp8_preshuffled_a(xb,y,acc[c]);')]:
  assert body.count(old)==1,('attention consumer ABI changed',old)
  body=body.replace(old,new)
 return text[:a+1]+body+text[z:]
