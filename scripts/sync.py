from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parent.parent

CODEX_DIR = ROOT / "codex"
DOCS_DIR = ROOT / "docs"

CARTOGRAPHY_DIR_NAME = "03_Cartografia"


def should_skip(source):
    """
    Determina si un archivo no debe copiarse a docs.
    """

    if source.name == "BOOK.DEBUG.md":
        return True

    if (
        source.suffix.lower() == ".geojson"
        and CARTOGRAPHY_DIR_NAME in source.parts
    ):
        return True

    return False


def copy_codex():
    """
    Copia el Codex a docs excluyendo
    las capas GeoJSON cartográficas fuente.
    """

    for source in CODEX_DIR.rglob("*"):

        relative = source.relative_to(
            CODEX_DIR
        )

        destination = (
            DOCS_DIR
            / relative
        )

        if source.is_dir():
            destination.mkdir(
                parents=True,
                exist_ok=True,
            )
            continue

        if should_skip(source):
            print(
                f"[SYNC] Skipping cartography source: "
                f"{relative}"
            )
            continue

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            destination,
        )


def run():
    print("[SYNC] Cleaning docs...")

    if DOCS_DIR.exists():
        shutil.rmtree(
            DOCS_DIR
        )

    DOCS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("[SYNC] Copying Codex...")

    copy_codex()

    print("[SYNC] Done.")


if __name__ == "__main__":
    run()
