import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import import_pdfs as imp
from parse_fs import parse

class SalaSanctionTests(unittest.TestCase):
    def setUp(self):
        self.data=parse(Path(__file__).resolve().parents[1]/'pdfs/2026-2027/CLASIFICACION_FS_J06_20261114.pdf')

    def test_complete_official_pdf_with_negative_points(self):
        self.assertEqual(len(self.data['clasificacion']),14)
        self.assertEqual(len(self.data['partidos']),7)
        rows=[r for r in self.data['clasificacion'] if r['pts']<0]
        self.assertEqual([(r['pts'],r['sancion']) for r in rows],[(-3,3)])
        imp.check_results(self.data)

    def test_unjustified_negative_points_rejected(self):
        row=next(r for r in self.data['clasificacion'] if r['pts']<0)
        row['pts']=-4
        with self.assertRaises(ValueError):imp.check_results(self.data)

    def test_negative_goals_still_rejected(self):
        self.data['clasificacion'][0]['gf']=-1
        with self.assertRaises(ValueError):imp.check_results(self.data)
