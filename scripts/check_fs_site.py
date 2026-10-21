#!/usr/bin/env python3
"""Validate rendered futsal league and every team's upcoming fixture."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
data = ROOT / "data/2026-2027/fs"
site = ROOT / "site/2026-2027/fs"
j1 = json.loads((data / "j01.json").read_text("utf-8"))
j2 = json.loads((data / "j02.json").read_text("utf-8"))
schedule = json.loads((data / "proximas/j03.json").read_text("utf-8"))
teams = {r["equipo_id"] for r in j2["clasificacion"]}
assert len(teams) == 14
for j in (j1, j2):
    assert len(j["partidos"]) == 7 and len(j["clasificacion"]) == 14
    assert sum(r["gf"] for r in j["clasificacion"]) == sum(r["gc"] for r in j["clasificacion"])
    assert all(r["pj"] == r["pg"] + r["pe"] + r["pp"] and r["pts"] == 3*r["pg"] + r["pe"] - r["sancion"] for r in j["clasificacion"])
assert len(schedule["partidos"]) == 7
assert {p[side+"_id"] for p in schedule["partidos"] for side in ("local","visitante")} == teams
assert (ROOT / "site/assets/campo02.jpg").is_file()
home = (ROOT / "site/index.html").read_text("utf-8")
assert "Fútbol Sala" in home and "TORNEO APERTURA F.SALA" in home
league = (site / "index.html").read_text("utf-8")
assert "<h2>Próxima jornada" in league and "<h2>Clasificación</h2>" in league
assert league.index("<h2>Próxima jornada") < league.index("<h2>Clasificación</h2>")
for p in schedule["partidos"]:
    for term in (p["local"], p["visitante"], p["hora"], p["campo"]):
        assert term in league, term
    for side in ("local", "visitante"):
        tid = p[side+"_id"]
        page = site / "equipos" / (tid+".html")
        assert page.is_file(), tid
        html = page.read_text("utf-8")
        for term in ("Próxima jornada", p["local"], p["visitante"], p["hora"], p["campo"]):
            assert term in html, (tid, term)
for n in (1,2):
    assert (site / f"jornada-{n:02d}.html").is_file()
print("OK: futsal 14 teams, J1/J2, seven J3 fixtures and all team pages")
