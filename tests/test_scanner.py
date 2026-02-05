
import unittest
from pathlib import Path
from exttester.security_scanner import _max_risk, _risk_score

class TestSecurityScanner(unittest.TestCase):

    def test_max_risk(self):
        self.assertEqual(_max_risk("Low", "High"), "High")
        self.assertEqual(_max_risk("Critical", "Medium"), "Critical")
        self.assertEqual(_max_risk("Low", "Low"), "Low")
        
    def test_risk_score(self):
        # 100 - (findings*6) - (perm*8)
        score = _risk_score([], [])
        self.assertEqual(score, 100)
        
        score_mix = _risk_score(['one'], ['perm'])
        # 100 - 6 - 8 = 86
        self.assertEqual(score_mix, 86)
        
        score_bad = _risk_score(['a']*20, [])
        # 100 - 120 = -20 -> 0
        self.assertEqual(score_bad, 0)

if __name__ == '__main__':
    unittest.main()
