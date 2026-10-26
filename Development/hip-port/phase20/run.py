from pathlib import Path
import subprocess
p=Path(__file__).resolve().parent
subprocess.run(['python3',str(p/'bench.py'),'candidate-quick','--warmup','3','--iterations','5'],check=True)
f=(p/'telemetry.csv').open('w');mon=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,pstate,temperature.gpu,power.draw,clocks.sm,clocks.mem,utilization.gpu','--format=csv','-lms','100'],stdout=f,stderr=subprocess.STDOUT)
try:
 for w in [1280,1600,1920]:
  for name in ['baseline-a','candidate-b','candidate-b2','baseline-a2']:subprocess.run(['python3',str(p/'bench.py'),name,'--width',str(w)],check=True)
finally:mon.terminate();mon.wait();f.close()
