$(document).ready(function () {
  $('.tooltip').tooltipster({
    theme: 'tooltipster-light',
    animation: 'fade',
    delay: 100,
		maxWidth: 400,
		trigger: 'custom',
    triggerOpen: {
        click: true,
        tap: true
    },
    triggerClose: {
        click: true,
        tap: true
    }
  });
});