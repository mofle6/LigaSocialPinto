# Liga de Fútbol 7 — resultados y clasificaciones

Web estática generada a partir de los PDF de cada jornada. Se publica sola en GitHub Pages.

## Poner en marcha (una vez)
1. Crea un repositorio en GitHub y sube todo este contenido a la rama `main`.
2. En **Settings → Pages**, en *Source* elige **GitHub Actions**.
3. Listo: cada vez que subas un PDF a `pdfs/` se actualiza la web.

## Cada jornada
Sube el PDF a `pdfs/` (da igual el nombre o la subcarpeta; la división, temporada y jornada se leen del propio PDF).
La Action lo lee, valida que los números cuadran, guarda los datos en `data/` y publica.
Si algo no cuadra, la Action falla y la web anterior sigue publicada (mira el error en la pestaña *Actions*).
Para corregir una jornada, sustituye el PDF por el nuevo con el mismo nombre.

## Estructura
- `pdfs/` PDFs originales.
- `data/<temporada>/<division>/jNN.json` datos extraídos (resultados + clasificación oficial de cada jornada).
- `data/alias.json` une nombres de equipo que cambian entre PDFs: `{"NOMBRE EN EL PDF": "id-del-equipo"}`.
- `data/<temporada>/<division>/equipos/<id>.json` (opcional) datos extra de un equipo, p. ej.
  `{"jugadores": [{"nombre": "Ana", "dorsal": 9, "goles": 3}]}` y aparece en su página.
- `scripts/` extracción (`parse_jornada.py`, `ingest.py`) y generador de la web (`build_site.py`).
- `templates/` plantillas HTML.

## Probar en local
```
pip install -r requirements.txt
python scripts/ingest.py && python scripts/build_site.py
python -m http.server -d site
```
