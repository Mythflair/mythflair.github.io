(() => {
  function initGallery(root) {
    const buttons = [...root.querySelectorAll('[data-gallery-open]')];
    const dialog = root.querySelector('.zisai-gallery__dialog');
    const image = root.querySelector('[data-gallery-large]');
    const counter = root.querySelector('[data-gallery-count]');
    const caption = root.querySelector('[data-gallery-caption]');
    if (!buttons.length || !dialog || !image || !counter) return;

    let currentIndex = 0;
    let previousFocus = null;
    let swipeStart = null;

    function show(index) {
      currentIndex = (index + buttons.length) % buttons.length;
      const button = buttons[currentIndex];
      image.src = button.dataset.full;
      image.alt = button.dataset.alt || '';
      if (caption) {
        caption.textContent = button.dataset.caption || '';
        caption.hidden = !caption.textContent;
      }
      counter.textContent = `${currentIndex + 1} / ${buttons.length}`;
    }

    buttons.forEach((button, index) => {
      button.addEventListener('click', () => {
        if (typeof dialog.showModal !== 'function') return;
        previousFocus = button;
        show(index);
        dialog.showModal();
      });
    });

    root.querySelector('[data-gallery-prev]').addEventListener('click', () => show(currentIndex - 1));
    root.querySelector('[data-gallery-next]').addEventListener('click', () => show(currentIndex + 1));
    root.querySelector('[data-gallery-close]').addEventListener('click', () => dialog.close());

    dialog.addEventListener('click', (event) => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft') { event.preventDefault(); show(currentIndex - 1); }
      if (event.key === 'ArrowRight') { event.preventDefault(); show(currentIndex + 1); }
    });
    dialog.addEventListener('close', () => {
      swipeStart = null;
      image.removeAttribute('src');
      if (previousFocus && typeof previousFocus.focus === 'function') previousFocus.focus();
    });

    image.addEventListener('pointerdown', (event) => {
      if (event.pointerType !== 'touch' || !event.isPrimary) return;
      swipeStart = { id: event.pointerId, x: event.clientX, y: event.clientY };
      image.setPointerCapture(event.pointerId);
    });
    image.addEventListener('lostpointercapture', () => { swipeStart = null; });
    image.addEventListener('pointerup', (event) => {
      if (event.pointerId !== swipeStart?.id) return;
      const dx = event.clientX - swipeStart.x;
      const dy = event.clientY - swipeStart.y;
      swipeStart = null;
      if (Math.abs(dx) >= 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        show(currentIndex + (dx < 0 ? 1 : -1));
      }
    });
  }

  function init() { document.querySelectorAll('[data-gallery]').forEach(initGallery); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
