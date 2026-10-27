from pathlib import Path
p=Path(__file__).resolve().parent;src=(p/'bench.py').read_text();src=src[:src.index("if sys.argv[1]=='smoke':")];src=src.replace("(p/('smoke.json' if sys.argv[1]=='smoke' else 'bench.json'))", "(p/'conditional-bench.json')");exec(src)
for direction,widths in [('forward',[1280,1600,1920]),('reverse',[1920,1600,1280])]:
 for w in widths:
  order=['c','abc','abc','c'] if direction=='forward' else ['abc','c','c','abc']
  for j,v in enumerate(order):run(f'conditional-{direction}-{j}',v,w)
