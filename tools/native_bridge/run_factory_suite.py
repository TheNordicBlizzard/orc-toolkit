"""Original MIT parent-retest runner; outputs local/private evidence only."""
import subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
blender=sys.argv[1];fixtures=Path(sys.argv[2]).resolve();reference=Path(sys.argv[3]).resolve();evidence=Path(sys.argv[4]).resolve();evidence.mkdir(parents=True,exist_ok=False)
results=[]
for asset in ('tweed','adawong','elitehunter'):
 for mode in ('import','reopen'):
  command=[blender,'--background','--factory-startup','--python-exit-code','1','--python',str(ROOT/'tests/blender_test.py'),'--',str(fixtures/(asset+'-0.edgemodel')),str(evidence/asset),mode,str(reference)]
  completed=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150)
  (evidence/(asset+'-'+mode+'.log')).write_bytes(completed.stdout)
  result={'asset':asset,'mode':mode,'exit_code':completed.returncode,'log':asset+'-'+mode+'.log'}
  results.append(result);print(result,flush=True)
  if completed.returncode:print(completed.stdout.decode(errors='replace'));raise SystemExit(1)
(evidence/'suite.json').write_text(json.dumps(results,indent=2))
assert len(results)==6 and all(r['exit_code']==0 for r in results)
