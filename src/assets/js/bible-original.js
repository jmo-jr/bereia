(() => {
  const triggers = document.querySelectorAll('.bible-original');
  if (!triggers.length) return;
  let active;
  let timer;
  let restoringFocus = false;
  function close(restoreFocus = false) {
    clearTimeout(timer);
    if (!active) return;
    const trigger = active;
    trigger.querySelector('[role="dialog"]').hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
    active.classList.remove('is-open');
    active = undefined;
    if (restoreFocus === true) {
      restoringFocus = true;
      trigger.focus();
      restoringFocus = false;
    }
  }
  function open(trigger) {
    clearTimeout(timer);
    if (active !== trigger) close();
    active = trigger;
    const tip = trigger.querySelector('[role="dialog"]');
    tip.hidden = false;
    trigger.setAttribute('aria-expanded', 'true');
    trigger.classList.add('is-open');
    const box = trigger.getBoundingClientRect();
    tip.style.left = '8px';
    tip.style.top = '8px';
    const width = tip.getBoundingClientRect().width;
    const height = tip.getBoundingClientRect().height;
    tip.style.left = `${Math.max(8, Math.min(box.left, window.innerWidth - width - 8))}px`;
    const below = box.bottom + 8;
    tip.style.top = `${Math.max(8, below + height < window.innerHeight - 8 ? below : box.top - height - 8)}px`;
  }
  triggers.forEach(trigger => {
    trigger.addEventListener('pointerenter', event => {
      if (event.pointerType === 'touch') return;
      clearTimeout(timer);
      timer = setTimeout(() => open(trigger), 180);
    });
    trigger.addEventListener('pointerleave', () => {
      if (trigger.contains(document.activeElement)) return;
      clearTimeout(timer);
      timer = setTimeout(close, 180);
    });
    trigger.addEventListener('focus', () => { if (!restoringFocus) open(trigger); });
    trigger.addEventListener('focusout', event => {
      if (!trigger.contains(event.relatedTarget)) close();
    });
    trigger.addEventListener('click', event => {
      if (!trigger.querySelector('[role="dialog"]').contains(event.target)) open(trigger);
    });
    trigger.querySelector('.bible-original-close').addEventListener('click', event => {
      event.stopPropagation();
      close(true);
    });
  });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') close(Boolean(active?.contains(document.activeElement))); });
  document.addEventListener('pointerdown', event => { if (active && !active.contains(event.target)) close(); });
  window.addEventListener('scroll', event => {
    if (!active?.contains(event.target)) close();
  }, true);
  window.addEventListener('resize', close);
})();
