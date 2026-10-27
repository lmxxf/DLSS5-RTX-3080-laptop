from pathlib import Path
p=Path(__file__).resolve().parent;src=(p/'bench.py').read_text();src=src[:src.index("if sys.argv[1]=='smoke':")];src=src.replace("(p/('smoke.json' if sys.argv[1]=='smoke' else 'bench.json'))", "(p/'fb0-bench.json')");exec(src);variants['fb0']=json.loads((p/'fb0-build.json').read_text())
for direction,widths in [('forward',[1280,1920]),('reverse',[1920,1280])]:
 for w in widths:
  order=['baseline','fb0','fb0','baseline'] if direction=='forward' else ['fb0','baseline','baseline','fb0']
  for j,v in enumerate(order):run(f'fb0-{direction}-{j}',v,w)
