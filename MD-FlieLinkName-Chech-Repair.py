import os
import re

CONTENT_DIR = "./content"
STATIC_IMAGES_DIR = "./static/images"

# 支持的文档格式
DOC_EXTS = {".md", ".markdown"}


def scan_existing_images(images_dir):
    """
    扫描 static/images 目录，建立映射：
    - 按纯文件名映射: basename.lower() -> 真实后缀集合 (例如 'banner': {'.jpg'})
    - 按相对路径映射: rel_path_without_ext.lower() -> 真实后缀 (用于解决不同子目录同名冲突)
    """
    stem_map = {}
    rel_map = {}

    for root, _, files in os.walk(images_dir):
        for f in files:
            name, ext = os.path.splitext(f)
            ext_lower = ext.lower()
            if ext_lower not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}:
                continue

            stem_lower = name.lower()
            stem_map.setdefault(stem_lower, set()).add(ext_lower)

            rel_file = os.path.relpath(os.path.join(root, f), images_dir)
            rel_no_ext = os.path.splitext(rel_file)[0].replace("\\", "/").lower()
            rel_map[rel_no_ext] = ext_lower

    return stem_map, rel_map


def get_corrected_ext(path_str, stem_map, rel_map):
    """
    判断该路径如果原先是 .png，现在是否应该改成真实存在的扩展名（如 .jpg）。
    如果不需要改动或找不到明确对应，返回 None。
    """
    # 去除 query 参数和 hash（如 ?v=123 或 #center）
    clean_path = path_str.split("?")[0].split("#")[0]

    # 提取纯文件名与后缀
    base_file = os.path.basename(clean_path)
    stem, ext = os.path.splitext(base_file)
    ext_lower = ext.lower()

    # 只关注原链接指向 .png 的情况
    if ext_lower != ".png":
        return None

    stem_lower = stem.lower()

    # 1. 优先尝试从路径中匹配 static/images 后面的相对子路径
    norm_path = clean_path.replace("\\", "/").lower()
    for prefix in ["/images/", "images/", "/static/images/", "static/images/"]:
        if prefix in norm_path:
            rel_part = norm_path.split(prefix, 1)[1]
            rel_no_ext = os.path.splitext(rel_part)[0]
            if rel_no_ext in rel_map:
                actual_ext = rel_map[rel_no_ext]
                if actual_ext != ext_lower:
                    return actual_ext

    # 2. 回退：通过纯文件名比对
    if stem_lower in stem_map:
        exts = stem_map[stem_lower]
        # 如果对应的文件已经没有 .png 了，并且存在 .jpg / .jpeg
        if ".png" not in exts:
            if ".jpg" in exts:
                return ".jpg"
            if ".jpeg" in exts:
                return ".jpeg"

    return None


def fix_markdown_links():
    stem_map, rel_map = scan_existing_images(STATIC_IMAGES_DIR)

    # 正则匹配 1: Markdown 语法 ![alt](url)
    md_img_pattern = re.compile(r'(!\[.*?\]\()([^\s\)]+)(.*?\))')
    # 正则匹配 2: HTML <img> 标签 src="url" 或 src='url'
    html_img_pattern = re.compile(r'(<img\b[^>]*?\bsrc=["\'])([^"\'>]+)(["\'])', re.IGNORECASE)

    total_files_changed = 0
    total_links_fixed = 0

    for root, _, files in os.walk(CONTENT_DIR):
        for f in files:
            if os.path.splitext(f)[1].lower() not in DOC_EXTS:
                continue

            md_path = os.path.join(root, f)
            with open(md_path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()

            file_fixed_count = 0

            # 替换 Markdown 图片语法
            def md_replace(match):
                nonlocal file_fixed_count
                prefix, url, suffix = match.groups()
                new_ext = get_corrected_ext(url, stem_map, rel_map)
                if new_ext:
                    # 仅替换扩展名部分，保留前后路径和 query 字符串
                    updated_url = re.sub(r'\.png(?=($|[?#]))', new_ext, url, flags=re.IGNORECASE)
                    if updated_url != url:
                        file_fixed_count += 1
                        return f"{prefix}{updated_url}{suffix}"
                return match.group(0)

            # 替换 HTML img src 语法
            def html_replace(match):
                nonlocal file_fixed_count
                prefix, url, suffix = match.groups()
                new_ext = get_corrected_ext(url, stem_map, rel_map)
                if new_ext:
                    updated_url = re.sub(r'\.png(?=($|[?#]))', new_ext, url, flags=re.IGNORECASE)
                    if updated_url != url:
                        file_fixed_count += 1
                        return f"{prefix}{updated_url}{suffix}"
                return match.group(0)

            new_content = md_img_pattern.sub(md_replace, content)
            new_content = html_img_pattern.sub(html_replace, new_content)

            if file_fixed_count > 0:
                with open(md_path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                total_files_changed += 1
                total_links_fixed += file_fixed_count
                rel_doc = os.path.relpath(md_path, CONTENT_DIR)
                print(f"[已修复] {rel_doc} (修正 {file_fixed_count} 处链接)")

    print("-" * 50)
    print(f"处理完成！共更新 {total_files_changed} 个文件，修复了 {total_links_fixed} 处图片链接。")


if __name__ == "__main__":
    fix_markdown_links()