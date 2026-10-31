from pathlib import Path
import json
from stage import run
p=Path(__file__).resolve().parent
run(['bench.py','timed']);run(['summarize.py'])
if json.loads((p/'repeat-eligible.json').read_text()):run(['bench.py','repeat']);run(['summarize.py'])
run(['validate.py'])
