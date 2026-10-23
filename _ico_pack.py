# -*- coding: utf-8 -*-
"""手写 ICO 封装，绕开 PIL IcoImagePlugin 的 sizes=/append_images= 冲突。

ICO 结构：
  ICONDIR  6 字节：reserved(2)=0, type(2)=1, count(2)
  每帧 16 字节目录项：w(1) h(1) colors(1)=0 reserved(1)=0 planes(2)=1 bits(2)=32
                     bytesInRes(4) offset(4)      （w/h 为 0 表示 256）
  数据：>=256 直接放 PNG 原始字节；其余放 BMP DIB（BITMAPINFOHEADER + bottom-up 像素 + AND 掩码）
"""
import io
import struct

from PIL import Image


def _bmp_dib(im):
    """把 RGBA 图转成 ICO 用的 BMP DIB 字节。"""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    # 像素数据：bottom-up，BGRA
    rows = []
    for y in range(h - 1, -1, -1):
        row = bytearray()
        for x in range(w):
            r, g, b, a = px[x, y]
            row += bytes((b, g, r, a))
        rows.append(bytes(row))
    pixels = b"".join(rows)
    # AND 掩码：全 0（alpha 通道已负责透明），每行按 4 字节对齐
    stride = ((w + 31) // 32) * 4
    mask = b"\x00" * (stride * h)
    header = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32,
                         0, len(pixels) + len(mask), 0, 0, 0, 0)
    return header + pixels + mask


def write_ico(path, frames):
    """frames: [(size, PIL.Image)] —— 会按 size 从大到小排好写入。"""
    frames = sorted(frames, key=lambda p: -p[0])
    items = []
    for size, im in frames:
        if im.size != (size, size):
            im = im.resize((size, size), Image.LANCZOS)
        im = im.convert("RGBA")
        if size >= 256:
            buf = io.BytesIO()
            im.save(buf, format="PNG", optimize=True)
            data = buf.getvalue()
        else:
            data = _bmp_dib(im)
        items.append((size, data))

    n = len(items)
    out = bytearray()
    out += struct.pack("<HHH", 0, 1, n)
    offset = 6 + 16 * n
    body = bytearray()
    for size, data in items:
        wh = 0 if size >= 256 else size
        out += struct.pack("<BBBBHHII", wh, wh, 0, 0, 1, 32, len(data), offset)
        body += data
        offset += len(data)
    with open(path, "wb") as f:
        f.write(bytes(out) + bytes(body))
    return path, [s for s, _ in items]


def verify(path):
    """读回每一帧，返回 [(size, 平均亮度)] 供自检。"""
    im = Image.open(path)
    res = []
    for size in sorted(im.ico.sizes()):
        im.size = size
        f = im.copy().convert("RGBA")
        sm = f.resize((16, 16), Image.LANCZOS)
        px = list(sm.getdata())
        lum = sum((r + g + b) / 3 for r, g, b, a in px) / len(px)
        res.append((size[0], round(lum, 1)))
    return res
