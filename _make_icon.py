# -*- coding: utf-8 -*-
"""从 GitHub 拉官方 SVG 图标，精确渲染成 PNG，再合成 App 图标。

做法：
1. 用 24 网格的 Lucide / Tabler 图标（都是 stroke 线性风格，与 UI 一致）
2. 写一个最小 SVG path 解析器（M L H V C S A Q T Z + 相对指令），
   只处理描边（stroke），因为我们只画线条
3. 4x 超采样渲染后 LANCZOS 缩小
4. 底版：暖红对角渐变 + 顶部受光 + 底部暗角 + 图形轻投影

产出：shots/icons/<name>.png（单图标）+ shots/icon_sheet.png（候选对比）
"""
import json
import math
import os
import re
import urllib.request

from PIL import Image, ImageDraw, ImageFilter

S = 2048
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "shots")
ICO_DIR = os.path.join(OUT, "icons")
os.makedirs(ICO_DIR, exist_ok=True)

C_TOP = (245, 96, 116)
C_MID = (232, 69, 95)
C_BOT = (188, 39, 63)

UA = {"User-Agent": "Mozilla/5.0"}


# --------------------------------------------------------------------------- #
# 1. 下载 SVG
# --------------------------------------------------------------------------- #
ICONS = {
    # Lucide
    "lucide_book_open": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/book-open.svg",
    "lucide_graduation": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/graduation-cap.svg",
    "lucide_book_a": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/book-a.svg",
    "lucide_book_marked": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/book-marked.svg",
    "lucide_brain": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/brain.svg",
    "lucide_languages": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/languages.svg",
    "lucide_notebook_pen": "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/notebook-pen.svg",
    # Tabler
    "tabler_book_2": "https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/book-2.svg",
    "tabler_school": "https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/school.svg",
    "tabler_language": "https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/language.svg",
    "tabler_books": "https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/books.svg",
    "tabler_bulb": "https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/bulb.svg",
}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


def parse_svg(svg):
    """取出 viewBox 与所有 path 的 d 属性。"""
    vb = re.search(r'viewBox="([^"]+)"', svg)
    view = [float(v) for v in vb.group(1).replace(",", " ").split()] if vb else [0, 0, 24, 24]
    paths = re.findall(r'<path[^>]*\sd="([^"]+)"', svg)
    if not paths:
        paths = re.findall(r'<path[^>]*\sd=\'([^\']+)\'', svg)
    return view, paths


# --------------------------------------------------------------------------- #
# 2. 最小 SVG path 解析 → 多段折线
# --------------------------------------------------------------------------- #
TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?")


def arc_to_points(p0, rx, ry, rot, large, sweep, p1, seg=28):
    """SVG 椭圆弧 → 折线（端点参数化转中心参数化）。"""
    if rx == 0 or ry == 0:
        return [p0, p1]
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(rot)
    cos_p, sin_p = math.cos(phi), math.sin(phi)
    dx2 = (p0[0] - p1[0]) / 2.0
    dy2 = (p0[1] - p1[1]) / 2.0
    x1 = cos_p * dx2 + sin_p * dy2
    y1 = -sin_p * dx2 + cos_p * dy2
    lam = (x1 * x1) / (rx * rx) + (y1 * y1) / (ry * ry)
    if lam > 1:
        k = math.sqrt(lam)
        rx *= k
        ry *= k
    num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    den = rx * rx * y1 * y1 + ry * ry * x1 * x1
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        co = -co
    cx1 = co * rx * y1 / ry
    cy1 = -co * ry * x1 / rx
    cx = cos_p * cx1 - sin_p * cy1 + (p0[0] + p1[0]) / 2.0
    cy = sin_p * cx1 + cos_p * cy1 + (p0[1] + p1[1]) / 2.0

    def ang(ux, uy, vx, vy):
        d = (ux * vx + uy * vy) / (math.hypot(ux, uy) * math.hypot(vx, vy))
        a = math.acos(max(-1.0, min(1.0, d)))
        if ux * vy - uy * vx < 0:
            a = -a
        return a

    th1 = ang(1, 0, (x1 - cx1) / rx, (y1 - cy1) / ry)
    dth = ang((x1 - cx1) / rx, (y1 - cy1) / ry,
              (-x1 - cx1) / rx, (-y1 - cy1) / ry)
    if not sweep and dth > 0:
        dth -= 2 * math.pi
    elif sweep and dth < 0:
        dth += 2 * math.pi

    pts = []
    n = max(6, int(abs(dth) / (2 * math.pi) * seg) + 2)
    for i in range(n + 1):
        t = th1 + dth * i / n
        xx = cx + rx * math.cos(t) * cos_p - ry * math.sin(t) * sin_p
        yy = cy + rx * math.cos(t) * sin_p + ry * math.sin(t) * cos_p
        pts.append((xx, yy))
    return pts


