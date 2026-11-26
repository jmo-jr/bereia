const CACHE = "bereia-v4";
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
self.addEventListener("activate", evt => {
  evt.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(key => key.startsWith("bereia-") && key !== CACHE)
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});
self.addEventListener("fetch", evt => {
  const url = new URL(evt.request.url);
  if (url.origin === self.location.origin && url.pathname.endsWith("/css/style.css")) {
    evt.respondWith((async () => {
      const cached = await caches.match(evt.request);
      let response;
      try {
        response = await fetch(evt.request, { cache: "no-cache" });
      } catch (error) {
        if (cached) return cached;
        throw error;
      }
      if (response.ok) {
        const cache = await caches.open(CACHE);
        await cache.put(evt.request, response.clone());
      }
      return response;
    })());
    return;
  }
  evt.respondWith(caches.match(evt.request).then(r => r || fetch(evt.request)));
});