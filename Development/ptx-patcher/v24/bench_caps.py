from pathlib import Path
p=Path(__file__).resolve().parent
src=(p/'bench.py').read_text();src=src[:src.index("if sys.argv[1]=='smoke':")];src=src.replace("(p/('smoke.json' if sys.argv[1]=='smoke' else 'bench.json'))", "(p/'caps-bench.json')");exec(src)
caps=json.loads((p/'caps.json').read_text());variants|=caps
for direction in ['forward','reverse']:
 for name in sorted(caps):
  order=['abc',name,name,'abc'] if direction=='forward' else [name,'abc','abc',name]
  for j,v in enumerate(order):run(f'caps-{direction}-{name}-{j}',v,1920)
