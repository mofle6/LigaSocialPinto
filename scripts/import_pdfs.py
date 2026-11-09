#!/usr/bin/env python3
"""Versioned PDF import. Validate the complete batch in a disposable data tree."""
import argparse
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from parse_jornada import parse as parse_f7, validate, slug
from parse_f11 import parse as parse_f11
from parse_fs import parse as parse_fs
from parse_horarios import parse as parse_schedule

ROOT = Path(__file__).resolve().parent.parent
NAME = re.compile(r'(CLASIFICACION|HORARIOS)_(1DVF7|2DVF7|3DVF7|4DVF7|F11|FS)_J(\d{2})_(\d{8})(?:_V([1-9]\d*))?\.pdf', re.I)
COUNTS = {'1dvf7': 13, '2dvf7': 13, '3dvf7': 13, '4dvf7': 12, 'f11': 10, 'fs': 14}
STATS = ('pj', 'pg', 'pe', 'pp', 'gf', 'gc', 'pts', 'sancion')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path):
    m = NAME.fullmatch(path.name)
    if not m:
        raise ValueError(f'{path.name}: nombre inválido; usa TIPO_DIVISION_JNN_AAAAMMDD.pdf')
    kind, division, jornada, published, revision = m.groups()
    datetime.strptime(published, '%Y%m%d')
    if not 1 <= int(jornada) <= 99:
        raise ValueError('Jornada fuera de 01..99')
    return kind.upper(), division.lower(), int(jornada), (published, int(revision or 1))


def select(root):
    legacy = read(root / 'data/pdf-legacy.json')
    groups = {}
    for p in sorted((root / 'pdfs').rglob('*')):
        if not p.is_file() or p.suffix.lower() != '.pdf':
            continue
        rel = p.relative_to(root).as_posix()
        sha = digest(p)
        if rel in legacy:
            if sha != legacy[rel]:
                raise ValueError(f'{rel}: PDF histórico modificado; sube la corrección con el nombre nuevo')
            continue
        kind, division, jornada, version = identity(p)
        # Season is a directory, so two seasons cannot silently collide.
        season = p.parent.name
        if not re.fullmatch(r'\d{4}-\d{4}', season) or int(season[5:]) != int(season[:4]) + 1:
            raise ValueError(f'{rel}: debe estar en pdfs/AAAA-AAAA/ (temporada consecutiva)')
        key = (season, division, jornada, kind)
        versions = groups.setdefault(key, {})
        if version in versions and versions[version][1] != sha:
            raise ValueError(f'{key}: misma fecha/revisión con distinto contenido; usa _V2')
        versions[version] = (p, sha)
    return {k: (max(v), *v[max(v)]) for k, v in groups.items()}


def target(data, key):
    season, division, jornada, kind = key
    return data / season / division / ('proximas' if kind == 'HORARIOS' else '') / f'j{jornada:02d}.json'


def check_teams(d, known):
    teams = [p[s + '_id'] for p in d['partidos'] for s in ('local', 'visitante')]
    if d.get('descansa_id'):
        teams.append(d['descansa_id'])
    if len(teams) != len(set(teams)) or set(teams) != known:
        raise ValueError('Equipos duplicados, ausentes o desconocidos en partidos/descanso')


def check_results(d):
    errors = validate(d)
    if errors:
        raise ValueError('; '.join(errors))
    rows = d['clasificacion']
    known = {r['equipo_id'] for r in rows}
    if len(rows) != COUNTS[d['division']] or len(known) != len(rows):
        raise ValueError('Número de equipos incorrecto o clasificación duplicada')
    if sorted(r['pos'] for r in rows) != list(range(1, len(rows) + 1)):
        raise ValueError('Posiciones de clasificación inválidas')
    if any(type(r[k]) is not int or r[k] < 0 for r in rows for k in STATS):
        raise ValueError('Estadísticas negativas o no enteras')
    check_teams(d, known)
    for p in d['partidos']:
        scores = [p.get('goles_local'), p.get('goles_visitante')]
        if p['estado'] == 'jugado':
            if any(type(x) is not int or x < 0 for x in scores):
                raise ValueError('Resultado jugado inválido')
        elif p['estado'] not in ('sin_resultado', 'aplazado', 'suspendido') or scores != [None, None]:
            raise ValueError('Estado pendiente/suspendido inválido')


