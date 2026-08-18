// DunhuangGold MES - Service Worker (PWA)
// 策略: stale-while-revalidate
//   - HTML: network-first(保证内容新鲜), 失败回 cache
//   - 静态资源 (JS/CSS/图片): cache-first, 后台更新
//   - API GET: network-first, 失败回 cache
//   - API POST: network-only(写操作不入缓存)

const CACHE_NAME = 'dunhuang-mes-v1';
const PRECACHE = [
    '/',
    '/index.html',
    '/manifest.json',
    '/assets/css/common.css',
    '/assets/js/api.js',
    '/assets/js/renderers.js',
    '/assets/js/app.js',
    '/assets/js/shortcuts.js',
    '/assets/js/beautify.js',
    '/pages/page_dashboard.html',
    '/pages/page_bigscreen.html',
    '/pages/page_loss_monitor.html',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        ).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    if (url.origin !== location.origin) return;

    // POST/PUT/DELETE → network only
    if (event.request.method !== 'GET') {
        return;
    }

    // HTML 页面 → network first, 失败回 cache
    if (event.request.mode === 'navigate' || event.request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(
            fetch(event.request)
                .then((res) => {
                    const copy = res.clone();
                    caches.open(CACHE_NAME).then((c) => c.put(event.request, copy));
                    return res;
                })
                .catch(() => caches.match(event.request).then((r) => r || caches.match('/')))
        );
        return;
    }

    // API GET → network first
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request)
                .then((res) => {
                    const copy = res.clone();
                    caches.open(CACHE_NAME).then((c) => c.put(event.request, copy));
                    return res;
                })
                .catch(() => caches.match(event.request))
        );
        return;
    }

    // 静态资源 → cache first, 后台更新
    event.respondWith(
        caches.match(event.request).then((cached) => {
            const network = fetch(event.request).then((res) => {
                const copy = res.clone();
                caches.open(CACHE_NAME).then((c) => c.put(event.request, copy));
                return res;
            }).catch(() => cached);
            return cached || network;
        })
    );
});
