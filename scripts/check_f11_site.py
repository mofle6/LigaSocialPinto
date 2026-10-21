#!/usr/bin/env python3
"""Fail CI if the generated F11 league or team pages are incomplete."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
data = root / "data/2026-2027/f11"
out = root / "site/2026-2027/f11"
j1 = json.loads((data / "j01.json").read_text("utf-8"))
j2 = json.loads((data / "j02.json").read_text("utf-8"))
next_round = json.loads((data / "proximas/j03.json").read_text("utf-8"))
assert len(j1["partidos"]) == len(j2["partidos"]) == len(next_round["partidos"]) == 5
assert len(j1["clasificacion"]) == len(j2["clasificacion"]) == 10
teams = {r["equipo_id"] for r in j2["clasificacion"]}
assert len(teams) == 10
assert sum(r["gf"] for r in j2["clasificacion"]) == sum(r["gc"] for r in j2["clasificacion"])
assert sum(r["pts"] for r in j2["clasificacion"]) == 30
scheduled = [p[side + "_id"] for p in next_round["partidos"] for side in ("local", "visitante")]
assert len(scheduled) == len(set(scheduled)) == 10
assert set(scheduled) == teams
assert (root / "site/assets/campo03.jpg").is_file()
home = (root / "site/index.html").read_text("utf-8")
assert "PRIMERA AFICIONADOS F11" in home
assert "campo03" in home
league = (out / "index.html").read_text("utf-8")
assert "Próxima jornada" in league and "Clasificación" in league
assert league.index("<h2>Próxima jornada") < league.index("<h2>Clasificación</h2>")
for match in next_round["partidos"]:
    for term in (match["local"], match["visitante"], match["hora"], match["campo"]):
        assert term in league, f"Falta {term} en liga F11"
    for side in ("local", "visitante"):
        tid = match[side + "_id"]
        page = out / "equipos" / (tid + ".html")
        assert page.is_file(), f"Falta ficha {tid}"
        html = page.read_text("utf-8")
        for term in ("Próxima jornada", match["local"], match["visitante"], match["hora"], match["campo"]):
            assert term in html, f"Falta {term} en ficha {tid}"
for number in (1, 2):
    assert (out / f"jornada-{number:02d}.html").is_file()
print("OK: F11 J1/J2, J3, portada, campo03 y diez fichas comprobadas")
