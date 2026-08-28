"""
Aetheon Book Tools

Herramientas editoriales para reorganizar la estructura
literaria almacenada en las entradas de Bitácora.

Estas herramientas MODIFICAN la fuente canónica.

Fuentes:
    codex/04_Bitacora/*.md

Principios:
- La Bitácora es la fuente de verdad.
- Las herramientas sólo se ejecutan manualmente.
- Nunca forman parte de build.py.
- Los cambios pendientes en Git se advierten, pero no bloquean la operación.
- Los archivos objetivo no pueden cambiar entre el plan y la escritura.
- Primero se valida toda la operación.
- Si existe cualquier ambigüedad, no se modifica nada.
- Las entradas sin Capítulo o Secuencia quedan intactas.
- Las herramientas no toman decisiones editoriales.

Operaciones:

    renumber-sequences
        Renumera las secuencias dentro de cada capítulo
        utilizando incrementos de 10.

    renumber-chapters
        Renumera los capítulos conservando su orden actual.
        El incremento puede configurarse mediante --step.

    replace-chapter
        Sustituye una definición completa de capítulo
        por otra en todas las entradas afectadas.
"""

from pathlib import Path
import argparse
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent

BITACORA_DIR = (
    ROOT
    / "codex"
    / "04_Bitacora"
)

SEQUENCE_STEP = 10


# ============================================================
# Utilidades generales
# ============================================================


def fail(message):
    print()
    print(f"[ERROR] {message}")
    print()
    sys.exit(1)


def read_text(path):
    """
    Lee un archivo Markdown en UTF-8.
    """

    try:
        return path.read_text(
            encoding="utf-8"
        )

    except OSError as exc:
        fail(
            f"Unable to read {path}\n"
            f"        {exc}"
        )


def write_text(path, content):
    """
    Escribe un archivo Markdown en UTF-8.
    """

    try:
        path.write_text(
            content,
            encoding="utf-8",
        )

    except OSError as exc:
        fail(
            f"Unable to write {path}\n"
            f"        {exc}"
        )


def get_changed_git_paths():
    """Devuelve rutas con cambios, incluidas las no rastreadas."""

    commands = [
        ["git", "diff", "--name-only", "-z"],
        ["git", "diff", "--cached", "--name-only", "-z"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
    ]
    changed = set()

    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
        )

        if result.returncode != 0:
            fail("Unable to determine Git status.")

        for raw_path in result.stdout.split(b"\0"):
            if not raw_path:
                continue
            relative = raw_path.decode(
                "utf-8",
                errors="surrogateescape",
            )
            changed.add((ROOT / relative).resolve())

    return changed


def display_path(path):
    """Muestra rutas del repositorio de forma relativa cuando sea posible."""

    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def warn_about_git_changes(target_paths):
    """Informa de cambios pendientes y devuelve los objetivos solapados."""

    changed = get_changed_git_paths()

    if not changed:
        return set()

    targets = {path.resolve() for path in target_paths}
    overlap = changed & targets
    unrelated = changed - targets

    print()
    print("[WARNING] Git contains pending changes.")

    if overlap:
        print()
        print("Target files already modified before renumbering:")
        for path in sorted(overlap, key=str):
            print(f"    {display_path(path)}")

    if unrelated:
        print()
        print(
            f"There are also {len(unrelated)} pending change(s) "
            "outside the target files."
        )

    print()
    print("Pending changes do not block this operation.")

    return overlap


def confirm_changes(target_paths):
    """Solicita confirmación, reforzada si un objetivo ya estaba modificado."""

    overlap = warn_about_git_changes(target_paths)
    print()

    if overlap:
        confirmation = input(
            "Type APPLY to update the already modified target files: "
        ).strip()
        return confirmation == "APPLY"

    confirmation = input(
        "Apply these changes? [y/N] "
    ).strip().lower()
    return confirmation == "y"


def ensure_sources_unchanged(originals):
    """Evita sobrescribir cambios ocurridos después de calcular el plan."""

    changed_during_operation = [
        path
        for path, original in originals.items()
        if read_text(path) != original
    ]

    if changed_during_operation:
        details = "\n".join(
            f"        {display_path(path)}"
            for path in changed_during_operation
        )
        fail(
            "Target files changed after the plan was calculated. "
            "No files were written.\n"
            f"{details}"
        )


