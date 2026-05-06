"""截图比对工具 — 像素级对比，判断运维终端是否渲染成功"""
import os
from PIL import Image
from utils.logger import get_logger

logger = get_logger(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "screenshots")


def compare_images(actual_path: str, expected_path: str, threshold: float = 0.80):
    """
    逐像素对比两张截图。
    返回: (matched: bool, similarity: float, diff_path: str | None)
    """
    if not os.path.exists(expected_path):
        logger.warning(f"基准图片不存在: {expected_path}，跳过对比")
        return True, 1.0, None

    if not os.path.exists(actual_path):
        logger.error(f"实际截图不存在: {actual_path}")
        return False, 0.0, None

    actual = Image.open(actual_path).convert("RGB")
    expected = Image.open(expected_path).convert("RGB")

    if actual.size != expected.size:
        logger.warning(f"图片尺寸不一致: actual={actual.size}, expected={expected.size}")
        actual = actual.resize(expected.size)

    a_pixels = actual.load()
    e_pixels = expected.load()
    width, height = actual.size
    total_pixels = width * height
    diff_pixels = 0

    diff_img = Image.new("RGB", actual.size, (0, 0, 0))
    d_pixels = diff_img.load()

    for x in range(width):
        for y in range(height):
            if a_pixels[x, y] != e_pixels[x, y]:
                diff_pixels += 1
                d_pixels[x, y] = (255, 0, 0)
            else:
                d_pixels[x, y] = a_pixels[x, y]

    similarity = 1.0 - (diff_pixels / total_pixels)
    matched = similarity >= threshold

    diff_path = None
    if not matched:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        diff_path = os.path.join(REPORTS_DIR, "web_ssh_diff.png")
        diff_img.save(diff_path)
        logger.info(f"差异截图已保存: {diff_path}")

    logger.info(f"图片对比: similarity={similarity:.2%}, matched={matched}")
    return matched, similarity, diff_path
