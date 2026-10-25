"""Controlled source rewrite: only C32 W16 expansion, invariant across h2."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hip'))
from phase2_transform import masked,end_at

def transform(text):
    mask=masked(text);start=mask.index('for(uint h2=0;h2<4;h2++)');end=end_at(mask,mask.index('{',start),'{','}')
    b=text[start:end+1]
    b,n=__import__('re').subn(r'sm86_wmma_fp8_maybe_pre_b<\(W16!=0\)>\(bp\.(lo|hi),input\[([01])\],',r'sm86_wmma_fp8_cached_input(bp.\1,cached_input[\2],',b)
    assert n==2,n
    # Put before the loop pragma as well, so nounroll still decorates the for.
    before=text.rfind('#pragma clang loop unroll(disable)',0,start)
    assert text[before:start].strip()=='#pragma clang loop unroll(disable)'
    text=text[:start]+b+text[end+1:]
    text=text[:before]+'sm86_u4 cached_input[2]={__sm86_unpack_fp8(input[0]),__sm86_unpack_fp8(input[1])};\n'+text[before:]
    helper='''__attribute__((device,always_inline)) inline sm86_f8 sm86_wmma_fp8_cached_input(sm86_i2 w,sm86_u4 input,sm86_f8 c){
 return __sm86_d_to_rdna4(sm86_mma_prepared_core(__sm86_unpack_fp8(w),input,__sm86_c_to_ampere(c)));}
'''
    # Prefix after the compatibility header's definitions, before the C32 reader.
    at=text.index('using cw_h2=')
    return text[:at]+helper+text[at:]
