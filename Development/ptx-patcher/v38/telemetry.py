from pathlib import Path
import subprocess,json
p=Path(__file__).resolve().parent
with (p/'artifacts/telemetry.csv').open('w') as f:
 proc=subprocess.Popen(['nvidia-smi','--query-gpu=timestamp,temperature.gpu,clocks.sm,clocks.mem,power.draw,utilization.gpu,clocks_event_reasons.sw_thermal_slowdown','--format=csv','-lms','200'],stdout=f)
 (p/'artifacts/telemetry-pid.json').write_text(json.dumps({'pid':proc.pid})+'\n');proc.wait()
