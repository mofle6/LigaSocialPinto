import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from import_cup_pdfs import ROOT, build, parse_pdf
from import_cup_pdfs import guard_versions

class HorariosTests(unittest.TestCase):
    def setUp(self):
        self.base=json.loads((ROOT/'data/copa/2026-2027/competicion.json').read_text(encoding='utf-8'))
        self.folder=ROOT/'pdfs-copa/2026-2027/horarios'
        self.pdf=next(self.folder.glob('*.pdf'))

    def test_real_pdf_wrapped_names_dates_fields(self):
        matches=parse_pdf(self.pdf,self.base,0)
        self.assertEqual(len(matches),19)
        gal=next(m for m in matches if m['local']=='GALACTICOS DEL LOCAL')
        self.assertEqual((gal['fecha'],gal['hora']),('2026-11-21','16:30'))
        self.assertIn('C2',gal['campo'])
        self.assertEqual(sum(m['fecha']=='2026-11-22' for m in matches),8)
        self.assertTrue(any(m['visitante']=='P.S. VETERANOS/DELAIRE 2000, SL' for m in matches))

    def test_preserves_results_league_and_unknown_slots(self):
        before=copy.deepcopy(self.base)
        before['rondas'][0]['partidos'][0].update(goles_local=2,goles_visitante=1,estado='jugado')
        result,_=build(self.folder,before)
        self.assertEqual(result['equipos'],before['equipos'])
        self.assertEqual(result['rondas'][1:],before['rondas'][1:])
        match=next(m for m in result['rondas'][0]['partidos'] if m.get('local')=='GEERTAFE FC')
        self.assertEqual((match['goles_local'],match['goles_visitante'],match['estado']),(2,1,'jugado'))
        self.assertEqual(before['rondas'][0]['partidos'][0]['goles_local'],2)

    def test_latest_revision_duplicates_and_conflicts(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td); payload=self.pdf.read_bytes()
            (folder/self.pdf.name).write_bytes(b'invalid older PDF')
            rev=folder/'HORARIOS_COPAF7_RONDAPREVIA_20261113_v02.pdf';rev.write_bytes(payload)
            duplicate=folder/'copy';duplicate.mkdir();(duplicate/rev.name).write_bytes(payload)
            result,manifest=build(folder,self.base)
            self.assertEqual(len(manifest),1)
            (duplicate/rev.name).write_bytes(b'different')
            with self.assertRaisesRegex(ValueError,'distinto contenido'):build(folder,self.base)

    def test_bad_name_and_changed_pair_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td);(folder/'oops.pdf').write_bytes(self.pdf.read_bytes())
            with self.assertRaisesRegex(ValueError,'Nombre inválido'):build(folder,self.base)
        changed=copy.deepcopy(self.base);changed['rondas'][0]['partidos'][0]['local']='ADYCTOS FC'
        with self.assertRaisesRegex(ValueError,'cruces han cambiado'):build(self.folder,changed)

    def test_incomplete_and_wrong_round_rejected(self):
        changed=copy.deepcopy(self.base);changed['rondas'][0]['partidos'].append({'local':'NEW','visitante':'OTHER'})
        with self.assertRaisesRegex(ValueError,'incompleto'):parse_pdf(self.pdf,changed,0)
        with self.assertRaisesRegex(ValueError,'ronda'):parse_pdf(self.pdf,self.base,2)

    def test_rollback_and_reused_revision_rejected(self):
        current=copy.deepcopy(self.base)
        current['rondas'][0]['fuente_horarios']='HORARIOS_COPAF7_RONDAPREVIA_20261114.pdf'
        with self.assertRaisesRegex(ValueError,'anterior'):build(self.folder,current)
        current['rondas'][0]['fuente_horarios']=self.pdf.name
        current['rondas'][0]['horarios_sha256']='old-hash'
        with self.assertRaisesRegex(ValueError,'revisión nueva'):build(self.folder,current)

    def test_git_guard_protects_pdf_versions_between_builds(self):
        for status in ('D','M','T'):
            payload=(status+'\0pdfs-copa/2026-2027/horarios/'+self.pdf.name+'\0').encode()
            with patch('import_cup_pdfs.subprocess.check_output',return_value=payload):
                with self.assertRaisesRegex(ValueError,'conserva la versión anterior'):guard_versions('a'*40)
        with patch('import_cup_pdfs.subprocess.check_output',return_value=b'') as git:
            guard_versions('a'*40);git.assert_called_once()

if __name__=='__main__':unittest.main()
