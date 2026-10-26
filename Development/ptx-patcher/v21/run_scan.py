from pathlib import Path
import subprocess
from bench import run
p=Path(__file__).resolve().parent;f=(p/'scan-telemetry.csv').open('w');mon=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,pstate,temperature.gpu,power.draw,clocks.sm,clocks.mem,utilization.gpu','--format=csv','-lms','100'],stdout=f)
try:
 for i,v in enumerate(['baseline','c256-168','c256-255','baseline','fb00-255','fb04-255','baseline','fb05-255','fb06-255','baseline','hot255','all255','baseline']):run(f'scan{i:02d}',v,1920)
finally:mon.terminate();mon.wait();f.close()
