# 紫塞网综合评价（2026-10-31，含 ESA 缓存规则复核）

评测对象：`https://zisai.com/`（含 `www.zisai.com`、`esa.zisai.com`、`zisai.net`）与当前仓库。
背景：站点刚接入阿里云 ESA 边缘加速，并配置了一条名为「Hugo HTML Cache」的缓存规则。

> 本版修正：上一版把测试机出口误判为境外。实际测试机在**河北承德联通**，系统装有 `127.0.0.1:7897` 代理，走 `urllib` 的请求被代理带到欧洲节点；本版时延一律改为**绕过代理的直连 socket 测量**。

---

## 一句话结论

方向对，但**三个环节各漏了一层**：主域 DNS 把大陆用户送到巴黎节点、边缘 TTL 只有 5 分钟、回源还在 GitHub 欧洲。ESA 本身没问题，问题在接入方式与缓存规则。

综合评分 **7.6 / 10**；ESA 配置单项 **5.5 / 10**。

---

## 一、评测方法与边界

- 直连 socket（不走系统代理）测 TCP/TLS/TTFB；分别命中 ESA 北京节点（`61.240.144.x`）与主域 anycast（`163.181.214.1`）。
- 对照 GitHub Pages 源站（直连 `185.199.108.153`，SNI/Host 为 `zisai.com`）区分「源站策略」与「ESA 改写」。
- 多公共 DNS（阿里 DoH、DNSPod、Google）核对解析结果。
- 本地仓库与构建产物核对：1,510 个 HTML、4,712 个文件、244 MB。
- **未做**：真实浏览器 Lighthouse/Core Web Vitals、WAF/DDoS 实拦验证、渗透测试、多省节点矩阵。

测试机：河北承德联通（`110.245.39.93`），到北京 ESA 节点 RTT 约 15 ms——这是一个真实的大陆读者视角。

---

## 二、站点画像

| 项目 | 现状 |
| --- | --- |
| 中文文章 | 104 篇，全部有日期，最近 2026-10-30 |
| 平均篇幅 | 约 2,525 字符 |
| 分类 | 生活 43、技术 31、承德 14 |
| 遗址档案 | 9 组，含来源栏与「待核实」标注 |
| 多语言 | 英/日各 8 篇精选译文，hreflang 与分语言 sitemap 完整 |
| 检索订阅 | 站内搜索、RSS、`llms.txt`、PWA manifest |
| 第三方依赖 | 无统计、无广告、无评论、无外部字体/脚本 |

架构：

```
Cloudflare DNS
   ├─ zisai.com       A 163.181.214.1     ← 阿里云国际 anycast（实测落到巴黎）
   ├─ www.zisai.com   CNAME initbb.com    → 61.240.144.x 北京联通
   └─ esa.zisai.com   CNAME initbb.com    → 61.240.144.x 北京联通（ESA 默认测试域，公开可访问）
            ↓
       阿里云 ESA（TLS、缓存、安全）
            ↓ 回源
       GitHub Pages（Fastly；x-github-edge-region: fra / switzerlandnorth）
```

---

## 三、ESA 实测

### 3.1 生效证据

| 证据 | 观测 |
| --- | --- |
| 响应头 | `Server: ESA`、`EagleId`、`Ali-Swift-*`、`X-Site-Cache-Status` |
| ESA 错误页 | `http://www.zisai.com/` 的 301 页面底部 `Powered by ESA` |
| Cookie | `cdn_sec_tc`（HttpOnly，1 小时） |
| 证书 | Let's Encrypt，主域与 www 各自独立；TLS 1.3 正常，TLS 1.2 回退正常 |
| 缓存 | 同一 URL 连续请求：`MISS → HIT`，`X-Swift-CacheTime: 300` |

### 3.2 关键发现

