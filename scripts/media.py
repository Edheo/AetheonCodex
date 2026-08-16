"""
Aetheon Media Processor

Materializa referencias multimedia del Codex
en representaciones adecuadas para publicación.

El Codex permanece como fuente de verdad.
Este script modifica únicamente archivos derivados
dentro de docs.
"""

from pathlib import Path
from html import escape
import re
import shutil
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
RESOURCE_MEDIA_DIR = ROOT / "recursos" / "media"
PUBLIC_MEDIA_DIR = DOCS_DIR / "assets" / "media"
STYLESHEET_FILE = DOCS_DIR / "assets" / "stylesheets" / "media.css"
JAVASCRIPT_FILE = DOCS_DIR / "assets" / "javascripts" / "media.js"
PUBLISHED_IMAGES = set()


YOUTUBE_PATTERN = re.compile(
    r"^\*\*youtube:\*\*\s*([A-Za-z0-9_-]{11})\s*$",
    re.MULTILINE,
)

MEDIA_SECTION_PATTERN = re.compile(
    r"^(##[ \t]*Media[ \t]*$)(.*?)"
    r"(?=^##(?:[ \t]|$)|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)

IMAGE_PATTERN = re.compile(
    r"^[^\r\n]+\.(?:avif|gif|jpe?g|png|webp)$",
    re.IGNORECASE,
)

MEDIA_STYLESHEET = """.aetheon-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(12rem, 100%), 1fr));
  gap: 0.75rem;
  margin: 1rem 0;
}

.aetheon-gallery__item {
  display: block;
  padding: 0;
  overflow: hidden;
  border: 0;
  border-radius: 0.4rem;
  background: transparent;
  cursor: zoom-in;
  aspect-ratio: 4 / 3;
}

.aetheon-gallery__item img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  transition: transform 180ms ease;
}

.aetheon-gallery__item:hover img,
.aetheon-gallery__item:focus-visible img {
  transform: scale(1.035);
}

.aetheon-gallery-viewer {
  width: min(96vw, 78rem);
  max-width: none;
  padding: 0;
  border: 0;
  border-radius: 0.5rem;
  background: #111;
  color: #fff;
}

.aetheon-gallery-viewer::backdrop { background: rgb(0 0 0 / 82%); }
.aetheon-gallery-viewer__figure { margin: 0; }
.aetheon-gallery-viewer__image {
  display: block;
  width: 100%;
  max-height: 86vh;
  object-fit: contain;
}

.aetheon-gallery-viewer__caption { padding: 0.6rem 3.5rem; text-align: center; }
.aetheon-gallery-viewer__close,
.aetheon-gallery-viewer__previous,
.aetheon-gallery-viewer__next {
  position: absolute;
  border: 0;
  border-radius: 50%;
  background: rgb(0 0 0 / 58%);
  color: #fff;
  cursor: pointer;
  font-size: 1.5rem;
  width: 2.5rem;
  height: 2.5rem;
}
.aetheon-gallery-viewer__close { top: 0.6rem; right: 0.6rem; }
.aetheon-gallery-viewer__previous { left: 0.6rem; top: 50%; }
.aetheon-gallery-viewer__next { right: 0.6rem; top: 50%; }
"""

MEDIA_JAVASCRIPT = r"""(() => {
  "use strict";
  const items = Array.from(document.querySelectorAll(".aetheon-gallery__item"));
  if (!items.length || typeof HTMLDialogElement === "undefined") return;

  const dialog = document.createElement("dialog");
  dialog.className = "aetheon-gallery-viewer";
  dialog.innerHTML = `<figure class="aetheon-gallery-viewer__figure">
    <img class="aetheon-gallery-viewer__image" alt="">
    <figcaption class="aetheon-gallery-viewer__caption"></figcaption>
  </figure>
  <button class="aetheon-gallery-viewer__close" aria-label="Cerrar">&times;</button>
  <button class="aetheon-gallery-viewer__previous" aria-label="Imagen anterior">&#8249;</button>
  <button class="aetheon-gallery-viewer__next" aria-label="Imagen siguiente">&#8250;</button>`;
  document.body.append(dialog);

  const image = dialog.querySelector(".aetheon-gallery-viewer__image");
  const caption = dialog.querySelector(".aetheon-gallery-viewer__caption");
  let group = [];
  let index = 0;

  const show = (nextIndex) => {
    index = (nextIndex + group.length) % group.length;
    const item = group[index];
    image.src = item.dataset.full;
    image.alt = item.dataset.alt;
    caption.textContent = item.dataset.alt;
  };

  items.forEach((item) => item.addEventListener("click", () => {
    const gallery = item.closest(".aetheon-gallery");
    group = Array.from(gallery.querySelectorAll(".aetheon-gallery__item"));
    show(group.indexOf(item));
    dialog.showModal();
  }));

  dialog.querySelector(".aetheon-gallery-viewer__close").addEventListener("click", () => dialog.close());
  dialog.querySelector(".aetheon-gallery-viewer__previous").addEventListener("click", () => show(index - 1));
  dialog.querySelector(".aetheon-gallery-viewer__next").addEventListener("click", () => show(index + 1));
  dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") show(index - 1);
    if (event.key === "ArrowRight") show(index + 1);
  });
})();
"""


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


def image_gallery(path, section):
    """Materializa las referencias de una seccion Media como galeria."""

    references = [line.strip() for line in section.splitlines() if line.strip()]
    images = []

    for reference in references:
        if not IMAGE_PATTERN.fullmatch(reference):
            continue

        image_path = RESOURCE_MEDIA_DIR / reference
        if not image_path.is_file():
            print(f"[MEDIA] WARNING missing image: {image_path.relative_to(ROOT)}")
            continue

        destination = PUBLIC_MEDIA_DIR / reference
        if reference not in PUBLISHED_IMAGES:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_path, destination)
            PUBLISHED_IMAGES.add(reference)

        # MkDocs publica cada Markdown como ``documento/index.html``.
        # Calculamos el ascenso necesario hasta ``docs/assets`` para no
        # depender de un dominio o subruta de despliegue concretos.
        document_parts = path.relative_to(DOCS_DIR).with_suffix("").parts
        source = "../" * len(document_parts) + "assets/media/" + quote(reference)
        alt = Path(reference).stem.replace("-", " ")
        images.append((source, alt))

    if not images:
        return ""

    lines = ['<div class="aetheon-gallery" role="group" aria-label="Galería de imágenes">']
    for source, alt in images:
        safe_source = escape(source, quote=True)
        safe_alt = escape(alt, quote=True)
        lines.extend([
            '  <button class="aetheon-gallery__item" type="button"',
            f'          data-full="{safe_source}" data-alt="{safe_alt}"',
            f'          aria-label="Ampliar {safe_alt}">',
            f'    <img src="{safe_source}" alt="{safe_alt}" loading="lazy">',
            "  </button>",
        ])
    lines.append("</div>")
    return "\n".join(lines)


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

    gallery_count = 0

    def replace_media(match):
        nonlocal gallery_count
        gallery = image_gallery(path, match.group(2))
        if gallery:
            gallery_count += 1
        suffix = "\n" if match.end() == len(transformed) else "\n\n"
        return f"{match.group(1)}\n\n{gallery}{suffix}"

    transformed = MEDIA_SECTION_PATTERN.sub(replace_media, transformed)

    if youtube_count == 0 and gallery_count == 0 and transformed == content:
        return 0

    path.write_text(
        transformed,
        encoding="utf-8",
    )

    print(
        f"[MEDIA] {path.relative_to(DOCS_DIR)} "
        f"({youtube_count} YouTube, {gallery_count} galleries)"
    )

    return youtube_count + gallery_count


def write_assets():
    PUBLISHED_IMAGES.clear()
    if PUBLIC_MEDIA_DIR.exists():
        shutil.rmtree(PUBLIC_MEDIA_DIR)
    STYLESHEET_FILE.parent.mkdir(parents=True, exist_ok=True)
    JAVASCRIPT_FILE.parent.mkdir(parents=True, exist_ok=True)
    STYLESHEET_FILE.write_text(MEDIA_STYLESHEET, encoding="utf-8")
    JAVASCRIPT_FILE.write_text(MEDIA_JAVASCRIPT, encoding="utf-8")


def run():
    print("[MEDIA] Processing media references...")

    write_assets()

    total = 0

    for path in DOCS_DIR.rglob("*.md"):
        total += process_markdown(path)

    print(
        f"[MEDIA] Done. "
        f"{total} media block(s) materialized."
    )


if __name__ == "__main__":
    run()
