from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parent
for script,args in [('profile_versions.py',[]),('bench.py',['smoke']),('bench.py',['timed'])]:subprocess.run([sys.executable,str(p/script),*args],check=True)
