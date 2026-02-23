$(document).ready(function () {
  $('.tooltip').tooltipster({
    theme: 'tooltipster-light',
    animation: 'fade',
    delay: 100,
		maxWidth: 400,
		trigger: 'custom',
    triggerOpen: {
        mouseenter: true,
        touchstart: true
    },
    triggerClose: {
        click: true,
        scroll: true,
        tap: true
    }
  });
});