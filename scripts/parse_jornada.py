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
RE_REST = re.compile(r"^(?:Descansa\s+-\s+(?P<right>.+)|(?P<left>.+?)\s+-\s+Descansa)$")
RE_SUSPENDED = re.compile(r"^(?P<home>.+?)\s+(?:S\s*-|-\s*S)\s+(?P<away>.+)$")
RE_PENDING = re.compile(r"^(?P<home>.+?)\s+-\s+(?P<away>.+)$")
RE_ROW = re.compile(
    r"^(?P<pos>\d+)\s+(?P<team>.+?)\s+(?P<pts>-?\d+)\s+(?P<j>\d+)\s+(?P<g>\d+)\s+(?P<e>\d+)\s+"
    r"(?P<p>\d+)\s+(?P<gf>\d+)\s+(?P<gc>\d+)\s*(?P<form>(?:[GEP]\s?)*)\s+(?P<sanc>\d+)$"
)

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def normalize_wrapped_results(lines):
    """Resolve three-line score rows using only exact names in the official table."""
    known = [m['team'] for line in lines if (m := RE_ROW.match(line))]
    normalized = list(lines)
    i = 1
    while i < len(normalized) - 1:
        score = re.fullmatch(r"(\d+)\s*-\s*(\d+)", normalized[i])
        if not score:
            i += 1
            continue
        prefix, suffix = normalized[i - 1], normalized[i + 1]
        complete = {(home, away) for home in known for away in known
                    if home != away and prefix == home + ' ' + away}
        if len(complete) == 1:
            home, away = complete.pop()
            normalized[i-1:i+1] = [f'{home} {score[1]} - {score[2]} {away}']
            i = max(1, i - 1)
            continue
        if len(complete) > 1:
            raise ValueError('Equipos ambiguos en resultado separado: ' + prefix)
        candidates = set()
        for home in known:
            for away in known:
                if home == away:
                    continue
                # A wrapped name can belong to either side of the score.
                for team, is_home in ((home, True), (away, False)):
                    words = team.split()
                    for cut in range(1, len(words)):
                        first, rest = ' '.join(words[:cut]), ' '.join(words[cut:])
                        expected = first + ' ' + away if is_home else home + ' ' + first
                        if prefix == expected and suffix == rest:
                            candidates.add((home, away))
        if len(candidates) != 1:
            raise ValueError('Resultado en varias líneas sin equipos inequívocos en la tabla: ' + prefix)
        home, away = candidates.pop()
        normalized[i-1:i+2] = [f'{home} {score[1]} - {score[2]} {away}']
        i = max(1, i - 1)
    return normalized


def normalize_wrapped_rest(lines):
    """Join an explicit rest label and its separately extracted dash."""
    known = {m['team'] for line in lines if (m := RE_ROW.match(line))}
    normalized = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if i + 1 < len(lines) and lines[i + 1] == '-':
            if line.endswith(' Descansa') and line[:-len(' Descansa')] in known:
                normalized.append(line[:-len(' Descansa')] + ' - Descansa')
                i += 2
                continue
            if line.startswith('Descansa ') and line[len('Descansa '):] in known:
                normalized.append('Descansa - ' + line[len('Descansa '):])
                i += 2
                continue
        normalized.append(line)
        i += 1
    return normalized


def parse(path):
    with pdfplumber.open(path) as pdf:
        lines = [l.strip() for pg in pdf.pages for l in (pg.extract_text() or "").splitlines() if l.strip()]

    lines = normalize_wrapped_results(normalize_wrapped_rest(lines))

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
                out["descansa"] = m["right"] or m["left"]
            elif (m := RE_SCORED.match(l)):
                out["partidos"].append({"local": m["home"], "visitante": m["away"],
                                        "goles_local": int(m["hg"]), "goles_visitante": int(m["ag"]), "estado": "jugado"})
            elif (m := RE_SUSPENDED.match(l)):
                out["partidos"].append({"local": m["home"], "visitante": m["away"],
                                        "goles_local": None, "goles_visitante": None, "estado": "suspendido"})
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
