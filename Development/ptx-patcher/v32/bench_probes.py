import sys,os,json
sys.argv=['bench_probes.py','probes'];os.environ['V32_DATASET']='probe-bench.json'
import bench as b
b.variants={'baseline':b.variants['baseline']}|json.loads((b.p/'probes.json').read_text())
for direction,widths in [('forward',[1280,1600,1920]),('reverse',[1920,1600,1280])]:
 for w in widths:
  order=['baseline','probe_p0','probe_p1','probe_p2'] if direction=='forward' else ['probe_p2','probe_p1','probe_p0','baseline']
  for repeat in range(2):
   for j,v in enumerate(order):b.run(f'probe-{direction}-{repeat}-{j}',v,w)
