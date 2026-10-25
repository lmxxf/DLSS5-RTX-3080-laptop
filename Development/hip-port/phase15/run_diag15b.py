from pathlib import Path
import argparse,datetime,os,subprocess,sys,re
p=Path(__file__).resolve().parent;a=argparse.ArgumentParser();a.add_argument('--tag',default='diagnostic15b-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));a=a.parse_args();assert re.fullmatch(r'diagnostic15b[A-Za-z0-9_-]*',a.tag),'tag must startdiagnostic15b'
assert not (p/'artifacts'/a.tag).exists(),'choose a fresh diagnostic tag'
env=os.environ.copy();env['DLSS5_DIAG15B_ROOT']=str(p/'artifacts'/a.tag)
for name in ['diag15b_prepare.py','diag15b_build.py','diag15b_run.py','diag15b_stages.py','diag15b_spatial.py','diag15b_post.py','diag15b_expand_build.py','diag15b_expand_replay.py','diag15b_attention_cpu.py','diag15b_head.py','diag15b_branches.py','diag15b_controls.py','diag15b_plot.py','diag15b_validate.py']:
 subprocess.run([sys.executable,str(p/name)],env=env,check=True)
print('Diagnostic only; no performance/default/gold change. Raw buffers may be cleaned after summaries/hashes are saved.')
