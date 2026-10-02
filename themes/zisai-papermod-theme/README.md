# ZISAI × PaperMod 视觉主题包

这是为 **zisai.com** 定制的 PaperMod 覆盖层（overlay），不是 PaperMod 的 fork。它保留 PaperMod 的文章页、搜索、RSS、SEO、代码块、目录等能力，只重做品牌视觉、首页和公共头部，因此后续仍可以升级 PaperMod。

## 视觉方向

- 主色取自“紫”Logo：深紫 / 洋红 / 暖金，文字使用深靛蓝。
- 首页参考“山河有故事，生活自有光”的构图：透明导航、左侧叙事文案、承德山河大景、底部四篇精选文章卡片。
- Hero 采用本地 SVG 插画：抽象承德山河、磬锤峰、长城、亭阁、湖面，不依赖第三方图库。
- Logo 使用你提供的图形源文件处理为透明 PNG/WebP，并同步生成 favicon.ico。
- 内页仍是 PaperMod 的阅读结构，只统一成更克制的“紫塞”排版和色彩。
- 全部本地资源，无 Google Fonts，兼顾中国大陆访问速度。

## 目录

- `layouts/index.html`：全新首页。
- `layouts/partials/header.html`：PaperMod 旧版/你当前项目可用的 Header 覆盖。
- `layouts/_partials/header.html`：兼容新版 Hugo/PaperMod 的 Header 路径。
- `assets/css/extended/zisai.css`：PaperMod 自动合并的扩展样式。
- `static/images/zisai/`：Logo、Hero 和四张默认栏目图。
- `static/favicon.ico`：由新 Logo 生成。
- `zisai-config-snippet.toml`：建议合并进现有 `hugo.toml` 的参数与菜单。
- `install.ps1` / `install.sh`：自动复制并先备份同名文件。

## 安装到你当前的 Mythflair/mythflair.github.io

你的仓库当前已经是 `theme = "PaperMod"`，无需更换主题，也无需动 `themes/PaperMod` 子模块。

### Windows PowerShell

把本主题包解压到任意目录，然后在主题包目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -SiteRoot "D:\你的\mythflair.github.io"
```

### macOS / Linux

```bash
./install.sh /path/to/mythflair.github.io
```

脚本会把被覆盖的文件保存到站点根目录的 `.zisai-theme-backup-时间戳/`。

然后把 `zisai-config-snippet.toml` 中的配置合并进你已有的 `hugo.toml`。重点是：

1. `[params.profileMode] enabled = false`，否则旧的个人 Profile 首页配置没有意义；
2. 用推荐的 6 个导航项替换现有 `menu.main`；
3. `[params.zisai]` 可随时修改首页标题、介绍和右上角文案。

本地预览：

```bash
hugo server -D
```

构建：

```bash
hugo --minify
```

## 文章封面规则

首页前四篇文章优先使用文章 front matter 中 PaperMod 已支持的 `cover.image`：

```yaml
cover:
  image: "/images/posts/example.webp"
  alt: "文章封面"
```

如果文章没有 `cover.image`，主题会自动按顺序使用四张内置承德风格 SVG，不会出现空白卡片。

## 建议的下一步资源替换

目前 Hero 和默认卡片是轻量 SVG 视觉资产，优势是加载快、统一、无需版权图库。以后若你希望进一步接近效果图，可把：

- `static/images/zisai/hero-chengde.svg`
- `card-resort.svg`
- `card-mountain.svg`
- `card-temple.svg`
- `card-greatwall.svg`

直接换成同文件名 WebP/JPG，并同时在 `layouts/index.html` / CSS 中改扩展名即可。建议 Hero 1920×1080、WebP 质量 75–82，单张控制在约 400 KB 内；卡片建议 800×450，单张尽量控制在 120 KB 内。

## 回滚

删除本次新增的覆盖文件，然后把 `.zisai-theme-backup-时间戳/` 中的文件复制回原位置即可。PaperMod 子模块本身没有被修改。
