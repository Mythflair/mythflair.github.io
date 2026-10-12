import os
from PIL import Image


def compress_images(input_dir, output_dir, max_size=(1920, 1920), quality=75):
    """
    批量压缩指定目录下的所有图片。

    :param input_dir: 输入图片根目录
    :param output_dir: 输出目录（若与 input_dir 相同则原地覆盖）
    :param max_size: 最大宽和高 (宽, 高)，超过会自动等比例缩小；如无需缩放尺寸设为 None
    :param quality: JPG/WEBP 等有损格式压缩质量 (1-100)，建议 70-85
    """
    # 支持的常见图片后缀
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

    for root, _, files in os.walk(input_dir):
        # 计算相对路径，以便在输出目录保持相同的多层级目录结构
        rel_path = os.path.relpath(root, input_dir)
        target_dir = os.path.join(output_dir, rel_path)
        os.makedirs(target_dir, exist_ok=True)

        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in valid_extensions:
                continue

            src_path = os.path.join(root, filename)
            dst_path = os.path.join(target_dir, filename)

            try:
                with Image.open(src_path) as img:
                    img_format = img.format  # 保持原始格式 (如 JPEG, PNG, WEBP)

                    # 1. 等比例缩小超大分辨率（可选，根据需要启用）
                    if max_size:
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)

                    # 2. 根据格式针对性压缩保存
                    save_kwargs = {}

                    if img_format in ("JPEG", "WEBP"):
                        # 有损格式：通过 quality 和 optimize 压缩
                        save_kwargs["quality"] = quality
                        save_kwargs["optimize"] = True
                        # JPEG 不支持透明通道，若带 alpha 则转为 RGB
                        if img_format == "JPEG" and img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")

                    elif img_format == "PNG":
                        # 无损格式：开启 optimize，通过 compress_level 压缩数据流
                        save_kwargs["optimize"] = True
                        save_kwargs["compress_level"] = 9  # 0-9，9为最高无损压缩率

                    # 原地覆盖时的临时写入防冲突机制
                    temp_dst = dst_path + ".tmp"
                    img.save(temp_dst, format=img_format, **save_kwargs)
                    os.replace(temp_dst, dst_path)

                print(f"压缩成功: {filename}")
            except Exception as e:
                print(f"处理失败: {filename}, 原因: {e}")


if __name__ == "__main__":
    # 配置路径
    SOURCE_DIRECTORY = "./static/images"  # 原图所在目录
    TARGET_DIRECTORY = "./static/images"  # 压缩后保存目录（填 SOURCE_DIRECTORY 即为原地替换）

    # 执行压缩
    compress_images(
        input_dir=SOURCE_DIRECTORY,
        output_dir=TARGET_DIRECTORY,
        max_size=(1920, 1920),  # 若不需要改变分辨率，改为 None
        quality=75  # JPEG/WEBP 质量 (1-100)
    )