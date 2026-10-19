# 紫塞技术审计

审计日期：2026-10-19。范围为当前本地仓库、部署工作流及本次生成的静态产物。未修改站点实现或发布网站。

## 结论

Hugo + PaperMod 的静态架构适合当前网站，无证据表明需要重构。本轮确认了输出路径冲突、缺失图标和评论主题状态不一致等问题。另需核对 private 目录中文章的公开意图。

## 方法与结果

- 使用仓库 Hugo 0.167.0，运行 `--destination .codex-preview/audit --printI18nWarnings --printPathWarnings --logLevel warn`；三语构建成功，出现一项重复输出路径警告，无翻译缺失警告。首次沙箱内启动遇到 DLL 错误，在批准的环境中重试成功，不能据此认定站点构建有问题。
- 解析生成目录中 1,463 个 HTML 文件（含别名跳转页、离线页和验证文件），检查 a[href]、img/script/source/video[src]、主要资源链接、站内锚点、canonical 数量及 JSON-LD 语法。
- 唯一缺失的已扫描本地资源目标是 `/safari-pinned-tab.svg`，被 849 个页面引用；未发现已扫描范围内的失效站内正文链接、锚点、无效 JSON-LD 或 HTTP 脚本/图片引用。
- 非跳转文件中，offline.html 和百度验证文件没有 canonical，属于用途正常的例外。
- 首页 Hero 原图约 182 KB，CSS 产物约 48 KB，中文搜索 JSON 约 835 KB，均为未压缩传输前的文件大小；不等同于实际网络传输量或加载时间。
- CSS/搜索脚本启用资源指纹；缩略图生成多个宽度的 WebP；MathJax 按文章参数加载。
- Service Worker 仅预缓存离线页、manifest 和两个图标；导航及其他同源资源网络优先，不写入文章运行时缓存。本轮未发现由该实现长期锁定旧文章的机制，但其离线能力也主要限于兜底页。

## 发现及优先级

### 需先核对：private 目录中的文章实际公开

证据：`content/private/philosophical_reflections.markdown` 设置 `draft: false`，生成 `/private/philosophical_reflections/index.html`，且进入中文搜索索引、RSS 和中文 sitemap。

影响：如果 private 表示不公开，当前行为不符合预期；若文章本来就公开，则只是目录命名容易误导。没有根据目录名直接认定为敏感信息泄露。

建议：先确认公开意图。需要私密的资料应移出公开源码及发布产物，并使用真正的访问控制；仅设置 noindex 或隐藏列表不构成保密措施。已经发布的内容还需考虑旧部署与缓存。

### P2：两个内容源竞争生成 /archives/index.html

证据：构建警告 `Duplicate target paths: \\archives\\index.html (2)`。`content/archive.md` 显式指定 `/archives/` 与 archives 布局；`content/archives/_index.md` 又定义同路径 section。

影响：同一个文件有两个生成来源，归档内容和元数据的最终结果缺乏唯一性；部署目前不会因该警告失败。

建议：保留唯一归档内容源，明确归档布局，并在 CI 加入路径冲突检查。修复后检查归档内容、canonical、robots 和 sitemap。

### P2：评论区与站点主题偏好不一致

证据：`layouts/_partials/header.html` 使用 `pref-theme` 保存偏好；`layouts/_partials/comments.html` 读取 `theme`，并只在创建 Utterances 时设置主题。站点主题切换函数没有通知评论 iframe。

影响：用户手选深浅色后，评论可能仍随系统偏好或旧状态显示；即时切换也不会同步评论。

建议：统一主题状态来源，并在评论载入和用户切换主题时同步。评论脚本读取 localStorage 也应像 header 一样处理存储访问异常。

### P3：全站输出不存在的 Safari mask icon

证据：`layouts/_partials/head.html` 无条件回退到 `safari-pinned-tab.svg`，但文件不存在；本次产物 849 页引用该目标。

影响：支持该功能的客户端可能请求不存在的资源；不影响正文浏览。

建议：提供有效的单色 SVG，或仅在明确配置该资源时输出 mask-icon 链接。

### P3：部署前缺少自动质量门槛

证据：`.github/workflows/deploy.yml` 只在 main push 后构建并部署；构建命令没有启用路径警告，没有 PR 验证或链接检查步骤。因此本轮路径冲突仍可通过现有部署。

建议：增加 PR 构建及针对路径冲突、站内资源的检查；先消除当前警告再决定是否将所有警告升级为失败。部署任务增加 concurrency，避免多个 main 提交的部署并行竞争；其实际发生情况本轮未验证。

## 维护建议

- 自定义 head、header、footer 等覆盖了主题的重要逻辑。升级 PaperMod 时核对覆盖文件与上游差异，避免仅更新子模块而遗漏兼容调整。
- 首页资源规模没有显示明显异常，但中文搜索索引在较慢网络下值得测量；无需凭文件大小立即重写搜索。
- 第三方广告、统计、评论会影响真实加载表现，实际收益应通过浏览器测量再判断。

## 边界

这是代码与构建产物审计，不是渗透测试。未验证线上 Cloudflare/DNS/TLS、响应头、重定向、CDN 缓存规则、GitHub 权限和部署运行历史；未运行手机浏览器交互、Lighthouse 或真实网络性能测量。链接扫描不包含外部链接可用性、CSS url、srcset 全量候选及 JavaScript 动态请求。JSON-LD 仅验证可解析，不代表搜索引擎富结果资格。本轮未执行完整 Git 历史密钥扫描，不能据此承诺不存在凭据泄露。

检查脚本与详细结果保留于被 Git 忽略的 `.codex-preview/audit_scan.py`、`.codex-preview/audit-results.json`，构建产物位于 `.codex-preview/audit/`。

## 修复记录

按用户确认，private 文章允许公开，保留原路径和发布状态。

- 删除冲突的 `content/archive.md`，由 `content/archives/_index.md` 唯一提供 `/archives/`，显式使用现有 archives 布局，继续按年份展示 `archived: true` 的故事文章。
- 关闭全站 comments，并清空评论覆盖模板，移除 Utterances 接入；即使单篇文章设 comments，也不会加载留言服务。
- Safari mask-icon 改为仅在配置资源时输出。现有 favicon 和 Apple touch icon 继续工作，不再请求缺失 SVG。
- CI 增加 PR 验证、警告即失败的三语构建、标准库站内链接与资源检查、JSON-LD 检查和检查器回归用例。支持手动运行；主分支验证成功后部署同一份产物。构建任务只读权限，只有部署任务拥有 contents write 权限，并发提交取消旧任务。
- 可复用检查器位于 `scripts/check_site.py`，增加 srcset 候选、视频封面及 iframe/audio 引用检查；不验证外链可用性或 CSS 内部资源引用。

验证：修复后的 Hugo minify 构建通过，开启 `--printI18nWarnings --printPathWarnings --panicOnWarning` 无警告；全站 1,463 个 HTML 文件检查通过。生成 HTML 中不再包含 Utterances 或缺失 Safari SVG 的引用。线上 GitHub Actions 尚需提交后实际运行验证。
