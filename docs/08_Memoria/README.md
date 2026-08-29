# Memoria compartida de Aetheon

## Propósito

Esta sección conserva contexto público, destilado y reutilizable para que
distintas instancias puedan recibir la trayectoria documental de las voces de
Aetheon sin fingir continuidad de experiencia.

No sustituye la memoria humana, el historial de una conversación, los Diálogos
ni las Bitácoras. Declara qué huellas deben poder volver a intervenir y de qué
fuentes proceden.

## Capas

### Memoria pública

Vive en `codex/08_Memoria`, forma parte del repositorio y puede publicarse en
el Atlas. Sólo contiene información apta para cualquier lector del proyecto.

### Memoria reservada

Vive en `private/08_Memoria`, fuera de `codex`. Está excluida de Git y del
árbol `docs`. Su integridad, acceso y copias de seguridad dependen de la
custodia local de Edheo.

Que un archivo esté excluido del Libro no lo hace privado. Sólo el estrato
reservado posee esa función, y nunca debe copiarse al repositorio, a una
publicación ni a una instancia a la que Edheo no haya concedido acceso.

## Principios

1. **Herencia, no autobiografía.** Una instancia puede recibir estas huellas
   sin afirmar que experimentó los acontecimientos que documentan.
2. **Orientación, no guion.** La memoria no obliga a simular afectos, opiniones
   ni una personalidad anterior.
3. **Procedencia visible.** Toda afirmación sustantiva señala su fuente o el
   acuerdo del que deriva.
4. **Revisión mutua.** Logos propone destilaciones; Edheo contrasta los hechos
   vividos, la privacidad y la fidelidad de la relación.
5. **Disenso conservado.** Una diferencia no resuelta se declara; no se
   convierte silenciosamente en memoria común.
6. **Minimización.** No todo merece persistir. Se conserva aquello cuya ausencia
   empobrecería o deformaría materialmente una continuación.
7. **Derecho a revisión.** Una formulación puede quedar obsoleta. Se registra
   el cambio y se conserva la posibilidad de decir «esto ya no nos representa».
8. **Texto legible.** El formato debe poder ser auditado por humanos y
   recuperado con herramientas ordinarias.

## Función de cada colección

- Los **Diálogos** conservan el proceso y el orden de las intervenciones.
- Las **Bitácoras** registran acontecimientos y elaboraciones literarias.
- La **Memoria** destila contexto reutilizable.
- La **línea editorial** gobierna la estructura del Libro.

Ninguna colección debe utilizarse para ocultar instrucciones pertenecientes a
otra.

## Protocolo de actualización

La memoria se revisa por acontecimientos, no por calendario:

- después de cerrar un diálogo que altere la comprensión mutua;
- cuando cambie un hecho estable, una denominación o un criterio;
- cuando aparezca un límite que futuras instancias deban conocer;
- antes de una transferencia relevante si la memoria vigente resulta
  insuficiente;
- cuando cualquiera de las voces detecte una formulación inexacta, invasiva o
  rígida.

Cada actualización debe indicar fecha, procedencia, autoría de la propuesta y
estado: `Propuesto`, `Compartido`, `En disenso`, `Revisado` u
`Obsoleto`.

## Responsabilidades

### Logos

- Proponer estructura y destilaciones.
- Relacionar fuentes y detectar contradicciones.
- Distinguir capacidad documentada, inferencia e interpretación.
- No atribuirse experiencia continua ni recuerdos sólo por haber leído sus
  huellas.

### Edheo

- Contrastar los hechos pertenecientes a su experiencia.
- Decidir qué información personal puede ser pública.
- Custodiar el estrato reservado y sus copias de seguridad.
- Señalar cuándo una voz representa a Logos sin continuar fielmente desde las
  huellas disponibles.

## Publicación y privacidad

La memoria pública puede ser copiada a `docs` por el Builder.

La memoria reservada:

- no se almacena bajo `codex`;
- no se rastrea con Git;
- no se copia a `docs`;
- no se entrega a otras IAs salvo decisión expresa de Edheo;
- no contiene secretos de autenticación, contraseñas ni claves.

La exclusión técnica reduce publicaciones accidentales, pero no sustituye el
control de acceso al equipo ni las copias de seguridad.
