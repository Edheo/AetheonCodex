"""
Aetheon Atlas Index

Genera automáticamente la portada del Atlas
a partir de la estructura del Codex.
"""

from pathlib import Path
import re

import codex


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
INDEX = DOCS / "index.md"
VERSION_FILE = ROOT / "VERSION"


GENERATED_ENTRIES = {
    "03_Cartografia": [
        {
            "title": "Mapa de Aetheon",
            "relative": Path(
                "03_Cartografia"
            ) / "MAPA.md",
        },
    ],
    "05_Libro": [
        {
            "title": "Libro de Aetheon",
            "relative": Path(
                "05_Libro"
            ) / "BOOK.md",
        },
    ],
}


INTERNAL_FILES = {
    "BOOK.DEBUG.md",
}


def read_version():
    """Lee la versión canónica del artefacto publicable."""

    version = VERSION_FILE.read_text(encoding="utf-8-sig").strip()
    if not version:
        raise ValueError("VERSION no puede estar vacío.")
    if re.fullmatch(r"\d+\.\d+\.\d+", version) is None:
        raise ValueError("VERSION debe utilizar el formato X.Y.Z.")
    return version


def build():

    lines = []

    lines.append("# Aetheon")
    lines.append("")
    lines.append("> Atlas generado automáticamente a partir del Codex.")
    lines.append(f"> **Versión publicada:** {read_version()}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for section in codex.sections():

        lines.append(f"## {section.name}")
        lines.append("")

        entries = [
            entry
            for entry in codex.section_entries(section.name)
            if entry["path"].name not in INTERNAL_FILES
        ]

        entries.extend(
            GENERATED_ENTRIES.get(
                section.name,
                [],
            )
        )

        if not entries:

            lines.append("_Sin contenido._")
            lines.append("")
            continue

        for entry in entries:

            title = entry["title"]

            relative = entry["relative"].as_posix()

            lines.append(f"- [{title}]({relative})")

        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_Este documento ha sido generado automáticamente por el Builder._")
    lines.append("")

    return "\n".join(lines)


def write(markdown):

    INDEX.write_text(
        markdown,
        encoding="utf-8",
    )


def run():

    print("[INDEX] Building Atlas index...")

    markdown = build()

    write(markdown)

    print("[INDEX] Done.")
