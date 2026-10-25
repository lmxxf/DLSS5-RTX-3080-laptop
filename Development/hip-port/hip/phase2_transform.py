"""Pair CPU Ampere weight tiles with explicit, audited static operand sites.

Never replace generic FP8 prep globally: Q/K/V and row-major weight paths retain it.
Applied after the original source transformations and before LLVM SSA cancellation.
"""
import re
FP8='__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12'
F16='__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12'

def masked(s):
    return re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"',lambda m:''.join('\n' if c=='\n' else ' ' for c in m[0]),s,flags=re.S)

def end_at(s,start,op='(',cl=')'):
    depth=1
    for i in range(start+1,len(s)):
        depth+=(s[i]==op)-(s[i]==cl)
        if depth==0:return i
    raise ValueError('unbalanced C++')

def args_of(s):
    depth=0;start=0;out=[]
    for i,c in enumerate(s):
        if c in '([{':depth+=1
        elif c in ')]}':depth-=1
        elif c==',' and depth==0:out.append(s[start:i].strip());start=i+1
    out.append(s[start:].strip());return out

def calls(body,funcs,replace):
    mask=masked(body);changes=[]
    pat=re.compile(r'\b('+ '|'.join(map(re.escape,funcs))+r')\s*\(')
    for m in pat.finditer(mask):
        end=end_at(mask,m.end()-1);args=args_of(body[m.end():end]);new=replace(m[1],args,body[max(0,m.start()-220):m.start()])
        if new is not None:changes.append((m.start(),end+1,new))
    for a,b,new in reversed(changes):body=body[:a]+new+body[b:]
    return body

def rewrite_weights(name,b):
    def change(fn,a,prior):
        if len(a)!=3:return None
        op=None
        if name=='cw_body' and fn.startswith('sm86_wmma_fp8_preshuffled_') and fn.endswith(('_a','_b')):
            flag='true' if '34944+' in prior else '(W16!=0)'
            return 'sm86_wmma_fp8_maybe_pre_'+fn[-1]+'<'+flag+'>('+','.join(a)+')'
        if (name.startswith('w2_') or 'w2_weight(' in b or 'w2_weight16(' in b) and fn in ('sm86_wmma_fp8_preshuffled_a','sm86_wmma_fp8_preshuffled_b'):
            flag='true' if 'diag+' in prior else 'sm86_phase2_fragment_weights'
            return 'sm86_wmma_fp8_maybe_pre_'+fn[-1]+'<'+flag+'>('+','.join(a)+')'
        # Phase-3 Q is recomputed at its consumer; its narrow activation was
        # already preshuffled by the source pass, just like the original q[].
        if name=='cw_body' and fn==FP8 and a[2].startswith('q_acc['):
            side='a' if a[0].startswith('feature[') else 'b'
            return 'sm86_wmma_fp8_maybe_pre_'+side+'<(W16!=0)>('+','.join(a)+')'
        if fn!=FP8:return None
        if name=='c5c_body' and re.match(r'(?:b(?:\[|$)|cb(?:\[|0$|1$))',a[0]):op='a'
        if name in ('vit_expand_blocked_body_w16','vit_stream_project_tiles','vit_project_frag_tiles','dot8_frag','vit_project_bytein_bout_body'):
            if re.match(r'(?:b\d?|y\d?)(?:\[.*\])?$',a[1]):op='b'
        if name in ('vit_expand_blocked_body','vit_expand_blocked_body_m','vit_contract_blocked_body'):
            if re.match(r'b[01]$',a[1]):op='b'
            elif a[1] in ('b','b[n]'):
                return 'sm86_wmma_fp8_maybe_weight_b<Frag>('+','.join(a)+')'
        if name=='split_projection_frag_w16_body':
            if a[0] in ('b0','b1'):op='a'
            elif a[1] in ('b0','b1'):op='b'
        if name=='mh_attention_project_frag_c512_w16_body':
            if a[0] in ('b0','b1'):op='a'
            elif a[1] in ('b0','b1'):op='b'
        if name=='c512_ffn_one_w2f8_w16_body':
            if a[0] in ('b0','b1','eb0','eb1'):op='a'
            elif a[1]=='cb':op='b'
        if name=='decoder_project2x_h16w_wide_body' and a[1].startswith('i2{bw['):op='b'
        if name=='mh_pool_project_group_body' and a[1].startswith('i2{') and 'b[' in a[1]:op='b'
        # Fragment-native C512 projection (8B twin, same host FragmentPackedMatrix).
        if name in ('mh_attention_project_frag_c512_body','split_projection_frag') and a[1]=='b':op='b'
        if 'diag+' in prior or '34944+' in prior or 'vit_weight_fragment_native(' in prior:
            if a[0]=='b':op='a'
            elif a[1]=='b':op='b'
        if ('frag_b(' in b or 'vit_weight_fragment_native(' in b) and 'if constexpr(Frag)' in b:
            if a[0]=='b':return 'sm86_wmma_fp8_maybe_weight_a<Frag>('+','.join(a)+')'
            if a[1]=='b':return 'sm86_wmma_fp8_maybe_weight_b<Frag>('+','.join(a)+')'
        if op:return 'sm86_wmma_fp8_weight_'+op+'('+','.join(a)+')'
    return calls(b,[FP8,'sm86_wmma_fp8_preshuffled_a','sm86_wmma_fp8_preshuffled_b'],change)

