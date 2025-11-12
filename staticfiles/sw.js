// Service worker tolerante para CONTAFY
// Precarga con Promise.allSettled y fallback network-first -> cache
const CACHE_NAME = 'contafy-v1';
const PRECACHE_ASSETS = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/offline.html'
];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    // Intentar cachear todos los recursos pero no fallar si alguno falla
    await Promise.allSettled(PRECACHE_ASSETS.map(async (url) => {
      try {
        const res = await fetch(url, { cache: 'no-cache' });
        if (res && res.ok) await cache.put(url, res.clone());
      } catch (err) {
        // Ignorar errores individuales, seguir con los demás
        console.warn('[sw] Failed to precache', url, err);
      }
    }));
  })());
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    // Limpiar caches antiguos si se desea (simplemente mantener la actual)
    const keys = await caches.keys();
    await Promise.all(keys.map(k => {
      if (k !== CACHE_NAME) return caches.delete(k);
      return Promise.resolve(true);
    }));
  })());
  self.clients.claim();
});

// Network-first strategy with cache fallback
self.addEventListener('fetch', event => {
  const req = event.request;
  // Ignore non-GET
  if (req.method !== 'GET') return;

  event.respondWith((async () => {
    try {
      const networkResponse = await fetch(req);
      // Optionally update cache for navigation requests
      if (req.mode === 'navigate') {
        const cache = await caches.open(CACHE_NAME);
        cache.put(req, networkResponse.clone()).catch(() => {});
      }
      return networkResponse;
    } catch (err) {
      // Fall back to cache
      const cached = await caches.match(req);
      if (cached) return cached;
      // If nothing cached, return a generic offline page for navigations
      if (req.mode === 'navigate') {
        return caches.match('/offline.html');
      }
      return new Response(null, { status: 503, statusText: 'Service Unavailable' });
    }
  })());
});