"""
Aetheon Book Builder

Construye dos representaciones del Libro de Aetheon
a partir de las secciones "Literaria" de las entradas de Bitácora.

Fuentes:
    codex/04_Bitacora/*.md

Salidas:
    codex/05_Libro/BOOK.DEBUG.md
    docs/05_Libro/BOOK.md

Principios:
- La Bitácora es la fuente de verdad.
- BOOK.DEBUG.md es una herramienta editorial derivada.
- BOOK.md es la representación limpia destinada a lectura.
- El orden literario se define mediante Capítulo y Secuencia.
- Las entradas en borrador pueden formar parte del libro provisional.
- Las entradas sin clasificación se muestran únicamente en DEBUG.
- No se toman decisiones editoriales automáticamente.
"""

from pathlib import Path
from datetime import date
import re
import sys


ROOT = Path(__file__).resolve().parent.parent

BITACORA_DIR = (
    ROOT
    / "codex"
    / "04_Bitacora"
)

DEBUG_DIR = (
    ROOT
    / "codex"
    / "05_Libro"
)

DEBUG_FILE = (
    DEBUG_DIR
    / "BOOK.DEBUG.md"
)

BOOK_DIR = (
    ROOT
    / "docs"
    / "05_Libro"
)

BOOK_FILE = (
    BOOK_DIR
    / "BOOK.md"
)


def read_text(path):
    """
    Lee un archivo Markdown en UTF-8.
    """

    try:
        return path.read_text(
            encoding="utf-8"
        )

    except OSError as exc:
        print()
        print(f"[ERROR] Unable to read: {path}")
        print(f"        {exc}")
        sys.exit(1)


