$(function () {
  let active;
  const triggers = $('.lexical-trigger');
  triggers.each(function () {
    const source = document.getElementById(this.dataset.lexicalContent);
    if (!source) return;
    const trigger = $(this);
    trigger.tooltipster({
      content: $(source).children().clone(),
      theme: 'tooltipster-light',
      maxWidth: 400,
      interactive: true,
      trigger: 'custom',
      triggerOpen: { mouseenter: true },
      triggerClose: { mouseleave: true, scroll: true },
      functionBefore(instance) {
        if (active && active !== instance) active.close();
        active = instance;
      },
      functionReady(instance, helper) {
        // The original description is already linked to the focusable button.
        helper.tooltip.setAttribute('aria-hidden', 'true');
      },
      functionAfter(instance) {
        if (active === instance) active = undefined;
      },
    });
    trigger.on('focus click', () => trigger.tooltipster('open'));
    trigger.on('blur', () => trigger.tooltipster('close'));
  });

  if (triggers.length) {
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && active) active.close();
    });
    document.addEventListener('pointerdown', event => {
      if (active && !event.target.closest('.lexical-trigger, .tooltipster-base')) active.close();
    });
  }
});