def path_to_polylines(d):
    """解析 d，返回 [(points, closed), ...]。

    注意：SVG 的 A 指令里 large-arc / sweep 是单字符标志位，
    直接按数字切词会把 "0022" 当成一个数（Lucide 图标常这么写）。
    所以这里用字符游标手写扫描器，flag 只读一个字符。
    """
    s = d
    n = len(s)
    pos = 0
    polys = []
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    prev_c = None      # 上一段三次曲线的第二控制点（给 S 做反射）
    prev_q = None      # 上一段二次曲线的控制点（给 T 做反射）
    cmd = None
    pts = []
    closed = False

    def skip_sep():
        nonlocal pos
        while pos < n and s[pos] in " ,\t\r\n":
            pos += 1

    def num():
        nonlocal pos
        skip_sep()
        st = pos
        if pos < n and s[pos] in "+-":
            pos += 1
        seen_dot = False
        while pos < n:
            ch = s[pos]
            if ch.isdigit():
                pos += 1
            elif ch == ".":
                if seen_dot:
                    break        # "-7.967.517" 这种：第二个点开始是新数字
                seen_dot = True
                pos += 1
            else:
                break
        if pos < n and s[pos] in "eE":
            pos += 1
            if pos < n and s[pos] in "+-":
                pos += 1
            while pos < n and s[pos].isdigit():
                pos += 1
        if st == pos:
            raise ValueError("第 %d 字符处要数字，实际是 %r（%r）"
                             % (pos, s[pos:pos + 6], s))
        txt = s[st:pos]
        if txt in ("+", "-", ".", "+.", "-."):
            raise ValueError("残缺数字 %r，位置 %d（%r）" % (txt, st, s))
        return float(txt)

    def flag():
        nonlocal pos
        skip_sep()
        ch = s[pos]
        pos += 1
        return 1 if ch == "1" else 0

    def flush():
        nonlocal pts, closed
        if len(pts) >= 2:
            polys.append((list(pts), closed))
        pts = []
        closed = False

    while pos < n:
        skip_sep()
        if pos >= n:
            break
        t = s[pos]
        if t.isalpha():
            cmd = t
            pos += 1
            if cmd in "Zz":
                closed = True
                if pts:
                    pts.append(start)
                flush()
                cur = start
                prev_c = prev_q = None
                continue
        if cmd is None:
            break
        rel = cmd.islower()
        c = cmd.upper()

        if c == "M":
            x, y = num(), num()
            if rel:
                x, y = cur[0] + x, cur[1] + y
            flush()
            cur = (x, y)
            start = (x, y)
            pts = [cur]
            cmd = "l" if rel else "L"
        elif c == "L":
            x, y = num(), num()
            if rel:
                x, y = cur[0] + x, cur[1] + y
            cur = (x, y)
            pts.append(cur)
        elif c == "H":
            x = num()
            if rel:
                x += cur[0]
            cur = (x, cur[1])
            pts.append(cur)
        elif c == "V":
            y = num()
            if rel:
                y += cur[1]
            cur = (cur[0], y)
            pts.append(cur)
        elif c in ("C", "S"):
            if c == "C":
                x1, y1 = num(), num()
                if rel:
                    x1, y1 = cur[0] + x1, cur[1] + y1
            elif prev_c is not None:
                # S 的第一控制点 = 上一段 C 第二控制点关于当前点的反射
                x1, y1 = 2 * cur[0] - prev_c[0], 2 * cur[1] - prev_c[1]
            else:
                x1, y1 = cur
            x2, y2 = num(), num()
            if rel:
                x2, y2 = cur[0] + x2, cur[1] + y2
            x, y = num(), num()
            if rel:
                x, y = cur[0] + x, cur[1] + y
            for k in range(1, 17):
                tt = k / 16.0
                u = 1 - tt
                bx = (u**3 * cur[0] + 3 * u * u * tt * x1
                      + 3 * u * tt * tt * x2 + tt**3 * x)
                by = (u**3 * cur[1] + 3 * u * u * tt * y1
                      + 3 * u * tt * tt * y2 + tt**3 * y)
                pts.append((bx, by))
            prev_c = (x2, y2)
            prev_q = None
            cur = (x, y)
        elif c in ("Q", "T"):
            if c == "Q":
                x1, y1 = num(), num()
                if rel:
                    x1, y1 = cur[0] + x1, cur[1] + y1
            elif prev_q is not None:
                x1, y1 = 2 * cur[0] - prev_q[0], 2 * cur[1] - prev_q[1]
            else:
                x1, y1 = cur
            x, y = num(), num()
            if rel:
                x, y = cur[0] + x, cur[1] + y
            for k in range(1, 17):
                tt = k / 16.0
                u = 1 - tt
                bx = u * u * cur[0] + 2 * u * tt * x1 + tt * tt * x
                by = u * u * cur[1] + 2 * u * tt * y1 + tt * tt * y
                pts.append((bx, by))
            prev_q = (x1, y1)
            prev_c = None
            cur = (x, y)
        elif c == "A":
            rx, ry, rot = num(), num(), num()
            large, sweep = flag(), flag()
            x, y = num(), num()
            if rel:
                x, y = cur[0] + x, cur[1] + y
            pts.extend(arc_to_points(cur, rx, ry, rot, large, sweep, (x, y))[1:])
            prev_c = prev_q = None
            cur = (x, y)
        else:
            raise ValueError("不支持的指令 %r：%r" % (cmd, d))
    flush()
    return polys


