"""Offline, inspectable demonstrations for workbench capability topics."""
import json
import subprocess
import sys
import time
import uuid
from workbench import Workbench, ROOT

def demonstrate(name, directory=None):
    app=Workbench(directory)
    try:
        if name=='memory':
            scope='memory-demo-'+uuid.uuid4().hex
            active=app.remember(scope,'Use quarterly periods and consistent synthetic units.','user preference in memory demonstration',86400)
            stale=app.remember(scope,'Old assumption: use monthly periods.','superseded synthetic assumption',86400)
            with app.db:
                app.db.execute('UPDATE memory SET expires=? WHERE id=?',(time.time()-1,stale))
            key=app.create(scope=scope)
            retrieved=app.inspect(key)['state']['memory']
            isolated=app.memories(scope+'-other')
            app.finish(key)
            run=app.inspect(key)
            checks=[{'name':'Active preference retrieved with provenance','passed':any(m['id']==active and m['source'] for m in retrieved)}, {'name':'Expired assumption excluded','passed':not any(m['id']==stale for m in retrieved)}, {'name':'Other scope cannot retrieve this preference','passed':not isolated}, {'name':'Conversation and working results persisted separately','passed':bool(run['state']['history'] and run['state']['results'])}]
            return {'topic':'Memory','meaning':'Keeps useful context, excludes stale assumptions, and separates sessions. Retrieval does not prove that an LLM used the preference.', 'checks':checks,'observations':{'active_memory':retrieved,'excluded_memory_id':stale,'other_scope_memory':isolated,'conversation_turns':len(run['state']['history']),'working_results':len(run['state']['results'])},'run':run}
        if name=='resume':
            key=app.create()
            app.step(key)
            app.step(key)
            before=app.inspect(key)
            directory=str(app.directory.resolve())
            app.close()
            app=None
            code='from workbench import Workbench; a=Workbench('+repr(directory)+'); a.finish('+repr(key)+'); a.close()'
            subprocess.run([sys.executable,'-c',code],cwd=ROOT,check=True,timeout=30,capture_output=True)
            app=Workbench(directory)
            after=app.inspect(key)
            first_id=before['state']['results'][0]['tool_call_id']
            checks=[{'name':'Completed tool result survives a new process','passed':after['state']['results'][0]['tool_call_id']==first_id}, {'name':'Run resumes to completion','passed':after['state']['status']=='completed'}, {'name':'Completed tool not duplicated','passed':sum(r['tool_call_id']==first_id for r in after['state']['results'])==1}]
            return {'topic':'Restart and resume','meaning':'A separate Python process resumes the saved checkpoint without losing completed work. This is local durability, not distributed reliability.', 'checks':checks,'observations':{'before_checkpoint':before['checkpoint_id'],'after_checkpoint':after['checkpoint_id'],'saved_result_id':first_id,'before_next':before['next'],'after_next':after['next']},'run':after}
        if name=='models':
            references=app.references()
            return {'topic':'Model access and tools','meaning':'The existing EAD model calculates exposure. The AI adapter can select only registered tools; credentials stay on the server. Live generation has not been demonstrated.', 'checks':[{'name':'EAD references pass','passed':all(c['passed'] for c in references['checks'])}], 'observations':{'configured_model':app.config['model'],'providers':['offline','gemini'],'tools':['evidence','ead'],'source':references['evidence'],'prompt_asset':'Workbench.context instruction; versioned in workbench.py'},'run':None}
        if name not in ('orchestration','failure','budget','evaluation','observability'):
            raise ValueError('Unknown demonstration')
        key=app.create(inject=name=='failure',budget=0 if name=='budget' else None)
        run=app.finish(key)
        if name=='budget':
            checks=[{'name':'Stops before a request with no remaining budget','passed':run['state']['status']=='budget_stopped'}, {'name':'No provider request or charge','passed':not run['ledger'] and run['estimated_cost_usd']==0}]
            meaning='Reserves estimated spending before each request. Stops before exceeding the configured allowance; estimates are separate from invoices.'
        elif name=='failure':
            kinds=[e['kind'] for e in run['events']]
            checks=[{'name':'Temporary failure recorded','passed':'injected_failure' in kinds}, {'name':'Bounded retry recorded','passed':'tool_retry' in kinds}, {'name':'Recovered run completes','passed':run['state']['status']=='completed'}]
            meaning='A synthetic timeout triggers a bounded retry. Invalid inputs return errors; ambiguous provider calls stop instead of risking duplicate spending.'
        elif name=='evaluation':
            checks=app.references()['checks']+run['evaluation']['checks']
            meaning='Checks numerical tool outputs and evidence identifier presence. This does not measure live explanation quality or establish independent model validation.'
        elif name=='observability':
            checks=[{'name':'Run and tool identifiers recorded','passed':all('tool_call_id' in r for r in run['state']['results'])}, {'name':'Usage labels distinguish simulation','passed':all(c['usage'].get('kind')=='simulated' for c in run['ledger'])}, {'name':'Timeline records decisions and tools','passed':bool(run['events'])}]
            meaning='Shows the sequence of decisions, tool calls, outcomes, latency and usage so a reviewer can explain what happened.'
        else:
            checks=[{'name':'Evidence and analytical tools invoked','passed':len(run['state']['results'])==3}, {'name':'Authoritative outputs match references','passed':run['evaluation']['passed']}]
            meaning='LangGraph coordinates decisions and tool execution. This demonstration uses scripted decisions; live model-driven orchestration remains an evidence gap.'
        return {'topic':name.title(),'meaning':meaning,'checks':checks,'observations':{'status':run['state']['status'],'tool_results':run['state']['results'],'estimated_cost_usd':run['estimated_cost_usd']},'run':run}
    finally:
        if app is not None:
            app.close()