def table_signature(d):
    return {r['equipo_id']: tuple(r[k] for k in STATS) for r in d['clasificacion']}


def match_signature(d):
    return sorted((p['local_id'], p['visitante_id'], p['estado'], p.get('goles_local'), p.get('goles_visitante')) for p in d['partidos'])


def protect_history(before, after, changed, choices):
    for key in changed:
        if key[3] != 'CLASIFICACION':
            continue
        old_path, new_path = target(before, key), target(after, key)
        old = read(old_path) if old_path.exists() else None
        new = read(new_path)
        material = old is None or table_signature(old) != table_signature(new) or match_signature(old) != match_signature(new)
        if not material:
            continue
        for later in new_path.parent.glob('j*.json'):
            n = read(later)['jornada']
            later_key = (*key[:2], n, 'CLASIFICACION')
            if n > key[2] and (later_key not in choices or choices[later_key][0] < choices[key][0]):
                raise ValueError(f'{key}: corrección histórica; añade clasificación oficial actualizada J{n:02d} para proteger las acumuladas')
        # Check all later official snapshots against known results (incomplete history is allowed).
        for later in new_path.parent.glob('j*.json'):
            snapshot = read(later)
            if snapshot['jornada'] < key[2]:
                continue
            totals = {r['equipo_id']: dict.fromkeys(('pj', 'pg', 'pe', 'pp', 'gf', 'gc'), 0) for r in snapshot['clasificacion']}
            for history in new_path.parent.glob('j*.json'):
                h = read(history)
                if h['jornada'] > snapshot['jornada']:
                    continue
                for p in h['partidos']:
                    if p['estado'] != 'jugado':
                        continue
                    for side, other in (('local', 'visitante'), ('visitante', 'local')):
                        t = totals[p[side + '_id']]
                        gf, gc = p['goles_' + side], p['goles_' + other]
                        t['pj'] += 1
                        t['gf'] += gf
                        t['gc'] += gc
                        t['pg' if gf > gc else 'pe' if gf == gc else 'pp'] += 1
            for r in snapshot['clasificacion']:
                if any(r[k] < v for k, v in totals[r['equipo_id']].items()):
                    raise ValueError(f'{later}: clasificación incompatible con los resultados conocidos de {r["equipo"]}')


def preserve_pending_states(old, new):
    """An unspecified pending PDF does not revoke a confirmed suspension."""
    existing = {(p['local_id'], p['visitante_id']): p for p in old['partidos']}
    notes = []
    for p in new['partidos']:
        prior = existing.get((p['local_id'], p['visitante_id']))
        if (prior and prior['estado'] in ('suspendido', 'aplazado')
                and p['estado'] == 'sin_resultado'
                and all(m.get(k) is None for m in (prior, p) for k in ('goles_local', 'goles_visitante'))):
            p['estado'] = prior['estado']
            notes.append(f"{p['local']} - {p['visitante']}: se conserva {p['estado']}; el PDF no especifica estado")
    if notes:
        new['observaciones_importacion'] = notes
    return notes