def packed_sums(name,b):
    b=re.sub(r'\s*(_Pragma\("unroll"\))\s*',r'\1 ',b)
    if name.startswith('mh_pool_project'):
        # The FP8 MMA results and previous H accumulators are exact half values.
        # C32 has only one K32 chunk; RNE addition to zero also preserves its RTZ result.
        old='_Pragma("unroll") for(uint j=0;j<4;j++){sum[j]=__sm86_c_to_ampere_f32(sum[j]);_Pragma("unroll") for(uint e=0;e<8;e++)acc[j][e]=H(acc[j][e]+sum[j][e]);}'
        if old in b:
            b=b.replace('f8 acc[4]{};','f8 acc[4]{};sm86_u4 packed_acc[4]{};')
            b=b.replace(old,'_Pragma("unroll") for(uint j=0;j<4;j++)packed_acc[j]=sm86_add_u4_f16x2(packed_acc[j],__sm86_c_to_ampere(sum[j]));')
            b=b.replace('acc[j]=__sm86_d_to_rdna4_f32(acc[j]);','acc[j]=__sm86_d_to_rdna4(packed_acc[j]);')
        old='sum=__sm86_c_to_ampere_f32(sum);_Pragma("unroll") for(uint e=0;e<8;e++)acc[e]=channels==32?Hrtz(acc[e]+sum[e]):H(acc[e]+sum[e]);'
        if old in b:
            b=b.replace('f8 acc{};','f8 acc{};sm86_u4 packed_acc{};').replace(old,'packed_acc=sm86_add_u4_f16x2(packed_acc,__sm86_c_to_ampere(sum));').replace('acc=__sm86_d_to_rdna4_f32(acc);','acc=__sm86_d_to_rdna4(packed_acc);')
    if name=='vit_contract_blocked_body':
        b=b.replace('f8 total[4]{};','f8 total[4]{};sm86_u4 packed_total[4]{};')
        pattern=r'(?:_Pragma\("unroll"\)\s*)?for\(uint n=0;n<4;n\+\+\)(?:_Pragma\("unroll"\)\s*)?for\(uint e=0;e<8;e\+\+\)\{if constexpr\(Partial\)([^;]+);else total\[n\]\[e\]\+=acc\[n\]\[e\];\}'
        b,count=re.subn(pattern,lambda m:'_Pragma("unroll") for(uint n=0;n<4;n++){if constexpr(Partial){_Pragma("unroll") for(uint e=0;e<8;e++){'+m[1]+';}}else{packed_total[n]=sm86_add_u4_f16x2(packed_total[n],__sm86_c_to_ampere(acc[n]));}}',b)
        if count:
            anchor='if constexpr(W16){'
            assert anchor in b
            init='if constexpr(!Partial){_Pragma("unroll") for(uint n=0;n<4;n++)packed_total[n]=__sm86_c_to_ampere(total[n]);}\n '
            b=b.replace(anchor,init+anchor,1)
            pos=b.rfind('if constexpr(!Partial)')
            b=b[:pos]+'if constexpr(!Partial){_Pragma("unroll") for(uint n=0;n<4;n++)total[n]=__sm86_d_to_rdna4(packed_total[n]);}\n '+b[pos:]
    if name=='vit_stream_project_tiles':
        b=b.replace('f8 total[TM][TN]{};','f8 total[TM][TN]{};sm86_u4 packed_total[TM][TN]{};')
        old='if(p==0)total[t][j]=__sm86_c_to_ampere_f32(total[t][j]);a[t][j]=__sm86_c_to_ampere_f32(a[t][j]);_Pragma("unroll") for(uint e=0;e<8;e++)total[t][j][e]+=a[t][j][e];'
        b=b.replace(old,'packed_total[t][j]=sm86_add_u4_f16x2(packed_total[t][j],__sm86_c_to_ampere(a[t][j]));')
        anchor=re.search(r'(?:#pragma clang loop unroll\(disable\)|_Pragma\("clang loop unroll\(disable\)"\))\s*for\(uint p=0;p<4;p\+\+\)',b)
        assert anchor, 'project partition preheader not found'
        init='_Pragma("unroll") for(uint t=0;t<TM;t++)_Pragma("unroll") for(uint j=0;j<TN;j++)packed_total[t][j]=__sm86_c_to_ampere(total[t][j]);\n '
        b=b[:anchor.start()]+init+b[anchor.start():]
        b=b.replace('total[t][j]=__sm86_d_to_rdna4_f32(total[t][j]);','total[t][j]=__sm86_d_to_rdna4(packed_total[t][j]);')
    if name=='decoder_project2x_h16w_wide_body':
        b=b.replace('f8 total{};','f8 total{};sm86_u4 packed_total{};')
        b=b.replace('a=__sm86_c_to_ampere_f32(a);_Pragma("unroll") for(uint e=0;e<8;e++)total[e]=p?total[e]+a[e]:a[e];','sm86_u4 pa=__sm86_c_to_ampere(a);packed_total=p?sm86_add_u4_f16x2(packed_total,pa):pa;')
        b=b.replace('total=__sm86_d_to_rdna4_f32(total);','total=__sm86_d_to_rdna4(packed_total);')
    return re.sub(r'([A-Za-z0-9_])_Pragma',r'\1 _Pragma',b)

