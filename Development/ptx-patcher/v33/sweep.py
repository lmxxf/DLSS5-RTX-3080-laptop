"""Only called after all builds, primitive tests and resource queries finish."""
import sys,os,json
stage=sys.argv[1];os.environ['V33_DATASET']={'smoke':'smoke.json','probes':'probes.json','timed':'bench.json','repeat':'repeat.json'}[stage]
import bench as b
candidates=[v for v in b.variants if v!='baseline' and not v.startswith('probe_')]
if stage=='smoke':
 for w in [1280,1600,1920]:
  for v in ['baseline']+candidates:b.run('smoke',v,w,1,1)
elif stage=='probes':
 versions=['baseline','probe_shared','probe_global_family','probe_global','probe_mixed','probe_both','probe_all']
 for direction,widths in [('forward',[1280,1600,1920]),('reverse',[1920,1600,1280])]:
  for w in widths:
   for k in range(2):
    for j,v in enumerate(versions if direction=='forward' else versions[::-1]):b.run(f'probe-{direction}-{k}-{j}',v,w)
else:
 if stage=='repeat':candidates=json.loads((b.p/'repeat-eligible.json').read_text())
 for direction,widths in [('forward',[1280,1600,1920]),('reverse',[1920,1600,1280])]:
  for w in widths:
   for v in candidates:
    order=['baseline',v,v,'baseline'] if direction=='forward' else [v,'baseline','baseline',v]
    for j,version in enumerate(order):b.run(f'{direction}-{v}-{j}',version,w)
