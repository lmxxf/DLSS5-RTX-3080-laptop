"""Elide D -> RDNA4 -> AB only across coordinate-independent quantizers.

Runs after the established source rewrites. Query/key normalization, positional
biases, residual element-addressing and final outputs deliberately keep RDNA4.
"""
import re
from phase2_transform import masked,end_at

def amp(expr):return f'{expr}=sm86_unpack_acc(__sm86_c_to_ampere({expr}));'

def rewrite_body(b,c32):
    changes=[]
    # Each preprocessed pack8 region is a local scalar, coordinate-free map.
    pack='cw_pack8' if c32 else 'w2_pack8'
    pat=re.compile(r'\bi2 (\w+);float \1_t\[8\];(.*?)\1='+pack+r'(?:<[^;]+?>)?\(\1_t\);',re.S)
    for m in pat.finditer(b):
        var,q=m[1],m[2]
        reads=re.findall(r'\b((?:expanded|contract|result)(?:\[[^\]\n]+\])*|acc|av)\[e\]',q)
        if not reads:continue
        expr=reads[0]
        if any(r!=expr for r in reads):raise ValueError('multiple accumulator sources in quantizer')
        if c32 and expr not in ('expanded','acc'):continue
        if c32 and expr=='acc' and not b[m.end():m.end()+100].startswith('av[ci]='):continue
        # The existing next preshuffle must consume this exact packed variable.
        tail=b[m.end():m.end()+240];shuffle=f'sm86_preshuffle_fp8({var})';pos=tail.find(shuffle)
        if pos<0:continue
        if c32 and expr=='expanded' and not (tail.startswith('\n     act[hp]=') or tail.startswith('\n    a=') or 'act[hp]=' in tail[:pos] or tail.lstrip().startswith('a=')):
            raise ValueError('unexpected C32 expansion consumer: '+tail[:100])
        changes.append((m.start(),m.start(),amp(expr)))
        p=m.end()+pos;changes.append((p,p+len(shuffle),f'sm86_d_bytes_to_ab({var})'))
    # RTZ-pair fallback packs `rounded` rather than indexing contract directly.
    if not c32:
        for m in re.finditer(r'f8 rounded=w2_rtz8\((contract(?:\[[^\]]+\])+)\);',b):
            tail=b[m.end():];n=re.search(r'\bi2 (\w+);float \1_t\[8\];.*?\1=w2_pack8\(\1_t\);',tail,re.S)
            if not n:continue
            var=n[1];sh=f'sm86_preshuffle_fp8({var})';pos=tail.find(sh,n.end())
            assert 0<=pos<n.end()+200
            changes.append((m.start(),m.start(),amp(m[1])))
            p=m.end()+pos;changes.append((p,p+len(sh),f'sm86_d_bytes_to_ab({var})'))
    for a,z,new in sorted(changes,reverse=True):b=b[:a]+new+b[z:]
    return b,len(changes)//2

def transform(text,c32=True,wave2=True,bounds=True):
    mask=masked(text);changes=[]
    for name,on in [('cw_body',c32),('swin_wave2_body',wave2)]:
        if not on:continue
        m=re.search(r'\bvoid\s+'+name+r'\s*\(',mask)
        if not m:continue
        i=end_at(mask,m.end()-1)+1
        while mask[i].isspace():i+=1
        assert mask[i]=='{';j=end_at(mask,i,'{','}')
        b,n=rewrite_body(text[i+1:j],name=='cw_body')
        assert n>=3 if name=='cw_body' else n>=6,(name,n)
        changes.append((i+1,j,b))
    for a,z,b in reversed(changes):text=text[:a]+b+text[z:]
    if bounds:
        text=re.sub(r'(__attribute__\(\(launch_bounds\()(?:32|64)(\)\)\)\s+void\s+split_ffn_one\w*\s*\()',r'\g<1>64,8\2',text)
        text=re.sub(r'(__attribute__\(\(launch_bounds\()32(\)\)\)\s+void\s+vit_stream_project_n64\w*\s*\()',r'\g<1>32,16\2',text)
    return text

def low_register_fp8(text):
    """Use the bit-equivalent Phase-6 expression in two register-sensitive modules.

The monolithic Phase-7 asm raised live ranges in these modules. Bounds alone
spilled. Keep the Phase-7 clamp/LOP3 improvements and all layout transforms.
"""
    mask=masked(text);m=re.search(r'\bsm86_f32_to_e4m3_byte\s*\(float x\)',mask);assert m
    i=mask.index('{',m.end());j=end_at(mask,i,'{','}')
    body='''
    sm86_u32 b=__builtin_bit_cast(sm86_u32,x),s=(b>>24)&128,a=b&0x7fffffff;
    float magic;
    asm("add.rn.f32 %0,%1,0f46800000;":"=f"(magic):"f"(__builtin_bit_cast(float,a)));
    sm86_u32 sub=__builtin_bit_cast(sm86_u32,magic)&255,r=a+0x7ffff+((a>>20)&1),norm=r>=0x43e00000?126:((r>>20)-960);
    return s|((a<0x3c800000)?sub:((a>=0x7f800000)?127:norm));
'''
    return text[:i+1]+body+text[j:]
