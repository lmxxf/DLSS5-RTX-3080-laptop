from pathlib import Path
p=Path(__file__).resolve().parent;src=(p/'bench.py').read_text();src=src[:src.index("if __name__=='__main__':")];src=src.replace("(p/('smoke.json' if sys.argv[1]=='smoke' else 'bench.json'))", "(p/'extra-bench.json')");exec(src);variants|=json.loads((p/'extra.json').read_text())
for case,candidate,widths in [('add-A','a_cap0',[1280,1600,1920]),('prefix-only','prefix168',[1280,1920])]:
 for direction,ws in [('forward',widths),('reverse',list(reversed(widths)))]:
  for w in ws:
   order=['cap0-168',candidate,candidate,'cap0-168'] if direction=='forward' else [candidate,'cap0-168','cap0-168',candidate]
   for j,v in enumerate(order):run(f'{case}-{direction}-{j}',v,w)
