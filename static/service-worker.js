/*
 * EduTrack Pro - Service Worker
 * PWA Offline Support and Caching
 */

const CACHE_NAME = 'edutrack-v1';
const OFFLINE_PAGE = '/offline.html';

// Assets to pre-cache (only existing files)
const PRECACHE_ASSETS = [
    '/',
    '/dashboard/',
    '/offline.html'
];

// Install Event - Pre-cache assets with error handling
self.addEventListener('install', function(event) {
    console.log('[ServiceWorker] Install');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('[ServiceWorker] Pre-caching assets');
                // Cache each asset individually with error handling
                return Promise.all(
                    PRECACHE_ASSETS.map(function(url) {
                        return fetch(url)
                            .then(function(response) {
                                if (response.ok) {
                                    return cache.put(url, response);
                                }
                            })
                            .catch(function(error) {
                                console.log('[ServiceWorker] Failed to cache:', url, error);
                            });
                    })
                );
            })
            .then(function() {
                console.log('[ServiceWorker] Skip waiting');
                return self.skipWaiting();
            })
    );
});

// Activate Event - Clean up old caches
self.addEventListener('activate', function(event) {
    console.log('[ServiceWorker] Activate');
    
    event.waitUntil(
        caches.keys()
            .then(function(cacheNames) {
                return Promise.all(
                    cacheNames.map(function(cacheName) {
                        if (cacheName !== CACHE_NAME) {
                            console.log('[ServiceWorker] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(function() {
                console.log('[ServiceWorker] Claiming clients');
                return self.clients.claim();
            })
    );
});

// Fetch Event - Network first for navigation, cache first for static assets
self.addEventListener('fetch', function(event) {
    const url = event.request.url;
    const request = event.request;
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip chrome-extension and other non-http(s) requests
    if (!url.startsWith('http')) {
        return;
    }
    
    // API endpoints - Network only (always fresh)
    if (url.includes('/api/')) {
        event.respondWith(
            fetch(request)
                .catch(function(error) {
                    console.log('[ServiceWorker] API fetch failed:', error);
                    return new Response(JSON.stringify({
                        error: 'Offline - Unable to fetch data',
                        offline: true
                    }), {
                        status: 503,
                        headers: { 'Content-Type': 'application/json' }
                    });
                })
        );
        return;
    }
    
    // Navigation requests - Network first with cache fallback
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then(function(response) {
                    // Cache successful responses
                    if (response.ok) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then(function(cache) {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                })
                .catch(function(error) {
                    console.log('[ServiceWorker] Navigation fetch failed, trying cache');
                    return caches.match(request)
                        .then(function(cachedResponse) {
                            if (cachedResponse) {
                                return cachedResponse;
                            }
                            // If not in cache, serve offline page
                            return caches.match(OFFLINE_PAGE);
                        });
                })
        );
        return;
    }
    
    // Static assets - Cache first with network fallback
    event.respondWith(
        caches.match(request)
            .then(function(cachedResponse) {
                if (cachedResponse) {
                    // Return cached version, but also update cache in background
                    fetch(request).then(function(response) {
                        if (response.ok) {
                            caches.open(CACHE_NAME).then(function(cache) {
                                cache.put(request, response);
                            });
                        }
                    }).catch(function() {
                        // Network failed, but we have cache
                    });
                    return cachedResponse;
                }
                
                // Not in cache, fetch from network
                return fetch(request)
                    .then(function(response) {
                        if (response.ok) {
                            const responseClone = response.clone();
                            caches.open(CACHE_NAME).then(function(cache) {
                                cache.put(request, responseClone);
                            });
                        }
                        return response;
                    })
                    .catch(function(error) {
                        console.log('[ServiceWorker] Fetch failed:', error);
                        // Return offline placeholder for images
                        if (request.destination === 'image') {
                            return new Response('', {
                                status: 404,
                                statusText: 'Offline'
                            });
                        }
                    });
            })
    );
});

// Background Sync for Attendance
self.addEventListener('sync', function(event) {
    console.log('[ServiceWorker] Sync event:', event.tag);
    
    if (event.tag === 'sync-attendance') {
        event.waitUntil(syncAttendance());
    }
});

function syncAttendance() {
    // Get pending attendance data from IndexedDB
    // This would require implementing IndexedDB storage
    console.log('[ServiceWorker] Syncing attendance data');
    
    // In a full implementation, you would:
    // 1. Read pending attendance from IndexedDB
    // 2. Send each record to the server
    // 3. Remove successfully synced records
    // 4. Keep failed records for retry
    
    return Promise.resolve();
}

// Push Notifications (for future implementation)
self.addEventListener('push', function(event) {
    console.log('[ServiceWorker] Push received');

    const options = {
        body: event.data ? event.data.text() : 'New notification',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'view',
                title: 'View'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('EduTrack Pro', options)
    );
});

// Notification Click Handler
self.addEventListener('notificationclick', function(event) {
    console.log('[ServiceWorker] Notification click received');
    
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/notifications/')
        );
    }
});

// Message Handler
self.addEventListener('message', function(event) {
    console.log('[ServiceWorker] Message received:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

console.log('[ServiceWorker] Service Worker loaded');
