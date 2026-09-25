## Propósito
El Libro de Aetheon es una representación literaria derivada de la Bitácora.
Su contenido no se mantiene directamente en esta sección. 
Se construye durante el proceso de build a partir de las secciones Literaria de las entradas de la Bitácora, ordenadas mediante sus atributos Capítulo y Secuencia.

## LÍNEA EDITORIAL
En governance se haya el archivo LINEA-EDITORIAL.md donde se detallan los objetivos definidos para los capítulos, habrá que ir completando sus scopes, a medida que surjan los capítulos.

## Primera incorporación al Codex

Las bitácoras pueden incluir, junto a la autoría, el campo `### Primera incorporación al Codex`, con una fecha ISO (`AAAA-MM-DD`). El Libro muestra esta fecha sin repetir ni sustituir la fecha del acontecimiento. No acredita la fecha exacta de escritura ni se actualiza al revisar o reclasificar la entrada.

El build completa automáticamente las fechas ausentes antes de sincronizar el Codex con la publicación. Si creas una bitácora copiando otra, elimina toda la sección `Primera incorporación al Codex`, incluido su comentario de procedencia. Antes de su primer commit permanecerá sin fecha; el primer build posterior la incorporará. Las fechas ya presentes nunca se recalculan. Este paso modifica las fuentes del Codex y no crea commits. La ejecución directa de `book.py` solo muestra los datos existentes.

Para revisar o recuperar fechas manualmente: `python scripts/journal_dates.py` muestra la propuesta; `python scripts/journal_dates.py --apply` la incorpora. Se consulta la primera adición conservada en Git siguiendo renombrados detectados por similitud, usando la fecha del committer en su zona original. Un comentario oculto conserva el commit de referencia. Las fechas existentes se respetan; un archivo sin historial queda sin fecha y un repositorio superficial se rechaza. Un renombrado acompañado de una reescritura extensa puede requerir contraste manual. Después se regenera el Codex con el proceso habitual.