def transform(text):
    # Original Phase-1 preprocessing has already selected the dynamic operands.
    def reduce(fn,a,prior):
        if len(a)!=3:return None
        if a[0]=='ones':return 'sm86_wmma_ones_a('+','.join(a[1:])+')'
        if a[1]=='ones':return 'sm86_wmma_ones_b('+a[0]+','+a[2]+')'
        if a[:2]==['zero','zero']:return a[2]
    text=calls(text,[F16],reduce)
    mask=masked(text);changes=[]
    # Definitions, not call expressions; default arguments may contain parentheses.
    pat=re.compile(r'\b(?:void|f8|i2)\s+(\w+)\s*\(')
    for m in pat.finditer(mask):
        end=end_at(mask,m.end()-1);start=end+1
        while start<len(mask) and mask[start].isspace():start+=1
        if start>=len(mask) or mask[start]!='{':continue
        stop=end_at(mask,start,'{','}');body=text[start+1:stop]
        body=rewrite_weights(m[1],body);body=packed_sums(m[1],body)
        if m[1]=='vit_stream_qkv_frag_bin_w5f8':body=body.replace('__sm86_prep_fp8(s','__sm86_unpack_fp8(s')
        changes.append((start+1,stop,body))
    for a,b,v in reversed(changes):text=text[:a]+v+text[b:]
    return text
