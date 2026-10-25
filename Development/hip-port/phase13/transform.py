"""Stream each hp activation into its two independent C32 contraction chains.
No h2 predecode/Graph/precision changes. Preserve hp0,hp1 accumulation order.
"""
from phase2_transform import masked,end_at

def transform(s,site):
 assert site in ['prefix','post','both']
 mask=masked(s);a=mask.index('if constexpr(W16==1){',mask.index('void cw_body('));z=end_at(mask,a+len('if constexpr(W16==1)'),'{','}')
 old=s[a:z+1]
 contract='''_Pragma("unroll") for(uint ci=0;ci<2;ci++){
     cw_i2_pair cp=cw_matrix16(fw+4608,(ci*4+h2)*512+(g*16+r)*16);
     ffn[ci]=sm86_wmma_fp8_maybe_pre_b<(W16!=0)>(cp.lo,act[0],ffn[ci]);
     ffn[ci]=sm86_wmma_fp8_maybe_pre_b<(W16!=0)>(cp.hi,act[1],ffn[ci]);
    }'''
 assert contract in old
 new=old.replace('i2 act[2];','').replace(contract,'')
 immediate='''i2 activation=sm86_d_bytes_to_ab(a);
    _Pragma("unroll") for(uint ci=0;ci<2;ci++){
     cw_i2_pair cp=cw_matrix16(fw+4608,(ci*4+h2)*512+(g*16+r)*16);
     ffn[ci]=sm86_wmma_fp8_maybe_pre_b<true>(hp==0?cp.lo:cp.hi,activation,ffn[ci]);
    }'''
 assert new.count('act[hp]=sm86_d_bytes_to_ab(a);')==1
 new=new.replace('act[hp]=sm86_d_bytes_to_ab(a);',immediate)
 cond={'prefix':'Prefix','post':'Post','both':'(Prefix||Post)'}[site]
 # Only target W16 branch; other entrypoints are byte-for-byte original source.
 start=old.index('{')
 return s[:a]+old[:start+1]+f'if constexpr({cond}){{'+new[start+1:-1]+'}else{'+old[start+1:-1]+'}}'+s[z+1:]
