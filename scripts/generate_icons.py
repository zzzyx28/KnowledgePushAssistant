"""生成应用图标 → assets/icon.icns (macOS) + assets/icon.ico (Windows)"""

import os
import struct
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS = PROJECT_ROOT / "assets"
ICONSET = ASSETS / "icon.iconset"

# ── 尺寸规格 ──
SIZES_MAC = [16, 32, 64, 128, 256, 512, 1024]
SIZES_WIN = [16, 24, 32, 48, 64, 128, 256]


def draw_icon(size: int) -> Image.Image:
    """绘制一个简洁现代的图标：圆角方块 + 书本折角。"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = int(size * 0.10)
    r = int(size * 0.22)

    # 圆角矩形背景（渐变蓝色）
    for y in range(size):
        t = y / size
        r_val = int(40 + (10 - 40) * t)    # 40 → 10
        g_val = int(100 + (80 - 100) * t)   # 100 → 80
        b_val = int(220 + (200 - 220) * t)  # 220 → 200
        draw.rectangle(
            [margin, y, size - margin, y + 1],
            fill=(r_val, g_val, b_val, 255),
        )

    # 圆角遮罩
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=r,
        fill=255,
    )
    img.putalpha(mask)

    # 白色书本折角图形（简约风格）
    draw = ImageDraw.Draw(img)
    left = int(size * 0.24)
    right = int(size * 0.76)
    top = int(size * 0.22)
    bottom = int(size * 0.78)
    mid_x = int(size * 0.50)

    # 左页（竖矩形）
    draw.rounded_rectangle(
        [left, top, mid_x, bottom],
        radius=int(size * 0.04),
        fill=(255, 255, 255, 255),
    )
    # 右页（稍短，表示折角）
    draw.rounded_rectangle(
        [mid_x, top, right, int(bottom - size * 0.10)],
        radius=int(size * 0.04),
        fill=(255, 255, 255, 230),
    )
    # 折角三角
    fold_x, fold_y = right, int(bottom - size * 0.10)
    draw.polygon(
        [
            (mid_x, fold_y),
            (fold_x, fold_y),
            (fold_x, int(fold_y + size * 0.18)),
        ],
        fill=(255, 255, 255, 180),
    )

    # 书脊线
    spine_x = mid_x
    draw.line(
        [(spine_x, top + 2), (spine_x, bottom - 2)],
        fill=(40, 100, 220, 80),
        width=max(1, size // 128),
    )

    return img


def build_iconset():
    """生成 macOS .iconset 文件夹。"""
    ICONSET.mkdir(parents=True, exist_ok=True)

    for s in SIZES_MAC:
        img = draw_icon(s)
        # 标准分辨率
        name = f"icon_{s}x{s}.png"
        img.save(ICONSET / name, "PNG")
        # @2x 版本（用 2x 尺寸）
        if s * 2 <= 1024:
            name2x = f"icon_{s}x{s}@2x.png"
            img2 = draw_icon(s * 2)
            img2.save(ICONSET / name2x, "PNG")

    # 使用 iconutil 生成 .icns（仅 macOS）
    icns_path = ASSETS / "icon.icns"
    ret = os.system(f"iconutil -c icns '{ICONSET}' -o '{icns_path}'")
    if ret == 0:
        print(f"✓ 生成: {icns_path}")
        shutil.rmtree(ICONSET)
    else:
        print("⚠ iconutil 不可用（非 macOS？），使用备用 PNG")
        fallback = draw_icon(256)
        fallback.save(ASSETS / "icon.png", "PNG")
        print(f"✓ 生成备用: {ASSETS / 'icon.png'}")


def build_ico():
    """生成 Windows .ico（含多种尺寸）。"""
    images = [draw_icon(s) for s in SIZES_WIN]
    ico_path = ASSETS / "icon.ico"
    images[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in SIZES_WIN],
        append_images=images[1:],
    )
    print(f"✓ 生成: {ico_path}")


if __name__ == "__main__":
    ASSETS.mkdir(parents=True, exist_ok=True)
    build_iconset()
    build_ico()
    print("完成。")
