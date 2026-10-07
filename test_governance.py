import tempfile
import unittest
from unittest.mock import patch
from governance import tool_decision, PolicyDenied
from workbench import Workbench

class GovernanceTests(unittest.TestCase):
    def test_allowlist_and_synthetic_inputs(self):
        self.assertTrue(tool_decision('ead',{'case_id':'amortization'})['allowed'])
        self.assertFalse(tool_decision('ead',{'current_balance':100})['allowed'])
        self.assertFalse(tool_decision('shell',{})['allowed'])
        self.assertFalse(tool_decision('approve_model',{})['allowed'])
    def test_enforced_in_actual_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            app=Workbench(directory)
            try:
                key=app.create()
                with patch.object(app,'offline',return_value={'tool':'ead','args':{'current_balance':100}}):
                    result=app.finish(key)
                self.assertEqual(result['state']['status'],'governance_blocked')
                self.assertFalse(result['next'])
                with self.assertRaises(PolicyDenied):
                    app.remember('demo','Keep forever','user',90000)
                key=app.create(provider='gemini')
                with patch('urllib.request.urlopen') as network:
                    result=app.finish(key)
                self.assertEqual(result['state']['status'],'governance_blocked')
                self.assertFalse(result['ledger'])
                network.assert_not_called()
            finally:
                app.close()
