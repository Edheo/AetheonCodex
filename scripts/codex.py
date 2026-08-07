"""
Aetheon Codex

Este módulo conoce la estructura del Codex.

No interpreta su significado.
No modifica su contenido.
No publica el Atlas.

Únicamente aprende a recorrer Aetheon.
"""

"""
Aetheon Codex Library

Responsabilidad:
    Leer y representar la estructura del Codex.

Este módulo NO publica, NO copia archivos y NO genera documentación.
Únicamente proporciona una representación del Codex para el resto
del Builder.
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
    Recorre todo el Codex y devuelve todos los archivos Markdown.
    """

    return sorted(CODEX.rglob("*.md"))


# ==========================================================
# Sections
# ==========================================================

def sections():
    """
    Devuelve las secciones principales del Codex.
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
    Devuelve todas las entradas del Codex como diccionarios.
    """

    result = []

    for md in scan():

        result.append(
            {
                "title": md.stem,
                "path": md,
                "relative": md.relative_to(CODEX),
                "section": md.relative_to(CODEX).parts[0],
            }
        )

    return result


# ==========================================================
# Helpers
# ==========================================================

def guardians():

    return [
        entry
        for entry in entries()
        if entry["section"] == "03_Guardianes"
    ]


def philosophy():

    return [
        entry
        for entry in entries()
        if entry["section"] == "02_Filosofia"
    ]


def aetheon():

    return [
        entry
        for entry in entries()
        if entry["section"] == "01_Aetheon"
    ]


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
        print(f" - {entry['relative']}")