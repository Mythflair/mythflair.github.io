from PIL import Image
import os
import zipfile

# 映射原图到新文件名（支持jpg/png等常见格式）
rename_map = {
    "c9a27115f7fe4e632da0717a38feecc1": "01_甜柿集夜市长廊俯瞰",
    "63f0c38853c62ca37f404ab535085d04": "02_热气球一生所求爱与自由夜景",
    "2ec1b769fcbc184cd4dbaf467fae406d": "03_奥体中心热气球与夜市全景",
    "cda5343ed9b21c9a47974a3243d23b68": "04_甜柿集入口门头近景",
    "c052ba60047ed4da9c3357670339d585": "05_奥体中心商街日景航拍",
}

output_files = []
for file in os.listdir("."):
    name, ext = os.path.splitext(file)
    if name in rename_map:
        new_name = f"{rename_map[name]}.webp"
        with Image.open(file) as img:
            img.save(new_name, "WEBP", quality=85)
        output_files.append(new_name)
        print(f"已转换: {new_name}")

# 打包压缩
with zipfile.ZipFile("images_webp.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    for f in output_files:
        zipf.write(f)

print("打包完成：images_webp.zip")