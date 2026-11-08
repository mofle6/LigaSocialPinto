# Liga Social Pinto — actualización con PDFs

Sube los documentos a **`pdfs/2026-2027/`**. GitHub Actions valida el lote,
genera los resultados y horarios y publica la web al subirlos a `main`.
Para revisarlos antes, súbelos a una rama y abre una PR: se genera una vista
previa descargable y no se publica hasta fusionar.

## Nombres exactos

`TIPO_DIVISION_JNN_AAAAMMDD.pdf`

La jornada lleva dos cifras. La fecha es la de **publicación de esa versión**
del documento, no la del partido. La temporada del directorio y la división y
jornada del nombre deben coincidir con el encabezado oficial del PDF.

| División | Clasificación y resultados J4 | Horarios J5 |
|---|---|---|
| Primera F7 · Oro | `CLASIFICACION_1DVF7_J04_20261108.pdf` | `HORARIOS_1DVF7_J05_20261108.pdf` |
| Segunda F7 · Plata | `CLASIFICACION_2DVF7_J04_20261108.pdf` | `HORARIOS_2DVF7_J05_20261108.pdf` |
| Tercera F7 · Bronce | `CLASIFICACION_3DVF7_J04_20261108.pdf` | `HORARIOS_3DVF7_J05_20261108.pdf` |
| Cuarta F7 · Zinc | `CLASIFICACION_4DVF7_J04_20261108.pdf` | `HORARIOS_4DVF7_J05_20261108.pdf` |
| Fútbol 11 | `CLASIFICACION_F11_J04_20261108.pdf` | `HORARIOS_F11_J05_20261108.pdf` |
| Fútbol Sala | `CLASIFICACION_FS_J04_20261108.pdf` | `HORARIOS_FS_J05_20261108.pdf` |

Por ejemplo, para Sala J5 y próximos partidos J6:
`CLASIFICACION_FS_J05_20261108.pdf` y `HORARIOS_FS_J06_20261108.pdf`.
Los PDF llamados `Jornada5_f11.pdf` deben renombrarse como horarios antes de subirlos.

## Correcciones, aplazados y suspendidos

Conserva las versiones anteriores y **añade** una versión con fecha posterior:
`CLASIFICACION_FS_J03_20261115.pdf`.
Si hay dos versiones publicadas el mismo día, añade `_V2` al final:
`CLASIFICACION_FS_J03_20261115_V2.pdf`.
No reemplaces ni borres el archivo versionado anterior: CI lo rechaza para
impedir que reaparezca una versión antigua. También protege los PDFs históricos
con nombres antiguos mediante huellas SHA-256.

Se utiliza la mayor fecha y, después, el mayor número de versión. Duplicados
idénticos de la misma revisión se aceptan; dos contenidos distintos con la misma
fecha/revisión se rechazan. Una versión inválida bloquea el lote; no se recurre
silenciosamente a una antigua. El informe incluye origen y SHA-256.

Los partidos sin resultado conservan goles vacíos y su estado; no cuentan como
0–0. No se permite devolver un partido jugado a pendiente ni cambiar los
emparejamientos existentes automáticamente. Un PDF escaneado, incompleto o con
un formato de horarios no reconocido bloquea la publicación y requiere revisión.

**Una corrección de J3 no puede sustituir la clasificación vigente de J5.**
Si cambia resultados o estadísticas, sube en el mismo lote las clasificaciones
oficiales actualizadas de todas las jornadas posteriores que ya existan en la web
(por ejemplo J4 y J5), con fecha/revisión igual o posterior a la corrección.
El error indica la jornada que falta. Los totales se contrastan con los resultados
conocidos. No se reconstruyen puestos, desempates o sanciones por suposición:
se conservan las tablas oficiales. Si solo tienes el PDF antiguo corregido, la
actualización queda bloqueada hasta aportar las tablas posteriores actualizadas.

Los horarios se guardan aparte; no cambian resultados ni clasificaciones. Se
valida que estén todos los equipos una sola vez (incluido el descanso), las fechas,
las horas y los campos. La web muestra la primera jornada programada posterior a
la última clasificación disponible. Los PDF actuales deben contener la programación
completa; un aplazamiento sin horario que el lector no pueda interpretar requiere revisión.

## Qué hacer si falla

Abre **Actions → Actualizar Liga Social Pinto** y consulta el paso de importación.
Corrige el nombre, sube la versión o clasificación que indica el error, y vuelve
a intentarlo. Toda la validación ocurre en una copia temporal antes de escribir:
un PDF inválido no deja una actualización parcial por validación. GitHub Pages solo
recibe la web cuando termina la generación; ante un fallo mantiene la publicación anterior.
La escritura local usa reemplazo atómico por archivo; un fallo de disco durante
la escritura puede requerir repetir la importación.

Los JSON generados no se guardan automáticamente en la rama: se reconstruyen en
cada publicación desde los JSON históricos y los PDF versionados conservados.
Puedes descargar el informe y `data/` en el artefacto **pdf-import** de Actions;
en una PR, **pdf-preview** incluye también la web. No edites estos JSON a mano
para corregir un PDF versionado: aporta una revisión nueva del documento.

## Desarrollo y comprobaciones

```sh
pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/import_pdfs.py --check
python scripts/import_pdfs.py
python scripts/build_site.py
python scripts/check_fs_site.py
python scripts/check_f11_site.py
```

`--check` valida todo sin escribir datos. `--base-ref SHA` añade la comprobación
de inmutabilidad de versiones frente al commit anterior; CI lo usa en PR y push.
`ingest.py` e `ingest_horarios.py` se mantienen como accesos compatibles al mismo
importador conjunto. Los JSON históricos ausentes se han materializado desde los
lectores anteriores; los JSON ya existentes se han conservado byte por byte.
`data/pdf-legacy.json` registra los PDF históricos que no se vuelven a importar.
Las correcciones antiguas de `j3_updates.py` quedan como referencia y no se aplican
a los documentos nuevos. La cantidad de equipos se configura en `COUNTS` del importador;
una temporada con estructura distinta requiere actualizar esa configuración.
