import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from parse_jornada import normalize_wrapped_results

class SeparateScoreTests(unittest.TestCase):
    def test_pair_above_score_preserves_next_match(self):
        lines=['EL INTER NOVELLA & GARCIA OLD ROKERS LA OSTRA','4 - 3','ASTON BIRRA 3 - 2 MACHOTES DE ANTONIO','1 EL INTER NOVELLA & GARCIA OLD ROKERS 6 2 2 0 0 7 4 G G 0','2 LA OSTRA 1 3 0 1 2 6 8 E P P 0']
        result=normalize_wrapped_results(lines)
        self.assertEqual(result[0],'EL INTER NOVELLA & GARCIA OLD ROKERS 4 - 3 LA OSTRA')
        self.assertEqual(result[1],lines[2])
        self.assertEqual(len(result),len(lines)-1)

    def test_unknown_pair_rejected(self):
        with self.assertRaises(ValueError):normalize_wrapped_results(['UNKNOWN LA OSTRA','4 - 3','NEXT MATCH','1 LA OSTRA 1 3 0 1 2 6 8 E P P 0'])
