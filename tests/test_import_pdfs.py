import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import import_pdfs as imp
from parse_jornada import parse


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT, prefix='.pdf-stage-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / 'data', self.root / 'data')
        (self.root / 'pdfs/2026-2027').mkdir(parents=True)
        self.fixture = json.loads((ROOT / 'data/2026-2027/fs/j05.json').read_text('utf-8'))

    def pdf(self, name, content=b'fake pdf'):
        p = self.root / 'pdfs/2026-2027' / name
        p.write_bytes(content)
        return p

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in (self.root / 'data').rglob('*.json')}

    def run_import(self, **kw):
        with contextlib.redirect_stdout(io.StringIO()):
            imp.run(self.root, **kw)

    def test_name_and_calendar_validation(self):
        for name in ('Jornada5_fs.pdf', 'HORARIOS_FS_J00_20261108.pdf', 'HORARIOS_FS_J06_20260230.pdf'):
            with self.assertRaises(ValueError):
                imp.identity(Path(name))
        self.assertEqual(imp.identity(Path('HORARIOS_FS_J06_20261108_V2.pdf'))[-1], ('20261108', 2))

    def test_latest_and_duplicates(self):
        self.pdf('CLASIFICACION_FS_J05_20261108.pdf')
        self.pdf('CLASIFICACION_FS_J05_20261109.pdf', b'new')
        self.pdf('CLASIFICACION_FS_J05_20261109_V1.pdf', b'new')
        chosen = next(iter(imp.select(self.root).values()))
        self.assertEqual(chosen[0], ('20261109', 1))
        self.pdf('CLASIFICACION_FS_J05_20261109_V1.pdf', b'conflict')
        with self.assertRaisesRegex(ValueError, 'distinto contenido'):
            imp.select(self.root)

    def test_idempotent_and_check_does_not_write(self):
        self.pdf('CLASIFICACION_FS_J05_20261108.pdf')
        before = self.snapshot()
        with patch.object(imp, 'parse_fs', return_value=deepcopy(self.fixture)):
            self.run_import(check=True)
            self.assertEqual(before, self.snapshot())
            self.run_import()
        imported = self.snapshot()
        with patch.object(imp, 'parse_fs', side_effect=AssertionError('must not reparse')):
            self.run_import()
        self.assertEqual(imported, self.snapshot())
        self.assertEqual(set(before), set(imported))

    def test_bad_batch_is_not_partially_written(self):
        self.pdf('CLASIFICACION_FS_J05_20261108.pdf')
        self.pdf('HORARIOS_FS_J06_20261108.pdf')
        before = self.snapshot()
        with patch.object(imp, 'parse_fs', return_value=deepcopy(self.fixture)), patch.object(imp, 'parse_schedule', side_effect=ValueError('ilegible')):
            with self.assertRaisesRegex(ValueError, 'ilegible'):
                self.run_import()
        self.assertEqual(before, self.snapshot())

    def test_header_mismatch(self):
        self.pdf('CLASIFICACION_FS_J04_20261108.pdf')
        with patch.object(imp, 'parse_fs', return_value=self.fixture):
            with self.assertRaisesRegex(ValueError, 'encabezado'):
                self.run_import()

    def test_historical_correction_requires_updated_later_snapshots(self):
        self.pdf('CLASIFICACION_FS_J03_20261108.pdf')
        fixture = json.loads((ROOT / 'data/2026-2027/fs/j03.json').read_text('utf-8'))
        fixture['partidos'][0]['goles_local'] += 1
        before = self.snapshot()
        with patch.object(imp, 'parse_fs', return_value=fixture):
            with self.assertRaisesRegex(ValueError, 'corrección histórica'):
                self.run_import()
        self.assertEqual(before, self.snapshot())

    def test_historical_correction_with_official_later_tables(self):
        documents = {}
        for n in (3, 4, 5):
            self.pdf(f'CLASIFICACION_FS_J{n:02d}_20261115.pdf', str(n).encode())
            documents[n] = json.loads((ROOT / f'data/2026-2027/fs/j{n:02d}.json').read_text('utf-8'))
        game = documents[3]['partidos'][0]
        game['goles_local'] += 1
        game['goles_visitante'] += 1
        affected = {game['local_id'], game['visitante_id']}
        for d in documents.values():
            for row in d['clasificacion']:
                if row['equipo_id'] in affected:
                    row['gf'] += 1
                    row['gc'] += 1
        with patch.object(imp, 'parse_fs', side_effect=lambda p: deepcopy(documents[imp.identity(p)[2]])):
            self.run_import()
        for n in (3, 4, 5):
            actual = json.loads((self.root / f'data/2026-2027/fs/j{n:02d}.json').read_text('utf-8'))
            self.assertEqual(actual['clasificacion'], documents[n]['clasificacion'])
        self.assertEqual(len(actual['partidos']), 7)

    def test_played_match_cannot_regress_to_pending(self):
        self.pdf('CLASIFICACION_FS_J05_20261115.pdf')
        d = deepcopy(self.fixture)
        d['partidos'][0].update(estado='aplazado', goles_local=None, goles_visitante=None)
        with patch.object(imp, 'parse_fs', return_value=d):
            with self.assertRaisesRegex(ValueError, 'devolver'):
                self.run_import()

    def test_git_guard_rejects_modification_and_deletion(self):
        for status in ('M', 'D'):
            output = f'{status}\0pdfs/2026-2027/HORARIOS_FS_J06_20261108.pdf\0'.encode()
            with patch.object(imp.subprocess, 'check_output', return_value=output):
                with self.assertRaisesRegex(ValueError, 'inmutables'):
                    imp.check_git_changes(self.root, 'base')

    def test_actual_pdf_all_f7_teams_and_scores(self):
        pdf = ROOT / 'pdfs/Clasificación_j3_f7_zinc2.pdf'
        d = parse(pdf)
        imp.check_results(d)
        self.assertEqual((d['division'], d['jornada']), ('4dvf7', 3))

    def test_historical_pdf_change_rejected(self):
        legacy = ROOT / 'pdfs/J2_2DF7_CLASIFICACION.pdf'
        dest = self.root / 'pdfs' / legacy.name
        dest.write_bytes(legacy.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'histórico modificado'):
            self.run_import()

    def test_invalid_team_and_pending_score(self):
        d = deepcopy(self.fixture)
        d['partidos'][0]['estado'] = 'aplazado'
        with self.assertRaisesRegex(ValueError, 'pendiente'):
            imp.check_results(d)
        d = deepcopy(self.fixture)
        d['partidos'][1] = deepcopy(d['partidos'][0])
        with self.assertRaisesRegex(ValueError, 'duplicados'):
            imp.check_results(d)

    def test_real_schedule_and_canonical_header(self):
        source = ROOT / 'pdfs/HORARIOS_Jornada4_fs.pdf'
        p = self.pdf('HORARIOS_FS_J04_20261108.pdf', source.read_bytes())
        self.run_import()
        result = json.loads((self.root / 'data/2026-2027/fs/proximas/j04.json').read_text('utf-8'))
        self.assertEqual(len(result['partidos']), 7)
        self.assertTrue(all(p['hora'] and p['fecha'] for p in result['partidos']))


if __name__ == '__main__':
    unittest.main()
