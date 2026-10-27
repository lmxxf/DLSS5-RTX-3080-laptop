from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parent
for script in ['bench.py','bench_caps.py']:subprocess.run([sys.executable,str(p/script),'timed'],check=True)
