from pathlib import Path
import json
import sys

old={k['name']:k for k in json.loads(Path(sys.argv[1]).read_text())}
new={k['name']:k for k in json.loads(Path(sys.argv[2]).read_text())}
report={'old_count':len(old),'new_count':len(new),'added':sorted(new.keys()-old.keys()),'removed':sorted(old.keys()-new.keys()),'common':{}}
for name in sorted(old.keys()&new.keys()):
    a,b=old[name],new[name]
    report['common'][name]={'same_code':a['code_sha256']==b['code_sha256'],'old_bytes':a['bytes'],'new_bytes':b['bytes'],'old_resources':a['resources'],'new_resources':b['resources']}
print(json.dumps(report,indent=2))
