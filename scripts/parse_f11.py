"""Read RFFM F11 standings/results PDF (10 teams, 5 fixtures)."""
import re
import pdfplumber
from parse_jornada import slug

SCORE = re.compile(r"^(.+?)\s+(\d+)\s*-\s*(\d+)\s+(.+)$")
ROW = re.compile(r"^(\d+)\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+((?:[GEP]\s*)+)\s+(\d+)$")

def parse(path):
    with pdfplumber.open(path) as pdf:
        lines = [x.strip() for page in pdf.pages for x in (page.extract_text() or "").splitlines() if x.strip()]
    header = next((m for line in lines if (m := re.search(r"PRIMERA AFICIONADOS F11,.*?Temporada\s+(\d{4}-\d{4})", line))), None)
    jornada = next((m for line in lines if (m := re.search(r"^Jornada\s+(\d+)\s+\((\d{2}-\d{2}-\d{4})\)", line))), None)
    if not header or not jornada:
        raise ValueError("El PDF no es una clasificación F11 reconocible")
    start = next(i for i, line in enumerate(lines) if line.startswith("Equipos"))
    matches = []
    for line in lines[:start]:
        if m := SCORE.match(line):
            a, ga, gb, b = m.groups()
            matches.append({"local": a, "visitante": b, "goles_local": int(ga), "goles_visitante": int(gb), "local_id": slug(a), "visitante_id": slug(b), "estado": "jugado"})
    rows = []
    for line in lines[start+1:]:
        if m := ROW.match(line):
            pos, name, pts, pj, pg, pe, pp, gf, gc, form, sanc = m.groups()
            rows.append({"pos": int(pos), "equipo": name, "equipo_id": slug(name), "pts": int(pts), "pj": int(pj), "pg": int(pg), "pe": int(pe), "pp": int(pp), "gf": int(gf), "gc": int(gc), "ultimos": form.split(), "sancion": int(sanc)})
    if len(matches) != 5 or len(rows) != 10:
        raise ValueError(f"Se esperaban 5 encuentros y 10 equipos: {len(matches)} y {len(rows)}")
    return {"competicion": "PRIMERA AFICIONADOS F11", "division": "f11", "nombre_division": "PRIMERA AFICIONADOS F11", "temporada": header[1], "jornada": int(jornada[1]), "fecha": "-".join(reversed(jornada[2].split("-"))), "partidos": matches, "descansa": None, "descansa_id": None, "clasificacion": rows}