# --------------------------------------------------------------------------- #
# 3. 描边渲染（圆头 + 圆角拐弯）
# --------------------------------------------------------------------------- #
def stroke_polys(draw, polys, k, ox, oy, w, fill):
    r = w / 2.0
    for pts, closed in polys:
        seq = [(x * k + ox, y * k + oy) for x, y in pts]
        if closed and len(seq) > 2:
            seq = seq + [seq[0]]
        if len(seq) >= 2:
            draw.line(seq, fill=fill, width=int(round(w)), joint="curve")
        for p in seq:
            draw.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=fill)


def render_glyph(svg, canvas_size, target_ratio, stroke_units=2.0,
                 color=(255, 255, 255, 255)):
    """把 SVG 描边渲染成 RGBA 图层，居中占据 target_ratio。"""
    view, paths = parse_svg(svg)
    vx, vy, vw, vh = view
    polys = []
    for p in paths:
        polys.extend(path_to_polylines(p))

    size = canvas_size * target_ratio
    k = size / max(vw, vh)
    ox = (canvas_size - vw * k) / 2.0 - vx * k
    oy = (canvas_size - vh * k) / 2.0 - vy * k
    w = stroke_units * k

    layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    stroke_polys(ImageDraw.Draw(layer), polys, k, ox, oy, w, color)
    return layer


