"""
Sincroniza el Codex con el directorio docs/.

Responsabilidades:

- Copiar Markdown.
- Copiar recursos.
- Mantener la estructura.
- No modificar contenido.
"""
from pathlib import Path
import shutil


ROOT = Path(__file__).parent.parent

DOCS = ROOT / "docs"
CODEX = ROOT / "codex"
ASSETS = ROOT / "assets"


def clean_docs():
    """Vacía docs sin eliminar la carpeta."""
    DOCS.mkdir(exist_ok=True)

    for item in DOCS.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def copy_tree(source: Path, destination: Path):
    """Copia recursivamente una carpeta sobre otra."""
    if not source.exists():
        return

    for item in source.rglob("*"):
        relative = item.relative_to(source)
        target = destination / relative

        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)

def copy_codex():
    copy_tree(CODEX, DOCS)

def copy_assets():
    copy_tree(ASSETS, DOCS)
    
def run():
    print("[SYNC] Cleaning docs...")

    clean_docs()

    print("[SYNC] Copying Codex...")

    copy_codex()

    print("[SYNC] Copying assets...")

    copy_assets()

    print("[SYNC] Done.")


if __name__ == "__main__":
    run()
