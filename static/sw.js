
const CACHE_NAME = "zisai-pwa-v1.1";
const CACHE_PREFIX = "zisai-pwa-";

const PRECACHE = [
  "/offline.html",
  "/manifest.webmanifest",
  "/icons/pwa-192.png",
  "/icons/pwa-512.png"
];

// 安装：只预缓存最基础的资源
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

// 激活：清理旧版紫塞 PWA 缓存
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) =>
            key.startsWith(CACHE_PREFIX) &&
            key !== CACHE_NAME
          )
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

// 请求处理：网络优先，离线时尝试缓存
self.addEventListener("fetch", (event) => {
  const request = event.request;

  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // 不处理第三方域名
  if (url.origin !== self.location.origin) return;

  // 页面导航
  if (request.mode === "navigate") {
    event.respondWith(
      (async () => {
        try {
          const response = await fetch(request);

          if (!response.ok && response.status >= 500) {
            const cached = await caches.match(request);
            return cached || response;
          }

          return response;
        } catch (error) {
          const cached = await caches.match(request);

          if (cached) return cached;

          const offline = await caches.match("/offline.html");

          if (offline) return offline;

          return Response.error();
        }
      })()
    );

    return;
  }

  // 其他同源资源：网络优先
  event.respondWith(
    fetch(request).catch(async () => {
      const cached = await caches.match(request);
      return cached || Response.error();
    })
  );
});