def prepare(root, staged):
    choices = select(root)
    aliases = read(root / 'data/alias.json')
    changed = set()
    report = []
    for key, (version, pdf, sha) in sorted(choices.items()):
        dest = target(staged, key)
        old = read(dest) if dest.exists() else None
        provenance = (old or {}).get('pdf_import', {})
        previous = tuple(provenance.get('version', ('', 0)))
        if previous > version:
            raise ValueError(f'{pdf}: versión anterior a los datos guardados')
        if previous == version and provenance.get('sha256') != sha:
            raise ValueError(f'{pdf}: revisión ya importada con otro contenido; usa _V2')
        if provenance.get('sha256') == sha:
            continue
        kind = key[3]
        parser = parse_schedule if kind == 'HORARIOS' else {'f11': parse_f11, 'fs': parse_fs}.get(key[1], parse_f7)
        d = parser(pdf)
        if (d.get('temporada'), d.get('division'), d.get('jornada')) != key[:3]:
            raise ValueError(f'{pdf}: nombre/directorio no coincide con el encabezado del PDF')
        if kind == 'CLASIFICACION':
            if old:
                preserve_pending_states(old, d)
            try:
                check_results(d)
            except ValueError as exc:
                raise ValueError(f'{pdf}: {exc}') from exc
            if old:
                existing = {(p['local_id'], p['visitante_id']): p for p in old['partidos']}
                incoming = {(p['local_id'], p['visitante_id']): p for p in d['partidos']}
                if existing.keys() != incoming.keys():
                    raise ValueError(f'{pdf}: los emparejamientos difieren de los datos guardados')
                if any(p['estado'] == 'jugado' and incoming[k]['estado'] != 'jugado' for k, p in existing.items()):
                    raise ValueError(f'{pdf}: intenta devolver un partido jugado a pendiente')
        else:
            for p in d['partidos']:
                for side in ('local', 'visitante'):
                    p[side + '_id'] = aliases.get(p[side], slug(p[side]))
                date.fromisoformat(p['fecha'])
                datetime.strptime(p['hora'], '%H:%M')
                if not p['campo']:
                    raise ValueError('Campo vacío')
            if d.get('descansa'):
                d['descansa_id'] = aliases.get(d['descansa'], slug(d['descansa']))
        d['origen'] = pdf.relative_to(root).as_posix()
        d['pdf_import'] = {'version': list(version), 'sha256': sha}
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        changed.add(key)
        report.append(f'{d["origen"]} -> {dest.relative_to(staged).as_posix()} sha256={sha}')
    for key in changed:
        if key[3] == 'HORARIOS':
            dest = target(staged, key)
            refs = sorted(dest.parent.parent.glob('j*.json'))
            if not refs:
                raise ValueError(f'{key}: falta clasificación para validar equipos')
            check_teams(read(dest), {r['equipo_id'] for r in read(refs[-1])['clasificacion']})
    protect_history(root / 'data', staged, changed, choices)
    return changed, report


def verified_archive(root, base, source):
    """Allow only documented, byte-preserving moves out of the active PDF set."""
    manifest = root / 'data/pdf-archive.json'
    entry = read(manifest).get(source) if manifest.exists() else None
    if not entry or (root / source).exists():
        return False
    destination = entry.get('destino', '')
    if not destination.startswith('archivo/pdfs/'):
        return False
    archived = (root / destination).resolve()
    if not archived.is_relative_to((root / 'archivo/pdfs').resolve()) or not archived.is_file():
        return False
    original = subprocess.check_output(['git', 'show', f'{base}:{source}'], cwd=root)
    return hashlib.sha256(original).hexdigest() == entry.get('sha256') == digest(archived)


def check_git_changes(root, base):
    changes = subprocess.check_output(['git', 'diff', '--name-status', '-z', '--no-renames', base, 'HEAD', '--', 'pdfs/'], cwd=root).decode('utf-8').split('\0')
    for status, path in zip(changes[0::2], changes[1::2]):
        if status in ('D', 'M', 'T') and NAME.fullmatch(Path(path).name):
            if status == 'D' and verified_archive(root, base, path):
                continue
            raise ValueError(f'{path}: versiones inmutables; conserva el PDF y añade otra fecha o _V2')


def run(root=ROOT, check=False, base_ref=None):
    if base_ref:
        check_git_changes(root, base_ref)
    # No destination is touched until every PDF and cross-round check succeeds.
    with tempfile.TemporaryDirectory(prefix='.pdf-stage-', dir=root) as tmp:
        staged = Path(tmp) / 'data'
        shutil.copytree(root / 'data', staged)
        changed, report = prepare(root, staged)
        if not check:
            for key in sorted(changed):
                dest = target(root / 'data', key)
                dest.parent.mkdir(parents=True, exist_ok=True)
                pending = dest.with_suffix('.json.tmp')
                shutil.copyfile(target(staged, key), pending)
                pending.replace(dest)
        print('\n'.join(report) or 'Sin cambios: históricos protegidos y versiones ya importadas.')
        print(f'VALIDADO: {len(changed)} documentos' + (' (sin escribir)' if check else ''))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--check', action='store_true', help='Validar sin modificar data/')
    cli.add_argument('--base-ref', help='Comparar con el commit anterior y proteger PDFs versionados')
    args = cli.parse_args()
    try:
        run(check=args.check, base_ref=args.base_ref)
    except Exception as exc:
        cli.exit(1, f'ERROR: no se actualiza/publica el lote: {exc}\n')
