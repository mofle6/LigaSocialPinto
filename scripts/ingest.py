#!/usr/bin/env python3
"""Lee todos los PDF de pdfs/ y escribe data/<temporada>/<division>/jNN.json.

La temporada, la división y la jornada se leen del propio PDF, así que da igual
cómo se llame el archivo o en qué subcarpeta de pdfs/ lo pongas.
Si un PDF falla la validación, se avisa y el proceso termina con error (no se publica).
"""
import json, sys
from pathlib import Path
from parse_jornada import parse, validate

ROOT = Path(__file__).resolve().parent.parent
failed, seen = False, {}

for pdf in sorted((ROOT / "pdfs").rglob("*.pdf")):
    rel = pdf.relative_to(ROOT).as_posix()
    try:
        d = parse(pdf)
    except Exception as e:  # PDF ilegible, escaneado, etc.
        print(f"ERROR {rel}: no se pudo leer ({e})", file=sys.stderr); failed = True; continue
    errs = validate(d)
    # Permitir solo la J1 reconstruida explícitamente, sin relajar futuras jornadas.
    if errs and pdf.name == "J1 2DF7 CLASIFICACIÓN.pdf":
        fallback = ROOT / "data" / "2026-2027" / "2dvf7" / "j01.json"
        if fallback.exists():
            try:
                curated = json.loads(fallback.read_text(encoding="utf-8"))
                key_ok = (curated.get("temporada"), curated.get("division"), curated.get("jornada")) == ("2026-2027", "2dvf7", 1)
                if key_ok and curated.get("reconstruida_manualmente") is True and not validate(curated) and len(curated.get("partidos", [])) == 6:
                    print(f"OK {rel}: se conserva J1 reconstruida y validada")
                    continue
            except (OSError, ValueError, TypeError) as e:
                print(f"ERROR {rel}: fallo al verificar J1 ({e})", file=sys.stderr)
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
