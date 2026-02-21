// Service Worker for Progressive Web App
// Enables offline functionality and caching

const CACHE_NAME = 'atis-cache-v1';
const OFFLINE_URL = '/';

// Assets to cache for offline use
const CACHE_ASSETS = [
    '/',
    '/static/css/style.css',
    '/static/js/websocket_client.js',
    '/galaxy',
    '/watchlist',
    '/alerts',
    '/analytics',
    '/offline.html'
];

// Install event - cache assets
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Caching assets');
                return cache.addAll(CACHE_ASSETS);
            })
            .catch((error) => {
                console.error('[Service Worker] Cache failed:', error);
            })
    );
    
    // Force waiting service worker to become active
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[Service Worker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    
    // Take control of all open pages
    self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }
    
    // Skip WebSocket connections
    if (event.request.url.includes('/api/ws')) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                // Return cached response if found
                if (cachedResponse) {
                    return cachedResponse;
                }
                
                // Otherwise fetch from network
                return fetch(event.request)
                    .then((networkResponse) => {
                        // Cache successful responses
                        if (networkResponse.ok && event.request.url.startsWith('http')) {
                            const responseClone = networkResponse.clone();
                            caches.open(CACHE_NAME).then((cache) => {
                                cache.put(event.request, responseClone);
                            });
                        }
                        
                        return networkResponse;
                    })
                    .catch((error) => {
                        console.error('[Service Worker] Fetch failed:', error);
                        
                        // Return offline page for navigation requests
                        if (event.request.mode === 'navigate') {
                            return caches.match(OFFLINE_URL);
                        }
                        
                        // Return generic offline response
                        return new Response('Offline', {
                            status: 503,
                            statusText: 'Service Unavailable',
                            headers: new Headers({
                                'Content-Type': 'text/plain'
                            })
                        });
                    });
            })
    );
});

// Background sync for pending alerts (when online)
self.addEventListener('sync', (event) => {
    console.log('[Service Worker] Background sync:', event.tag);
    
    if (event.tag === 'sync-alerts') {
        event.waitUntil(syncAlerts());
    }
});

// Push notifications
self.addEventListener('push', (event) => {
    console.log('[Service Worker] Push notification received');
    
    let options = {
        body: 'New threat detected',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        vibrate: [200, 100, 200],
        tag: 'threat-alert',
        requireInteraction: true,
        actions: [
            {action: 'view', title: 'View Details'},
            {action: 'dismiss', title: 'Dismiss'}
        ]
    };
    
    if (event.data) {
        try {
            const data = event.data.json();
            options.body = data.message || options.body;
            options.tag = data.tag || options.tag;
        } catch (e) {
            options.body = event.data.text();
        }
    }
    
    event.waitUntil(
        self.registration.showNotification('ATIS Alert', options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    console.log('[Service Worker] Notification clicked:', event.action);
    
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/alerts')
        );
    }
});

// Helper function for background sync
async function syncAlerts() {
    try {
        const response = await fetch('/api/alerts/history?limit=10');
        const data = await response.json();
        
        // Store in IndexedDB or send notification
        console.log('[Service Worker] Synced alerts:', data);
    } catch (error) {
        console.error('[Service Worker] Sync failed:', error);
        throw error; // Retry sync
    }
}

// Message handler for communication with main thread
self.addEventListener('message', (event) => {
    console.log('[Service Worker] Message received:', event.data);
    
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => caches.delete(cacheName))
                );
            })
        );
    }
});
