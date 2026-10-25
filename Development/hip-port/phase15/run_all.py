"""Pinned correctness regression only. Intentionally no performance experiment."""
from pathlib import Path
import argparse,datetime,subprocess,sys
p=Path(__file__).resolve().parent;r=p.parent;a=argparse.ArgumentParser();a.add_argument('--tag',default='retest-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));a=a.parse_args()
def run(name,*args):subprocess.run([sys.executable,str(p/name),*args],check=True)
run('prepare.py')
subprocess.run([sys.executable,str(r/'hip/build_sm86_modules.py'),str(r/'hip'),str(p/'artifacts/selected/modules')],check=True)
run('verify_modules.py');run('make_inputs.py');run('build_host.py');run('build_probe.py');run('trace_layout.py');run('coverage.py');run('actual_qkv.py');run('rounding_audit.py');run('run_suite.py','--tag',a.tag);run('analyze_suite.py','--tag',a.tag);run('validate_all.py','--tag',a.tag)
print('Correctness regression complete. Real HDR/gameplay evidence gap remains: no C32 experiment or performance timing.')
