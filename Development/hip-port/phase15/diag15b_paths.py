from pathlib import Path
import os,json
p=Path(__file__).resolve().parent
fallback=p/'artifacts/diagnostic15b'
if (p/'diag15b-inputs.json').exists():
 data=json.loads((p/'diag15b-inputs.json').read_text())
 if data:fallback=Path(data[0]['input_file']).parent.parent
ROOT=Path(os.environ.get('DLSS5_DIAG15B_ROOT',str(fallback))).resolve()
