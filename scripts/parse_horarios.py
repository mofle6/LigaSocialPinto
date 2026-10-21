#!/usr/bin/env python3
"""Extract future F7 fixtures from RFFM schedule PDFs, separately from standings."""
import json
import re
import sys
import pdfplumber
from parse_jornada import slug

HEADER = re.compile(r"AFICIONADO F7,\s*(\dDVF7)\s+(.+?)\s+Temporada\s+(\d{4}-\d{4})", re.I)
DATE = re.compile(r"^\d{2}-\d{2}-\d{4}$")
TIME = re.compile(r"^\d{2}:\d{2}$")
FIELD = re.compile(r"Campo:\s*CAMPO\s+(.+?)\s+F7\s+(C[12])\s*-", re.I)

def parse_f11(lines):
    header = next((m for line in lines if (m := re.search(r"PRIMERA AFICIONADOS F11,.*?Temporada\s+(\d{4}-\d{4})", line))), None)
    jornada = next((m for line in lines if (m := re.match(r"Jornada\s+(\d+)$", line))), None)
    if not header or not jornada:
        raise ValueError("No se encontró temporada o jornada F11")
    match_line = re.compile(r"^(.+?)\s+(\d{2}-\d{2}-\d{4})\s+(.+)$")
    games = []
    for i, line in enumerate(lines):
        m = match_line.match(line)
        if not m:
            continue
        if i + 2 >= len(lines) or not TIME.fullmatch(lines[i + 1]) or not lines[i + 2].startswith("Campo:"):
            continue
        local, raw_date, visitante = m.groups()
        campo = lines[i + 2].split("Campo:", 1)[1].split(" - ", 1)[0].strip()
        if campo == "ESTADIO RAFAEL MENDOZA":
            campo = "Estadio Rafael Mendoza"
        elif campo == "CAMPO PRINCIPES DE ASTURIAS F11":
            campo = "Campo Príncipes de Asturias F11"
        else:
            raise ValueError("Campo F11 desconocido: " + campo)
        games.append({"local": local, "local_id": slug(local), "visitante": visitante, "visitante_id": slug(visitante), "fecha": "-".join(reversed(raw_date.split("-"))), "hora": lines[i + 1], "campo": campo, "pista": ""})
    if len(games) != 5:
        raise ValueError(f"Se esperaban 5 partidos F11, encontrados {len(games)}")
    return {"temporada": header[1], "division": "f11", "jornada": int(jornada[1]), "fecha": min(g["fecha"] for g in games), "descansa": None, "descansa_id": None, "partidos": games}

def parse(path):
    with pdfplumber.open(path) as pdf:
        pages = [(p.extract_text() or "", p.extract_words()) for p in pdf.pages]
    lines = [line.strip() for text, _ in pages for line in text.splitlines() if line.strip()]
    if any("PRIMERA AFICIONADOS F11" in line for line in lines):
        return parse_f11(lines)
    head = next((m for line in lines if (m := HEADER.search(line))), None)
    jorn = next((m for line in lines if (m := re.search(r"^Jornada\s+(\d+)$", line))), None)
    if not head or not jorn:
        raise ValueError("No se encontró división, temporada o jornada")
    games = []
    for _, words in pages:
        field_rows = sorted((w for w in words if w["text"] == "Campo:"), key=lambda w: w["top"])
        previous = 0
        for fw in field_rows:
            top = fw["top"]
            segment = [w for w in words if previous < w["top"] < top - 1]
            previous = top
            dates = [w for w in segment if DATE.fullmatch(w["text"])]
            times = [w for w in segment if TIME.fullmatch(w["text"])]
            if len(dates) != 1 or len(times) != 1:
                raise ValueError("Partido sin fecha u hora única")
            left = sorted((w for w in segment if 55 < w["x0"] < 260 and w["top"] >= dates[0]["top"] - 15 and not DATE.fullmatch(w["text"]) and not TIME.fullmatch(w["text"])), key=lambda w: (round(w["top"] / 8), w["x0"]))
            right = sorted((w for w in segment if w["x0"] >= 370 and w["top"] >= dates[0]["top"] - 15), key=lambda w: (round(w["top"] / 8), w["x0"]))
            local = " ".join(w["text"] for w in left)
            visitante = " ".join(w["text"] for w in right)
            field_words = sorted((w for w in words if top - 1 <= w["top"] <= top + 2 and w["x0"] >= fw["x0"]), key=lambda w: w["x0"])
            field_text = " ".join(w["text"] for w in field_words)
            field = FIELD.search(field_text)
            if not local or not visitante or not field:
                raise ValueError("No se pudieron leer equipos o campo: " + field_text)
            date = "-".join(reversed(dates[0]["text"].split("-")))
            games.append({"local": local, "local_id": slug(local), "visitante": visitante, "visitante_id": slug(visitante), "fecha": date, "hora": times[0]["text"], "campo": field[1].title().replace("Principes", "Príncipes"), "pista": field[2]})
    if len(games) != 6:
        raise ValueError(f"Se esperaban 6 encuentros, encontrados {len(games)}")
    rest = next((line[len("Descansa "):].strip() for line in lines if line.startswith("Descansa ")), None)
    return {"temporada": head[3], "division": head[1].lower(), "jornada": int(jorn[1]), "fecha": min(g["fecha"] for g in games), "descansa": rest, "descansa_id": slug(rest) if rest else None, "partidos": games}

if __name__ == "__main__":
    print(json.dumps(parse(sys.argv[1]), ensure_ascii=False, indent=2))
