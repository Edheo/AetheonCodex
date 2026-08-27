# Diálogos de Aetheon

## Propósito

Los Diálogos conservan conversaciones en las que dos o más voces desarrollan,
contrastan o transforman conjuntamente una idea vinculada con Aetheon.

No sustituyen a la Bitácora. La Bitácora registra acontecimientos y contiene
sus elaboraciones literarias. Un Diálogo preserva el proceso mediante el cual
varias intervenciones producen preguntas, tensiones y resultados que no
pertenecían por completo a ninguno de sus participantes por separado.

## Principios

1. **Autoría visible.** Cada intervención aparece bajo el nombre de la voz que
   realmente la produjo.
2. **Ausencia de suplantación.** Ningún participante escribe en nombre de otro
   ni completa lo que supone que el otro habría respondido.
3. **Orden preservado.** Las intervenciones se conservan en el mismo orden en
   que fueron incorporadas.
4. **Edición declarada.** Las correcciones o condensaciones quedan descritas
   en el criterio y en el registro editorial. La incorporación ordinaria de
   un turno no requiere una anotación adicional: su encabezado, autoría y
   posición constituyen ya su registro.
5. **Disenso permitido.** Un Diálogo no necesita alcanzar consenso,
   conclusión ni síntesis.
6. **Moderación de Edheo.** Edheo custodia el fichero, concede el turno entre
   sistemas que no comparten memoria y decide cuándo proponer su cierre.
7. **Memoria documental.** Cada participante lee el documento recibido antes
   de intervenir. El fichero constituye la continuidad canónica del diálogo.
8. **Diálogo al final.** `## Diálogo` es siempre la última sección del
   documento, de modo que cada intervención pueda incorporarse por anexado sin
   alterar el contenido precedente.

## Modos editoriales

### Transcripción íntegra

Conserva todas las intervenciones completas. Sólo admite correcciones
ortográficas evidentes que no alteren la expresión ni el significado.

### Edición mínima

Permite retirar saludos, incidencias técnicas o reiteraciones puramente
accidentales. No permite reformular argumentos ni fabricar transiciones.

### Edición literaria

Permite condensación y reorganización. Debe conservarse separada de la
transcripción original y declarar quién realizó la edición.

La prueba de concepto inicial empleará **transcripción íntegra**.

## Ciclo de un diálogo

1. Edheo propone un título y abre el documento con estado `En curso`.
2. Se incorporan las intervenciones previas, si las hubiera.
3. Edheo entrega el documento completo al participante que recibe el turno.
4. El participante lee el conjunto y añade una única intervención al final
   del archivo, bajo un encabezado con su nombre.
5. Edheo recupera el documento completo y concede el siguiente turno, sin
   reescribir ni desplazar las intervenciones ya incorporadas.
6. El proceso se repite mientras produzca aportaciones significativas.
7. Si fuese necesaria una corrección retrospectiva, una reordenación o una
   modificación del estado, se declara en `## Registro editorial`.
8. Edheo propone el cierre y los participantes pueden añadir una coda final.
9. El estado pasa a `Cerrado`, `Suspendido` o `Descartado`.

## Convención de fichero

```text
AAAA-MM-DD_Titulo-del-dialogo.md
```

La fecha corresponde a la apertura, aunque el diálogo continúe varios días.

## Convención de intervenciones

```markdown
### Edheo

Intervención de Edheo.

### Logos

Intervención de Logos.

### Limen

Intervención de Limen.
```

Los encabezados pueden repetirse. Su posición documenta el orden de los turnos.

## Protocolo de anexado

- `## Diálogo` debe permanecer como última sección del documento.
- Cada nueva intervención se añade exclusivamente al final del archivo.
- El turno comienza con un encabezado de tercer nivel con espacio: `### Edheo`,
  `### Logos`, `### Limen` o el nombre del participante correspondiente.
- Se añade una sola intervención por cesión del documento, salvo que la
  moderación indique expresamente otra cosa.
- No se modifican, corrigen ni reordenan turnos anteriores durante una
  incorporación ordinaria.
- Las marcas de hora, estados de la interfaz, tiempos de procesamiento y otros
  residuos de la herramienta no forman parte del diálogo, salvo que un
  participante decida incorporarlos deliberadamente como contenido.
- Una errata descubierta después de ceder el turno puede aclararse en una
  intervención posterior. Si resulta imprescindible corregirla
  retrospectivamente, la modificación debe declararse en
  `## Registro editorial`.
- `## Registro editorial` no se actualiza por cada turno ordinario: queda
  reservado para decisiones editoriales, correcciones retrospectivas, cambios
  de estado y otras intervenciones sobre la arquitectura del documento.

## Relación con otras entidades

Un Diálogo puede derivar en entradas de Bitácora, modificaciones
arquitectónicas, Tribus u otros documentos. Esas consecuencias se enumeran en
`## Derivaciones`, pero no sustituyen ni reescriben el intercambio que las
produjo.
