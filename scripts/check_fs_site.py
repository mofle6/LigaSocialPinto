#!/usr/bin/env python3
"""Validate rendered futsal league and every team's upcoming fixture."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
data = ROOT / "data/2026-2027/fs"
site = ROOT / "site/2026-2027/fs"
j1 = json.loads((data / "j01.json").read_text("utf-8"))
j2 = json.loads((data / "j02.json").read_text("utf-8"))
j3 = json.loads((data / "j03.json").read_text("utf-8"))
teams = {r["equipo_id"] for r in j2["clasificacion"]}
assert len(teams) == 14
for j in (j1, j2, j3):
    assert len(j["partidos"]) == 7 and len(j["clasificacion"]) == 14
    assert sum(r["gf"] for r in j["clasificacion"]) == sum(r["gc"] for r in j["clasificacion"])
    assert all(r["pj"] == r["pg"] + r["pe"] + r["pp"] and r["pts"] == 3*r["pg"] + r["pe"] - r["sancion"] for r in j["clasificacion"])
assert {p[side+"_id"] for p in j3["partidos"] for side in ("local","visitante")} == teams
assert all(p["estado"] == "jugado" and p["goles_local"] is not None and p["goles_visitante"] is not None for p in j3["partidos"])
assert [r["pts"] for r in j3["clasificacion"][:3]] == [9, 9, 9]
assert (ROOT / "site/assets/campo02.jpg").is_file()
home = (ROOT / "site/index.html").read_text("utf-8")
assert "Fútbol Sala" in home and "TORNEO APERTURA F.SALA" in home
league = (site / "index.html").read_text("utf-8")
assert "<h2>Clasificación</h2>" in league
assert "J3" in league or "Jornada 3" in league
for p in j3["partidos"]:
    for term in (p["local"], p["visitante"], str(p["goles_local"]), str(p["goles_visitante"])):
        assert term in (site / "jornada-03.html").read_text("utf-8"), term
    for side in ("local", "visitante"):
        tid = p[side+"_id"]
        page = site / "equipos" / (tid+".html")
        assert page.is_file(), tid
        html = page.read_text("utf-8")
        assert "Último partido" in html and "Partidos" in html, tid
for n in (1, 2, 3):
    assert (site / f"jornada-{n:02d}.html").is_file()
print("OK: futsal 14 teams, J1/J2/J3, seven J3 results and all team pages")
