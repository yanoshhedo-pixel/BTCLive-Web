// Service Worker (sw.js) - minimal helper to show notifications when page is installed/open.
// Save this file at the repository root (same folder as mobile.html) so GitHub Pages can serve it at /sw.js

self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(clients.claim());
});

self.addEventListener('message', event => {
  try {
    const d = event.data;
    if (d && d.type === 'notify') {
      self.registration.showNotification(d.title || 'Notification', { body: d.body || '' });
    }
  } catch (e) {}
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: "window" }).then(clientList => {
      if (clientList.length > 0) {
        return clientList[0].focus();
      }
      return clients.openWindow('/');
    })
  );
});