# --------------------------------------------------------------------------- #
# 4. 底版 + 合成
# --------------------------------------------------------------------------- #
def make_base(radius_ratio=0.225):
    n = 128
    small = Image.new("RGB", (n, n))
    px = small.load()
    for y in range(n):
        for x in range(n):
            t = (x * 0.42 + y * 0.58) / (n - 1.0)
            if t < 0.5:
                a = t / 0.5
                c = tuple(int(C_TOP[i] + (C_MID[i] - C_TOP[i]) * a) for i in range(3))
            else:
                a = (t - 0.5) / 0.5
                c = tuple(int(C_MID[i] + (C_BOT[i] - C_MID[i]) * a) for i in range(3))
            px[x, y] = c
    base = small.resize((S, S), Image.BICUBIC).convert("RGBA")

    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, S - 1, S - 1), radius=int(S * radius_ratio), fill=255)

    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    canvas.paste(base, (0, 0), mask)

    gl = Image.new("L", (S, S), 0)
    gd = ImageDraw.Draw(gl)
    h = int(S * 0.5)
    for i in range(h):
        gd.line([(0, i), (S, i)], fill=int(48 * (1 - i / h) ** 2.1))
    gl = gl.filter(ImageFilter.GaussianBlur(S * 0.03))
    gl = Image.composite(gl, Image.new("L", (S, S), 0), mask)
    canvas = Image.composite(Image.new("RGBA", (S, S), (255, 255, 255, 255)),
                             canvas, gl)

    sh = Image.new("L", (S, S), 0)
    sd = ImageDraw.Draw(sh)
    h2 = int(S * 0.4)
    for i in range(h2):
        sd.line([(0, S - 1 - i), (S, S - 1 - i)], fill=int(55 * (1 - i / h2) ** 2.2))
    sh = sh.filter(ImageFilter.GaussianBlur(S * 0.035))
    sh = Image.composite(sh, Image.new("L", (S, S), 0), mask)
    canvas = Image.composite(Image.new("RGBA", (S, S), (155, 24, 46, 255)),
                             canvas, sh)
    return canvas, mask


def compose(layer, size=None):
    global S
    if size is not None:
        S = size
    canvas, mask = make_base()
    alpha = layer.split()[3]
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sh.paste((88, 8, 26, 105), (0, 0), alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(S * 0.011))
    sh = sh.transform(sh.size, Image.AFFINE, (1, 0, 0, 0, 1, -S * 0.005))
    canvas = Image.alpha_composite(canvas, sh)

    lm = Image.new("L", (S, S), 0)
    lm.paste(alpha, (0, 0))
    lm = Image.composite(lm, Image.new("L", (S, S), 0), mask)
    layer.putalpha(lm)
    return Image.alpha_composite(canvas, layer)


# --------------------------------------------------------------------------- #
# 5. 跑起来
# --------------------------------------------------------------------------- #
def main():
    ok = {}
    for name, url in ICONS.items():
        try:
            svg = fetch(url)
            view, paths = parse_svg(svg)
            if not paths:
                print("跳过（没 path）:", name)
                continue
            ok[name] = svg
            print("OK  %-22s viewBox=%s paths=%d" % (name, view, len(paths)))
        except Exception as e:  # noqa: BLE001
            print("ERR %-22s %s" % (name, e))

    made = []
    for name, svg in ok.items():
        layer = render_glyph(svg, S, 0.60, 2.0)
        im = compose(layer)
        p = os.path.join(ICO_DIR, name + ".png")
        im.resize((256, 256), Image.LANCZOS).save(p)
        made.append(name)

    # 对比表：每行 4 个
    cols = 4
    cell, pad = 190, 34
    rows = (len(made) + cols - 1) // cols
    sheet = Image.new("RGBA", (pad * 2 + cell * cols, pad + rows * (cell + 34)),
                      (246, 247, 249, 255))
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(made):
        r, c = divmod(i, cols)
        x = pad + c * cell
        y = pad + r * (cell + 34)
        ic = Image.open(os.path.join(ICO_DIR, name + ".png")).convert("RGBA")
        sheet.alpha_composite(ic.resize((cell - 30, cell - 30), Image.LANCZOS),
                              (x, y))
        sheet.alpha_composite(ic.resize((32, 32), Image.LANCZOS),
                              (x + cell - 30, y + 120))
        d.text((x + 2, y + cell - 22), name, fill=(70, 70, 80))
    sheet.save(os.path.join(OUT, "icon_sheet.png"))
    print("\n对比图 ->", os.path.join(OUT, "icon_sheet.png"), sheet.size)


if __name__ == "__main__":
    main()