| # | 发现 | 证据 | 影响 |
| --- | --- | --- | --- |
| 1 | **主域 DNS 把大陆用户送到巴黎** | 承德联通直连 `163.181.214.1`：TCP 231 ms、TTFB 448 ms，`Via: ens-cache9.fr4`（巴黎）；而 www/esa 的 CNAME 落到北京联通：TCP 15 ms、HIT TTFB 40 ms | 规范域名（主域）走的是最慢的那条路，ESA 的大陆节点等于没用上 |
| 2 | **缓存规则实际覆盖全站，不只是 HTML** | 规则条件只有主机名；实测 CSS、图片、`index.json` 全部返回 `max-age=60` | 指纹化的静态资源也被 1 分钟浏览器 / 5 分钟边缘缓存，完全浪费 |
| 3 | **TTL 比源站更短** | 源站直连 `max-age=600`；经 ESA 变 `max-age=60`；`X-Swift-CacheTime: 300` 与规则里的「5 分钟」完全对应 | 低流量站每个边缘节点 5 分钟就过期，冷启动回源比例高 |
| 4 | **HTTP/2 未启用** | ALPN 只给 `h2` → `no application protocol`；给 `h2,http/1.1` → 选 `http/1.1` | 首屏 15+ 资源受 6 连接上限与队头阻塞限制 |
| 5 | **Brotli 未启用且不降级** | `br` → 不压缩（28,946 B）；`br,gzip` → gzip（8,821 B）；`zstd` → 不压缩 | 文本多传 10–15% |
| 6 | **主域 80 端口无响应** | `zisai.com:80` TCP 超时；`www:80` 正常 301 | 手输域名且未自动升级 HTTPS 时会一直转圈 |
| 7 | **www 到主域两跳** | `http://www` → `https://www` → `https://zisai.com` | 多一次 RTT |
| 8 | **无任何安全头** | 无 HSTS / XCTO / CSP / Referrer-Policy / Permissions-Policy | 已上边缘却把最容易统一加的防护留空 |
| 9 | **每个响应 Set-Cookie** | `cdn_sec_tc`，无 `Secure`/`SameSite`，HTTP 响应也下发 | 静态站不需要会话 Cookie |
| 10 | **`esa.zisai.com` 公开可访问** | 返回 200，内容与主站一致，同样可被搜索引擎抓取 | 重复内容；且绕过基于主机的规则 |
| 11 | **`zisai.net` HTTPS 不可用** | `http` 正常 301 到主域；`https` TLS 握手超时 | 旧域名/书签访问失败（也需排除本机网络因素） |

### 3.3 缓存规则逐项点评（截图配置）

当前规则「Hugo HTML Cache」：

- 条件：`http.host in {"esa.zisai.com" "zisai.com"}`
- 缓存资格：符合缓存条件
- 浏览器缓存：忽略源站，**1 分钟**
- 边缘缓存：忽略源站，**5 分钟**

问题：

1. **名不副实**：名字叫 HTML 缓存，但条件里没有路径/后缀，等于给整站套了 1 分钟 / 5 分钟。CSS、图片、`index.json`、`robots.txt` 全部中招。
2. **1 分钟浏览器 TTL 太短**：回访用户每分钟对每个资源做一次条件请求；虽有 ETag 304 兜底，但平白多出 RTT。
3. **5 分钟边缘 TTL 太短**：`X-Swift-CacheTime: 300` 就是它。个人站流量低，单个 POP 五分钟内往往只见到一次同一 URL，统计上有命中，体验上接近每次回源（实测北京节点 MISS 450 ms，命中 40 ms）。
4. **主机名列表**：缺 `www.zisai.com`（影响小，www 只做 301）；多了 `esa.zisai.com`（ESA 默认测试域，当前公开可访问，建议限制访问或直接停用）。
5. **没有区分资源类型**：指纹资源（`stylesheet.<hash>.css`、`*_hu_<hash>.webp`）本可以缓存一年，却和 HTML 同等待遇。

建议拆成两条规则（顺序：资源规则在前，或给 HTML 规则加排除条件）：

| 规则 | 匹配 | 浏览器 TTL | 边缘 TTL | 备注 |
| --- | --- | --- | --- | --- |
| 静态资源 | 路径前缀 `/assets/`、`/images/`、`/icons/`，或后缀 `.css/.js/.webp/.png/.woff2` | **1 年** | **30 天** | 文件名含内容哈希，改内容即改 URL，可放心长缓存 |
| HTML 与文本 | 其余路径（`/`、`/posts/*`、`/*.xml`、`*.json`、`*.txt`） | **10 分钟** | **1 小时** | 发布后按 URL/目录刷新，或接受最多 1 小时延迟 |

其他建议：

- **边缘状态码缓存**：404 设 1 分钟，5xx 不缓存。
- **自定义 CacheKey**：静态站可忽略全部 query，提高命中率。
- **响应过期缓存**：开启。GitHub Pages 从大陆偶发不可达时，ESA 仍能用旧副本兜底。
- **缓存保持**：若有此能力建议开启，跨 POP 共享，进一步减少回源。
- **POST 缓存**：保持关闭。
- `/sw.js` 与 manifest 不要套长缓存（Service Worker 更新会被拖住）。

### 3.4 时延账本（直连，承德联通 → ESA）

| 场景 | TCP | TLS | TTFB | 总耗时 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 主域现状（→ 巴黎） | 231 ms | 230 ms | **448 ms** | — | 命中也要跨洲 |
| 北京节点 · HTML 命中 | 15 ms | 30 ms | **40 ms** | 105 ms | ESA 应有的水平 |
| 北京节点 · HTML 未命中 | 15 ms | 22 ms | **450 ms** | 491 ms | 回源 GitHub 欧洲 |
| 北京节点 · CSS 未命中 | 14 ms | 29 ms | 702 ms | 757 ms | 冷缓存 |
| 北京节点 · hero 未命中 | 15 ms | 30 ms | 786–1001 ms | **1.9–2.6 s** | 421 KB 跨境传输 |

