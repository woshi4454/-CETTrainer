# -*- coding: utf-8 -*-
"""毕业帽「实心剪影」绘制工具（供小尺寸图标使用）。

大尺寸用 Lucide 描边版；16/20/24px 描边只有 1px 宽，抗锯齿后必然糊成一团，
所以小尺寸改成实心剪影：只保留「帽顶菱形 + 帽箍 + 流苏」三个识别特征。
"""


def cap(n, ratio,
        crown_w=0.96, crown_top=0.06, crown_bot=0.50,
        band_w=0.44, band_top=0.40, band_bot=0.78,
        tassel_x=0.975, tassel_bot=0.68, tassel_w=0.038):
    """返回 n×n 的 RGBA 图层，白色实心毕业帽。

    ratio     —— 图形占画布的比例
    crown_*   —— 帽顶菱形（左右宽、上尖、下尖）
    band_*    —— 帽箍（下方梯形，底下圆角）
    tassel_*  —— 右侧垂下的流苏
    """
    from PIL import Image, ImageDraw

    lay = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    box = n * ratio
    ox = oy = (n - box) / 2.0

    def P(x, y):
        return (ox + x * box, oy + y * box)

    cx = 0.5
    hw = crown_w / 2.0
    crown_mid = (crown_top + crown_bot) / 2.0

    # 帽箍先画，等下被帽顶盖住上沿
    d.polygon([P(cx - band_w / 2, band_top),
               P(cx + band_w / 2, band_top),
               P(cx + band_w / 2, band_bot - 0.06),
               P(cx + band_w / 2 - 0.10, band_bot),
               P(cx - band_w / 2 + 0.10, band_bot),
               P(cx - band_w / 2, band_bot - 0.06)],
              fill=(255, 255, 255, 255))

    # 帽顶菱形
    d.polygon([P(cx, crown_top),
               P(cx + hw, crown_mid),
               P(cx, crown_bot),
               P(cx - hw, crown_mid)],
              fill=(255, 255, 255, 255))

    # 流苏
    d.rectangle([P(tassel_x - tassel_w, crown_mid),
                 P(tassel_x + tassel_w, tassel_bot)],
                fill=(255, 255, 255, 255))
    return lay


PREVIEW = [
    ("C1", dict(ratio=0.84, crown_w=0.92, crown_top=0.08, crown_bot=0.54,
                band_w=0.42, band_top=0.44, band_bot=0.80,
                tassel_x=0.955, tassel_bot=0.70)),
    ("C2", dict(ratio=0.88, crown_w=0.96, crown_top=0.06, crown_bot=0.50,
                band_w=0.44, band_top=0.40, band_bot=0.78,
                tassel_x=0.975, tassel_bot=0.68)),
    ("C3", dict(ratio=0.86, crown_w=1.00, crown_top=0.10, crown_bot=0.56,
                band_w=0.46, band_top=0.46, band_bot=0.84,
                tassel_x=0.990, tassel_bot=0.74, tassel_w=0.042)),
]


def _preview():
    import os

    from PIL import Image, ImageDraw

    from _make_icon import compose

    here = os.path.dirname(os.path.abspath(__file__))
    zoom = 7
    sizes = (16, 24, 32, 48)
    cell = max(sizes) * zoom + 24
    row = max(sizes) * zoom + 46
    sheet = Image.new("RGB", (130 + cell * len(sizes), 24 + row * len(PREVIEW)),
                      (246, 247, 249))
    d = ImageDraw.Draw(sheet)
    for i, (name, kw) in enumerate(PREVIEW):
        y0 = 20 + i * row
        d.text((16, y0 + max(sizes) * zoom // 2), "方案 " + name,
               fill=(60, 60, 70))
        base = compose(cap(512, **kw), 512)
        for j, s in enumerate(sizes):
            im = base.resize((s, s), Image.LANCZOS)
            z = im.convert("RGB").resize((s * zoom, s * zoom), Image.NEAREST)
            sheet.paste(z, (120 + j * cell, y0 + 20))
    out = os.path.join(here, "shots", "ico_c.png")
    sheet.save(out)
    print("写出", out, sheet.size)


if __name__ == "__main__":
    _preview()
