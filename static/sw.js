const CACHE_NAME = "zisai-pwa-v1";

const PRECACHE = [
  "/",
  "/manifest.webmanifest",
  "/icons/pwa-192.png",
  "/icons/pwa-512.png"
];

// 安装：缓存基本资源
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE))
  );
  self.skipWaiting();
});

// 激活：清理旧版本缓存
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key.startsWith("zisai-pwa-") && key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// 请求：网络优先，失败后尝试缓存
self.addEventListener("fetch", (event) => {
  const request = event.request;

  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // 只处理紫塞自身的资源
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});