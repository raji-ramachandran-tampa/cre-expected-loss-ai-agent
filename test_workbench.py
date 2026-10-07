import json
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import io
from pathlib import Path
from workbench import Workbench, ROOT

class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=Workbench(self.tmp.name)

    def tearDown(self):
        self.app.close()
        self.tmp.cleanup()

    def test_model_references(self):
        self.assertTrue(all(c['passed'] for c in self.app.references()['checks']))

    def test_restart_and_injected_failure(self):
        key=self.app.create(inject=True)
        first=self.app.step(key)
        self.assertEqual(first['next'],['tools'])
        self.app.step(key)
        self.app.close()
        # Resume in a separate Python process, proving no in-memory runtime is required.
        code='from workbench import Workbench; import json; a=Workbench('+repr(self.tmp.name)+'); print(json.dumps(a.finish('+repr(key)+'))); a.close()'
        done=json.loads(subprocess.check_output([sys.executable,'-c',code],cwd=ROOT,text=True))
        self.app=Workbench(self.tmp.name)
        self.assertEqual(done['state']['status'],'completed')
        self.assertEqual(len(done['state']['results']),3)
        self.assertEqual(done['state']['results'][1]['output'],[90,70])
        self.assertEqual(done['state']['results'][2]['output'],[95,105])
        self.assertEqual(sum(e['kind']=='injected_failure' for e in done['events']),1)
        self.assertEqual(sum(e['kind']=='tool_result' for e in done['events']),3)
        self.assertEqual(len(done['ledger']),4)
        self.assertEqual(done['estimated_cost_usd'],0)

    def test_budget_stops_before_request(self):
        key=self.app.create(budget=0,provider='gemini')
        result=self.app.finish(key)
        self.assertEqual(result['state']['status'],'budget_stopped')
        self.assertEqual(result['ledger'],[])

    def test_memory_expiry_scope_and_restart(self):
        self.app.remember('alpha','Use quarterly periods','user',10)
        stale=self.app.remember('alpha','Stale preference','user',10)
        with self.app.db:
            self.app.db.execute('UPDATE memory SET expires=? WHERE id=?',(time.time()-1,stale))
        self.assertEqual(len(self.app.memories('alpha')),1)
        self.assertEqual(self.app.memories('beta'),[])
        key=self.app.create(scope='alpha')
        self.assertEqual(len(self.app.inspect(key)['state']['memory']),1)

    def test_uncertain_call_never_replayed(self):
        key=self.app.create()
        with self.app.db:
            self.app.db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?)',(key+':agent:0',key,'inflight',.001,0,'{}',None))
        result=self.app.finish(key)
        self.assertEqual(result['state']['status'],'uncertain_provider_call')
        self.assertEqual(result['reserved_usd'],.001)

    def test_completed_run_is_idempotent(self):
        key=self.app.create()
        first=self.app.finish(key)
        again=self.app.finish(key)
        self.assertEqual(len(first['events']),len(again['events']))
        self.assertEqual(len(first['ledger']),len(again['ledger']))

    def test_gemini_reported_usage_and_cost_without_network(self):
        key=self.app.create(provider='gemini')
        body={'candidates':[{'content':{'parts':[{'text':json.dumps({'tool':'evidence','args':{}})}]}}], 'usageMetadata':{'promptTokenCount':100,'candidatesTokenCount':10,'totalTokenCount':115}}
        with patch('workbench.require_provider'), patch.dict('os.environ',{'GEMINI_API_KEY':'fake-test-key'}), patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(body).encode())) as request:
            result=self.app.step(key)
        self.assertEqual(result['state']['status'],'tool_pending')
        self.assertEqual(result['ledger'][0]['usage']['kind'],'provider_reported')
        self.assertAlmostEqual(result['estimated_cost_usd'],.000016)
        self.assertNotIn('fake-test-key',json.dumps(result))
        self.assertEqual(request.call_count,1)

    def test_malformed_response_keeps_usage_and_stops(self):
        key=self.app.create(provider='gemini')
        body={'candidates':[{'content':{'parts':[{'text':'bad json'}]}}], 'usageMetadata':{'promptTokenCount':100,'totalTokenCount':110}}
        with patch('workbench.require_provider'), patch.dict('os.environ',{'GEMINI_API_KEY':'fake-test-key'}), patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(body).encode())):
            result=self.app.finish(key)
        self.assertEqual(result['state']['status'],'provider_failed')
        self.assertGreater(result['reserved_usd'],0)
        self.assertEqual(result['ledger'][0]['usage']['promptTokenCount'],100)

    def test_answer_without_tools_requires_review(self):
        key=self.app.create()
        with patch.object(self.app,'offline',return_value={'answer':'Unsupported completion'}):
            result=self.app.finish(key)
        self.assertEqual(result['state']['status'],'review_required')
        self.assertFalse(result['evaluation']['passed'])

if __name__=='__main__':
    unittest.main()
