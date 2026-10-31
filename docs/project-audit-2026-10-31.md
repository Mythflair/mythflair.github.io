# 项目检查（2026-10-31）

## 结论

当前项目可完成无警告的三语生产构建，未发现已扫描范围内的失效站内链接、资源引用、锚点或无效 JSON-LD。确认一个本地检查器兼容性问题、一个备用域名配置问题，以及一项结构化数据规范化建议。本轮只检查并记录结果，未修改站点实现或发布网站。

## 发现

### P2：SEO 检查器在当前 Windows 环境默认执行失败

`scripts/check_seo.py:11` 以及第 17、24、26、29 行使用没有显式编码的 `read_text()`。当前 Windows Python 默认 GBK，读取 Hugo 的 UTF-8 产物时抛出 `UnicodeDecodeError`，检查无法完成。使用同一 Python 加 `-X utf8` 后全部通过，说明是检查器编码兼容性问题，不是站点内容损坏。Linux CI 本轮未执行，不据此认定其失败。

建议：所有文本读取显式指定 `encoding="utf-8"`，使本地与 CI 使用相同输入编码。

### P2（备用域名部署时）：robots.txt 的 sitemap 固定指向 zisai.com

`hugo.toml:10` 明确说明 Cloudflare Pages 使用 `--baseURL https://zisai.net/`。但 `static/robots.txt:11` 固定声明 `https://zisai.com/sitemap.xml`；静态文件内容不会随 baseURL 替换。因此备用域名的构建仍会向爬虫声明主域名 sitemap，与各域名自行生成绝对地址的部署方式不一致。主域名构建不受影响。

建议：通过 `layouts/robots.txt` 使用当前站点 BaseURL 生成 sitemap 地址，并处理现有静态文件覆盖；若产品意图是统一主域名，应改为统一的 canonical/重定向策略。未检查备用域名线上实际部署状态。

### P3：作者结构化数据未按配置注释转换为绝对地址

`layouts/_partials/schema-jsonld.html:20` 直接使用配置的 `/about/`，第 21 行生成 `/about/#person`。产物中 192 个 Person 实体声明均使用该相对 ID，Person.url 同样为相对地址。

相对 IRI 本身不构成 JSON-LD 语法错误；这是地址规范化建议。配置注释已要求模板使用 `absURL`，模板尚未落实。建议先将作者 canonical URL 转为绝对地址，再生成 Person ID；同时验证两个域名与三种语言的实体引用一致性。

## 验证记录

- Hugo：项目自带 0.167.0，生产构建命令启用 `--minify --printI18nWarnings --printPathWarnings --panicOnWarning`，通过，无警告。
- 构建输出：中文 1,315 页、英语 94 页、日语 92 页（Hugo 统计口径）；检查器实际解析 1,510 个 HTML 文件，包含静态 HTML 与别名页。
- `python -m unittest discover -s scripts -p 'test_*.py'`：3 项通过。
- `scripts/check_site.py`：1,510 个 HTML 的站内链接、资源、srcset、锚点和 JSON-LD 语法检查通过。
- 额外核对产物路径大小写：未发现 Windows 文件系统掩盖的引用大小写错误。
- `python -X utf8 scripts/check_seo.py`：通过；中文 169 篇文章/224 个 sitemap URL，英文 8/20，日文 8/20；搜索、归档、sitemap 集合一致，检查范围内无广告/Google 统计标记，单页最多一个 H1。
- 搜索 JSON 原始大小：中文 839,970 字节，英文 36,451 字节，日文 44,401 字节；不是实际压缩传输量或性能测试。

产物位于被 Git 忽略的 `.codex-preview/audit-2026-10-31/`。Hugo 在沙箱内遇到 Windows DLL 启动错误，在获准环境中运行成功；不能将环境启动错误视为项目缺陷。使用随环境提供的 Python，未安装额外依赖。

## 检查边界

检查覆盖配置、部署工作流、自定义模板、图片处理、PWA、维护脚本及完整构建产物；主题依赖以集成构建验证为主，并非对每个第三方文件逐行审计。没有运行线上 DNS/TLS/CDN 检查、外链可用性检查、浏览器交互或 Lighthouse；未验证 GitHub Actions 实际运行历史，也未进行完整 Git 历史密钥扫描。资源检查不包含 CSS 内部 url 与 JavaScript 动态请求。JSON-LD 可解析不等于富结果资格通过。

检查期间观察到 `.idea/vcs.xml` 的工作区改动，未修改或回退该文件。

## 修复记录

已根据本报告完成以下修复：

- `scripts/check_seo.py` 的所有 `read_text()` 显式使用 UTF-8，Windows 默认 GBK 环境直接运行通过，无需 `-X utf8`。
- 删除 `static/robots.txt`，新增 `layouts/robots.txt`，保留现有爬虫规则，使用 `absURL` 根据构建 baseURL 生成 sitemap 地址。
- 作者 canonical URL 在生成 Person.url 和 Person ID 前通过 `absURL` 转换，默认值改为 `/about/`，随构建域名解析；三种语言继续共享同一作者实体地址。

修复后验证：

- 分别使用 `https://zisai.com/` 和 `https://zisai.net/` 构建到独立的新目录，均在开启 `--panicOnWarning` 的情况下通过。
- 两份产物各自通过 1,510 个 HTML 的站内链接、资源、锚点和 JSON-LD 检查，以及 SEO 检查。
- 额外检查两份产物的 robots sitemap 地址和各 192 个 Person 实体声明，均为对应域名的绝对地址，覆盖三种语言。
- 现有 3 项回归测试通过，`git diff --check` 通过。

构建产物位于 `.codex-preview/fix-audit-com/` 和 `.codex-preview/fix-audit-net/`。未发布网站，未修改用户的 `.idea/vcs.xml` 改动。
