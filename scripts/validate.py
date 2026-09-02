"""
Valida la integridad del Codex.

Responsabilidades:

- Enlaces.
- Recursos.
- Markdown.
- GeoJSON.
- Coherencia interna.
"""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent.parent
PRIVATE_DIR = ROOT / "private"
GITIGNORE = ROOT / ".gitignore"


def validate_private_memory():
    """
    Impide que la memoria reservada entre accidentalmente en Git o en docs.

    La memoria privada vive fuera de codex para que el sincronizador no pueda
    copiarla al Atlas. La exclusión de Git es una segunda frontera explícita.
    """

    ignored = {
        line.strip()
        for line in GITIGNORE.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    if "/private/" not in ignored:
        raise ValueError(
            "La memoria reservada debe permanecer excluida mediante /private/."
        )

    published_private = ROOT / "docs" / "private"
    if published_private.exists():
        raise ValueError(
            "La memoria reservada no puede existir dentro de docs."
        )

    result = subprocess.run(
        ["git", "ls-files", "--", "private"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise ValueError(
            "No se pudo verificar si Git rastrea la memoria reservada."
        )

    if result.stdout.strip():
        raise ValueError(
            "Git está rastreando archivos de la memoria reservada."
        )

def validate_links():
    pass


def validate_images():
    pass


def validate_geojson():
    pass


def run():

    validate_private_memory()
    validate_links()
    validate_images()
    validate_geojson()
