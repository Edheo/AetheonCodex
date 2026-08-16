"""
Aetheon Codex Builder

Orquesta el proceso completo de construcción del Codex.

El Builder no crea contenido.

Su única responsabilidad es preparar el Atlas
para que pueda ser publicado de forma coherente.

El Codex es la fuente de verdad.
Todo lo demás se deriva de él.

Pipeline:

    Sync
        ↓
    Validate
        ↓
    Index

Cada etapa debe ser independiente y reutilizable.
"""

from pathlib import Path
import subprocess
import sys

import sync
import validate
import index
import cartography
import book
import media
import member_journal

ROOT = Path(__file__).resolve().parent.parent


def build_site():
    print("[SITE] Building MkDocs site...")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mkdocs",
            "build",
        ],
        cwd=ROOT,
    )

    if result.returncode != 0:
        print()
        print("[ERROR] MkDocs build failed.")
        sys.exit(result.returncode)

    print("[SITE] Done.")


def main():
    print("======================================")
    print(" AETHEON CODEX BUILDER")
    print("======================================")

    sync.run()

    validate.run()

    index.run()

    cartography.run()

    book.run()

    member_journal.run()

    media.run()
    
    build_site()

    print()
    print("Build completed successfully.")


if __name__ == "__main__":
    main()
