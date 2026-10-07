import json
import tempfile
import unittest
from pathlib import Path
from lgd_comparison import FILES, compare_existing_lgd
from governance import tool_decision

class LGDComparisonTests(unittest.TestCase):
    def test_shared_outcome_and_matching_cases_required(self):
        with tempfile.TemporaryDirectory() as directory:
            reports=[{'outcome_version':'signed-v1','target':'signed ratio'}, {'target':'unchanged signed-v1','pooled_comparison':{'ridge_loss_sharing':{'cases':20,'mae':.2,'rmse':.3},'signed_hurdle':{'cases':20,'mae':.25,'rmse':.35}},'limitations':[]}]
            for name,report in zip(FILES,reports):
                path=Path(directory)/name
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(report))
            result=compare_existing_lgd(directory)
            self.assertAlmostEqual(result['mae_difference_hurdle_minus_ridge'],.05)
            self.assertEqual(len(result['provenance']),2)
            reports[1]['pooled_comparison']['signed_hurdle']['cases']=19
            (Path(directory)/FILES[1]).write_text(json.dumps(reports[1]))
            with self.assertRaises(ValueError):
                compare_existing_lgd(directory)
            self.assertFalse(tool_decision('lgd_compare',{'path':'arbitrary.parquet'})['allowed'])
