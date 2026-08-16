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
- Git debe estar limpio antes de modificar archivos.
- Primero se valida toda la operación.
- Si existe cualquier ambigüedad, no se modifica nada.
- Las entradas sin Capítulo o Secuencia quedan intactas.

Operaciones previstas:

    renumber-sequences
    renumber-chapters
    replace-chapter

Actualmente implementada:

    renumber-sequences
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


def ensure_clean_git():
    """
    Impide modificar el Codex si existen
    cambios pendientes en Git.

    Una vez ejecutada la operación,
    Git queda como mecanismo natural de
    revisión y rollback.
    """

    result = subprocess.run(
        [
            "git",
            "status",
            "--porcelain",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        fail(
            "Unable to determine Git status."
        )

    if result.stdout.strip():
        print()
        print(
            "[ERROR] Working tree is not clean."
        )
        print()
        print(
            "Commit or discard pending changes "
            "before using book tools."
        )
        print()
        print(result.stdout.rstrip())
        print()

        sys.exit(1)


# ============================================================
# Parsing literario
# ============================================================


def extract_literary_section(text):
    """
    Obtiene ## Literaria hasta el siguiente
    encabezado de nivel 2 o EOF.

    Devuelve también las posiciones del bloque
    dentro del documento completo.
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
    Soporta:

        **Secuencia:** 002

    y:

        ### Secuencia
        002

    Igual para Capítulo.
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
        value = match.group(1).strip()

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
        value = match.group(1).strip()

        if value:
            return value

    return None


def parse_chapter(value):
    """
    Ejemplos válidos:

        03 Evolución
        03 - Evolución
        3 Evolución
        0 Prólogo

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

    return number, title


def parse_sequence(value):
    if not value.isdigit():
        return None

    return int(value)


# ============================================================
# Carga de estructura editorial
# ============================================================


def load_entries():
    """
    Lee todas las entradas que tengan
    Capítulo Y Secuencia definidos.

    Las entradas pendientes simplemente se ignoran.
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

    for path in files:

        text = read_text(path)

        literary = extract_literary_section(
            text
        )

        if literary is None:
            continue

        section = literary["content"]

        chapter_raw = extract_field(
            section,
            "Capítulo",
        )

        sequence_raw = extract_field(
            section,
            "Secuencia",
        )

        # Una entrada no clasificada
        # no pertenece a esta operación.
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

        chapter_number, chapter_title = (
            chapter
        )

        entries.append(
            {
                "path": path,
                "text": text,
                "chapter_raw": chapter_raw,
                "chapter_number": (
                    chapter_number
                ),
                "chapter_title": (
                    chapter_title
                ),
                "sequence_raw": sequence_raw,
                "sequence": sequence,
            }
        )

    return entries


def check_duplicate_positions(entries):
    """
    Una duplicidad Capítulo + Secuencia
    hace imposible determinar el orden
    editorial de forma inequívoca.
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
                f"  - {first['path'].name}"
            )
            print(
                f"  - {entry['path'].name}"
            )
            print()
            print(
                "Renumbering aborted."
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
    """

    literary = extract_literary_section(
        text
    )

    if literary is None:
        fail(
            f"Unable to locate Literaria "
            f"while replacing {field}."
        )

    section = literary["content"]

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
        text[:literary["start"]]
        + replaced
        + text[literary["end"]:]
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
            chapter_filter is not None
            and chapter != chapter_filter
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
            chapters[chapter_number],
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
                    "old": (
                        entry["sequence"]
                    ),
                    "new": (
                        new_sequence
                    ),
                }
            )

    return plan


def print_sequence_plan(plan):
    """
    Presenta visualmente la operación
    antes de aplicarla.
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

        entry = item["entry"]

        chapter_number = (
            entry["chapter_number"]
        )

        if (
            chapter_number
            != current_chapter
        ):
            current_chapter = (
                chapter_number
            )

            print()

            if entry["chapter_title"]:
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
        f"{changed} file(s) will change."
    )


def apply_sequence_plan(plan):
    """
    Prepara primero en memoria TODOS
    los documentos modificados.

    Sólo después de validar la operación
    completa empieza a escribir.
    """

    prepared = []

    for item in plan:

        if item["old"] == item["new"]:
            continue

        entry = item["entry"]

        old_value = (
            entry["sequence_raw"]
        )

        new_value = (
            f"{item['new']:03d}"
        )

        new_text = replace_field_value(
            entry["text"],
            "Secuencia",
            old_value,
            new_value,
        )

        prepared.append(
            (
                entry["path"],
                new_text,
            )
        )

    # Si hemos llegado hasta aquí,
    # toda la transformación ha podido
    # calcularse correctamente.

    for path, content in prepared:
        write_text(
            path,
            content,
        )

    return len(prepared)


def renumber_sequences(args):
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
        if item["old"] != item["new"]
    ]

    if not changes:
        print()
        print(
            "Sequences are already normalized."
        )
        print()
        return

    if args.dry_run:
        print()
        print(
            "[DRY RUN] "
            "No files were modified."
        )
        print()
        return

    print()
    confirmation = input(
        "Apply these changes? [y/N] "
    ).strip().lower()

    if confirmation != "y":
        print()
        print(
            "[BOOK TOOLS] "
            "Operation cancelled."
        )
        print()
        return

    ensure_clean_git()

    changed = apply_sequence_plan(
        plan
    )

    print()
    print(
        f"[OK] {changed} file(s) updated."
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
# CLI
# ============================================================


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Editorial tools for "
            "the Aetheon book."
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # --------------------------------------------------------
    # renumber-sequences
    # --------------------------------------------------------

    sequences_parser = (
        subparsers.add_parser(
            "renumber-sequences",
            help=(
                "Renumber literary "
                "sequences using steps of 10."
            ),
        )
    )

    sequences_parser.add_argument(
        "--chapter",
        type=int,
        help=(
            "Only renumber the specified "
            "chapter."
        ),
    )

    sequences_parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Show the resulting operation "
            "without modifying files."
        ),
    )

    sequences_parser.set_defaults(
        handler=renumber_sequences
    )

    return parser


def main():
    print()
    print(
        "======================================"
    )
    print(
        " AETHEON BOOK TOOLS"
    )
    print(
        "======================================"
    )

    parser = build_parser()

    args = parser.parse_args()

    args.handler(args)


if __name__ == "__main__":
    main()