/**
 * Progressive Web App Service Worker
 *
 * Provides:
 * - Offline caching for core shell assets
 * - Navigation fallback for SPA routing
 * - Push notification handling
 * - Background sync hooks
 */

const CACHE_VERSION = 'v2';
const CACHE_NAME = `encompliance-${CACHE_VERSION}`;
const PRECACHE_URLS = ['/', '/index.html', '/vite.svg'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_URLS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) =>
      Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName.startsWith('encompliance-') && cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;

  if (request.method !== 'GET' || request.url.includes('/api/')) {
    return;
  }

  // Handle navigation requests (SPA routes)
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          return response;
        })
        .catch(() => caches.match(request).then((cached) => cached || caches.match('/index.html')))
    );
    return;
  }

  // Cache-first strategy for static assets
  if (request.url.includes('/assets/') || request.destination === 'style' || request.destination === 'script') {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request).then((response) => {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          return response;
        });
      })
    );
    return;
  }

  // Network-first fallback for other GET requests
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});

self.addEventListener('push', (event) => {
  let notificationData = {};

  if (event.data) {
    try {
      notificationData = event.data.json();
    } catch (_error) {
      notificationData = {
        title: 'EnCompliance Notification',
        body: event.data.text() || 'You have a new notification',
        icon: '/vite.svg'
      };
    }
  } else {
    notificationData = {
      title: 'EnCompliance Notification',
      body: 'You have a new notification',
      icon: '/vite.svg'
    };
  }

  const notificationOptions = {
    body: notificationData.body,
    icon: notificationData.icon || '/vite.svg',
    badge: notificationData.badge || '/vite.svg',
    data: notificationData.data || {},
    actions: notificationData.actions || [
      { action: 'view', title: 'View' },
      { action: 'dismiss', title: 'Dismiss' }
    ],
    requireInteraction: notificationData.requireInteraction ?? false,
    silent: notificationData.silent ?? false,
    vibrate: notificationData.vibrate || [200, 100, 200]
  };

  event.waitUntil(
    self.registration.showNotification(notificationData.title, notificationOptions)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'dismiss') {
    return;
  }

  const urlToOpen = event.notification.data?.actionUrl || '/notifications';

  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then((clientList) => {
      for (const client of clientList) {
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(Promise.resolve());
  }
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});