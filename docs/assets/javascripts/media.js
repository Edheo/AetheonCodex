(() => {
  "use strict";
  const items = Array.from(document.querySelectorAll(".aetheon-gallery__item"));
  if (!items.length || typeof HTMLDialogElement === "undefined") return;

  const dialog = document.createElement("dialog");
  dialog.className = "aetheon-gallery-viewer";
  dialog.innerHTML = `<figure class="aetheon-gallery-viewer__figure">
    <img class="aetheon-gallery-viewer__image" alt="">
    <figcaption class="aetheon-gallery-viewer__caption"></figcaption>
    <a class="aetheon-gallery-viewer__original"
       target="_blank" rel="noopener noreferrer">
      Abrir imagen original
    </a>
  </figure>
  <button class="aetheon-gallery-viewer__close" aria-label="Cerrar">&times;</button>
  <button class="aetheon-gallery-viewer__previous" aria-label="Imagen anterior">&#8249;</button>
  <button class="aetheon-gallery-viewer__next" aria-label="Imagen siguiente">&#8250;</button>`;
  document.body.append(dialog);

  const image = dialog.querySelector(".aetheon-gallery-viewer__image");
  const caption = dialog.querySelector(".aetheon-gallery-viewer__caption");
  const original = dialog.querySelector(".aetheon-gallery-viewer__original");
  let group = [];
  let index = 0;

  const show = (nextIndex) => {
    index = (nextIndex + group.length) % group.length;
    const item = group[index];
    image.src = item.dataset.full;
    image.alt = item.dataset.alt;
    caption.textContent = item.dataset.alt;
    original.href = item.dataset.full;
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
