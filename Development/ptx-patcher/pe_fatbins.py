"""Place compiled fatbins without lowering optimization to satisfy old PE slots.

Oversized blobs go into one extra data section. Only verified LEA r8,[rip+disp32]
references or an existing absolute wrapper pointer are relocated; unknown layouts fail.
"""
import struct

def assemble(data, locations, blobs, dp):
    data=bytearray(data)
    sections=dp.read_pe_sections(data)
    pe=dp.pe_header_offset(data);opt=pe+24
    base=struct.unpack_from('<Q',data,opt+24)[0]
    section_align,file_align=struct.unpack_from('<II',data,opt+32)
    align=lambda n,a:(n+a-1)//a*a
    grown={i:blob for i,blob in blobs.items() if len(blob)>locations[i].size}
    if grown:
        section_count=len(sections)
        table=opt+struct.unpack_from('<H',data,pe+20)[0]
        header=table+section_count*40
        first_raw=min(s.raw_offset for s in sections if s.raw_size)
        assert header+40<=first_raw and not any(data[header:header+40]), 'No spare PE section header'
        raw_start=align(len(data),file_align)
        rva_start=align(max(s.virtual_address+max(s.virtual_size,s.raw_size) for s in sections),section_align)
        payload=bytearray();offsets={}
        for i,blob in sorted(grown.items()):
            payload.extend(bytes(align(len(payload),8)-len(payload)))
            offsets[i]=len(payload);payload.extend(blob)
        raw_size=align(len(payload),file_align)
        data.extend(bytes(raw_start-len(data)));data.extend(payload);data.extend(bytes(raw_size-len(payload)))
        data[header:header+40]=struct.pack('<8sIIIIIIHHI',b'.dlssptx',len(payload),rva_start,raw_size,raw_start,0,0,0,0,0xc0000040)
        struct.pack_into('<H',data,pe+6,section_count+1)
        struct.pack_into('<I',data,opt+56,align(rva_start+len(payload),section_align))
        old_initialized=struct.unpack_from('<I',data,opt+8)[0]
        struct.pack_into('<I',data,opt+8,old_initialized+raw_size)
    manifest=[]
    for i,blob in sorted(blobs.items()):
        loc=locations[i]
        if i not in grown:
            data[loc.offset:loc.offset+loc.size]=blob+bytes(loc.size-len(blob))
            manifest.append((i,'inline',loc.offset,len(blob)));continue
        sec=next(s for s in sections if s.raw_offset<=loc.offset<s.raw_offset+s.raw_size)
        old_rva=sec.virtual_address+loc.offset-sec.raw_offset
        new_rva=rva_start+offsets[i]
        refs=[]
        # These blobs are registered by a direct 7-byte LEA r8 in this DLL.
        for code in sections:
            begin=code.raw_offset;end=begin+code.raw_size;pos=begin
            while (pos:=data.find(b'\x4c\x8d\x05',pos,end))>=0:
                ins_rva=code.virtual_address+pos-code.raw_offset
                displacement=struct.unpack_from('<i',data,pos+3)[0]
                if ins_rva+7+displacement==old_rva:
                    refs.append(('lea',pos,ins_rva))
                pos+=3
        pointer=struct.pack('<Q',base+old_rva);pos=0
        while (pos:=data.find(pointer,pos))>=0:
            refs.append(('pointer',pos,0));pos+=8
        assert len(refs)==1, f'Fatbin {i}: expected one verified host reference, got {refs}'
        kind,pos,ins_rva=refs[0]
        if kind=='lea':struct.pack_into('<i',data,pos+3,new_rva-(ins_rva+7))
        else:struct.pack_into('<Q',data,pos,base+new_rva)
        data[loc.offset:loc.offset+loc.size]=bytes(loc.size)
        manifest.append((i,'section',raw_start+offsets[i],len(blob),kind,pos,old_rva,new_rva))
    dp.read_pe_sections(data)
    return data,manifest
