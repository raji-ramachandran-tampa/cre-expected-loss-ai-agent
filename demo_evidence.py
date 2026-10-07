"""Reproducible offline demonstrations and exported inspection records."""
import json
import subprocess
import sys
from workbench import Workbench, ROOT

app=Workbench()
key=app.create(inject=True)
app.step(key)
app.step(key)
before=app.inspect(key)
app.close()
code='from workbench import Workbench; a=Workbench(); a.finish('+repr(key)+'); a.close()'
subprocess.check_call([sys.executable,'-c',code],cwd=ROOT)
app=Workbench()
after=app.inspect(key)
budget=app.create(budget=0,provider='gemini')
stopped=app.finish(budget)
record={'mode':'offline simulation; no live LLM quality measurement','before_restart':before,'after_process_restart':after,'budget_stop':stopped,'model_references':app.references()}
(ROOT/'demo-evidence.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print('Saved demo-evidence.json: restart, injected failure, references and budget stop.')
app.close()
