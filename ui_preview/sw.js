// DunhuangGold MES - Service Worker (PWA)
// 策略: stale-while-revalidate
//   - HTML: network-first(保证内容新鲜), 失败回 cache
//   - 静态资源 (JS/CSS/图片): cache-first, 后台更新
//   - API GET: network-first, 失败回 cache
//   - API POST: network-only(写操作不入缓存)

const CACHE_NAME = 'dunhuang-mes-v9';  // 递增失效旧缓存
// v1: 初始
// v2: 改字号 + KPI 132px
// v3: 字号阶 + 间距阶 + 按钮 + 表格
// v4: 侧栏 v3(字号回退,240 宽)
// v5: 字体规范(16px body + Tailwind 默认字号阶)
// v6: 侧栏分类栏加大(11→15px)
// v7: 继续加大(15→17px) + 菜单名 14→16px
// v8: 分类栏文字贴左(padding-left 12→6)
// v9: 收藏夹/最近访问格式完全统一(同色去 emoji)
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
    '/assets/js/export.js',
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
