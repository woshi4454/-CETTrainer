# -*- coding: utf-8 -*-
"""本地冒烟测试：无头创建 App，遍历所有 tab 触发 on_show / reload_data，捕获异常。"""
import sys
import tkinter as tk

# 屏蔽 TTS 实际发声（无音频设备 / CI）
import tts as _tts
_tts.TTSEngine.synthesize = lambda self, text: None
_tts.TTSEngine.speak = lambda self, text, blocking=False: None

import app as _app

root = tk.Tk()
root.withdraw()

errors = []
a = _app.App(root)

for key, page in a.pages.items():
    try:
        if hasattr(page, "reload_data"):
            page.reload_data()
        if hasattr(page, "on_show"):
            page.on_show()
    except Exception as e:  # noqa: BLE001
        errors.append((key, repr(e)))

if errors:
    print("SMOKE_FAIL")
    for k, e in errors:
        print(" -", k, e)
    sys.exit(1)
else:
    print("SMOKE_OK", len(a.pages), "pages")
