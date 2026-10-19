#!/usr/bin/env python3
"""Genera la web estática en site/ a partir de data/."""
import json, shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "data", ROOT / "site"

env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]))
env.filters["fecha"] = lambda iso: "/".join(reversed(iso.split("-"))) if iso else ""

def load(path, default):
    return json.loads(path.read_text("utf-8")) if path.exists() else default

def fix_ids(d, al):
    """Aplica data/alias.json ({"NOMBRE EN EL PDF": "id-canonico"}) para unificar nombres."""
    for r in d["clasificacion"]:
        r["equipo_id"] = al.get(r["equipo"], r["equipo_id"])
    for p in d["partidos"]:
        p["local_id"] = al.get(p["local"], p["local_id"])
        p["visitante_id"] = al.get(p["visitante"], p["visitante_id"])
    if d.get("descansa"):
        d["descansa_id"] = al.get(d["descansa"], d.get("descansa_id"))

def render(tpl, path, **ctx):
    path.parent.mkdir(parents=True, exist_ok=True)
    depth = len(path.relative_to(OUT).parts) - 1
    ctx["root"] = "../" * depth if depth else "./"
    path.write_text(env.get_template(tpl).render(**ctx), encoding="utf-8")

def team_history(jornadas, tid):
    hist = []
    for n in sorted(jornadas):
        j = jornadas[n]
        if j.get("descansa_id") == tid:
            hist.append({"n": n, "fecha": j["fecha"], "descansa": True})
        for p in j["partidos"]:
            if tid not in (p["local_id"], p["visitante_id"]):
                continue
            home = p["local_id"] == tid
            gf, gc = (p["goles_local"], p["goles_visitante"]) if home else (p["goles_visitante"], p["goles_local"])
            res = None if gf is None else ("G" if gf > gc else "P" if gf < gc else "E")
            hist.append({"n": n, "fecha": j["fecha"], "descansa": False, "casa": home, "gf": gf, "gc": gc, "res": res,
                         "rival": p["visitante"] if home else p["local"],
                         "rival_id": p["visitante_id"] if home else p["local_id"]})
    return hist

def main():
    aliases = load(DATA / "alias.json", {})
    seasons = {}
    for f in sorted(DATA.glob("*/*/j*.json")):
        d = json.loads(f.read_text("utf-8"))
        fix_ids(d, aliases)
        div = seasons.setdefault(d["temporada"], {}).setdefault(d["division"], {"jornadas": {}})
        div["jornadas"][d["jornada"]] = d
        div["nombre"] = d.get("nombre_division") or d["division"]

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    index = []
    for temp in sorted(seasons, reverse=True):
        for code in sorted(seasons[temp]):
            div = seasons[temp][code]
            jornadas = div["jornadas"]
            last = jornadas[max(jornadas)]
            base = OUT / temp / code
            names = {}
            for j in jornadas.values():
                for r in j["clasificacion"]:
                    names[r["equipo_id"]] = r["equipo"]
            names.update({r["equipo_id"]: r["equipo"] for r in last["clasificacion"]})
            index.append({"temporada": temp, "code": code, "nombre": div["nombre"], "ultima": last})

            render("division.html", base / "index.html", temporada=temp, div=div, last=last, jornadas=sorted(jornadas))
            for n, j in jornadas.items():
                render("jornada.html", base / f"jornada-{n:02d}.html", temporada=temp, div=div, j=j)
            rows = {r["equipo_id"]: r for r in last["clasificacion"]}
            for tid, name in names.items():
                extra = load(DATA / temp / code / "equipos" / f"{tid}.json", {})
                render("equipo.html", base / "equipos" / f"{tid}.html", temporada=temp, div=div, nombre=name,
                       row=rows.get(tid), hist=team_history(jornadas, tid), extra=extra)
    render("index.html", OUT / "index.html", items=index)
    (OUT / ".nojekyll").write_text("")
    print(f"Web generada: {sum(1 for _ in OUT.rglob('*.html'))} páginas")

if __name__ == "__main__":
    main()
