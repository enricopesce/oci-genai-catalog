const CACHE = 'ocillms-v1';

// Activate immediately — don't wait for existing tabs to close
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

self.addEventListener('fetch', event => {
  // Only intercept same-origin navigation requests (the HTML page itself)
  if (event.request.mode !== 'navigate') return;

  event.respondWith(
    // Network-first: always try to get the latest version
    fetch(event.request)
      .then(response => {
        const copy = response.clone();
        caches.open(CACHE).then(cache => cache.put(event.request, copy));
        return response;
      })
      // Fall back to cache only when offline
      .catch(() => caches.match(event.request))
  );
});
