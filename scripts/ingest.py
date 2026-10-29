#!/usr/bin/env python3
"""Lee todos los PDF de pdfs/ y escribe data/<temporada>/<division>/jNN.json.

La temporada, la división y la jornada se leen del propio PDF, así que da igual
cómo se llame el archivo o en qué subcarpeta de pdfs/ lo pongas.
Si un PDF falla la validación, se avisa y el proceso termina con error (no se publica).
"""
import json, sys
from pathlib import Path
from parse_jornada import parse, validate
from parse_f11 import parse as parse_f11
from parse_fs import parse as parse_fs
from j3_updates import apply as apply_j3_updates
import pdfplumber, re

ROOT = Path(__file__).resolve().parent.parent
failed, seen = False, {}

for pdf in sorted((ROOT / "pdfs").rglob("*.pdf")):
    rel = pdf.relative_to(ROOT).as_posix()
    # Los horarios se procesan por ingest_horarios.py; no tienen clasificación.
    if re.search(r"HO(?:RARIOS|ARIOS)", pdf.name, re.I):
        continue
    # En F11 los PDF de resultados sueltos no incluyen tabla; solo se ingiere clasificación.
    with pdfplumber.open(pdf) as doc:
        first = (doc.pages[0].extract_text() or "")
    is_f11 = "PRIMERA AFICIONADOS F11" in first
    is_fs = "TORNEO APERTURA F.SALA" in first
    if is_f11 and "Equipos" not in first:
        print(f"OMITIDO {rel}: PDF F11 de resultados/horarios sin clasificación")
        continue
    # La J1 de Segunda tiene clasificación reconstruida manualmente.
    # Verificar el JSON antes de conservarlo; las demás jornadas se procesan normalmente.
    if rel == "pdfs/J1 2DF7 CLASIFICACIÓN.pdf":
        fallback = ROOT / "data" / "2026-2027" / "2dvf7" / "j01.json"
        try:
            curated = json.loads(fallback.read_text(encoding="utf-8"))
            key_ok = (curated.get("temporada"), curated.get("division"), curated.get("jornada")) == ("2026-2027", "2dvf7", 1)
            if not key_ok or curated.get("reconstruida_manualmente") is not True or validate(curated) or len(curated.get("partidos", [])) != 6:
                raise ValueError("el JSON reconstruido no supera las validaciones")
            print(f"OK {rel}: se conserva la J1 reconstruida y validada")
            continue
        except (OSError, ValueError, TypeError, KeyError) as e:
            print(f"ERROR {rel}: no se pudo usar la J1 reconstruida ({e})", file=sys.stderr)
            failed = True
            continue
    # La clasificación FS J3 se actualizó con el PDF RFFM del 29/10,
    # posterior al PDF antiguo que sigue guardado en pdfs/.
    # Evitar que la publicación restaure aplazamientos ya resueltos.
    if is_fs and "Jornada 3" in first and "2026-2027" in first:
        curated_path = ROOT / "data/2026-2027/fs/j03.json"
        curated = json.loads(curated_path.read_text(encoding="utf-8"))
        if (curated.get("division"), curated.get("jornada"), curated.get("temporada")) != ("fs", 3, "2026-2027"):
            print(f"ERROR {rel}: identificación FS J3 incorrecta", file=sys.stderr)
            failed = True
            continue
        games = curated.get("partidos", [])
        if len(games) != 7 or any(p.get("estado") != "jugado" or p.get("goles_local") is None or p.get("goles_visitante") is None for p in games) or validate(curated):
            print(f"ERROR {rel}: clasificación FS J3 consolidada inválida", file=sys.stderr)
            failed = True
            continue
        print(f"OK {rel}: se conserva FS J3 consolidada (RFFM 29/10/2026)")
        continue
    try:
        d = parse_f11(pdf) if is_f11 else parse_fs(pdf) if is_fs else parse(pdf)
    except Exception as e:  # PDF ilegible, escaneado, etc.
        print(f"ERROR {rel}: no se pudo leer ({e})", file=sys.stderr); failed = True; continue
    # Corrección comprobada para la J2 de Primera: el Inter descansó.
    # Solo se aplica cuando el equipo está en la clasificación y no jugó partido.
    if (d.get("temporada"), d.get("division"), d.get("jornada")) == ("2026-2027", "1dvf7", 2):
        team_id = "el-inter-novella-garcia-old-rokers"
        candidates = [r for r in d["clasificacion"] if r["equipo_id"] == team_id]
        playing = any(team_id in (p["local_id"], p["visitante_id"]) for p in d["partidos"])
        if len(candidates) == 1 and not playing and not d.get("descansa"):
            d["descansa"] = candidates[0]["equipo"]
            d["descansa_id"] = team_id
            print(f"CORREGIDO {rel}: descansa {d['descansa']}")
        elif len(candidates) != 1 or playing or (d.get("descansa") and d["descansa_id"] != team_id):
            print(f"ERROR {rel}: no se puede verificar el descanso de J2 Primera", file=sys.stderr)
            failed = True
            continue
    try:
        d = apply_j3_updates(d)
    except ValueError as e:
        print(f'ERROR {rel}: {e}', file=sys.stderr)
        failed = True
        continue
    errs = validate(d)
    if not all(d.get(k) for k in ("temporada", "division", "jornada")):
        errs.append("No se encontró temporada, división o jornada en el encabezado")
    if errs:
        failed = True
        for e in errs: print(f"ERROR {rel}: {e}", file=sys.stderr)
        continue
    key = (d["temporada"], d["division"], d["jornada"])
    if key in seen:
        print(f"AVISO: {rel} repite {seen[key]} (jornada {d['jornada']}); se usa el último por orden alfabético")
    seen[key] = rel
    d["origen"] = rel
    target = ROOT / "data" / d["temporada"] / d["division"] / f"j{d['jornada']:02d}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK {rel} -> {target.relative_to(ROOT).as_posix()}")

sys.exit(1 if failed else 0)
