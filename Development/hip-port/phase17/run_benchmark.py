from pathlib import Path
import subprocess,argparse,datetime
p=Path(__file__).resolve().parent;a=argparse.ArgumentParser();a.add_argument('--tag',default=datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));a=a.parse_args();tele=(p/(a.tag+'-telemetry.csv')).open('w');mon=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,pstate,temperature.gpu,power.draw,clocks.sm,clocks.mem,utilization.gpu','--format=csv','-lms','100'],stdout=tele,stderr=subprocess.STDOUT)
try:
 for w in [1280,1600,1920]:
  for label in ['baseline-a','candidate-b','candidate-b2','baseline-a2']:
   subprocess.run(['python3',str(p/'bench.py'),label+'-'+a.tag,'--width',str(w)],check=True)
finally:mon.terminate();mon.wait();tele.close()