def extract_title(text, fallback):
    """
    Obtiene el título de la entrada si existe.

    Soporta:

        **Título:** ...

    Si no existe, utiliza el nombre del archivo.
    """

    match = re.search(
        r"^\*\*Título:\*\*[ \t]*(.*?)[ \t]*$",
        text,
        re.MULTILINE,
    )

    if match:
        value = match.group(1).strip()

        if value:
            return value

    match = re.search(
        r"^## Evento[ \t]*$"
        r"(.*?)"
        r"(?=^##\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )

    if match:
        for line in match.group(1).splitlines():
            value = line.strip()

            if value:
                return value

    return fallback


def extract_status(text):
    """
    Obtiene el estado de la entrada.

    Soporta:

        **Estado:** Borrador

    y:

        ## Estado
        Borrador
    """

    match = re.search(
        r"^\*\*Estado:\*\*[ \t]*(.*?)[ \t]*$",
        text,
        re.MULTILINE,
    )

    if match:
        value = match.group(1).strip()

        if value:
            return value

    match = re.search(
        r"^## Estado[ \t]*$"
        r"\n"
        r"[ \t]*(.*?)[ \t]*$",
        text,
        re.MULTILINE,
    )

    if match:
        value = match.group(1).strip()

        if value:
            return value

    return "Desconocido"


def extract_literary_section(text):
    """
    Extrae el bloque ## Literaria completo.

    La sección termina al encontrar
    el siguiente encabezado de nivel 2.
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

    return match.group(1).strip()


def extract_musical_section(text):
    """
    Extrae el bloque ### Musical, si existe.

    La seccion termina al encontrar el siguiente
    encabezado de nivel 2 o 3.
    """

    match = re.search(
        r"^### Musical[ \t]*$"
        r"(.*?)"
        r"(?=^#{2,3}\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )

    if not match:
        return None

    return match.group(1).strip()


def extract_field(section, field):
    """
    Extrae campos literarios soportando dos formatos.

    Formato inline:

        **Capítulo:** 03 Evolución
        **Secuencia:** 002

    Formato mediante encabezado:

        ### Capítulo
        03 Evolución

        ### Secuencia
        002
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


def extract_content(section):
    """
    Extrae únicamente el contenido situado bajo:

        ### Contenido

    hasta el siguiente encabezado de nivel 3
    o el final de la sección Literaria.
    """

    match = re.search(
        r"^### Contenido[ \t]*$"
        r"(.*?)"
        r"(?=^###\s|\Z)",
        section,
        re.MULTILINE | re.DOTALL,
    )

    if not match:
        return None

    content = match.group(1).strip()

    if not content:
        return None

    return content


def parse_chapter(value):
    """
    Interpreta valores como:

        03 Evolución
        3 Evolución
        03
        3

    Devuelve:
        numero, titulo
    """

    match = re.match(
        r"^\s*(\d+)\s*(.*)$",
        value,
    )

    if not match:
        return None

    number = int(match.group(1))
    title = match.group(2).strip()

    return number, title


def parse_sequence(value):
    """
    Convierte la secuencia a entero.

    Ejemplos:
        001 -> 1
        12  -> 12
    """

    if not value.isdigit():
        return None

    return int(value)


def parse_event_date(path):
    """
    Obtiene la fecha canonica del prefijo del archivo de Bitacora.

    Formato esperado:
        YYYY-MM-DD_Titulo-del-evento.md
    """

    match = re.match(
        r"^(\d{4})-(\d{2})-(\d{2})(?:_|$)",
        path.stem,
    )

    if not match:
        return None

    try:
        return date(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
        )
    except ValueError:
        return None


def extract_event_time(text):
    """
    Obtiene el valor temporal canonico del encabezado principal.

    Las fechas ISO validas se convierten a ``date`` para humanizarlas.
    Cualquier otro valor no vacio se conserva literalmente.
    """

    match = re.search(
        r"^#[ \t]+(.*?)[ \t]*$",
        text,
        re.MULTILINE,
    )

    if not match:
        return None

    value = match.group(1).strip()

    if not value:
        return None

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass

    return value


def humanize_date_es(value):
    """
    Presenta una fecha en castellano sin depender del locale del sistema.

    Ejemplo:
        Viernes, 7 de agosto de 2026
    """

    weekdays = (
        "Lunes", "Martes", "Miércoles", "Jueves",
        "Viernes", "Sábado", "Domingo",
    )
    months = (
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre",
        "diciembre",
    )

    return (
        f"{weekdays[value.weekday()]}, {value.day} de "
        f"{months[value.month - 1]} de {value.year}"
    )


def present_event_time(value):
    """Humaniza fechas formales y preserva los literales temporales."""

    if isinstance(value, date):
        return humanize_date_es(value)

    return value


def entry_literary_header(entry):
    """Genera la cabecera literaria comun a BOOK y BOOK.DEBUG."""

    lines = [f"### {entry['title']}", ""]

    if entry["date"] is not None:
        lines.append(
            f"*{present_event_time(entry['date'])}*"
        )

        if entry["music_work"] and entry["music_performer"]:
            lines.append("")

    if entry["music_work"] and entry["music_performer"]:
        lines.append(
            f"*{entry['music_work']} — {entry['music_performer']}*"
        )

    if lines[-1] != "":
        lines.append("")

    return lines


def load_entries():
    """
    Lee y clasifica todas las entradas de Bitácora.
    """

    if not BITACORA_DIR.exists():
        print()
        print("[ERROR] Bitácora directory not found:")
        print(f"        {BITACORA_DIR}")
        sys.exit(1)

    classified = []
    pending = []

    files = sorted(
        BITACORA_DIR.rglob("*.md")
    )

    print()
    print(
        f"[BOOK] Found "
        f"{len(files)} Markdown file(s)."
    )

    for path in files:

        text = read_text(path)

        literary = extract_literary_section(
            text
        )

        if literary is None:
            continue

        content = extract_content(
            literary
        )

        if content is None:
            continue

        title = extract_title(
            text,
            path.stem,
        )

        status = extract_status(
            text
        )

        musical = extract_musical_section(
            text
        )

        music_work = None
        music_performer = None

        if musical is not None:
            music_work = extract_field(
                musical,
                "Obra",
            )
            music_performer = extract_field(
                musical,
                "Intérprete",
            )

        chapter_value = extract_field(
            literary,
            "Capítulo",
        )

        sequence_value = extract_field(
            literary,
            "Secuencia",
        )

        entry = {
            "path": path,
            "title": title,
            "date": extract_event_time(text),
            "status": status,
            "music_work": music_work,
            "music_performer": music_performer,
            "chapter_raw": chapter_value,
            "sequence_raw": sequence_value,
            "content": content,
        }

        if (
            chapter_value is None
            or sequence_value is None
        ):
            pending.append(entry)
            continue

        chapter = parse_chapter(
            chapter_value
        )

        sequence = parse_sequence(
            sequence_value
        )

        if chapter is None:
            print()
            print(
                f"[ERROR] Invalid chapter "
                f"in {path.name}:"
            )
            print(
                f"        {chapter_value}"
            )
            sys.exit(1)

        if sequence is None:
            print()
            print(
                f"[ERROR] Invalid sequence "
                f"in {path.name}:"
            )
            print(
                f"        {sequence_value}"
            )
            sys.exit(1)

        chapter_number, chapter_title = chapter

        entry.update(
            {
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "sequence": sequence,
            }
        )

        classified.append(entry)

    return classified, pending


def check_duplicates(entries):
    """
    Detecta duplicidades de Capítulo + Secuencia.
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

            print(
                f"  Chapter: "
                f"{entry['chapter_number']}"
            )

            print(
                f"  Sequence: "
                f"{entry['sequence']}"
            )

            print(
                f"  - {first['path'].name}"
            )

            print(
                f"  - {entry['path'].name}"
            )

            print()
            print(
                "Book build aborted."
            )

            sys.exit(1)

        seen[key] = entry


def sort_entries(entries):
    """
    Ordena las entradas por Capítulo + Secuencia.
    """

    return sorted(
        entries,
        key=lambda item: (
            item["chapter_number"],
            item["sequence"],
        ),
    )


def chapter_heading(entry):
    """
    Genera el encabezado de capítulo.
    """

    number = entry["chapter_number"]
    title = entry["chapter_title"]

    if title:
        return (
            f"## Capítulo "
            f"{number:02d} · "
            f"{title}"
        )

    return (
        f"## Capítulo "
        f"{number:02d}"
    )


def build_clean_book(entries):
    """
    Construye BOOK.md.

    Incluye:
    - título del libro
    - índice de capítulos
    - capítulos
    - contenido literario

    No incluye:
    - nombre del archivo origen
    - estado
    - secuencia
    - títulos técnicos de Bitácora
    - entradas pendientes
    """

    entries = sort_entries(entries)
    chapters = get_chapters(entries)

    lines = []

    lines.append("# Aetheon")
    lines.append("")

    # -------------------------------------------------
    # Índice de lectura
    # -------------------------------------------------

    if chapters:
        lines.append("## Índice")
        lines.append("")

        for chapter in chapters:

            number = chapter["number"]
            title = chapter["title"]

            if title:
                label = (
                    f"Capítulo {number:02d} · "
                    f"{title}"
                )
            else:
                label = (
                    f"Capítulo {number:02d}"
                )

            anchor = chapter_anchor(
                number,
                title,
            )

            lines.append(
                f"- [{label}](#{anchor})"
            )

        lines.append("")
        lines.append("---")
        lines.append("")

    # -------------------------------------------------
    # Cuerpo del libro
    # -------------------------------------------------

    current_chapter = None

    for entry in entries:

        chapter_number = (
            entry["chapter_number"]
        )

        if chapter_number != current_chapter:

            current_chapter = chapter_number

            lines.append(
                chapter_heading(entry)
            )

            lines.append("")

        lines.append(
            "\n".join(entry_literary_header(entry))
        )

        lines.append(entry["content"])

        lines.append("")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"

def build_debug_book(entries, pending):
    """
    Construye BOOK.DEBUG.md.

    Incluye:
    - advertencia de archivo generado
    - índice editorial completo
    - capítulos
    - secuencia
    - título
    - archivo origen
    - estado
    - contenido literario
    - entradas pendientes de clasificación
    """

    entries = sort_entries(entries)

    lines = []

    lines.append(
        "# Aetheon — Debug Editorial"
    )

    lines.append("")

    lines.append(
        "> ⚠️ ARCHIVO GENERADO AUTOMÁTICAMENTE"
    )

    lines.append(">")
    lines.append(
        "> No editar manualmente."
    )

    lines.append(
        "> Fuente: entradas de `04_Bitacora`."
    )

    lines.append("")

    # -------------------------------------------------
    # Índice editorial
    # -------------------------------------------------

    lines.append(
        "## Índice editorial"
    )

    lines.append("")

    current_chapter = None

    for entry in entries:

        chapter_number = (
            entry["chapter_number"]
        )

        if chapter_number != current_chapter:

            current_chapter = chapter_number

            chapter_title = (
                entry["chapter_title"]
            )

            if chapter_title:
                lines.append(
                    f"- **Capítulo "
                    f"{chapter_number:02d} · "
                    f"{chapter_title}**"
                )
            else:
                lines.append(
                    f"- **Capítulo "
                    f"{chapter_number:02d}**"
                )

        lines.append(
            f"  - "
            f"{entry['sequence']:03d} · "
            f"{entry['title']} "
            f"— `{entry['path'].name}`"
        )

    if not entries:
        lines.append(
            "- No existen entradas "
            "literarias clasificadas."
        )

    lines.append("")

    # -------------------------------------------------
    # Pendientes en índice editorial
    # -------------------------------------------------

    lines.append(
        "### Pendientes de clasificación"
    )

    lines.append("")

    if pending:

        for entry in pending:

            lines.append(
                f"- {entry['title']} "
                f"— `{entry['path'].name}`"
            )

    else:

        lines.append(
            "- Ninguna."
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # -------------------------------------------------
    # Cuerpo editorial
    # -------------------------------------------------

    current_chapter = None

    for entry in entries:

        chapter_number = (
            entry["chapter_number"]
        )

        if chapter_number != current_chapter:

            current_chapter = chapter_number

            lines.append(
                chapter_heading(entry)
            )

            lines.append("")

        lines.extend(entry_literary_header(entry))

        lines.append(
            f"- **Origen:** "
            f"`{entry['path'].name}`"
        )

        lines.append(
            f"- **Estado:** "
            f"{entry['status']}"
        )

        lines.append(
            f"- **Capítulo:** "
            f"{entry['chapter_number']:02d}"
        )

        lines.append(
            f"- **Secuencia:** "
            f"{entry['sequence']:03d}"
        )

        lines.append("")

        lines.append(
            entry["content"]
        )

        lines.append("")
        lines.append("---")
        lines.append("")

    # -------------------------------------------------
    # Entradas pendientes
    # -------------------------------------------------

    lines.append(
        "# Entradas pendientes de clasificación"
    )

    lines.append("")

    if not pending:

        lines.append(
            "No existen entradas literarias "
            "pendientes de clasificación."
        )

        lines.append("")

    else:

        lines.append(
            "Las siguientes entradas contienen "
            "contenido literario pero todavía "
            "no tienen Capítulo y/o Secuencia."
        )

        lines.append("")

        for entry in pending:

            chapter = (
                entry["chapter_raw"]
                or "Sin definir"
            )

            sequence = (
                entry["sequence_raw"]
                or "Sin definir"
            )

            lines.append(
                f"## {entry['title']}"
            )

            lines.append("")

            if entry["date"] is not None:
                lines.append(
                    f"*{present_event_time(entry['date'])}*"
                )

                if entry["music_work"] and entry["music_performer"]:
                    lines.append("")

            if entry["music_work"] and entry["music_performer"]:
                lines.append(
                    f"*{entry['music_work']} — "
                    f"{entry['music_performer']}*"
                )

            if lines[-1] != "":
                lines.append("")

            lines.append(
                f"- **Origen:** "
                f"`{entry['path'].name}`"
            )

            lines.append(
                f"- **Estado:** "
                f"{entry['status']}"
            )

            lines.append(
                f"- **Capítulo:** "
                f"{chapter}"
            )

            lines.append(
                f"- **Secuencia:** "
                f"{sequence}"
            )

            lines.append("")

            lines.append(
                entry["content"]
            )

            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"

def write_file(path, content):
    """
    Escribe un archivo generado.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        path.write_text(
            content,
            encoding="utf-8",
        )

    except OSError as exc:
        print()
        print(
            f"[ERROR] Unable to write "
            f"{path}"
        )
        print(f"        {exc}")
        sys.exit(1)

    print(
        f"[OK] Generated: {path}"
    )

def get_chapters(entries):
    """
    Devuelve los capítulos presentes en las entradas,
    respetando el orden numérico.

    Cada elemento contiene:
        number
        title
    """

    chapters = []
    seen = set()

    for entry in sort_entries(entries):

        number = entry["chapter_number"]

        if number in seen:
            continue

        seen.add(number)

        chapters.append(
            {
                "number": number,
                "title": entry["chapter_title"],
            }
        )

    return chapters


def chapter_anchor(number, title):
    """
    Genera un ancla Markdown compatible con MkDocs
    a partir del encabezado del capítulo.

    Ejemplo:

        Capítulo 03 · Evolución

    produce:

        #capítulo-03--evolución
    """

    if title:
        text = (
            f"capítulo-{number:02d}-"
            f"{title}"
        )
    else:
        text = (
            f"capítulo-{number:02d}"
        )

    text = text.lower()

    replacements = {
        "á": "á",
        "é": "é",
        "í": "í",
        "ó": "ó",
        "ú": "ú",
        "ñ": "ñ",
        "·": "",
    }

    for old, new in replacements.items():
        text = text.replace(
            old,
            new,
        )

    text = re.sub(
        r"[^\wáéíóúñ-]+",
        "-",
        text,
    )

    text = re.sub(
        r"-+",
        "-",
        text,
    )

    return text.strip("-")

def run():
    """
    Ejecuta la construcción literaria completa.
    """

    print()
    print("======================================")
    print(" AETHEON BOOK")
    print("======================================")

    classified, pending = load_entries()

    check_duplicates(
        classified
    )

    print()
    print(
        f"[BOOK] Classified entries: "
        f"{len(classified)}"
    )

    print(
        f"[BOOK] Pending classification: "
        f"{len(pending)}"
    )

    clean_book = build_clean_book(
        classified
    )

    debug_book = build_debug_book(
        classified,
        pending,
    )

    print()
    print(
        "[BOOK] Writing reading version..."
    )

    write_file(
        BOOK_FILE,
        clean_book,
    )

    print()
    print(
        "[BOOK] Writing debug version..."
    )

    write_file(
        DEBUG_FILE,
        debug_book,
    )

    print()
    print(
        "Book build completed "
        "successfully."
    )


if __name__ == "__main__":
    run()
