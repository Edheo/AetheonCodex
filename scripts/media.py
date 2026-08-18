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
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"

MEDIA_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "Edheo/Aetheon-Media/main/"
)

IMAGE_EXTENSIONS = {
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
}


YOUTUBE_PATTERN = re.compile(
    r"^\*\*youtube:\*\*\s*([A-Za-z0-9_-]{11})\s*$",
    re.MULTILINE,
)

MEDIA_SECTION_PATTERN = re.compile(
    r"^(?P<header>##\s*Media\s*)$"
    r"(?P<body>.*?)"
    r"(?=^##(?:\s|$)|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
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


def remote_image(reference):
    """Materializa una referencia lógica como imagen remota."""

    logical_path = reference.strip().replace("\\", "/")

    if (
        not logical_path
        or logical_path.startswith(("/", "http://", "https://"))
        or ".." in Path(logical_path).parts
        or Path(logical_path).suffix.lower() not in IMAGE_EXTENSIONS
    ):
        return None

    url = MEDIA_BASE_URL + quote(logical_path, safe="/")
    alt = Path(logical_path).stem
    return f"![{alt}]({url})"


def materialize_media_sections(content):
    """Convierte referencias de secciones Media en Markdown."""

    image_count = 0

    def replace_section(match):
        nonlocal image_count
        transformed = []
        section_image_count = 0

        for line in match.group("body").splitlines():
            image = remote_image(line)

            if image:
                image_count += 1
                section_image_count += 1

            transformed.append(image if image else line)

        if section_image_count == 0:
            return match.group(0)

        body = "\n".join(transformed)
        return f"{match.group('header')}\n{body}\n"

    return MEDIA_SECTION_PATTERN.sub(replace_section, content), image_count


def process_markdown(path):
    """
    Procesa un Markdown de docs sustituyendo
    referencias YouTube por su representación.
    """

    content = path.read_text(
        encoding="utf-8"
    )

    transformed, youtube_count = (
        YOUTUBE_PATTERN.subn(
            lambda match: youtube_embed(
                match.group(1)
            ),
            content,
        )
    )

    transformed, image_count = materialize_media_sections(transformed)

    if youtube_count == 0 and image_count == 0:
        return 0

    path.write_text(
        transformed,
        encoding="utf-8",
    )

    print(
        f"[MEDIA] {path.relative_to(DOCS_DIR)} "
        f"({youtube_count} YouTube, "
        f"{image_count} remote image(s))"
    )

    return youtube_count + image_count


def run():
    print("[MEDIA] Processing media references...")

    total = 0

    for path in DOCS_DIR.rglob("*.md"):
        total += process_markdown(path)

    print(
        f"[MEDIA] Done. "
        f"{total} media block(s) materialized."
    )


if __name__ == "__main__":
    run()
