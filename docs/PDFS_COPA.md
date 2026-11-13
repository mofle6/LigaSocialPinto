# Subir horarios de Copa F7

Los PDFs de Copa se guardan separados de los de Liga. Desde la raíz de GitHub, abre:

`pdfs-copa/2026-2027/horarios/`

Sube el documento completo de cada ronda. Se publicará automáticamente tras superar las comprobaciones de GitHub Actions.

| Ronda | Ejemplo de nombre |
| --- | --- |
| Previa | `HORARIOS_COPAF7_RONDAPREVIA_20261113.pdf` |
| Dieciseisavos | `HORARIOS_COPAF7_DIECISEISAVOS_20270201.pdf` |
| Octavos | `HORARIOS_COPAF7_OCTAVOS_20270510.pdf` |
| Cuartos | `HORARIOS_COPAF7_CUARTOS_20270510.pdf` |
| Semifinales | `HORARIOS_COPAF7_SEMIFINALES_20270614.pdf` |
| Final | `HORARIOS_COPAF7_FINAL_20270614.pdf` |

Las fechas futuras son ejemplos. Usa la fecha real de publicación o revisión del documento, no la del partido ni la de subida. Si hay dos revisiones el mismo día, añade `_v02`, `_v03`… antes de `.pdf`. Sin sufijo equivale a `_v01`.

Ejemplo corregido: `HORARIOS_COPAF7_RONDAPREVIA_20261113_v02.pdf`. Conserva las versiones anteriores: se selecciona la fecha más reciente y después la revisión más alta. Si un documento cambia de contenido, utiliza una revisión nueva.

La actualización solo modifica fecha, hora y campo de la ronda correspondiente. Conserva los resultados de Copa y no toca clasificaciones, resultados ni estadísticas de Liga. Ante equipos desconocidos o repetidos, cambio de cruces, documento incompleto o versiones en conflicto, se detiene la publicación y la web anterior sigue disponible.

La carpeta `pdfs-copa/2026-2027/resultados/` queda reservada. Nombre previsto: `RESULTADOS_COPAF7_RONDAPREVIA_AAAAMMDD.pdf`. La importación de resultados todavía no está habilitada: hace falta validar el formato del primer PDF real. No basta con subirlo para publicar marcadores.

## Liga y Copa

Los documentos de Liga siguen en `pdfs/2026-2027/` con sus nombres actuales `CLASIFICACION_DIVISION_JNN_AAAAMMDD.pdf` y `HORARIOS_DIVISION_JNN_AAAAMMDD.pdf`. No cambies su ubicación.

La ficha de cada equipo permite alternar entre Liga y Copa. La simulación está identificada como ficticia y se guarda solo en el navegador; no publica resultados, no modifica los PDFs y no se suma a las estadísticas oficiales.
