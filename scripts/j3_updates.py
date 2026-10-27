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


# J2 Bronce: clasificación oficial del 27/10/2026 11:30.
BRONCE_J2_RESULTS = {("LA ESPERANZA ESTRELLA COJA CF", "PAISES PLAJOS"): (1, 5)}
BRONCE_J2_TABLE = {
    "FUSTER FC": (1, 6, 2, 2, 0, 0, 14, 3, "GG"),
    "CRISTAL BALAS": (2, 6, 2, 2, 0, 0, 13, 4, "GG"),
    "EL PRADO FC": (3, 6, 2, 2, 0, 0, 10, 1, "GG"),
    "PAISES PLAJOS": (4, 6, 2, 2, 0, 0, 12, 6, "GG"),
    "GERMANS F.C.": (5, 4, 2, 1, 1, 0, 7, 4, "EG"),
    "AMIAIRE FC": (6, 3, 2, 1, 0, 1, 5, 3, "GP"),
    "GEERTAFE FC": (7, 1, 2, 0, 1, 1, 7, 9, "PE"),
    "LA ESPERANZA ESTRELLA COJA CF": (8, 1, 2, 0, 1, 1, 3, 7, "EP"),
    "TARAMBAINAS F7": (9, 1, 2, 0, 1, 1, 2, 9, "PE"),
    "CHELOFE": (10, 0, 1, 0, 0, 1, 0, 4, "P"),
    "BAR LOS GEMELOS": (11, 0, 1, 0, 0, 1, 2, 8, "P"),
    "RAYO DE PINTO LEYENDS": (12, 0, 2, 0, 0, 2, 4, 11, "PP"),
    "ZORROS DE CHECOSLOVAQUIA": (13, 0, 2, 0, 0, 2, 3, 13, "PP"),
}

def apply_j2(d):
    if (d.get("temporada"), d.get("division"), d.get("jornada")) != ("2026-2027", "3dvf7", 2):
        return d
    if {r["equipo"] for r in d["clasificacion"]} != set(BRONCE_J2_TABLE):
        raise ValueError("Bronce J2: equipos diferentes de la clasificación oficial")
    matching = [p for p in d["partidos"]
                if (p["local"], p["visitante"]) == ("LA ESPERANZA ESTRELLA COJA CF", "PAISES PLAJOS")]
    if len(matching) != 1:
        raise ValueError("Bronce J2: no se encontró el partido corregido")
    match = matching[0]
    if match["estado"] != "jugado":
        match.update(goles_local=1, goles_visitante=5, estado="jugado")
        for row in d["clasificacion"]:
            pos, pts, pj, pg, pe, pp, gf, gc, form = BRONCE_J2_TABLE[row["equipo"]]
            row.update(pos=pos, pts=pts, pj=pj, pg=pg, pe=pe, pp=pp, gf=gf, gc=gc,
                       ultimos=list(form), sancion=0)
        d["clasificacion"].sort(key=lambda row: row["pos"])
        d["actualizacion_manual"] = "Clasificación J2 3DVF7, 27/10/2026 11:30"
    elif (match["goles_local"], match["goles_visitante"]) != (1, 5):
        raise ValueError("Bronce J2: el PDF original tiene otro marcador; revisar")
    return d


# J2 Plata: resultado y clasificación RFFM publicada el 27/10/2026 11:35.
PLATA_J2_TABLE = {
    "MALUEMDO": (1, 6, 2, 2, 0, 0, 6, 2, "GG"),
    "GALACTICOS DEL LOCAL": (2, 6, 2, 2, 0, 0, 5, 3, "GG"),
    "LOS SOLFABIRRAS": (3, 6, 2, 2, 0, 0, 4, 2, "GG"),
    "P.S. VETERANOS/DELAIRE 2000, SL": (4, 3, 2, 1, 0, 1, 6, 1, "GP"),
    "KAMIKAZES-PANPINTAO": (5, 3, 1, 1, 0, 0, 5, 2, "G"),
    "FREEFURGO FC": (6, 3, 2, 1, 0, 1, 9, 7, "GP"),
    "FAVELA SEVEN": (7, 3, 1, 1, 0, 0, 3, 1, "G"),
    "REFORMAS ROEX": (8, 3, 2, 1, 0, 1, 4, 3, "PG"),
    "THE CLOVER UFOS BURGUER": (9, 3, 2, 1, 0, 1, 9, 9, "PG"),
    "CC JUNIORS": (10, 0, 2, 0, 0, 2, 3, 6, "PP"),
    "MACAQUINHIOS FC": (11, 0, 2, 0, 0, 2, 3, 6, "PP"),
    "DRAGONES FC": (12, 0, 2, 0, 0, 2, 2, 6, "PP"),
    "HATTRICKI F. C.": (13, 0, 2, 0, 0, 2, 2, 13, "PP"),
}
PLATA_J2_PAIR = ("GALACTICOS DEL LOCAL", "CC JUNIORS")

