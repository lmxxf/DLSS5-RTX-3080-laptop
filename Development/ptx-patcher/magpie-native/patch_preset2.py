"""Fix the known Magpie 0.6.6 native NR preset without changing model kernels."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dlssnr_patcher as pe

ORIGINAL_SHA256 = 'ec0a90fcf36430e5204f0df5e2b955d21fe60443250c51e8670143cf20ad880e'
PATCHED_SHA256 = 'b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea'


def patch(original: bytes) -> tuple[bytes, dict]:
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA256:
        raise ValueError('Unsupported original Magpie.exe SHA-256')
    data = bytearray(original)
    sections = pe.read_pe_sections(data)
    rva = 0x208f58
    offset = pe.rva_to_file_offset(rva, sections)
    assert offset is not None
    assert data[offset:offset + 9] == bytes.fromhex('45 33 c0 48 8b 01 ff 50 18')
    assert data[offset - 7:offset] == bytes.fromhex('48 8d 15 98 7e 12 00')
    text = sections[0]
    cave = text.raw_offset + (text.virtual_size + 15) // 16 * 16
    cave_rva = text.virtual_address + cave - text.raw_offset
    stub = bytes.fromhex('41 b8 02 00 00 00 48 8b 01 ff 50 18')
    stub += b'\xe9' + struct.pack('<i', rva + 9 - (cave_rva + len(stub) + 5))
    assert cave + len(stub) <= text.raw_offset + text.raw_size
    assert all(v in (0, 0xcc, 0x90) for v in data[cave:cave + len(stub)])
    data[cave:cave + len(stub)] = stub
    data[offset:offset + 9] = b'\xe9' + struct.pack('<i', cave_rva - rva - 5) + b'\x90' * 4
    header = pe.pe_header_offset(data)
    table = header + 24 + struct.unpack_from('<H', data, header + 20)[0]
    struct.pack_into('<I', data, table + 8, max(text.virtual_size, cave_rva + len(stub) - text.virtual_address))
    assert data.count(b'preset=fixed-0') == 1
    data = data.replace(b'preset=fixed-0', b'preset=fixed-2')
    pe.update_pe_checksum(data)
    digest = hashlib.sha256(data).hexdigest()
    assert digest == PATCHED_SHA256, digest
    return bytes(data), {'original_exe_sha256': ORIGINAL_SHA256, 'preset2_exe_sha256': digest,
                         'site_rva': hex(rva), 'cave_rva': hex(cave_rva), 'stub_hex': stub.hex()}


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--input', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    result, manifest = patch(args.input.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.output.with_suffix('.preset2.json').write_text(json.dumps(manifest, indent=2))
    print(PATCHED_SHA256)
