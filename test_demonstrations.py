import tempfile
import unittest
from demonstrations import demonstrate

class DemonstrationTests(unittest.TestCase):
    def test_mapped_demonstrations(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ('memory','resume','models','orchestration','failure','budget','evaluation','observability'):
                with self.subTest(name=name):
                    result=demonstrate(name,directory)
                    self.assertTrue(all(c['passed'] for c in result['checks']))
                    self.assertIn('meaning',result)
