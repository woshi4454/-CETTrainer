# -*- coding: utf-8 -*-
"""一次截取全部 14 个页面。用法：python _shots_all.py [key ...]"""
import os
import sys
import time

import tkinter as tk
from PIL import ImageGrab

sys.path.insert(0, os.getcwd())

import ui_common as ui  # noqa: E402
import app as appmod  # noqa: E402

os.makedirs("shots/all", exist_ok=True)


def shoot(root, path):
    root.attributes("-topmost", True)
    root.update_idletasks()
    root.update()
    time.sleep(0.35)
    root.lift()
    root.focus_force()
    root.update()
    time.sleep(0.12)
    x, y = root.winfo_rootx(), root.winfo_rooty()
    w, h = root.winfo_width(), root.winfo_height()
    ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(path)
    root.attributes("-topmost", False)


root = tk.Tk()
root.title("CETTrainer")
ui.setup_style(root)
ui.center_window(root, 1200, 800)
a = appmod.App(root)
root.update()

keys = sys.argv[1:] or [k for k, _c, _t, _i in appmod.PAGES]
for k in keys:
    a.switch_to(k)
    root.update()
    # 踢掉输入法焦点，避免中文候选窗糊在截图上
    try:
        root.tk.call("focus", "-force", ".")
    except tk.TclError:
        pass
    root.update()
    shoot(root, "shots/all/p_%s.png" % k)
    print("shot", k)

root.destroy()
print("done")
