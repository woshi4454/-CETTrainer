# -*- coding: utf-8 -*-
"""页面包：所有功能页共用的基类。

约定（与 app.py 对齐）：
  - 每个页面 class XxxPage(Page)
  - __init__(self, parent, app)：parent 为 ttk.Notebook，app 为 App 实例
  - self.app.tts        : TTSEngine，提供 speak()/stop()
  - self.app.store      : Store（数据库封装）
  - self.app.set_status : 更新底部状态栏
  - 可选实现 on_show()  / reload_data()（切到该页 / 全局刷新时调用）
"""

import tkinter as tk

import ui_common as ui


class Page(tk.Frame):
    def __init__(self, parent, app=None, *args, **kwargs):
        super().__init__(parent, bg=ui.BG)
        self.app = app
        self.store = app.store if app is not None else None