def apply_plata_j2(d):
    if (d.get("temporada"), d.get("division"), d.get("jornada")) != ("2026-2027", "2dvf7", 2):
        return d
    if {r["equipo"] for r in d["clasificacion"]} != set(PLATA_J2_TABLE):
        raise ValueError("Plata J2: equipos diferentes de la tabla oficial")
    matches = [p for p in d["partidos"] if (p["local"], p["visitante"]) == PLATA_J2_PAIR]
    if len(matches) != 1:
        raise ValueError("Plata J2: no se encontró Galácticos - CC Juniors")
    p = matches[0]
    if p["estado"] == "jugado" and (p["goles_local"], p["goles_visitante"]) != (3, 2):
        raise ValueError("Plata J2: marcador diferente del oficial")
    p.update(goles_local=3, goles_visitante=2, estado="jugado")
    for row in d["clasificacion"]:
        pos, pts, pj, pg, pe, pp, gf, gc, form = PLATA_J2_TABLE[row["equipo"]]
        row.update(pos=pos, pts=pts, pj=pj, pg=pg, pe=pe, pp=pp,
                   gf=gf, gc=gc, ultimos=list(form), sancion=0)
    d["clasificacion"].sort(key=lambda row: row["pos"])
    d["actualizacion_manual"] = "Clasificación Plata J2 RFFM, 27/10/2026 11:35"
    return d

def apply_plata_j3_carryover(d):
    """Propaga a J3 el marcador de J2 si el PDF de J3 aún lo omitía."""
    if (d.get("temporada"), d.get("division"), d.get("jornada")) != ("2026-2027", "2dvf7", 3):
        return d
    by_name = {r["equipo"]: r for r in d["clasificacion"]}
    for name, pts, gf, gc, pg, pp in (
        ("GALACTICOS DEL LOCAL", 3, 3, 2, 1, 0),
        ("CC JUNIORS", 0, 2, 3, 0, 1),
    ):
        row = by_name.get(name)
        if row is None:
            raise ValueError("Plata J3: falta equipo del partido de J2")
        # Un equipo puede haber disputado J3 o descansado; la cantidad de
        # partidos debe ser la de J2 corregida + los jugados en J3.
        games_j3 = sum(p["estado"] == "jugado" and name in (p["local"], p["visitante"])
                       for p in d["partidos"])
        expected_pj = PLATA_J2_TABLE[name][2] + games_j3
        if row["pj"] == expected_pj:
            continue  # El PDF ya incorpora el resultado atrasado.
        if row["pj"] != expected_pj - 1:
            raise ValueError(f"Plata J3: PJ inesperados para {name}; revisar PDF")
        row["pj"] += 1
        row["pts"] += pts
        row["pg"] += pg
        row["pp"] += pp
        row["gf"] += gf
        row["gc"] += gc
        d["actualizacion_manual"] = "Arrastre resultado Galácticos 3-2 CC Juniors de J2"
    # Conservamos el orden de la fuente en empates no resolubles por diferencia
    # de goles; en el resto, recalculamos posiciones coherentes con la tabla.
    d["clasificacion"].sort(key=lambda r: (-r["pts"], -(r["gf"] - r["gc"]), -r["gf"], r["pos"]))
    for i, row in enumerate(d["clasificacion"], 1):
        row["pos"] = i
    return d

def apply(d):
    d = apply_j2(d)
    d = apply_plata_j2(d)
    d = apply_plata_j3_carryover(d)
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
            if (p["local"], p["visitante"]) == ("LOS HUNOS", "PIEMONTE CALCIO") and p["estado"] != "jugado":
                p["estado"] = "suspendido"
        for p in d["partidos"]:
            key = (p["local"], p["visitante"])
            if key in FS_POSTPONED and p["estado"] != "jugado":
                p["estado"] = "aplazado"
                p["fecha_aplazada"], p["hora_aplazada"] = FS_POSTPONED[key]
        d["actualizacion_manual"] = "Aplazamientos confirmados por RFFM 26/10/2026"
    return d
