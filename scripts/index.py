"""
Aetheon Atlas Index

Genera automáticamente la portada del Atlas
a partir de la estructura del Codex.
"""

from pathlib import Path

import codex


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
INDEX = DOCS / "index.md"


def build():

    lines = []

    lines.append("# Aetheon")
    lines.append("")
    lines.append("> Atlas generado automáticamente a partir del Codex.")
    lines.append("")
    lines.append("---")
    lines.append("")

    for section in codex.sections():

        lines.append(f"## {section.name}")
        lines.append("")

        entries = codex.section_entries(section.name)

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