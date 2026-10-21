#!/usr/bin/env python3
"""Read schedule PDFs in pdfs/ and update only data/.../proximas/jNN.json."""
import json
import re
import sys
from pathlib import Path
from parse_horarios import parse
from parse_jornada import slug

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
aliases = json.loads((DATA / "alias.json").read_text("utf-8")) if (DATA / "alias.json").exists() else {}
failed = False
seen = set()
for pdf in sorted((ROOT / "pdfs").rglob("*.pdf")):
    if not re.search(r"HO(?:R|A)ARIOS?", pdf.name, re.I):
        continue
    try:
        d = parse(pdf)
        key = (d["temporada"], d["division"], d["jornada"])
        if key in seen:
            raise ValueError("Hay dos PDF de horarios para la misma jornada/división")
        seen.add(key)
        directory = DATA / d["temporada"] / d["division"]
        result_files = sorted(directory.glob("j*.json"))
        if not result_files:
            raise ValueError("No hay clasificación de referencia para validar equipos")
        latest = json.loads(result_files[-1].read_text("utf-8"))
        known = {aliases.get(r["equipo"], r["equipo_id"]) for r in latest["clasificacion"]}
        teams = []
        for p in d["partidos"]:
            for side in ("local", "visitante"):
                p[side + "_id"] = aliases.get(p[side], slug(p[side]))
                teams.append(p[side + "_id"])
        if d.get("descansa"):
            d["descansa_id"] = aliases.get(d["descansa"], slug(d["descansa"]))
            teams.append(d["descansa_id"])
        if len(teams) != len(set(teams)):
            raise ValueError("Hay equipos repetidos en los encuentros o descanso")
        unknown = set(teams) - known
        if unknown:
            raise ValueError("Equipos no reconocidos: " + ", ".join(sorted(unknown)))
        if set(teams) != known:
            raise ValueError("Faltan equipos en la programación: " + ", ".join(sorted(known - set(teams))))
        dest = directory / "proximas" / f"j{d['jornada']:02d}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"OK horarios {pdf.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")
    except Exception as exc:
        print(f"ERROR horarios {pdf.relative_to(ROOT)}: {exc}", file=sys.stderr)
        failed = True
sys.exit(1 if failed else 0)
