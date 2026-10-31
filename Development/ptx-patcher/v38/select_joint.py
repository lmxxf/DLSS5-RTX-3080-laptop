from pathlib import Path
import json,statistics as st
p=Path(__file__).resolve().parent;t=json.loads((p/'timing-summary.json').read_text())['timed'];policy=json.loads((p/'selection-policy.json').read_text());rank={};chosen=[]
for task in ['task_A','task_B']:
 score={n:[min(r['directions'][d]['gain_percent'] for r in t[n].values() for d in ['forward','reverse']),st.mean(r['gain_percent'] for r in t[n].values())] for n in policy[task] if all(r['quality_pass'] for r in t[n].values())};assert score;best=sorted(score,key=lambda n:(-score[n][0],-score[n][1],n))[0];chosen.append(best);rank[task]={'scores_min_direction_then_mean':score,'selected':best}
spec=json.loads((p/'specs.json').read_text());joint=next(n for n,s in spec.items() if s.get('joint_components')==chosen+['async_pool_only']);timed=json.loads((p/'timing-candidates.json').read_text());assert joint not in timed;timed.append(joint);(p/'timing-candidates.json').write_text(json.dumps(timed,indent=2)+'\n');(p/'joint-selection.json').write_text(json.dumps({'ranking':rank,'joint':joint,'selection_uses_first_round_only':True,'all_joint_modules_prebuilt_before_smoke':True},indent=2)+'\n');print('selected',joint)
