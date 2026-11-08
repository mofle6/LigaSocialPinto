"""Validate league and team output against the latest available data."""
import json
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]


def check(code, count):
    directory = ROOT / 'data/2026-2027' / code
    site = ROOT / 'site/2026-2027' / code
    rounds = [json.loads(p.read_text('utf-8')) for p in directory.glob('j*.json')]
    latest = max(rounds, key=lambda d: d['jornada'])
    for d in rounds:
        assert len(d['clasificacion']) == count
        assert sum(r['gf'] for r in d['clasificacion']) == sum(r['gc'] for r in d['clasificacion'])
        assert all(r['pj'] == r['pg'] + r['pe'] + r['pp'] and r['pts'] == 3*r['pg'] + r['pe'] - r['sancion'] for r in d['clasificacion'])
        assert (site / f'jornada-{d["jornada"]:02d}.html').is_file()
    league = (site / 'index.html').read_text('utf-8')
    assert 'Clasificación' in league
    schedules = [json.loads(p.read_text('utf-8')) for p in (directory / 'proximas').glob('j*.json')]
    future = [d for d in schedules if d['jornada'] > latest['jornada']]
    if future:
        upcoming = min(future, key=lambda d: d['jornada'])
        assert f'J{upcoming["jornada"]}' in league
        for match in upcoming['partidos']:
            for side in ('local', 'visitante'):
                page = (site / 'equipos' / (match[side + '_id'] + '.html')).read_text('utf-8')
                assert 'Próxima jornada' in page and match['hora'] in page
    for row in latest['clasificacion']:
        assert (site / 'equipos' / (row['equipo_id'] + '.html')).is_file()
    print(code, 'histórico, clasificación vigente y fichas OK')
