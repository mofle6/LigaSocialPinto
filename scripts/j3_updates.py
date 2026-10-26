"""Correcciones de J3 documentadas el 26/10/2026.

Bronce: clasificación oficial actualizada (26/10/2026 16:30), aportada por
el usuario como Clasificacion_j3_3df7.pdf. Mientras se sustituye el PDF
anterior del repositorio, aplicar solo si ambos resultados siguen pendientes.
Oro: el encuentro sin resultado está suspendido, según confirmación del usuario.
Futsal: dos partidos aplazados al 28/10/2026 según captura de RFFM.
"""
from parse_jornada import slug

BRONCE_RESULTS = {
    ("TARAMBAINAS F7", "LA ESPERANZA ESTRELLA COJA CF"): (4, 5),
    ("PAISES PLAJOS", "RAYO DE PINTO LEYENDS"): (5, 1),
}

# pos, pts, pj, pg, pe, pp, gf, gc, últimos (de la clasificación oficial)
BRONCE_TABLE = {
    "EL PRADO FC": (1, 9, 3, 3, 0, 0, 21, 1, "GGG"),
    "FUSTER FC": (2, 9, 3, 3, 0, 0, 20, 5, "GGG"),
    "PAISES PLAJOS": (3, 9, 3, 3, 0, 0, 17, 7, "GGG"),
    "CRISTAL BALAS": (4, 6, 2, 2, 0, 0, 13, 4, "GG"),
    "GEERTAFE FC": (5, 4, 3, 1, 1, 1, 10, 10, "PEG"),
    "GERMANS F.C.": (6, 4, 3, 1, 1, 1, 10, 10, "EGP"),
    "LA ESPERANZA ESTRELLA COJA CF": (7, 4, 3, 1, 1, 1, 8, 11, "EPG"),
    "AMIAIRE FC": (8, 3, 3, 1, 0, 2, 6, 6, "GPP"),
    "ZORROS DE CHECOSLOVAQUIA": (9, 3, 3, 1, 0, 2, 9, 16, "PPG"),
    "TARAMBAINAS F7": (10, 1, 3, 0, 1, 2, 6, 14, "PEP"),
    "BAR LOS GEMELOS": (11, 0, 2, 0, 0, 2, 4, 14, "PP"),
    "RAYO DE PINTO LEYENDS": (12, 0, 3, 0, 0, 3, 5, 16, "PPP"),
    "CHELOFE": (13, 0, 2, 0, 0, 2, 0, 15, "PP"),
}

FS_POSTPONED = {
    ("TUPA FC", "CASA PALMI FC"): ("2026-10-28", "20:30"),
    ("EL QUIOSCO DEL BETIS", "BAR LA OSTRA 93"): ("2026-10-28", "21:30"),
}

def apply(d):
    if (d.get("temporada"), d.get("jornada")) != ("2026-2027", 3):
        return d

    if d["division"] == "3dvf7":
        by_pair = {(p["local"], p["visitante"]): p for p in d["partidos"]}
        # Solo se necesita el parche cuando la fuente del repositorio sigue
        # siendo la clasificación incompleta. No alterar futuras revisiones.
        pending = [pair for pair in BRONCE_RESULTS
                   if pair in by_pair and by_pair[pair]["estado"] != "jugado"]
        if pending:
            if set(by_pair) != set(BRONCE_RESULTS) | {
                ("CHELOFE", "EL PRADO FC"),
                ("AMIAIRE FC", "GEERTAFE FC"),
                ("GERMANS F.C.", "ZORROS DE CHECOSLOVAQUIA"),
                ("FUSTER FC", "BAR LOS GEMELOS"),
            }:
                raise ValueError("Bronce J3: partidos distintos del PDF oficial; revisar parche")
            for pair in pending:
                p = by_pair[pair]
                p["goles_local"], p["goles_visitante"] = BRONCE_RESULTS[pair]
                p["estado"] = "jugado"
            if {r["equipo"] for r in d["clasificacion"]} != set(BRONCE_TABLE):
                raise ValueError("Bronce J3: equipos distintos del PDF oficial")
            for r in d["clasificacion"]:
                pos, pts, pj, pg, pe, pp, gf, gc, form = BRONCE_TABLE[r["equipo"]]
                r.update(pos=pos, pts=pts, pj=pj, pg=pg, pe=pe, pp=pp,
                         gf=gf, gc=gc, ultimos=list(form), sancion=0)
            d["clasificacion"].sort(key=lambda r: r["pos"])
            d["actualizacion_manual"] = "Clasificacion_j3_3df7.pdf (26/10/2026 16:30)"
    elif d["division"] == "1dvf7":
        pending = [p for p in d["partidos"] if p["estado"] == "sin_resultado"]
        if len(pending) == 1:
            pending[0]["estado"] = "suspendido"
            d["actualizacion_manual"] = "Suspensión confirmada 26/10/2026"
    elif d["division"] == "fs":
        for p in d["partidos"]:
            key = (p["local"], p["visitante"])
            if key in FS_POSTPONED and p["estado"] != "jugado":
                p["estado"] = "aplazado"
                p["fecha_aplazada"], p["hora_aplazada"] = FS_POSTPONED[key]
        d["actualizacion_manual"] = "Aplazamientos confirmados por RFFM 26/10/2026"
    return d
