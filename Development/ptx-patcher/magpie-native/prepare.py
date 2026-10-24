from pathlib import Path
import hashlib,struct,json,shutil,os,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dlssnr_patcher as dp
ROOT=Path('/mnt/c/DLSS5-5090-dll');LIVE=ROOT/'发布打包/Magpie-DLSS5-RTX30-0.1.0';TEST=ROOT/'magpie-native-test'
sha=lambda b:hashlib.sha256(b).hexdigest()
expected='ec0a90fcf36430e5204f0df5e2b955d21fe60443250c51e8670143cf20ad880e'
def cp(a,b):
 if Path(a).suffix.lower() in ['.ini','.json','.txt','.log']:return shutil.copy2(a,b)
 try:os.link(a,b)
 except OSError:shutil.copy2(a,b)
 return b
shutil.copytree(LIVE,TEST,copy_function=cp,ignore=shutil.ignore_patterns('logs','cache','*.log','*.bak','DLSS5-AMD','dxgi.dll','dlss5-amd.addon64'),dirs_exist_ok=True)
p=TEST/'Magpie.exe';raw=bytearray(p.read_bytes());assert sha(raw)==expected
# A single Set(int preset) call; immutable surrounding LEA identifies the parameter.
old=bytes.fromhex('45 33 c0 48 8b 01 ff 50 18');target_rva=0x208f58
secs=dp.read_pe_sections(raw);site=dp.rva_to_file_offset(target_rva,secs);assert raw[site:site+9]==old
assert raw[site-7:site]==bytes.fromhex('48 8d 15 98 7e 12 00')
pe=dp.pe_header_offset(raw);opt=pe+24;table=opt+struct.unpack_from('<H',raw,pe+20)[0]
text=secs[0];cave= text.raw_offset+((text.virtual_size+15)//16*16);cave_rva=text.virtual_address+cave-text.raw_offset
stub=bytes.fromhex('41 b8 02 00 00 00 48 8b 01 ff 50 18');stub+=b'\xe9'+struct.pack('<i',target_rva+9-(cave_rva+len(stub)+5))
assert cave+len(stub)<=text.raw_offset+text.raw_size
assert all(x in [0,0xcc,0x90] for x in raw[cave:cave+len(stub)])
raw[cave:cave+len(stub)]=stub;raw[site:site+9]=b'\xe9'+struct.pack('<i',cave_rva-(target_rva+5))+b'\x90'*4
struct.pack_into('<I',raw,table+8,max(text.virtual_size,cave_rva+len(stub)-text.virtual_address))
dp.update_pe_checksum(raw)
p.unlink();p.write_bytes(raw)
# Correct the status text too, so logs cannot pretend this is still preset zero.
data=p.read_bytes();assert data.count(b'preset=fixed-0')==1;data=data.replace(b'preset=fixed-0',b'preset=fixed-2');p.write_bytes(data)
exe=bytearray(data);dp.update_pe_checksum(exe);p.write_bytes(exe)
shutil.copy2(ROOT/'nvngx_dlssnr_sm86_fast.dll',TEST/'nvngx_dlssnr.dll')
assert sha((TEST/'nvngx_dlssnr.dll').read_bytes())=='3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a'
cfg=TEST/'config/config.json';j=json.loads(cfg.read_text(encoding='utf-8-sig'))
j['autoCheckForUpdates']=False
j['scalingModes'][6]['name']='DLSS5-RTX30-PTX'
j['scalingModes'][6]['effects']=[{'name':'DLSSNR\\DLSSNR_AI_Filter','scalingType':0,'scale':{'x':1.,'y':1.},'parameters':{'style':1.,'intensity':1.,'localToneStrength':1.,'localStructureStrength':1.,'skinStructureStrength':-1.,'useAutoMask':1.,'uiCorrection':0.,'motionVectorQuality':0.,'residualMultiplier':1.,'residualSaturation':1.,'residualLightness':1.,'shadowStructureMultiplier':1.,'reflectionGlowMultiplier':1.,'enableInputResolutionScaling':0.,'inputResolutionPercent':100.}}, {'name':'DLSS\\DLSS_SR','scalingType':1,'scale':{'x':1.,'y':1.},'parameters':{'opticalFlowMethod':0.}}]
j['profiles'][0]['scalingMode']=6;cfg.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
meta={'original_exe_sha256':expected,'preset2_exe_sha256':sha(p.read_bytes()),'site_rva':hex(target_rva),'cave_rva':hex(cave_rva),'stub_hex':stub.hex()}
Path(__file__).with_name('preset2-patch.json').write_text(json.dumps(meta,indent=2))
print(meta)
