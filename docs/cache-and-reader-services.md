# 缓存、统计与读者服务接入

## 当前状态

GA4 与 AdSense 已移除。Umami 和邮件订阅配置默认关闭；没有假订阅表单。GitHub Actions 仍发布到 GitHub Pages，未修改 DNS 或线上 Cloudflare 规则。

## Cloudflare 缓存规则

在实际代理本网站的 zone 创建 Cache Rule（只替换为该 zone 的真实主机名；zisai.com 和 zisai.net 若分属两个 zone，应分别配置）：

```text
(http.host in {"zisai.com" "www.zisai.com"}
 and http.request.method in {"GET" "HEAD"}
 and http.cookie eq ""
 and not any(http.request.headers["authorization"][*] ne "")
 and not starts_with(http.request.uri.path, "/private/")
 and not starts_with(http.request.uri.path, "/api/")
 and not starts_with(http.request.uri.path, "/cdn-cgi/")
 and http.request.uri.path ne "/sw.js")
```

设置：Eligible for cache；Edge TTL：Ignore cache-control header and use this TTL，3600 秒；Browser TTL：Respect existing headers。检查规则顺序，避免后续规则覆盖。上线后清除旧 HTML 缓存，更新文章后按 URL purge 或等待一小时。不要把此规则直接套在今后新增的登录、用户数据或表单处理服务上。

该配置由 Cloudflare 控制台生效，仓库文件不会自动设置线上 CDN。主机名必须处于代理状态。用两次请求同一篇文章检查 `CF-Cache-Status`、`Age` 和实际 `time_starttransfer`；区分冷缓存与热缓存，从大陆网络重复测量，不能预先承诺几百毫秒。

官方说明：
- https://developers.cloudflare.com/cache/how-to/cache-rules/examples/cache-everything/
- https://developers.cloudflare.com/cache/how-to/cache-rules/settings/

## 自托管 Umami

部署可从大陆正常访问的 Umami 服务，创建网站后，在 hugo.toml 填写已有的 `[params.umami]`：

```toml
scriptURL = "https://YOUR-ANALYTICS-HOST/script.js"
websiteID = "YOUR-UMAMI-WEBSITE-ID"
```

只有两项都填写时才输出 defer 脚本，尊重 Do Not Track。统计数据发送给该 Umami 服务；不要把接收端 `/api/` 放进 HTML 缓存规则。验证跨域配置、两个域名的收集行为、实际统计入库与大陆可达性后再判断是否恢复数据。检查部署的统计功能和面向读者的隐私说明；不要收集邮件地址等个人信息到分析事件。

官方说明：https://docs.umami.is/docs/tracker-configuration

## 邮件订阅

在实际邮件订阅服务创建订阅页，启用订阅确认与退订后，将 URL 填入已有 `[params.newsletter]` 的 `url`。三语页脚和文章文末会显示邮件订阅链接。服务未配置时保留 RSS 和邮件交流，不把发邮件给作者描述成订阅成功。

## 标签与文章维护

`data/core_tags.json` 定义 40 个核心标签。只有核心且至少有两篇文章的标签允许索引并进入 sitemap。长尾标签保留旧地址与原文章关联，但 noindex；未直接删掉历史标签。标签目录只显示满足条件的核心标签。更改核心名单后运行 SEO 检查。

首页总数、搜索、归档和 RSS 使用 `article-pages.html` 统一文章集合，文末相关阅读依据 Hugo 的文章相关度；无匹配时显示其他近期文章。

## 档案来源

遗址文章（legacy section 或 legacy: true）自动显示固定来源栏。可在 front matter 添加：

```yaml
archiveSources:
  - label: "原始报道标题 / 发布机构 / 发布日期"
    url: "https://真实来源地址"
  - label: "作者保存的现场照片；形成时间与保管人"
# 只有实际核实来源后才填写，不要使用页面更新日代替：
# verifiedAt: "2026-10-31"
```

尚无来源清单或核实时间时，页面显示待整理、待核实。机构合作尚未开展；遗址首页的资料征集入口只接受线索，不宣称任何机构背书。
