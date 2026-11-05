
/**
 * ZISAI Article Views
 * 紫塞网文章阅读量统计
 *
 * Hugo + Cloudflare Workers + D1
 *
 * 功能：
 * 1. 自动记录文章阅读量
 * 2. 浏览器端30分钟辅助去重
 * 3. 从API读取累计阅读量
 * 4. 阅读量显示在作者前面
 * 5. 统一元信息分隔符与间距
 */

(async () => {
  "use strict";

  const root = document.querySelector(".zisai-views");
  if (!root) return;

  const id = root.dataset.articleId;
  if (!id) return;

  const api =
    "https://api.zisai.com/api/views/" +
    encodeURIComponent(id);

  const output = root.querySelector("#zisai-view-count");

  // ========================================
  // 1. 将阅读量移动到文章元信息区域
  // ========================================

  const meta = document.querySelector(
    ".post-single .post-header .post-meta"
  );

  if (meta) {
    // 定位作者链接
    const author = Array.from(meta.querySelectorAll("a"))
      .find((a) => {
        try {
          return new URL(a.href).pathname === "/about/";
        } catch (_) {
          return false;
        }
      });

    // 恢复内联显示，沿用 PaperMod 元信息样式
    root.style.display = "inline";
    root.style.margin = "0 8px";
    root.style.padding = "0";
    root.style.opacity = "1";
    root.style.fontSize = "inherit";
    root.style.textAlign = "inherit";
    root.style.lineHeight = "inherit";

    // 清除原本附加的隐藏属性
    root.hidden = false;

    if (author) {
      // 阅读量放在作者前
      author.before(root);

      // 统一元信息的文本分隔符
      // 对阅读量前后的文本进行整理
      const prev = root.previousSibling;
      const next = root.nextSibling;

      if (prev && prev.nodeType === Node.TEXT_NODE) {
        prev.textContent =
          prev.textContent.replace(/\s*·\s*$/, "") + " · ";
      } else {
        root.before(document.createTextNode(" · "));
      }

      if (next && next.nodeType === Node.TEXT_NODE) {
        next.textContent =
          " · " + next.textContent.replace(/^\s*·\s*/, "");
      } else {
        root.after(document.createTextNode(" · "));
      }

    } else {
      // 未识别作者时，附加到元信息最后
      meta.append(
        document.createTextNode(" · "),
        root
      );
    }

    // 统一阅读量内部文字间距
    root.style.whiteSpace = "nowrap";
    // 阅读量模块左右各留 8px 间距
    root.style.marginLeft = "8px";
    root.style.marginRight = "8px";

  } else {
    // 找不到文章元信息时保持在原位置
    root.hidden = false;
  }

  // ========================================
  // 2. 查询阅读量
  // ========================================

  async function displayViews() {
    const response = await fetch(api, {
      method: "GET",
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(
        `Views API GET failed: ${response.status}`
      );
    }

    const data = await response.json();

    if (output) {
      output.textContent =
        Number(data.views || 0).toLocaleString("zh-CN");
    }
  }

  // ========================================
  // 3. 浏览器端30分钟辅助去重
  // ========================================

  const storageKey = "zisai-view-" + id;
  const interval = 5 * 60 * 1000;

  let previous = 0;

  try {
    previous = Number(
      localStorage.getItem(storageKey) || 0
    );
  } catch (_) {
    // 隐私模式或禁用本地存储时忽略
  }

  // ========================================
  // 4. 提交阅读事件
  // ========================================

  if (Date.now() - previous >= interval) {
    try {
      const response = await fetch(api, {
        method: "POST"
      });

      if (!response.ok) {
        throw new Error(
          `Views API POST failed: ${response.status}`
        );
      }

      const result = await response.json();

      if (result.success) {
        try {
          localStorage.setItem(
            storageKey,
            String(Date.now())
          );
        } catch (_) {
          // 忽略存储失败
        }
      }

    } catch (error) {
      console.debug(
        "ZISAI view recording unavailable:",
        error
      );
    }
  }

  // ========================================
  // 5. 显示累计阅读量
  // ========================================

  try {
    await displayViews();
  } catch (error) {
    console.debug(
      "ZISAI view display unavailable:",
      error
    );
  }

})();
