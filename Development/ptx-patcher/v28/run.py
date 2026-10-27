from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parent
for args in [('occupancy.py','caps'),('bench.py','smoke'),('bench.py','timed'),('analyze.py',)]:
 subprocess.run([sys.executable,str(p/args[0]),*args[1:]],check=True)
