from pathlib import Path
# Execute the existing harness definitions without its command-line loop.
p=Path(__file__).resolve().parent;src=(p/'bench.py').read_text();src=src[:src.index("if sys.argv[1]=='smoke':")];exec(src)
for tag,order in [('confirm-forward',['baseline','decode','decode','baseline']),('confirm-reverse',['decode','baseline','baseline','decode'])]:
 for i,v in enumerate(order):run(tag+f'-{i}',v,1920)
(p/'confirm-1080.json').write_text((p/'bench.json').read_text());(p/'bench.json').write_text((p/'bench-primary.json').read_text())
