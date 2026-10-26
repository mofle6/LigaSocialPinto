"""Read RFFM Torneo Apertura F.SALA standings with Pts/PJ column."""
import re
import pdfplumber
from parse_jornada import slug

HEAD = re.compile(r"TORNEO APERTURA F\.SALA,.*Temporada\s+(\d{4}-\d{4})")
ROUND = re.compile(r"Jornada\s+(\d+)\s+\((\d{2}-\d{2}-\d{4})\)")
MATCH = re.compile(r"^(.+?)\s+(\d+)\s*-\s*(\d+)\s+(.+)$")
PENDING = re.compile(r"^(.+?)\s+-\s+(.+)$")
SUSPENDED = re.compile(r"^(.+?)\s+(?:S\s*-|-\s*S)\s+(.+)$")
ROW = re.compile(r"^(\d+)\s+(.+?)\s+\d+,\d{4}\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+((?:[GEP]\s*)+)\s+(\d+)$")

def parse(path):
    with pdfplumber.open(path) as pdf:
        lines = [line.strip() for page in pdf.pages for line in (page.extract_text() or "").splitlines() if line.strip()]
    head = next((m for line in lines if (m := HEAD.search(line))), None)
    round_ = next((m for line in lines if (m := ROUND.search(line))), None)
    if not head or not round_:
        raise ValueError("Encabezado o jornada F.SALA no reconocidos")
    start = next(i for i, line in enumerate(lines) if line.startswith("Equipos"))
    matches = []
    for line in lines[:start]:
        if m := MATCH.match(line):
            a, x, y, b = m.groups()
            matches.append({"local": a, "visitante": b, "local_id": slug(a), "visitante_id": slug(b),
                            "goles_local": int(x), "goles_visitante": int(y), "estado": "jugado"})
        elif m := SUSPENDED.match(line):
            a, b = m.groups()
            matches.append({"local": a, "visitante": b, "local_id": slug(a), "visitante_id": slug(b),
                            "goles_local": None, "goles_visitante": None, "estado": "suspendido"})
        elif m := PENDING.match(line):
            a, b = m.groups()
            matches.append({"local": a, "visitante": b, "local_id": slug(a), "visitante_id": slug(b),
                            "goles_local": None, "goles_visitante": None, "estado": "sin_resultado"})
    rows = []
    for line in lines[start+1:]:
        if m := ROW.match(line):
            pos, name, pts, pj, pg, pe, pp, gf, gc, form, sanction = m.groups()
            rows.append({"pos": int(pos), "equipo": name, "equipo_id": slug(name), "pts": int(pts),
                         "pj": int(pj), "pg": int(pg), "pe": int(pe), "pp": int(pp), "gf": int(gf),
                         "gc": int(gc), "ultimos": form.split(), "sancion": int(sanction)})
    if len(matches) != 7 or len(rows) != 14:
        raise ValueError(f"F.SALA incompleto: {len(matches)} partidos y {len(rows)} equipos")
    return {"competicion": "TORNEO APERTURA F.SALA", "division": "fs",
            "nombre_division": "TORNEO APERTURA F.SALA", "temporada": head[1],
            "jornada": int(round_[1]), "fecha": "-".join(reversed(round_[2].split("-"))),
            "partidos": matches, "descansa": None, "descansa_id": None, "clasificacion": rows}
