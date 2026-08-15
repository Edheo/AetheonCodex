"""
Aetheon Media Processor

Materializa referencias multimedia del Codex
en representaciones adecuadas para publicación.

El Codex permanece como fuente de verdad.
Este script modifica únicamente archivos derivados
dentro de docs.
"""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"


YOUTUBE_PATTERN = re.compile(
    r"^\*\*youtube:\*\*\s*([A-Za-z0-9_-]{11})\s*$",
    re.MULTILINE,
)


def youtube_embed(video_id):
    """
    Genera la representación publicada
    de una referencia a YouTube.
    """

    return f"""<div class="aetheon-youtube">
  <iframe
    src="https://www.youtube-nocookie.com/embed/{video_id}"
    title="YouTube video"
    loading="lazy"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowfullscreen>
  </iframe>
</div>

<div class="aetheon-youtube-link">
  <a href="https://www.youtube.com/watch?v={video_id}"
     target="_blank"
     rel="noopener noreferrer">
    Ver en YouTube
  </a>
</div>"""


def process_markdown(path):
    """
    Procesa un Markdown de docs sustituyendo
    referencias YouTube por su representación.
    """

    content = path.read_text(
        encoding="utf-8"
    )

    transformed, count = (
        YOUTUBE_PATTERN.subn(
            lambda match: youtube_embed(
                match.group(1)
            ),
            content,
        )
    )

    if count == 0:
        return 0

    path.write_text(
        transformed,
        encoding="utf-8",
    )

    print(
        f"[MEDIA] {path.relative_to(DOCS_DIR)} "
        f"({count} YouTube)"
    )

    return count


def run():
    print("[MEDIA] Processing media references...")

    total = 0

    for path in DOCS_DIR.rglob("*.md"):
        total += process_markdown(path)

    print(
        f"[MEDIA] Done. "
        f"{total} YouTube reference(s) materialized."
    )


if __name__ == "__main__":
    run()