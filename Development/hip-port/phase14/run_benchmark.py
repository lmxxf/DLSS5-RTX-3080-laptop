"""Repeat final paired controls without overwriting archived run names."""
from pathlib import Path
import subprocess,datetime,argparse
p=Path(__file__).resolve().parent;a=argparse.ArgumentParser();a.add_argument('prefix',nargs='?',default='retest-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));a=a.parse_args();tag=a.prefix

def run(v,w,cap=None):
 cmd=['python3',str(p/'bench.py'),v,'--width',str(w)]
 if cap:cmd+=['--cap',str(cap)]
 subprocess.run(cmd,check=True)
for w in [1280,1600,1920]:
 run(('control256-' if w==1280 else 'baseline-')+tag,w,256 if w==1280 else None);run(tag,w)
for w in [1280,1600,1920]:
 run(tag+'-reverse',w);run(('control256-' if w==1280 else 'baseline-')+tag+'-reverse',w,256 if w==1280 else None)
subprocess.run(['python3',str(p/'analyze.py')],check=True)
subprocess.run(['python3',str(p/'final_quality.py'),'--forward',tag,'--reverse',tag+'-reverse'],check=True)
