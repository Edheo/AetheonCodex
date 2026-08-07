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
        ↓
    Publish

Cada etapa debe ser independiente y reutilizable.
"""

import sync
import validate
import index
import publish


def main():

    print("======================================")
    print(" AETHEON CODEX BUILDER")
    print("======================================")

    sync.run()
    validate.run()
    index.run()
    publish.run()

    print()
    print("Build completed successfully.")


if __name__ == "__main__":
    main()