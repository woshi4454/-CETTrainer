# -*- coding: utf-8 -*-
"""生成最终 cet.ico。

尺寸策略（这是图标设计的通用做法，直接缩放必然糊）：
  >=32px：官方 Lucide graduation-cap 描边版（细节丰富，和 UI 里的线性图标同源）
  <32px ：简化实心剪影版（帽顶菱形 + 帽箍 + 流苏），只保留最少识别特征

底版：暖红对角渐变 + 顶部受光 + 底部暗角 + 图形轻投影
"""
import os

from PIL import Image, ImageFilter

from _icon_c import cap
from _make_icon import compose, fetch, render_glyph

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/graduation-cap.svg"
OUT_ICO = os.path.join(HERE, "cet.ico")
OUT_PNG = os.path.join(HERE, "icon_app.png")
OUT_PNG64 = os.path.join(HERE, "icon_app64.png")

# 描边版：尺寸 / 图形占比 / 描边粗细（单位=视图单位，24 网格）
STROKE_PLAN = [(256, 0.58, 1.90), (128, 0.58, 1.90), (64, 0.59, 1.95),
               (48, 0.60, 2.05), (32, 0.63, 2.35)]
# 剪影版：16px 下要像「方帽」而不是「蘑菇」——帽顶收窄、帽箍加宽
SOLID_PLAN = [24, 20, 16]
SOLID_KW = dict(ratio=0.80, crown_w=0.80, crown_top=0.04, crown_bot=0.46,
                band_w=0.54, band_top=0.38, band_bot=0.80,
                tassel_x=0.930, tassel_bot=0.64, tassel_w=0.032)


def _retry(url, tries=8):
    import time
    last = None
    for i in range(tries):
        try:
            return fetch(url)
        except Exception as e:  # noqa: BLE001
            last = e
            print("拉取失败 %d/%d：%s" % (i + 1, tries, e))
            time.sleep(1.5 * (i + 1))
    raise last


def build():
    svg = _retry(URL)

    pairs = []
    for size, ratio, stroke in STROKE_PLAN:
        big = 1024 if size >= 48 else 512
        lay = render_glyph(svg, big, ratio, stroke)
        pairs.append((size, compose(lay, big).resize((size, size), Image.LANCZOS)))

    solid_base = compose(cap(512, **SOLID_KW), 512)
    for size in SOLID_PLAN:
        im = solid_base.resize((size, size), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=55, threshold=0))
        pairs.append((size, im))

    pairs.sort(key=lambda p: -p[0])
    sizes = [s for s, _ in pairs]
    imgs = [im for _, im in pairs]

    from _ico_pack import verify, write_ico
    write_ico(OUT_ICO, list(zip(sizes, imgs)))
    print("写出", OUT_ICO, os.path.getsize(OUT_ICO), "字节，尺寸", sizes)
    print("读回自检（尺寸, 亮度）:", verify(OUT_ICO))

    by_size = dict(pairs)
    by_size[256].save(OUT_PNG)
    by_size[64].save(OUT_PNG64)
    print("写出", OUT_PNG, os.path.getsize(OUT_PNG), "字节")

    # 各尺寸放大对比 + 真实尺寸条
    zoom = 6
    W = 40 + sum(min(s, 48) * zoom + 24 for s in sizes)
    sheet = Image.new("RGB", (W, max(s for s in sizes) // 2 + 300),
                      (246, 247, 249))
    x = 24
    for s in sizes:
        im = by_size[s]
        z = im.convert("RGB").resize((min(s, 48) * zoom, min(s, 48) * zoom),
                                     Image.NEAREST)
        sheet.paste(z, (x, 26))
        # 真实像素尺寸
        sheet.paste(im.convert("RGB"), (x, 26 + 48 * zoom + 24))
        x += min(s, 48) * zoom + 24
    out = os.path.join(HERE, "shots", "ico_final.png")
    sheet.save(out)
    print("对比 ->", out, sheet.size)


build()
