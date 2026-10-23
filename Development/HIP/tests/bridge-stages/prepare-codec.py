from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[4];out=Path('/tmp/bridge-stages');out.mkdir(exist_ok=True)
base='613c278c0281b4ee0b2ea5b6cc3f3b3315b9e3ae'
s=subprocess.check_output(['git','show',base+':src/native_game_codec.h'],cwd=root,text=True)
(out/'legacy_codec.h').write_text(s.replace('NativeGameCodec','LegacyGameCodec'))
(out/'full_codec.h').write_text(s.replace('NativeGameCodec','FullGameCodec').replace('DLSS5_STRENGTH','DLSS5_TEST_FULL_STRENGTH'))
(out/'old-shaders').mkdir(exist_ok=True)
for name in ('native_codec_decode.hlsl','native_codec_encode.hlsl'):(out/'old-shaders'/name).write_bytes(subprocess.check_output(['git','show',base+':shaders/'+name],cwd=root))
