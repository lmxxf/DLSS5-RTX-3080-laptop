import sys,os
sys.argv=['repair_forward.py','repair'];os.environ['V32_DATASET']='repair.json'
import bench as b
for v in ['split','up','split_up']:
 for j,version in enumerate(['baseline',v,v,'baseline']):b.run(f'replacement-forward-{v}-{j}',version,1280)