结论：**DNS 线路决定了「命中也要 448 ms」，缓存 TTL 决定了「多久要重新吃一次 450 ms + 2 秒」**。两者叠加，才是「上了 ESA 但没觉得快」的原因。

---

## 四、性能账本

| 资源 | 大小 | 说明 |
| --- | --- | --- |
| HTML 首页 | 8,821 B gzip / 28,946 B 原始 | 结构干净，无外部请求 |
| CSS | 10,748 B gzip / 49,712 B 原始 | 单文件、已指纹、无 `@font-face` |
| Hero | 157,880 / 265,660 / **421,606 B** | 移动 / 平板 / 桌面；桌面端 LCP 风险 |
| Logo | 14,846 B | 正常 |
| 首屏卡片 ×2 | 32,050 + 4,250 B | 正常 |
| `favicon.png` | **88,506 B** | 图标不该接近 90 KB |
| `favicon.ico` | **141,178 B** | 且被 gzip（对已压缩格式无意义） |
| `index.json` | 335,169 B gzip（约 840 KB 原始） | 仅搜索页加载 |

桌面首屏约 **492 KB**，移动端约 **229 KB**。421 KB 的 hero 在跨境回源时实测 1.9–2.6 秒，是当前最大的单点性能问题。

---

## 五、SEO 与可发现性

做得好的：

- canonical 唯一；`hreflang` 覆盖 `zh-CN / en-US / ja-JP / x-default`。
- sitemap index → 224 / 20 / 20 条，`/zh-cn/sitemap.xml` 实际可访问。
- `robots.txt` 允许 Googlebot 与 Google-Extended；`llms.txt` 对 AI 检索友好。
- JSON-LD 完整（WebSite + Person + Organization），`sameAs` 齐备。
- 404 返回真 404；标签有核心标签门槛。

小问题：

- `<meta name="author">` 带换行（`content="\n\n\n\n\n\n沈楠"`）。
- `og:title`「紫塞」与 `<title>`「紫塞 · 承德城市记忆与技术随笔」不一致。
- `manifest` 的 `theme_color` 是 `#ffffff`，页面 `theme-color` 是 `#7b167c`。
- `esa.zisai.com` 与主站内容相同且可公开访问，存在重复内容风险。
- `zisai.net` HTTPS 状态不明。

---

## 六、安全与合规

- 正面：全站 HTTPS、TLS 1.3、证书自动签发、无第三方跟踪、评论关闭、无表单收集。
- 缺口：无 HSTS、无 `X-Content-Type-Options`、无 CSP、无 `Referrer-Policy`、无 `Permissions-Policy`；ESA 安全 Cookie 未加 `Secure`/`SameSite`。
- **备案**：www 与 esa 走北京联通节点，若开通的是中国大陆加速，按规定需 ICP 备案并在页脚展示备案号；当前页面未发现。需你确认，外部探测无法下结论。
- `zisai.net` 建议明确「保留并修好」或「下掉」。

---

## 七、内容与产品

优点：

- 定位清晰：「承德 + 城市记忆 + 技术随笔 + 旧站档案」，不是泛技术博客。
- 长期主义：1998 年起点、遗址栏目、来源与核实时间标注，史料意识罕见。
- 三语是真本地化，不是机翻摆设。
- 阅读体验克制：无广告、无弹窗、无统计。

可提升：

- 承德题材约 14 篇，足以做「承德记忆」专题/时间线/地图，目前仍是普通分类列表。
- 现场照片建议统一图注（时间、地点、拍摄者）。
- 英/日各 8 篇，长期看语言版本偏薄。
- 无评论可以理解，但建议加「勘误/邮件反馈」入口，遗址类尤其需要。

---

## 八、评分

| 维度 | 权重 | 得分 | 依据 |
| --- | --- | --- | --- |
| 内容价值 | 25% | 8.5 | 27 年个人站延续、地方记忆、持续更新 |
| 架构与工程 | 15% | 8.5 | Hugo + CI + 检查器 + 零第三方依赖 |
| 性能 | 20% | 6.0 | 结构优秀，但 hero 421 KB、无 h2/br、TTL 过短 |
| SEO | 15% | 8.5 | canonical/hreflang/sitemap/JSON-LD/llms.txt 齐备 |
| 安全与合规 | 10% | 5.5 | TLS 好，安全头与备案缺失 |
| 运维与文档 | 10% | 7.5 | 流程完整，但缓存文档仍是 Cloudflare、域名状态不清 |
| 设计与可达性 | 5% | 7.5 | 视觉统一、alt 全覆盖；无 skip link |
| **加权** | 100% | **7.6** | |

