
(async () => {
  const root = document.querySelector(".zisai-views");
  if (!root) return;
  const meta = document.querySelector(
  ".post-single .post-header .post-meta"
  );

  if (meta) {
    const separator = document.createElement("span");
    separator.textContent = " · ";

    meta.appendChild(separator);
    meta.appendChild(root);

    root.hidden = false;
}

  const id = root.dataset.articleId;
  if (!id) return;

  const api = "https://api.zisai.com/api/views/" +
    encodeURIComponent(id);

  const output = document.getElementById("zisai-view-count");

  async function displayViews() {
    const res = await fetch(api, { cache: "no-store" });
    if (!res.ok) throw new Error("GET views failed");
    const data = await res.json();
    output.textContent = Number(data.views || 0)
      .toLocaleString("zh-CN");
  }

  // 浏览器端辅助去重，服务端仍负责最终去重
  const key = "zisai-view-" + id;
  let previous = 0;

  try {
    previous = Number(localStorage.getItem(key) || 0);
  } catch (_) {}

  if (Date.now() - previous >= 30 * 60 * 1000) {
    try {
      const res = await fetch(api, {
        method: "POST"
      });
      if (!res.ok) throw new Error("POST views failed");
      const result = await res.json();

      if (result.success) {
        try {
          localStorage.setItem(key, String(Date.now()));
        } catch (_) {}
      }
    } catch (error) {
      console.debug("ZISAI view recording unavailable", error);
    }
  }

  try {
    await displayViews();
  } catch (error) {
    console.debug("ZISAI view display unavailable", error);
  }
})();
