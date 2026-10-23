# -*- coding: utf-8 -*-
"""无头启动冒烟：建 App、逐页 switch、抓异常、截图。"""
import os, sys, traceback, time
sys.path.insert(0, os.getcwd())
import tkinter as tk
import app as appmod

root = tk.Tk()
errs = []
try:
    a = appmod.App(root)
except Exception:
    traceback.print_exc()
    sys.exit(1)

root.update()
keys = [k for k, _c, _t, _i in appmod.PAGES]
for k in keys:
    try:
        a.switch_to(k)
        root.update()
        root.update_idletasks()
        print("OK  ", k)
    except Exception as e:
        errs.append((k, repr(e)))
        print("FAIL", k, repr(e))
        traceback.print_exc()

root.update()
# 截图
try:
    from PIL import ImageGrab
    root.lift(); root.update(); time.sleep(0.6)
    x, y = root.winfo_rootx(), root.winfo_rooty()
    w, h = root.winfo_width(), root.winfo_height()
    im = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    im.save(os.path.join(os.getcwd(), "shot_smoke.png"))
    print("screenshot saved", im.size)
except Exception as e:
    print("screenshot failed:", e)

root.destroy()
print("ERRORS:", errs)
