#!/usr/bin/env python3
"""Extrae resultados y clasificación de un PDF de jornada (RFFM, Delegación Zonal).

Uso:  python scripts/parse_jornada.py pdfs/2dvf7/J2.pdf > data/2dvf7/j02.json
Sale con código 1 si alguna validación falla (para que la GitHub Action avise).
"""
import json, re, sys, unicodedata
import pdfplumber

RE_HEAD = re.compile(r"^(?P<comp>.+?),\s*(?P<code>\S+)\s+(?P<name>.+?)\s+Temporada\s+(?P<season>\d{4}-\d{4})$")
RE_JORN = re.compile(r"^Jornada\s+(?P<n>\d+)\s+\((?P<date>\d{2}-\d{2}-\d{4})\)$")
RE_SCORED = re.compile(r"^(?P<home>.+?)\s+(?P<hg>\d+)\s+-\s+(?P<ag>\d+)\s+(?P<away>.+)$")
RE_REST = re.compile(r"^(?P<team>.+?)\s+-\s+Descansa$")
RE_PENDING = re.compile(r"^(?P<home>.+?)\s+-\s+(?P<away>.+)$")
RE_ROW = re.compile(
    r"^(?P<pos>\d+)\s+(?P<team>.+?)\s+(?P<pts>\d+)\s+(?P<j>\d+)\s+(?P<g>\d+)\s+(?P<e>\d+)\s+"
    r"(?P<p>\d+)\s+(?P<gf>\d+)\s+(?P<gc>\d+)\s*(?P<form>(?:[GEP]\s?)*)\s+(?P<sanc>\d+)$"
)

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def parse(path):
    with pdfplumber.open(path) as pdf:
        lines = [l.strip() for pg in pdf.pages for l in (pg.extract_text() or "").splitlines() if l.strip()]

    out = {"competicion": None, "division": None, "nombre_division": None, "temporada": None, "jornada": None,
           "fecha": None, "partidos": [], "descansa": None, "clasificacion": []}
    in_matches = False
    for l in lines:
        if (m := RE_HEAD.match(l)):
            out.update(competicion=m["comp"], division=m["code"].lower(), nombre_division=m["name"], temporada=m["season"])
        elif (m := RE_JORN.match(l)):
            out.update(jornada=int(m["n"]), fecha="-".join(reversed(m["date"].split("-"))))
            in_matches = True
        elif l.startswith("Equipos"):
            in_matches = False
        elif in_matches:
            if (m := RE_REST.match(l)):
                out["descansa"] = m["team"]
            elif (m := RE_SCORED.match(l)):
                out["partidos"].append({"local": m["home"], "visitante": m["away"],
                                        "goles_local": int(m["hg"]), "goles_visitante": int(m["ag"]), "estado": "jugado"})
            elif (m := RE_PENDING.match(l)):
                out["partidos"].append({"local": m["home"], "visitante": m["away"],
                                        "goles_local": None, "goles_visitante": None, "estado": "sin_resultado"})
        elif (m := RE_ROW.match(l)):
            out["clasificacion"].append({
                "pos": int(m["pos"]), "equipo": m["team"], "equipo_id": slug(m["team"]),
                "pts": int(m["pts"]), "pj": int(m["j"]), "pg": int(m["g"]), "pe": int(m["e"]), "pp": int(m["p"]),
                "gf": int(m["gf"]), "gc": int(m["gc"]), "ultimos": m["form"].split(), "sancion": int(m["sanc"])})
    out["descansa_id"] = slug(out["descansa"]) if out["descansa"] else None
    for p in out["partidos"]:
        p["local_id"], p["visitante_id"] = slug(p["local"]), slug(p["visitante"])
    return out

def validate(d):
    errs, c = [], d["clasificacion"]
    if not c: errs.append("No se encontró la tabla de clasificación")
    for r in c:
        if r["pj"] != r["pg"] + r["pe"] + r["pp"]:
            errs.append(f"{r['equipo']}: J != G+E+P")
        if r["pts"] != 3 * r["pg"] + r["pe"] - r["sancion"]:
            errs.append(f"{r['equipo']}: puntos no cuadran con G/E/P y sanción")
    if sum(r["gf"] for r in c) != sum(r["gc"] for r in c):
        errs.append("Suma de goles a favor != goles en contra")
    names = {r["equipo"] for r in c}
    for p in d["partidos"]:
        for t in (p["local"], p["visitante"]):
            if t not in names: errs.append(f"Equipo del partido no está en la tabla: {t}")
    if d["descansa"] and d["descansa"] not in names:
        errs.append(f"Equipo que descansa no está en la tabla: {d['descansa']}")
    return errs

if __name__ == "__main__":
    data = parse(sys.argv[1])
    errs = validate(data)
    data["validacion"] = {"ok": not errs, "errores": errs}
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    print()
    for e in errs: print("ERROR:", e, file=sys.stderr)
    sys.exit(1 if errs else 0)
