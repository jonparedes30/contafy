const CACHE_NAME = 'contafy-v1';
const urlsToCache = [
  '/app-beta-2024/',
  '/app-beta-2024/aprendizaje/'
];

self.addEventListener('install', event => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      const results = await Promise.allSettled(
        urlsToCache.map(url => 
          fetch(url).then(resp => {
            if (!resp.ok) throw new Error(`Failed fetch ${url} ${resp.status}`);
            return cache.put(url, resp);
          })
        )
      );
      results.forEach((r, i) => {
        if (r.status === 'rejected') console.warn('SW: failed cache', urlsToCache[i]);
      });
    })()
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});