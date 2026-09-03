const CACHE = "bereia-v2";
self.addEventListener("install", evt => {
  evt.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll([
      "/",
	  "/manifest.json",
      "/css/style.css",
      "/assets/js/tooltipster.bundle.min.js"
    ]))
  );
  self.skipWaiting();
});
self.addEventListener("fetch", evt => {
  evt.respondWith(caches.match(evt.request).then(r => r || fetch(evt.request)));
});