from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parent
for script,args in [('bench.py',['smoke']),('bench.py',['timed']),('analyze.py',[])]:subprocess.run([sys.executable,str(p/script),*args],check=True)
