from pathlib import Path
import json
from build_safe import b
from pe_fatbins import assemble
root=Path('/mnt/c/DLSS5-5090-dll')
data=bytearray((root/'nvngx_dlssnr.dll').read_bytes());b.dp.strip_authenticode(data)
locs=b.dp.find_fatbins(data);b.dp.apply_host_patches(data,(b.dp.AMPERE,))
blobs={i:Path(f'/tmp/dlss-sky-audit/safe-o4/fatbin{i:02d}.bin').read_bytes() for i in range(15)}
data,manifest=assemble(data,locs,blobs,b.dp);b.fast_update_pe_checksum(data)
(root/'nvngx_dlssnr_sm86_safe.dll').write_bytes(data)
Path(__file__).with_name('safe-pe-manifest.json').write_text(json.dumps(manifest,indent=2))
print('Assembled 15 O4 fatbins; relocated:',[m[0] for m in manifest if m[1]=='section'])
