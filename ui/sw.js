/**
 * Nexus-Pulse Progressive Web App (PWA) Service Worker
 * Caches core shell assets for instant mobile & desktop app loading.
 * Ensures all /api/* requests bypass cache for real-time live data.
 */

const CACHE_NAME = 'nexus-pulse-v2.0';
const SHELL_ASSETS = [
  '/',
  '/manifest.json',
  '/ui/index.html',
  '/ui/css/cyberpunk.css',
  '/ui/js/app.js',
  '/ui/assets/icon.svg',
  '/ui/assets/icon-192.png',
  '/ui/assets/icon-512.png',
  '/favicon.ico'
];

// Install: pre-cache application shell
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(SHELL_ASSETS).catch((err) => {
        console.warn('[PWA SW] Pre-caching partial shell failure:', err);
      });
    })
  );
});

// Activate: clean up old cache versions
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: bypass API, serve cache with network fallback for shell
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Bypass cache for all API routes and non-GET requests
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/docs') || url.pathname.startsWith('/openapi.json') || event.request.method !== 'GET') {
    return;
  }

  // Network-First for navigation (HTML), Stale-While-Revalidate for static assets
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(event.request);
          if (cached) return cached;
          return caches.match('/');
        })
    );
    return;
  }

  // Stale-While-Revalidate for scripts, styles, images
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const clone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return networkResponse;
      }).catch(() => null);

      return cachedResponse || fetchPromise;
    })
  );
});