ESA 配置单项 **5.5 / 10**：接入了，但线路、TTL、协议、压缩四项都没按静态站最佳实践设置。

---

## 九、行动清单

### P0（今天，收益最大）

1. **修主域 DNS**：把 `zisai.com` 的 A 记录改为 ESA 提供的 CNAME（Cloudflare 会自动拉平），让大陆用户落到北京/就近节点。
   - 预期：TCP 231 ms → 15 ms，命中 TTFB 448 ms → 40 ms。
   - 若需要海外用户也快，改用阿里云解析做分线路（境内 → initbb CNAME，境外 → 国际 anycast）。
2. **拆分缓存规则**（见 3.3 表）：资源 1 年 / 30 天，HTML 10 分钟 / 1 小时，发布后刷新。
3. **开启 HTTP/2**，顺手确认 `alt-svc: h3` 是否真的可用（现在 h2 都没有）。
4. **开启 Brotli**。

### P1（本周）

5. **重压 hero**：421 KB → ≤160 KB（质量 62–68、最大宽 1920），加 `fetchpriority="high"`；移动端 ≤70 KB。
6. **修图标**：`favicon.png` → 5 KB 内，`favicon.ico` → 32×32 几 KB，停止 gzip ico。
7. **补 80 端口与单跳重定向**：`zisai.com:80` 必须 301 到 `https://zisai.com/`；`http://www` 直接 301 到主域。
8. **开 HSTS**（先 300 秒，再逐步加到一年）。

### P2（本月）

9. 统一安全头（XCTO、Referrer-Policy、Permissions-Policy，再评估 CSP）。
10. `cdn_sec_tc` 加 `Secure; SameSite=Lax`；未启用 CC 防护则关闭。
11. 限制或停用 `esa.zisai.com`；决定 `zisai.net` 去留。
12. 核实 ICP 备案号（若走大陆节点）。
13. 把 `docs/cache-and-reader-services.md` 从 Cloudflare 规则改写为 ESA。
14. 评估把源站迁到阿里云 OSS（境内/香港），冷回源从「跨境 450 ms + 2 秒」降到「同域几十毫秒」。
15. 内容侧：承德专题页/时间线、图注规范、勘误入口。
16. 清理模板细节：`meta author` 空白、`og:title`、`theme-color` 统一。

---

## 十、复测方法（务必绕过本机代理）

```bash
# 本机装有 127.0.0.1:7897 代理，测试时必须加 --noproxy
curl --noproxy '*' -sI https://zisai.com/ | grep -iE 'server|cache-control|via|age'
curl --noproxy '*' -sI --http2 https://zisai.com/ | head -1
curl --noproxy '*' -sI http://zisai.com/ | head -3
curl --noproxy '*' -sI https://zisai.com/ | grep -iE 'strict-transport|content-security|x-content-type|referrer-policy'

# 连续两次看缓存状态与节点
for i in 1 2; do curl --noproxy '*' -sI https://zisai.com/ | grep -iE 'x-site-cache-status|x-swift-cachetime|via'; done

# 对比北京节点与主域 anycast
curl --noproxy '*' -sI --resolve zisai.com:443:61.240.144.178 https://zisai.com/ | grep -i via
```

建议再用 17CE/站长工具从北京、上海、广州、成都各测 3 次，看 `time_starttransfer`、`X-Site-Cache-Status` 与 `Via` 里的节点。

---

## 附：关键响应头摘录

**主域（`163.181.214.1`，直连巴黎节点）**

```
Server: ESA
Cache-Control: max-age=60
Via: 1.1 varnish, ens-cache9.fr4[6,0,DP], ens-cache9.fr4[5,6,200-0,H], ...
X-Site-Cache-Status: REVALIDATED
X-Swift-CacheTime: 300
```

**北京节点（`61.240.144.178`，Host: zisai.com）**

```
HTTP/1.1 200 OK
Cache-Control: max-age=60
Via: 1.1 varnish, ens-cache2.cn8638[529,0,DP], ens-cache2.cn8638[0,0,200-0,H], ...
X-Site-Cache-Status: HIT
X-Swift-CacheTime: 300
```

**GitHub Pages 源站（同一对象）**

```
Server: GitHub.com
Cache-Control: max-age=600
Expires: Sat, 31 Oct 2026 05:59:52 GMT
Content-Encoding: gzip
X-GitHub-Edge-Region: fra
```

对照可确认：`max-age=60` 与 `X-Swift-CacheTime: 300` 均来自 ESA 规则，不是源站策略。
