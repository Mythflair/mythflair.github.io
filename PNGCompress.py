import os
from PIL import Image

def has_transparency(img):
    """
    精确判断图片是否包含透明或半透明内容
    """
    # 模式为包含 Alpha 通道的格式
    if img.mode in ("RGBA", "LA"):
        alpha = img.split()[-1]
        # 获取 alpha 通道的极值 (min, max)
        min_alpha, max_alpha = alpha.getextrema()
        # 如果最小 alpha < 255，说明存在透明或半透明像素
        return min_alpha < 255

    # 调色板模式（P 模式）且设置了透明度
    if img.mode == "P" and "transparency" in img.info:
        return True

    return False

def compress_images(input_dir, output_dir, max_size=None, jpg_quality=85):
    """
    批量压缩目录内的图片：
    - 无透明通道的 PNG 自动转为高画质 JPEG 保存（后缀变更为 .jpg）
    - 有透明通道的 PNG 保持原格式并进行色彩量化压缩
    - 其他 JPG/WEBP 正常压缩

    :param input_dir: 输入根目录
    :param output_dir: 输出目录（若与 input_dir 相同则原地覆盖/替换）
    :param max_size: 最大宽和高 (宽, 高)，不改变分辨率传 None
    :param jpg_quality: 输出 JPEG 的画质 (1-100)，85 属于高画质
    """
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

    for root, _, files in os.walk(input_dir):
        # 维持原有的子目录结构
        rel_path = os.path.relpath(root, input_dir)
        target_dir = os.path.join(output_dir, rel_path)
        os.makedirs(target_dir, exist_ok=True)

        for filename in files:
            base_name, ext = os.path.splitext(filename)
            ext_lower = ext.lower()

            if ext_lower not in valid_extensions:
                continue

            src_path = os.path.join(root, filename)

            try:
                with Image.open(src_path) as img:
                    orig_format = img.format

                    # 1. 可选分辨率调整（为 None 则不改变原始尺寸）
                    if max_size:
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)

                    target_format = orig_format
                    save_kwargs = {}
                    out_filename = filename

                    # 2. 核心分支：判断是否为 PNG
                    if orig_format == "PNG":
                        if has_transparency(img):
                            # 存在透明通道：保留 PNG，采用 256 色量化以大幅削减体积
                            target_format = "PNG"
                            img = img.quantize(colors=256, method=Image.Resampling.LANCZOS)
                            save_kwargs["optimize"] = True
                            save_kwargs["compress_level"] = 9
                        else:
                            # 没有透明通道：转为 JPEG
                            target_format = "JPEG"
                            out_filename = f"{base_name}.jpg"
                            if img.mode != "RGB":
                                img = img.convert("RGB")
                            save_kwargs["quality"] = jpg_quality
                            save_kwargs["optimize"] = True

                    elif orig_format in ("JPEG", "WEBP"):
                        save_kwargs["quality"] = jpg_quality
                        save_kwargs["optimize"] = True
                        if orig_format == "JPEG" and img.mode != "RGB":
                            img = img.convert("RGB")

                    dst_path = os.path.join(target_dir, out_filename)

                    # 3. 临时文件写入，避免中断导致文件损坏
                    temp_dst = dst_path + ".tmp"
                    img.save(temp_dst, format=target_format, **save_kwargs)
                    os.replace(temp_dst, dst_path)

                    # 若是在原地覆盖模式下 PNG 转成了 JPG，删除原有的 .png 文件
                    if input_dir == output_dir and out_filename != filename:
                        if os.path.exists(src_path):
                            os.remove(src_path)

                if out_filename != filename:
                    print(f"转换并压缩成功: {filename} -> {out_filename} (已转为 JPEG)")
                else:
                    print(f"压缩成功: {filename} (保持 {target_format})")

            except Exception as e:
                print(f"处理失败: {filename}, 原因: {e}")

if __name__ == "__main__":
    # 路径配置
    SOURCE_DIRECTORY = "./static/images"         # 原图目录
    TARGET_DIRECTORY = "./static/images"     # 目标目录（若填 SOURCE_DIRECTORY 则为原地替换）

    compress_images(
        input_dir=SOURCE_DIRECTORY,
        output_dir=TARGET_DIRECTORY,
        max_size=None,       # 设为 None 保持原图尺寸不变；若要限制长宽可填 (1920, 1920)
        jpg_quality=85       # JPEG 高画质输出
    )