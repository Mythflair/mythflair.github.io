import os
import re

CONTENT_DIR = r"./content"
STATIC_IMAGES_DIR = r"./static/images"
DOC_EXTS = {".md", ".markdown"}

def scan_static_images(images_dir):
    """
    扫描 static/images 目录建立两套映射表：
    1. stem_map: 纯文件名主干(小写) -> 包含的后缀集合，如 {'20250726104830': {'.jpg'}}
    2. rel_map: 规范化相对子路径(小写) -> 实际后缀，如 {'europe/20250726104830': '.jpg'}
    """
    stem_map = {}
    rel_map = {}

    for root, _, files in os.walk(images_dir):
        for f in files:
            stem, ext = os.path.splitext(f)
            ext_lower = ext.lower()
            if ext_lower not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}:
                continue

            stem_lower = stem.lower()
            stem_map.setdefault(stem_lower, set()).add(ext_lower)

            # 计算相对 static/images 的归一化路径
            rel_file = os.path.relpath(os.path.join(root, f), images_dir)
            rel_stem = os.path.splitext(rel_file)[0].replace("\\", "/").lower()
            rel_map[rel_stem] = ext_lower

    return stem_map, rel_map

def should_fix_to_jpg(full_match_path, stem_map, rel_map):
    """
    判断匹配到的 png 路径在 static 目录中是否实际为 jpg
    """
    # 清洗：去除 URL 参数/锚点，双斜杠合并为单斜杠
    clean = full_match_path.split("?")[0].split("#")[0]
    clean = re.sub(r'/+', '/', clean)

    filename = os.path.basename(clean)
    stem, _ = os.path.splitext(filename)
    stem_lower = stem.lower()

    # 1. 尝试通过相对子目录路径精准比对（如 /images/Europe/xxx.png）
    norm_path = clean.replace("\\", "/").lower()
    for prefix in ["/images/", "images/", "/static/images/", "static/images/"]:
        if prefix in norm_path:
            rel_part = norm_path.split(prefix, 1)[1]
            rel_stem = os.path.splitext(rel_part)[0]
            if rel_stem in rel_map:
                actual_ext = rel_map[rel_stem]
                if actual_ext in {".jpg", ".jpeg"}:
                    return actual_ext

    # 2. 兜底匹配：纯文件名主干比对
    if stem_lower in stem_map:
        exts = stem_map[stem_lower]
        # 如果物理磁盘上已经没有 .png，且存在 .jpg 或 .jpeg
        if ".png" not in exts:
            if ".jpg" in exts:
                return ".jpg"
            if ".jpeg" in exts:
                return ".jpeg"

    return None

def main():
    if not os.path.exists(STATIC_IMAGES_DIR) or not os.path.exists(CONTENT_DIR):
        print("错误: 目标目录不存在，请检查路径。")
        return

    stem_map, rel_map = scan_static_images(STATIC_IMAGES_DIR)

    # 匹配各类场景下以 .png 结尾的图片路径/文件名
    # 兼容: image: "...", ![](...), <img src="...">, ![[...]]
    pattern = re.compile(r'([^\s"\'\(\)\[\]<>]+\.png)', re.IGNORECASE)

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

            def replace_callback(match):
                nonlocal file_fixed_count
                raw_path = match.group(1)
                new_ext = should_fix_to_jpg(raw_path, stem_map, rel_map)
                if new_ext:
                    # 仅把末尾的 .png 换为实际对应的 .jpg / .jpeg
                    fixed_path = re.sub(r'\.png$', new_ext, raw_path, flags=re.IGNORECASE)
                    file_fixed_count += 1
                    return fixed_path
                return raw_path

            new_content = pattern.sub(replace_callback, content)

            if file_fixed_count > 0:
                with open(md_path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                total_files_changed += 1
                total_links_fixed += file_fixed_count
                rel_doc = os.path.relpath(md_path, CONTENT_DIR)
                print(f"[已修复] {rel_doc} -> 修复了 {file_fixed_count} 处链接")

    print("=" * 60)
    print(f"执行完毕！共修复了 {total_files_changed} 个文件中的 {total_links_fixed} 处图片链接。")

if __name__ == "__main__":
    main()