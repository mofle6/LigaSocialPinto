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

    def test_actual_oro_j2_wrapped_rest(self):
        d = parse(ROOT / 'pdfs/2026-2027/CLASIFICACION_1DVF7_J02_20261109.pdf')
        imp.check_results(d)
        self.assertEqual(d['descansa'], 'EL INTER NOVELLA & GARCIA OLD ROKERS')
        self.assertEqual(len(d['partidos']), 6)

    def test_unspecified_pending_keeps_confirmed_state(self):
        for state in ('suspendido', 'aplazado'):
            old = deepcopy(self.fixture)
            old['partidos'][0].update(estado=state, goles_local=None, goles_visitante=None)
            new = deepcopy(old)
            new['partidos'][0]['estado'] = 'sin_resultado'
            notes = imp.preserve_pending_states(old, new)
            self.assertEqual(new['partidos'][0]['estado'], state)
            self.assertEqual(len(notes), 1)
            self.assertEqual(new['observaciones_importacion'], notes)

    def test_scored_and_explicit_pending_states_are_not_overridden(self):
        old = deepcopy(self.fixture)
        old['partidos'][0].update(estado='suspendido', goles_local=None, goles_visitante=None)
        played = deepcopy(self.fixture)
        self.assertEqual(imp.preserve_pending_states(old, played), [])
        self.assertEqual(played['partidos'][0]['estado'], 'jugado')
        explicit = deepcopy(old)
        explicit['partidos'][0]['estado'] = 'aplazado'
        imp.preserve_pending_states(old, explicit)
        self.assertEqual(explicit['partidos'][0]['estado'], 'aplazado')

    def test_archive_move_requires_same_original_bytes(self):
        import hashlib
        source = 'pdfs/2026-2027/CLASIFICACION_FS_J06_20261108.pdf'
        destination = 'archivo/pdfs/2026-2027/copia.pdf'
        original = b'original-pdf'
        archived = self.root / destination
        archived.parent.mkdir(parents=True)
        archived.write_bytes(original)
        manifest = {source: {'destino': destination, 'sha256': hashlib.sha256(original).hexdigest()}}
        (self.root / 'data/pdf-archive.json').write_text(json.dumps(manifest), encoding='utf-8')
        changes = f'D\0{source}\0'.encode()
        with patch.object(imp.subprocess, 'check_output', side_effect=[changes, original]):
            imp.check_git_changes(self.root, 'base')
        archived.write_bytes(b'changed')
        with patch.object(imp.subprocess, 'check_output', side_effect=[changes, original]):
            with self.assertRaisesRegex(ValueError, 'inmutables'):
                imp.check_git_changes(self.root, 'base')

    def test_actual_archived_copy_is_j5_and_integrity_matches(self):
        manifest = imp.read(ROOT / 'data/pdf-archive.json')
        source, entry = next(iter(manifest.items()))
        self.assertFalse((ROOT / source).exists())
        archived = ROOT / entry['destino']
        self.assertEqual(imp.digest(archived), entry['sha256'])
        self.assertEqual(imp.parse_fs(archived)['jornada'], 5)

    def test_full_uploaded_season_preserves_later_plata_tables(self):
        shutil.copytree(ROOT / 'pdfs', self.root / 'pdfs', dirs_exist_ok=True)
        shutil.copytree(ROOT / 'archivo', self.root / 'archivo', dirs_exist_ok=True)
        directory = self.root / 'data/2026-2027/2dvf7'
        before = {n: imp.table_signature(imp.read(directory / f'j{n:02d}.json')) for n in (3, 4)}
        self.run_import()
        j2 = imp.read(directory / 'j02.json')
        game = next(p for p in j2['partidos'] if p['local_id'] == 'galacticos-del-local')
        self.assertEqual((game['goles_local'], game['goles_visitante'], game['estado']), (3, 2, 'jugado'))
        for n in (3, 4):
            self.assertEqual(before[n], imp.table_signature(imp.read(directory / f'j{n:02d}.json')))
        oro = imp.read(self.root / 'data/2026-2027/1dvf7/j03.json')
        game = next(p for p in oro['partidos'] if p['local_id'] == 'team-x-rest-kuntur-wasi')
        self.assertEqual(game['estado'], 'suspendido')
        self.assertFalse((self.root / 'data/2026-2027/fs/j06.json').exists())
        before_repeat = self.snapshot()
        self.run_import()
        self.assertEqual(before_repeat, self.snapshot())

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

    def test_actual_oro_j4_wrapped_away_team(self):
        d = parse(ROOT / 'pdfs/2026-2027/CLASIFICACION_1DVF7_J04_20261108.pdf')
        imp.check_results(d)
        self.assertEqual(len(d['partidos']), 6)
        game = next(p for p in d['partidos'] if p['local'] == 'MACHOTES DE ANTONIO')
        self.assertEqual(game['visitante'], 'EL INTER NOVELLA & GARCIA OLD ROKERS')
        self.assertEqual((game['goles_local'], game['goles_visitante']), (4, 4))

    def test_actual_oro_j3_wrapped_home_team(self):
        d = parse(ROOT / 'pdfs/Clasificación_j3_f7_oro.pdf')
        self.assertFalse(imp.validate(d))
        self.assertEqual(len(d['partidos']), 6)
        game = next(p for p in d['partidos'] if p['local'] == 'EL INTER NOVELLA & GARCIA OLD ROKERS')
        self.assertEqual(game['visitante'], 'LA OSTRA')

    def test_wrapped_unknown_teams_fail_instead_of_guessing(self):
        from parse_jornada import normalize_wrapped_results
        with self.assertRaisesRegex(ValueError, 'inequívocos'):
            normalize_wrapped_results(['UNKNOWN TEAMS', '4 - 4', 'ROKERS'])

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
