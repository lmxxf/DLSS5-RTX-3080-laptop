"""Optional C32 register-Q experiment, after the established reader rewrites.

Mask bits follow cw_kind, with a separate bit 6 for Up. Zero leaves shared Q intact.
"""
import re
from phase2_transform import masked,end_at

def transform(text,q_mask=0,prefix_min_blocks=0,c32_min_blocks=0):
    if q_mask:
        mask=masked(text);m=re.search(r'\bvoid\s+cw_body\s*\(',mask)
        if m:
            i=end_at(mask,m.end()-1)+1
            while mask[i].isspace():i+=1
            assert mask[i]=='{';j=end_at(mask,i,'{','}')
            b=text[i+1:j]
            decl='i2 cw_qkv_smem[3][8][32];'
            assert b.count(decl)==1
            b=b.replace(decl,f'''i2 cw_qkv_smem[((({q_mask}u >> (Up?6u:cw_kind))&1u)!=0)?2:3][8][32];
 constexpr bool c32_register_q=(({q_mask}u >> (Up?6u:cw_kind))&1u)!=0;
 i2 q_reg0[2],q_reg1[2],q_reg2[2],q_reg3[2];''')
            old='cw_qkv_smem[part][qt*2+ci][qlane]=sm86_preshuffle_fp8(a);'
            assert b.count(old)==1
            b=b.replace(old,'''{i2 qkv_cached=sm86_preshuffle_fp8(a);
 if constexpr(c32_register_q){
  if(part==0){if(qt==0)q_reg0[ci]=qkv_cached;else if(qt==1)q_reg1[ci]=qkv_cached;else if(qt==2)q_reg2[ci]=qkv_cached;else q_reg3[ci]=qkv_cached;}
  else cw_qkv_smem[part-1][qt*2+ci][qlane]=qkv_cached;
 }else cw_qkv_smem[part][qt*2+ci][qlane]=qkv_cached;}''')
            old='i2 q[2]={cw_qkv_smem[0][qt*2][lane],cw_qkv_smem[0][qt*2+1][lane]};'
            assert b.count(old)==1
            b=b.replace(old,'''i2 q[2];
 if constexpr(c32_register_q){
 q[0]=qt==0?q_reg0[0]:qt==1?q_reg1[0]:qt==2?q_reg2[0]:q_reg3[0];
 q[1]=qt==0?q_reg0[1]:qt==1?q_reg1[1]:qt==2?q_reg2[1]:q_reg3[1];
 }else{q[0]=cw_qkv_smem[0][qt*2][lane];q[1]=cw_qkv_smem[0][qt*2+1][lane];}''')
            for old,new in [('cw_qkv_smem[1][kt*2+ci][lane],q[ci]','cw_qkv_smem[c32_register_q?0:1][kt*2+ci][lane],q[ci]'),('cw_qkv_smem[2][kt*2+ci][lane],prob[kt]','cw_qkv_smem[c32_register_q?1:2][kt*2+ci][lane],prob[kt]')]:
                assert b.count(old)==1
                b=b.replace(old,new)
            text=text[:i+1]+b+text[j:]
    if prefix_min_blocks:
        # Prefix-only avoids forcing unrelated, larger Up kernels to spill.
        pat=r'(__attribute__\(\(launch_bounds\()32(\)\)\)\s+void\s+c32_wave1_prefix\w*\s*\()'
        text,n=re.subn(pat,lambda m:m[1]+f'32,{prefix_min_blocks}'+m[2],text)
        assert n>0,'prefix launch-bounds site missing'
    if c32_min_blocks:
        pat=r'(__attribute__\(\(launch_bounds\()32(\)\)\)\s+void\s+c32_wave1_(?!up)\w*\s*\()'
        text,n=re.subn(pat,lambda m:m[1]+f'32,{c32_min_blocks}'+m[2],text)
        assert n>0,'C32 launch-bounds site missing'
    return text