def originals_from_prepared(prepared, entries):
    """Relaciona cada documento preparado con la instantánea que lo originó."""

    target_paths = {path for path, _ in prepared}
    return {
        entry["path"]: entry["text"]
        for entry in entries
        if entry["path"] in target_paths
    }


def write_prepared_changes(prepared, originals):
    """Valida las instantáneas y escribe una operación ya preparada."""

    ensure_sources_unchanged(originals)

    for path, content in prepared:
        write_text(path, content)

    return len(prepared)


# ============================================================
# Parsing literario
# ============================================================


def extract_literary_section(text):
    """
    Obtiene el bloque ## Literaria hasta
    el siguiente encabezado de nivel 2
    o hasta EOF.

    Devuelve también las posiciones del
    bloque dentro del documento completo.
    """

    match = re.search(
        r"^## Literaria[ \t]*$"
        r"(.*?)"
        r"(?=^##\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )

    if not match:
        return None

    return {
        "content": match.group(1),
        "start": match.start(1),
        "end": match.end(1),
    }


def extract_field(section, field):
    """
    Extrae un campo literario.

    Soporta formato inline:

        **Capítulo:** 03 - Evolución
        **Secuencia:** 020

    y formato mediante encabezado:

        ### Capítulo
        03 - Evolución

        ### Secuencia
        020
    """

    inline_pattern = (
        rf"^\*\*{re.escape(field)}:\*\*"
        rf"[ \t]*(.*?)[ \t]*$"
    )

    match = re.search(
        inline_pattern,
        section,
        re.MULTILINE,
    )

    if match:

        value = (
            match.group(1)
            .strip()
        )

        if value:
            return value

        return None

    heading_pattern = (
        rf"^### {re.escape(field)}[ \t]*$"
        rf"\n"
        rf"[ \t]*(.*?)[ \t]*$"
    )

    match = re.search(
        heading_pattern,
        section,
        re.MULTILINE,
    )

    if match:

        value = (
            match.group(1)
            .strip()
        )

        if value:
            return value

    return None


def parse_chapter(value):
    """
    Interpreta valores como:

        03 Evolución
        03 - Evolución
        3 Evolución
        03
        0 - Prólogo

    Devuelve:

        número, título
    """

    match = re.match(
        r"^\s*(\d+)\s*(.*)$",
        value,
    )

    if not match:
        return None

    number = int(
        match.group(1)
    )

    title = (
        match.group(2)
        .strip()
    )

    return (
        number,
        title,
    )


def parse_sequence(value):
    """
    Convierte una secuencia a entero.

    Ejemplos:

        001 -> 1
        010 -> 10
        125 -> 125
    """

    if not value.isdigit():
        return None

    return int(value)


def normalize_chapter_title(title):
    """
    Normaliza únicamente el separador inicial
    del título de capítulo.

    parse_chapter():

        03 - Evolución

    produce:

        title = "- Evolución"

    Para reconstruir el valor evitamos
    duplicar ese guion.
    """

    if not title:
        return ""

    title = title.strip()

    if title.startswith("-"):
        title = (
            title[1:]
            .strip()
        )

    return title


def format_chapter_value(
    number,
    title,
):
    """
    Construye la representación canónica
    de un capítulo.

    Ejemplos:

        00 - Prólogo
        01 - Mi Contexto
        10 - Evolución

    Si no existe título:

        03
    """

    clean_title = (
        normalize_chapter_title(
            title
        )
    )

    if not clean_title:
        return (
            f"{number:02d}"
        )

    return (
        f"{number:02d} - "
        f"{clean_title}"
    )


def validate_chapter_value(value):
    """
    Valida y normaliza una definición
    completa de capítulo.

    Devuelve la representación canónica.

    Ejemplo:

        "3 - Evolución"
            ->
        "03 - Evolución"
    """

    parsed = parse_chapter(
        value
    )

    if parsed is None:
        fail(
            f"Invalid chapter value:\n"
            f"        {value}"
        )

    number, title = parsed

    return format_chapter_value(
        number,
        title,
    )


# ============================================================
# Carga de estructura editorial
# ============================================================


def load_entries():
    """
    Lee todas las entradas con Capítulo
    y Secuencia definidos.

    Las entradas todavía pendientes de
    clasificación quedan fuera de estas
    operaciones.
    """

    if not BITACORA_DIR.exists():
        fail(
            "Bitácora directory not found:\n"
            f"        {BITACORA_DIR}"
        )

    entries = []

    files = sorted(
        BITACORA_DIR.rglob("*.md")
    )

    print()
    print(
        f"[BOOK TOOLS] Found "
        f"{len(files)} Markdown file(s)."
    )

    for path in files:

        text = read_text(
            path
        )

        literary = (
            extract_literary_section(
                text
            )
        )

        if literary is None:
            continue

        section = literary[
            "content"
        ]

        chapter_raw = extract_field(
            section,
            "Capítulo",
        )

        sequence_raw = extract_field(
            section,
            "Secuencia",
        )

        # Una entrada pendiente no participa
        # en las operaciones editoriales.
        if (
            chapter_raw is None
            or sequence_raw is None
        ):
            continue

        chapter = parse_chapter(
            chapter_raw
        )

        if chapter is None:
            fail(
                f"Invalid chapter in "
                f"{path.name}:\n"
                f"        {chapter_raw}"
            )

        sequence = parse_sequence(
            sequence_raw
        )

        if sequence is None:
            fail(
                f"Invalid sequence in "
                f"{path.name}:\n"
                f"        {sequence_raw}"
            )

        (
            chapter_number,
            chapter_title,
        ) = chapter

        entries.append(
            {
                "path": path,
                "text": text,

                "chapter_raw":
                    chapter_raw,

                "chapter_number":
                    chapter_number,

                "chapter_title":
                    chapter_title,

                "sequence_raw":
                    sequence_raw,

                "sequence":
                    sequence,
            }
        )

    print(
        f"[BOOK TOOLS] Found "
        f"{len(entries)} classified "
        f"literary entr"
        f"{'y' if len(entries) == 1 else 'ies'}."
    )

    return entries


def check_duplicate_positions(entries):
    """
    Detecta duplicidades de:

        Capítulo + Secuencia

    Si existen, el orden editorial no puede
    determinarse de forma inequívoca.
    """

    seen = {}

    for entry in entries:

        key = (
            entry["chapter_number"],
            entry["sequence"],
        )

        if key in seen:

            first = seen[key]

            print()
            print(
                "[ERROR] Duplicate literary "
                "position detected:"
            )
            print()

            print(
                f"Chapter : "
                f"{entry['chapter_number']:02d}"
            )

            print(
                f"Sequence: "
                f"{entry['sequence']:03d}"
            )

            print()

            print(
                f"  - "
                f"{first['path'].name}"
            )

            print(
                f"  - "
                f"{entry['path'].name}"
            )

            print()
            print(
                "Operation aborted."
            )
            print()

            sys.exit(1)

        seen[key] = entry


# ============================================================
# Escritura de campos
# ============================================================


def replace_field_value(
    text,
    field,
    old_value,
    new_value,
):
    """
    Sustituye exactamente un campo dentro
    de ## Literaria conservando su formato.

    Soporta:

        **Secuencia:** 002

    y:

        ### Secuencia
        002

    Lo mismo se aplica a Capítulo.
    """

    literary = (
        extract_literary_section(
            text
        )
    )

    if literary is None:
        fail(
            f"Unable to locate Literaria "
            f"while replacing {field}."
        )

    section = literary[
        "content"
    ]

    # --------------------------------------------------------
    # Formato inline
    # --------------------------------------------------------

    inline_pattern = (
        rf"(^\*\*{re.escape(field)}:\*\*"
        rf"[ \t]*)"
        rf"{re.escape(old_value)}"
        rf"([ \t]*$)"
    )

    replaced, count = re.subn(
        inline_pattern,
        rf"\g<1>{new_value}\g<2>",
        section,
        count=1,
        flags=re.MULTILINE,
    )

    # --------------------------------------------------------
    # Formato heading
    # --------------------------------------------------------

    if count == 0:

        heading_pattern = (
            rf"(^### {re.escape(field)}"
            rf"[ \t]*$\n"
            rf"[ \t]*)"
            rf"{re.escape(old_value)}"
            rf"([ \t]*$)"
        )

        replaced, count = re.subn(
            heading_pattern,
            rf"\g<1>{new_value}\g<2>",
            section,
            count=1,
            flags=re.MULTILINE,
        )

    if count != 1:
        fail(
            f"Unable to replace {field} "
            f"'{old_value}'."
        )

    return (
        text[
            :literary["start"]
        ]
        + replaced
        + text[
            literary["end"]:
        ]
    )


# ============================================================
# Renumeración de secuencias
# ============================================================


def build_sequence_plan(
    entries,
    chapter_filter=None,
):
    """
    Calcula todos los cambios antes
    de modificar ningún archivo.

    Dentro de cada capítulo:

        posición 1 -> 010
        posición 2 -> 020
        posición 3 -> 030
        ...
    """

    chapters = {}

    for entry in entries:

        chapter = entry[
            "chapter_number"
        ]

        if (
            chapter_filter
            is not None
            and chapter
            != chapter_filter
        ):
            continue

        chapters.setdefault(
            chapter,
            [],
        ).append(entry)

    plan = []

    for chapter_number in sorted(
        chapters
    ):

        chapter_entries = sorted(
            chapters[
                chapter_number
            ],
            key=lambda item: (
                item["sequence"],
                item["path"].name,
            ),
        )

        for index, entry in enumerate(
            chapter_entries,
            start=1,
        ):

            new_sequence = (
                index
                * SEQUENCE_STEP
            )

            plan.append(
                {
                    "entry": entry,
                    "old":
                        entry["sequence"],
                    "new":
                        new_sequence,
                }
            )

    return plan


def print_sequence_plan(plan):
    """
    Presenta visualmente la renumeración
    de secuencias antes de aplicarla.
    """

    if not plan:

        print()
        print(
            "[BOOK TOOLS] "
            "No literary entries found."
        )

        return

    current_chapter = None

    changed = 0

    for item in plan:

        entry = item[
            "entry"
        ]

        chapter_number = (
            entry[
                "chapter_number"
            ]
        )

        if (
            chapter_number
            != current_chapter
        ):

            current_chapter = (
                chapter_number
            )

            print()

            if entry[
                "chapter_title"
            ]:

                print(
                    f"Chapter "
                    f"{chapter_number:02d} "
                    f"{entry['chapter_title']}"
                )

            else:

                print(
                    f"Chapter "
                    f"{chapter_number:02d}"
                )

            print(
                "-" * 60
            )

        old = item["old"]
        new = item["new"]

        marker = (
            " "
            if old == new
            else "*"
        )

        print(
            f"{marker} "
            f"{old:03d} -> "
            f"{new:03d}  "
            f"{entry['path'].name}"
        )

        if old != new:
            changed += 1

    print()

    print(
        f"[BOOK TOOLS] "
        f"{changed} file(s) "
        f"will change."
    )


def prepare_sequence_changes(plan):
    """
    Calcula primero en memoria TODOS
    los documentos modificados.

    No escribe nada.
    """

    prepared = []

    for item in plan:

        if (
            item["old"]
            == item["new"]
        ):
            continue

        entry = item[
            "entry"
        ]

        old_value = entry[
            "sequence_raw"
        ]

        new_value = (
            f"{item['new']:03d}"
        )

        new_text = (
            replace_field_value(
                entry["text"],
                "Secuencia",
                old_value,
                new_value,
            )
        )

        prepared.append(
            (
                entry["path"],
                new_text,
            )
        )

    return prepared


def apply_sequence_plan(plan):
    """
    Aplica una renumeración de secuencias
    previamente validada.
    """

    prepared = (
        prepare_sequence_changes(
            plan
        )
    )

    entries = [item["entry"] for item in plan]
    originals = originals_from_prepared(prepared, entries)
    return write_prepared_changes(prepared, originals)


def renumber_sequences(args):
    """
    Renumera las secuencias literarias
    utilizando incrementos de 10.
    """

    entries = load_entries()

    check_duplicate_positions(
        entries
    )

    plan = build_sequence_plan(
        entries,
        chapter_filter=args.chapter,
    )

    print_sequence_plan(
        plan
    )

    changes = [
        item
        for item in plan
        if (
            item["old"]
            != item["new"]
        )
    ]

    if not changes:

        print()
        print(
            "Sequences are already "
            "normalized."
        )
        print()

        return

    prepare_sequence_changes(
        plan
    )

    if args.dry_run:

        print()
        print(
            "[DRY RUN] "
            "No files were modified."
        )
        print()

        return

    prepared = prepare_sequence_changes(plan)

    if not confirm_changes(path for path, _ in prepared):

        print()
        print(
            "[BOOK TOOLS] "
            "Operation cancelled."
        )
        print()

        return

    changed = apply_sequence_plan(
        plan
    )

    print()
    print(
        f"[OK] {changed} "
        f"file(s) updated."
    )
    print()

    print(
        "Review the changes with:"
    )
    print()
    print(
        "    git diff"
    )
    print()


# ============================================================
# Renumeración de capítulos
# ============================================================


def collect_chapters(entries):
    """
    Agrupa las entradas por capítulo.

    Valida que un mismo número de capítulo
    no posea nombres diferentes.

    Ejemplo inválido:

        03 - Evolución
        03 - Guardianes
    """

    chapters = {}

    for entry in entries:

        number = entry[
            "chapter_number"
        ]

        title = (
            normalize_chapter_title(
                entry[
                    "chapter_title"
                ]
            )
        )

        if number not in chapters:

            chapters[number] = {
                "number": number,
                "title": title,
                "entries": [],
            }

        else:

            existing_title = (
                chapters[number][
                    "title"
                ]
            )

            if (
                existing_title
                != title
            ):

                print()
                print(
                    "[ERROR] Inconsistent "
                    "chapter definition:"
                )
                print()

                print(
                    f"Chapter: "
                    f"{number:02d}"
                )
                print()

                print(
                    f"  '{existing_title}'"
                )

                print(
                    f"  '{title}'"
                )

                print()
                print(
                    "Renumbering aborted."
                )
                print()

                sys.exit(1)

        chapters[number][
            "entries"
        ].append(entry)

    return chapters


def build_chapter_plan(
    entries,
    step=1,
):
    """
    Calcula la nueva numeración de capítulos.

    Reglas:

    - Se conserva el orden ordinal actual.
    - Si existe capítulo 0, continúa siendo 0.
    - Si no existe capítulo 0, se empieza por step.
    - El incremento lo determina step.
    - No se modifican las secuencias.
    """

    if step < 1:
        fail(
            "Chapter step must be "
            "greater than zero."
        )

    chapters = collect_chapters(
        entries
    )

    if not chapters:
        return []

    ordered_numbers = sorted(
        chapters
    )

    has_zero = (
        0 in chapters
    )

    plan = []

    current = (
        0
        if has_zero
        else step
    )

    for old_number in ordered_numbers:

        chapter = chapters[
            old_number
        ]

        if (
            has_zero
            and old_number == 0
        ):

            new_number = 0
            current = step

        else:

            new_number = current
            current += step

        plan.append(
            {
                "old":
                    old_number,
                "new":
                    new_number,
                "title":
                    chapter["title"],
                "entries":
                    chapter["entries"],
            }
        )

    return plan


def print_chapter_plan(plan):
    """Presenta la renumeracion de capitulos prevista."""

    if not plan:
        print()
        print("[BOOK TOOLS] No chapters found.")
        return

    print()
    print("Chapter renumbering plan")
    print("-" * 60)
    changed_chapters = 0
    changed_files = 0

    for item in plan:
        old = item["old"]
        new = item["new"]
        title = normalize_chapter_title(item["title"])
        marker = " " if old == new else "*"
        label = f" - {title}" if title else ""
        print(f"{marker} {old:02d} -> {new:02d}{label}")

        entry_count = len(item["entries"])
        print(f"    {entry_count} entr{'y' if entry_count == 1 else 'ies'}")

        if old != new:
            changed_chapters += 1
            changed_files += entry_count

    print()
    print(f"[BOOK TOOLS] {changed_chapters} chapter(s) will change.")
    print(f"[BOOK TOOLS] {changed_files} file(s) will be updated.")


def prepare_chapter_changes(plan):
    """Prepara y valida todos los cambios antes de escribir."""

    prepared = []

    for item in plan:
        if item["old"] == item["new"]:
            continue

        for entry in item["entries"]:
            new_value = format_chapter_value(
                item["new"],
                entry["chapter_title"],
            )
            new_text = replace_field_value(
                entry["text"],
                "Capítulo",
                entry["chapter_raw"],
                new_value,
            )
            prepared.append((entry["path"], new_text))

    return prepared


def apply_chapter_plan(plan):
    """Escribe una renumeracion de capitulos ya validada."""

    prepared = prepare_chapter_changes(plan)

    entries = [
        entry
        for item in plan
        for entry in item["entries"]
    ]
    originals = originals_from_prepared(prepared, entries)
    return write_prepared_changes(prepared, originals)


def renumber_chapters(args):
    """Renumera capitulos conservando su orden actual."""

    if args.step < 1:
        fail("Chapter step must be greater than zero.")

    entries = load_entries()
    check_duplicate_positions(entries)
    plan = build_chapter_plan(entries, step=args.step)

    print()
    print(f"[BOOK TOOLS] Chapter step: {args.step}")
    print_chapter_plan(plan)

    changes = [item for item in plan if item["old"] != item["new"]]

    if not changes:
        print()
        print("Chapters are already normalized for this step.")
        print()
        return

    prepare_chapter_changes(plan)

    if args.dry_run:
        print()
        print("[DRY RUN] No files were modified.")
        print()
        return

    prepared = prepare_chapter_changes(plan)

    if not confirm_changes(path for path, _ in prepared):
        print()
        print("[BOOK TOOLS] Operation cancelled.")
        print()
        return

    changed = apply_chapter_plan(plan)

    print()
    print(f"[OK] {changed} file(s) updated.")
    print()
    print("Review the changes with:")
    print()
    print("    git diff")
    print()


def replace_chapter(args):
    """Sustituye una definicion completa de capitulo por otra."""

    old_value = validate_chapter_value(args.old_chapter)
    new_value = validate_chapter_value(args.new_chapter)
    entries = load_entries()
    matches = [
        entry for entry in entries
        if validate_chapter_value(entry["chapter_raw"]) == old_value
    ]

    if not matches:
        fail(f"Chapter not found:\n        {old_value}")

    prepared = []
    for entry in matches:
        new_text = replace_field_value(
            entry["text"],
            "Capítulo",
            entry["chapter_raw"],
            new_value,
        )
        prepared.append((entry["path"], new_text))

    print()
    print(f"Chapter replacement: {old_value} -> {new_value}")
    print(f"[BOOK TOOLS] {len(prepared)} file(s) will be updated.")

    if args.dry_run:
        print()
        print("[DRY RUN] No files were modified.")
        print()
        return

    if not confirm_changes(path for path, _ in prepared):
        print()
        print("[BOOK TOOLS] Operation cancelled.")
        print()
        return

    originals = originals_from_prepared(prepared, matches)
    write_prepared_changes(prepared, originals)

    print()
    print(f"[OK] {len(prepared)} file(s) updated.")
    print()


def build_parser():
    """Construye la interfaz de linea de comandos."""

    parser = argparse.ArgumentParser(
        description="Editorial tools for the Aetheon book."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sequences_parser = subparsers.add_parser(
        "renumber-sequences",
        help="Renumber literary sequences using steps of 10.",
    )
    sequences_parser.add_argument("--chapter", type=int)
    sequences_parser.add_argument("--dry-run", action="store_true")
    sequences_parser.set_defaults(handler=renumber_sequences)

    chapters_parser = subparsers.add_parser(
        "renumber-chapters",
        help="Renumber chapters preserving their current order.",
    )
    chapters_parser.add_argument("--step", type=int, default=1)
    chapters_parser.add_argument("--dry-run", action="store_true")
    chapters_parser.set_defaults(handler=renumber_chapters)

    replace_parser = subparsers.add_parser(
        "replace-chapter",
        help="Replace one complete chapter definition with another.",
    )
    replace_parser.add_argument("old_chapter")
    replace_parser.add_argument("new_chapter")
    replace_parser.add_argument("--dry-run", action="store_true")
    replace_parser.set_defaults(handler=replace_chapter)

    return parser


def main():
    print()
    print("======================================")
    print(" AETHEON BOOK TOOLS")
    print("======================================")

    parser = build_parser()
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
