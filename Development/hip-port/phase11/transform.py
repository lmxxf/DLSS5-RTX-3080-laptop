"""Experimental Phase11 transformations; half-store-only is a negative control."""
from phase11_transform import HALF_PACK_HELPER,pack_ffn_half_features

def fold_ffn_half_store(text):
 old='h8 rounded=cw_rtz_half8(ffn[ci]);'
 assert text.count(old)==1,text.count(old)
 return text.replace(old,'h8 rounded=__builtin_convertvector(ffn[ci],h8);')
