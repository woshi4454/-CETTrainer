# -*- coding: utf-8 -*-
"""启动打包后的 exe（放在无空格路径下），等窗口出来整窗截图。

用户目录含空格时 PyInstaller onefile 引导器会报 Could not create temporary directory，
所以这里改成从 E:\\CETTrainerRun 启动。
"""
import ctypes
import os
import subprocess
import sys
import time

from ctypes import wintypes
from PIL import ImageGrab

RUN_DIR = r"E:\CETTrainerNew"
EXE = os.path.join(RUN_DIR, "CETTrainer.exe")
SRC = os.path.join(os.getcwd(), "dist", "CETTrainer.exe")
OUT = os.path.join(os.getcwd(), "shots", "exe_shot.png")

# ★ 必须最早调用：不声明 DPI 感知时，系统会给本进程虚拟化坐标（150% 缩放下
# 只有真实尺寸的 2/3），GetWindowRect 拿到的框偏小，截图只截到窗口左上角。
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)   # PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = ctypes.windll.user32


def find_window(title_part, timeout=45):
    handles = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _cb(hwnd, _lp):
        if not user32.IsWindowVisible(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n <= 0:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        if buf.value.strip() == title_part:
            handles.append(hwnd)
        return True

    end = time.time() + timeout
    while time.time() < end:
        handles.clear()
        user32.EnumWindows(_cb, 0)
        if handles:
            return handles[0]
        time.sleep(0.5)
    return None


def rect_of(hwnd):
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    r = RECT()
    if user32.GetWindowRect(hwnd, ctypes.byref(r)):
        return r.left, r.top, r.right, r.bottom
    return None


def grab_via_printwindow(hwnd, box):
    """纯 ctypes 版 PrintWindow 抓图（这台机器没有 pywin32）。

    PW_RENDERFULLCONTENT=2 让 DWM 合成内容也画进来，窗口在后台也能抓到。
    """
    from ctypes import windll
    from PIL import Image

    gdi32 = windll.gdi32
    user = windll.user32

    left, top, right, bottom = box
    w, h = right - left, bottom - top

    hdc_win = user.GetWindowDC(hwnd)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_win)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_win, w, h)
    gdi32.SelectObject(hdc_mem, hbmp)
    user.PrintWindow(hwnd, hdc_mem, 2)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32),
                    ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
                    ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
                    ("biSizeImage", ctypes.c_uint32),
                    ("biXPelsPerMeter", ctypes.c_int32),
                    ("biYPelsPerMeter", ctypes.c_int32),
                    ("biClrUsed", ctypes.c_uint32), ("biClrImportant", ctypes.c_uint32)]

    bih = BITMAPINFOHEADER()
    bih.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bih.biWidth = w
    bih.biHeight = -h          # 负数 = 自上而下
    bih.biPlanes = 1
    bih.biBitCount = 32
    bih.biCompression = 0      # BI_RGB

    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buf, ctypes.byref(bih), 0)

    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user.ReleaseDC(hwnd, hdc_win)

    return Image.frombuffer("RGB", (w, h), buf, "raw", "BGRX", 0, 1)


os.makedirs(RUN_DIR, exist_ok=True)
if os.path.abspath(SRC) != os.path.abspath(EXE):
    with open(SRC, "rb") as f:
        data = f.read()
    with open(EXE, "wb") as f:
        f.write(data)

proc = subprocess.Popen([EXE], cwd=RUN_DIR)
hwnd = find_window("四六级学习助手")
if not hwnd:
    print("FAIL: 找不到窗口")
    proc.kill()
    sys.exit(1)

HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_SHOWWINDOW = 0x0040

user32.ShowWindow(hwnd, 9)
# 强置顶 + 前移：只靠 SetForegroundWindow 在后台会话里会被前台锁拒绝，
# 截图会抓到上面压着的其它窗口。
user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                    SWP_NOSIZE | SWP_NOMOVE | SWP_SHOWWINDOW)
user32.BringWindowToTop(hwnd)
user32.SetForegroundWindow(hwnd)
time.sleep(4.0)

box = rect_of(hwnd)
if not box or box[2] - box[0] < 200:
    print("FAIL: 窗口尺寸异常", box)
    proc.kill()
    sys.exit(1)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img = grab_via_printwindow(hwnd, box)
img.save(OUT)
print("saved", OUT, box, "size", img.size)

proc.terminate()
try:
    proc.wait(timeout=8)
except Exception:
    proc.kill()
print("done")
