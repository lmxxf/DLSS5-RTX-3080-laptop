from pathlib import Path
import subprocess
from bench import run
p=Path(__file__).resolve().parent;f=(p/'compare-telemetry.csv').open('w');mon=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,pstate,temperature.gpu,power.draw,clocks.sm,clocks.mem,utilization.gpu','--format=csv','-lms','100'],stdout=f)
try:
 for w in [1280,1600,1920]:
  for tag,order in [('forward',['baseline','fb45','hot255','all255']),('reverse',['all255','hot255','fb45','baseline'])]:
   for v in order:run(tag,v,w)
finally:mon.terminate();mon.wait();f.close()
