"""
Aetheon Codex

Este módulo conoce la estructura del Codex.

No interpreta su significado.
No modifica su contenido.
No publica el Atlas.

Únicamente aprende a recorrer Aetheon.
"""

from pathlib import Path


# ==========================================================
# Paths
# ==========================================================

ROOT = Path(__file__).resolve().parent.parent
CODEX = ROOT / "codex"


# ==========================================================
# Scanner
# ==========================================================

def scan():
    """
    Devuelve todos los archivos Markdown del Codex.
    """

    return sorted(CODEX.rglob("*.md"))


# ==========================================================
# Sections
# ==========================================================

def sections():
    """
    Devuelve todas las secciones principales del Codex.
    """

    return sorted(
        [
            directory
            for directory in CODEX.iterdir()
            if directory.is_dir()
        ]
    )


# ==========================================================
# Entries
# ==========================================================

def entries():
    """
    Devuelve todas las entradas del Codex.
    """

    result = []

    for md in scan():

        relative = md.relative_to(CODEX)

        result.append(
            {
                "title": md.stem,
                "path": md,
                "relative": relative,
                "section": relative.parts[0],
            }
        )

    return result


def section_entries(section_name):
    """
    Devuelve todas las entradas pertenecientes
    a una sección concreta.
    """

    return sorted(
        [
            entry
            for entry in entries()
            if entry["section"] == section_name
        ],
        key=lambda entry: entry["title"],
    )


# ==========================================================
# Debug
# ==========================================================

if __name__ == "__main__":

    print("Sections:")

    for section in sections():
        print(" -", section.name)

    print()

    print("Entries:")

    for entry in entries():
        print(" -", entry["relative"])