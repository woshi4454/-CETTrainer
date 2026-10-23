# -*- coding: utf-8 -*-
"""CET 四六级学习助手 —— 主程序入口

界面：左侧竖向导航 + 白色顶栏 + 卡片化内容区（墨墨暖红设计体系）。
对接契约保持不变：
  self.store / self.tts / self.set_status / self.notebook / self.pages
  self.notebook 提供 select(page) / index(...) / enable_traversal() /
  bind("<<NotebookTabChanged>>", fn)，供各页面直接调用。
"""

import os
import sys

import tkinter as tk
from tkinter import ttk

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

import store
import tts
import cetpack
import ui_common as ui

from pages.page_vocab import VocabPage
from pages.page_wordbook import WordbookPage
from pages.page_wrong import WrongPage
from pages.page_dictation import DictationPage
from pages.page_listening import ListeningPage
from pages.page_reading import ReadingPage
from pages.page_cloze import ClozePage
from pages.page_translate import TranslatePage
from pages.page_writing import WritingPage
from pages.page_phrase import PhrasePage
from pages.page_grammar import GrammarPage
from pages.page_mock import MockPage
from pages.page_import import ImportPage
from pages.page_stats import StatsPage


TITLE = "四六级学习助手"
SUBTITLE = "背词 · 短语 · 语法 · 听写 · 听力 · 阅读 · 选词 · 翻译 · 作文 · 模考"

# (key, 页面类, 标签, 图标) —— 图标为 ui_common 里的线性图标名
PAGES = [
    ("vocab", VocabPage, "词汇记忆", "book"),
    ("wordbook", WordbookPage, "单词本", "star"),
    ("wrong", WrongPage, "错题本", "pen"),
    ("dict", DictationPage, "听写训练", "headphone"),
    ("listen", ListeningPage, "听力训练", "music"),
    ("read", ReadingPage, "阅读理解", "doc"),
    ("cloze", ClozePage, "选词填空", "grid"),
    ("trans", TranslatePage, "翻译训练", "swap"),
    ("writing", WritingPage, "作文模板", "sheet"),
    ("phrase", PhrasePage, "短语搭配", "tag"),
    ("grammar", GrammarPage, "语法知识", "brace"),
    ("mock", MockPage, "模拟考试", "clock"),
    ("import", ImportPage, "题库导入", "import"),
    ("stats", StatsPage, "学习统计", "chart"),
]

# 导航分组：让 14 项不显得拥挤
NAV_GROUPS = [
    ("学习", ("vocab", "wordbook", "wrong")),
    ("训练", ("dict", "listen", "read", "cloze", "trans", "writing")),
    ("资料", ("phrase", "grammar")),
    ("进度", ("mock", "import", "stats")),
]

NAV_W = 208

# 顶栏副标题：每个页面的定位说明
PAGE_HINTS = {
    "vocab": "看词 → 想想意思 → 点开释义，再用键盘快速过一遍",
    "wordbook": "收藏的重点词都在这里，支持筛选和朗读",
    "wrong": "做错的题自动收进来，重做对了就出本",
    "dict": "听音写句，交卷后按词判分，错词会标红",
    "listen": "先听音频，再逐题作答，交卷看解析",
    "read": "选篇目 → 读文章 → 做单选题 → 看解析",
    "cloze": "读短文 → 从词库选词填空 → 提交判分",
    "trans": "看中文写英文，交卷后按相似度打分",
    "writing": "背模板、套框架，写出来更稳",
    "phrase": "常用短语集中刷，边记边朗读",
    "grammar": "语法点速查，配例句理解",
    "mock": "按考试节奏完整走一遍，交卷出分",
    "import": "把自己的题库导进来，格式见页面说明",
    "stats": "看进度、看薄弱项、看每场练习记录",
}

# 状态栏右侧的页内快捷键提示——只对真的有键盘操作的页面显示
PAGE_TIPS = {
    "vocab": "空格 显示释义　·　← → 切换单词",
    "wordbook": "双击单词可直接朗读",
    "phrase": "空格 显示释义　·　← → 切换短语",
    "dict": "Ctrl + Enter 提交判分",
    "read": "选项可整行点选",
    "trans": "Ctrl + Enter 提交判分",
}


# --------------------------------------------------------------------------- #
# 左侧导航项（自绘圆角）
# --------------------------------------------------------------------------- #
class NavItem(tk.Canvas):
    H = 36

    def __init__(self, parent, key, text, icon, command):
        super().__init__(parent, bg=ui.CARD, highlightthickness=0, bd=0,
                         height=self.H, cursor="hand2")
        self.key = key
        self.text = text
        self.icon = icon
        self.command = command
        self.selected = False
        self.hover = False
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", lambda e: self.command(self.key))
        self.bind("<Configure>", lambda e: self._draw())
        self.after(1, self._draw)

    def _enter(self, _e):
        self.hover = True
        self._draw()

    def _leave(self, _e):
        self.hover = False
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.H
        if w <= 2:
            w = NAV_W - 24
        if self.selected:
            ui.round_rect(self, 0, 2, w, h - 2, ui.R_BTN,
                          fill=ui.PRIMARY_SOFT, outline=ui.PRIMARY_SOFT)
            # 左侧圆角主色指示条
            ui.round_rect(self, 0, 9, 3.5, h - 9, 1.75,
                          fill=ui.PRIMARY, outline=ui.PRIMARY)
            fg, font = ui.PRIMARY_DEEP, (ui.FONT_FAMILY, 10, "bold")
        elif self.hover:
            ui.round_rect(self, 0, 2, w, h - 2, ui.R_BTN,
                          fill=ui.PRIMARY_TINT, outline=ui.PRIMARY_TINT)
            fg, font = ui.PRIMARY_DEEP, ui.FONT_UI
        else:
            fg, font = ui.TEXT_MUTED, ui.FONT_UI
        ui.icon(self, self.icon, 13, (h - 17) / 2, 17, fg, width=1.6)
        self.create_text(40, h / 2, text=self.text, anchor="w",
                         fill=fg, font=font)

    def set_selected(self, flag):
        self.selected = bool(flag)
        self._draw()


# --------------------------------------------------------------------------- #
# 页面宿主（替代 ttk.Notebook，接口兼容）
# --------------------------------------------------------------------------- #
class NavHost(tk.Frame):
    """承载所有页面。提供 ttk.Notebook 的常用子集接口：
    add(page) / select(target) / index(target) / enable_traversal() /
    bind("<<NotebookTabChanged>>", fn)
    """

    def __init__(self, parent):
        super().__init__(parent, bg=ui.BG)
        self.body = tk.Frame(self, bg=ui.BG)
        self.body.pack(fill="both", expand=True)
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=1)
        self._pages = []
        self._cur = -1
        self._listeners = []

    # ---- 注册 ----
    def add(self, page, text=""):
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_remove()
        self._pages.append((page, text))
        return page

    def enable_traversal(self):
        pass

    def bind(self, seq, func, add=None):
        if seq == "<<NotebookTabChanged>>":
            self._listeners.append(func)
        return ""

    # ---- 索引 ----
    def index(self, target="current"):
        if target in ("current", None):
            return self._cur
        for i, (p, _t) in enumerate(self._pages):
            if p is target or p == target:
                return i
        try:
            return int(target)
        except (TypeError, ValueError):
            return -1

    def tabs(self):
        return [p for p, _t in self._pages]

    # ---- 切换 ----
    def select(self, target):
        idx = self.index(target)
        if idx < 0 or idx >= len(self._pages):
            return
        if idx == self._cur:
            return
        for i, (p, _t) in enumerate(self._pages):
            if i == idx:
                p.grid()
                p.tkraise()
            else:
                p.grid_remove()
        self._cur = idx
        for fn in list(self._listeners):
            try:
                fn()
            except Exception:  # noqa: BLE001
                import traceback
                traceback.print_exc()


# --------------------------------------------------------------------------- #
# 主应用
# --------------------------------------------------------------------------- #
class App:
    def __init__(self, root):
        self.root = root
        root.title(TITLE)
        root.configure(bg=ui.BG)

        ui.setup_style(root)
        ui.center_window(root, 1200, 800)
        try:
            root.minsize(1040, 680)
        except tk.TclError:
            pass

        # 核心服务
        self.store = store.Store()
        try:
            cetpack.import_pack(self.store)
        except Exception as e:
            print("数据包导入跳过：", e)

        self.tts = tts.TTSEngine()

        # TTS 控制变量
        self.voice_var = tk.StringVar(value=getattr(self.tts, "voice_en", "") or "")
        self.pitch_var = tk.IntVar(value=getattr(self.tts, "pitch", 0))
        self.speed_var = tk.IntVar(value=5)      # 1~9，5 = 正常语速
        self._voice_map = {}
        self.status_var = tk.StringVar(value="就绪")

        self.notebook = None
        self.pages = {}
        self._nav_items = {}

        self._build_shell()
        self._build_nav()
        self._build_header()
        self._build_body()
        self._build_statusbar()

        self.switch_to("vocab")
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- 外框：侧栏 + 主区 ----------
    def _build_shell(self):
        self.shell = tk.Frame(self.root, bg=ui.BG)
        self.shell.pack(fill="both", expand=True)

        self.side = tk.Frame(self.shell, bg=ui.CARD, width=NAV_W)
        self.side.pack(side="left", fill="y")
        self.side.pack_propagate(False)

        # 侧栏右侧 1px 分隔
        tk.Frame(self.shell, bg=ui.BORDER, width=1).pack(side="left", fill="y")

        self.main = tk.Frame(self.shell, bg=ui.BG)
        self.main.pack(side="left", fill="both", expand=True)

    # ---------- 侧栏 ----------
    def _build_nav(self):
        # 品牌区：App 图标（暖红毕业帽）+ 标题
        brand = tk.Frame(self.side, bg=ui.CARD)
        brand.pack(fill="x", padx=16, pady=(18, 14))

        logo = tk.Canvas(brand, width=40, height=40, bg=ui.CARD,
                         highlightthickness=0, bd=0)
        logo.pack(side="left")
        _logo_img = _load_brand_image(40)
        if _logo_img is not None:
            logo._img_ref = _logo_img            # 防 GC
            logo.create_image(20, 20, image=_logo_img)
        else:
            ui.round_rect(logo, 0, 0, 40, 40, 11, fill=ui.PRIMARY,
                          outline=ui.PRIMARY)
            logo.create_text(20, 20, text="四", fill="#FFFFFF",
                             font=(ui.FONT_FAMILY, 17, "bold"))

        txt = tk.Frame(brand, bg=ui.CARD)
        txt.pack(side="left", padx=(10, 0))
        tk.Label(txt, text="四六级", bg=ui.CARD, fg=ui.TEXT,
                 font=(ui.FONT_FAMILY, 12, "bold")).pack(anchor="w")
        tk.Label(txt, text="学习助手", bg=ui.CARD, fg=ui.TEXT_MUTED,
                 font=ui.FONT_SMALL).pack(anchor="w")

        # 导航滚动区
        self.nav_scroll, self.nav_inner = ui.scrollable(self.side, bg=ui.CARD)
        self.nav_scroll.pack(fill="both", expand=True, padx=(8, 4))

        labels = {}
        for key, cls, text, icon in PAGES:
            labels[key] = (text, icon)

        for group_name, keys in NAV_GROUPS:
            g = tk.Label(self.nav_inner, text=group_name, bg=ui.CARD,
                         fg=ui.TEXT_FAINT, font=(ui.FONT_FAMILY, 8, "bold"),
                         anchor="w")
            g.pack(fill="x", padx=14, pady=(8, 2))
            for key in keys:
                if key not in labels:
                    continue
                text, icon = labels[key]
                it = NavItem(self.nav_inner, key, text, icon, self.switch_to)
                it.pack(fill="x", pady=1)
                self._nav_items[key] = it

    # ---------- 顶栏 ----------
    def _build_header(self):
        bar = tk.Frame(self.main, bg=ui.CARD)
        bar.pack(fill="x")
        tk.Frame(self.main, bg=ui.BORDER, height=1).pack(fill="x")

        left = tk.Frame(bar, bg=ui.CARD)
        left.pack(side="left", padx=(20, 0), pady=(9, 9))
        self.page_title = tk.Label(left, text="词汇记忆", bg=ui.CARD, fg=ui.TEXT,
                                   font=(ui.FONT_FAMILY, 14, "bold"), anchor="w")
        self.page_title.pack(anchor="w")
        self.page_sub = tk.Label(left, text="", bg=ui.CARD,
                                 fg=ui.TEXT_FAINT, font=(ui.FONT_FAMILY, 8),
                                 anchor="w")
        self.page_sub.pack(anchor="w")

        right = tk.Frame(bar, bg=ui.CARD)
        right.pack(side="right", padx=16, pady=10)

        def small_label(t):
            return tk.Label(right, text=t, bg=ui.CARD, fg=ui.TEXT_MUTED,
                            font=ui.FONT_SMALL)

        voices = []
        self._voice_map = {}
        try:
            for text, value, _desc in self.tts.voice_options():
                voices.append(text)
                self._voice_map[text] = value
        except Exception:
            voices = []
        if voices and self.voice_var.get() not in voices:
            self.voice_var.set(voices[0])

        # 试听按钮先占右侧，保证任何情况下都不会被挤出窗口
        try_btn = ui.button(right, text="试听", icon="speaker", kind="soft",
                            command=self._try_speak, height=32)
        try_btn.pack(side="right", padx=(10, 0))

        small_label("语速").pack(side="left", padx=(0, 5))
        speed_sp = ttk.Spinbox(right, from_=1, to=9, width=3,
                               textvariable=self.speed_var,
                               command=self._on_rate_change)
        speed_sp.pack(side="left", padx=(0, 12))
        speed_sp.bind("<Return>", self._on_rate_change)

        small_label("音色").pack(side="left", padx=(0, 5))
        voice_cb = ttk.Combobox(right, textvariable=self.voice_var,
                                values=voices, width=15, state="readonly")
        voice_cb.pack(side="left")
        voice_cb.bind("<<ComboboxSelected>>", self._on_voice_change)

    # ---------- 内容区 ----------
    def _build_body(self):
        wrap = tk.Frame(self.main, bg=ui.BG)
        wrap.pack(fill="both", expand=True, padx=ui.S_MD, pady=(ui.S_MD, 0))

        nb = NavHost(wrap)
        nb.pack(fill="both", expand=True)
        self.notebook = nb

        for key, cls, text, icon in PAGES:
            page = cls(nb.body, self)
            self.pages[key] = page
            nb.add(page, text=text)

    # ---------- 状态栏 ----------
    def _build_statusbar(self):
        bar = tk.Frame(self.main, bg=ui.BG, height=30)
        bar.pack(fill="x", padx=ui.S_MD, pady=(4, 6))
        bar.pack_propagate(False)

        self.status_dot = tk.Canvas(bar, width=8, height=8, bg=ui.BG,
                                    highlightthickness=0, bd=0)
        self.status_dot.pack(side="left", padx=(6, 6), pady=10)
        self.status_dot.create_oval(0, 0, 7, 7, fill=ui.OK, outline="")

        tk.Label(bar, textvariable=self.status_var, bg=ui.BG,
                 fg=ui.TEXT_MUTED, font=(ui.FONT_FAMILY, 9),
                 anchor="w").pack(side="left")

        self.tip_var = tk.StringVar(value="")
        tk.Label(bar, textvariable=self.tip_var, bg=ui.BG,
                 fg=ui.TEXT_FAINT, font=(ui.FONT_FAMILY, 8),
                 anchor="e").pack(side="right", padx=8)

    # ---------- 页面切换 ----------
    def switch_to(self, key):
        if key not in self.pages:
            return
        self.notebook.select(self.pages[key])
        for k, item in self._nav_items.items():
            item.set_selected(k == key)
        for k, cls, text, icon in PAGES:
            if k == key:
                self.page_title.config(text=text)
                self.page_sub.config(text=PAGE_HINTS.get(k, ""))
                self.tip_var.set(PAGE_TIPS.get(k, ""))
                break

    # ---------- 事件 ----------
    def _on_voice_change(self, _e=None):
        label = self.voice_var.get()
        name = self._voice_map.get(label, label)
        try:
            self.tts.set_voice(name)
            desc = self.tts.current_voice_desc()
            self.set_status("音色已切换：%s%s" % (label.split("·")[0].strip(),
                                            ("　" + desc) if desc else ""))
        except Exception as e:
            self.set_status(f"切换音色失败：{e}")

    def _on_pitch_change(self, _e=None):
        try:
            self.tts.set_pitch(int(self.pitch_var.get()))
        except Exception:
            pass

    def _on_rate_change(self, _e=None):
        try:
            level = int(self.speed_var.get())
            self.tts.rate = max(-10, min(10, level - 5))
            # Edge 音色用 1~9 的原始档位换算百分比
            self.tts.speed_ui = level
        except Exception:
            pass

    def _try_speak(self):
        self.set_status("试听中…")
        try:
            self.tts.speak("Hello, let's start learning.", blocking=False)
        except Exception as e:
            self.set_status(f"试听失败：{e}")

    def _on_tab_change(self, _e=None):
        nb = self.notebook
        if nb is None:
            return
        try:
            idx = nb.index("current")
            page = list(self.pages.values())[idx]
            if hasattr(page, "on_show"):
                page.on_show()
        except Exception:
            pass

    def _on_close(self):
        try:
            self.tts.stop()
        except Exception:
            pass
        try:
            self.store.close()
        except Exception:
            pass
        self.root.destroy()

    def set_status(self, text):
        self.status_var.set(text)

    def refresh_all(self):
        for page in self.pages.values():
            if hasattr(page, "reload_data"):
                try:
                    page.reload_data()
                except Exception as e:
                    print("reload_data 失败：", e)


def _lock_dpi_scaling(root):
    """把 Tk 字号缩放锁到 96dpi 基准，保证打包版与源码版观感一致。

    PyInstaller 打出来的 exe 会被系统按真 DPI 处理（150% 缩放屏上 144dpi），
    Tk 的 scaling 随之变成 2.0，所有字号放大 1.5 倍——固定尺寸窗口里右侧就被
    挤出可视区。这里统一回 96/72 基准（即源码版运行时的表现）。
    """
    try:
        fpixels = root.winfo_fpixels("1i")
    except Exception:
        fpixels = 96.0
    try:
        if fpixels > 100:                       # 说明进程确实按高 DPI 渲染
            root.tk.call("tk", "scaling", 96.0 / 72.0)
    except Exception:
        pass


def _app_dir():
    """exe 所在目录（打包后）或源码目录（开发时）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _set_app_icon(root):
    """给窗口和任务栏换上 App 图标（暖红毕业帽）。

    依次尝试三处：exe 内嵌资源目录、exe 同目录、源码目录。
    .ico 用 iconbitmap（Windows 任务栏认它），另用 iconphoto 兜一层，
    这样 Alt+Tab 和任务栏都能拿到彩色大图。
    """
    names = ("icon_app.ico", "cet.ico")
    dirs = []
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        dirs.append(meipass)
    dirs.append(_app_dir())
    dirs.append(os.path.dirname(os.path.abspath(__file__)))

    seen = set()
    for d in dirs:
        if not d or d in seen:
            continue
        seen.add(d)
        for name in names:
            p = os.path.join(d, name)
            if not os.path.isfile(p):
                continue
            ok = False
            try:
                root.iconbitmap(default=p)
                ok = True
            except Exception:
                pass
            if not ok:
                try:
                    root.wm_iconbitmap(p)
                    ok = True
                except Exception:
                    pass
            # 再补一层彩色大图（iconphoto 影响 Alt+Tab 缩略图）
            for png_name in ("icon_app.png", "icon_app64.png"):
                pp = os.path.join(d, png_name)
                if not os.path.isfile(pp):
                    continue
                try:
                    img = tk.PhotoImage(file=pp)
                    root.iconphoto(True, img)
                    root._cet_icon_photo = img     # 防止被 GC 掉
                except Exception:
                    pass
            if ok:
                return p
    return ""


def _load_brand_image(size=40):
    """读 App 图标给侧栏品牌区用；找不到就返回 None，调用方回退色块 logo。"""
    names = ("icon_app.png", "cet.ico")
    dirs = []
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        dirs.append(meipass)
    dirs.append(_app_dir())
    dirs.append(os.path.dirname(os.path.abspath(__file__)))

    seen = set()
    for d in dirs:
        if not d or d in seen:
            continue
        seen.add(d)
        for name in names:
            p = os.path.join(d, name)
            if not os.path.isfile(p):
                continue
            try:
                if name.lower().endswith(".ico"):
                    img = tk.PhotoImage(file=p, format="ico")
                else:
                    img = tk.PhotoImage(file=p)
                if img.width() != size:
                    # PhotoImage 只能整数倍缩放，用 subsample 近似到目标尺寸
                    f = max(1, int(round(img.width() / float(size))))
                    if f > 1:
                        img = img.subsample(f, f)
                return img
            except Exception:
                continue
    return None


def _sweep_old_mei():
    """启动时清掉上一次运行残留的 _MEI 解压目录（后台线程，绝不阻塞启动）。

    PyInstaller onefile 退出时正常会自己删，但被强杀 / 崩溃时会留下约 27 MB。
    只删「不是当前进程正在用的」那一批，且只在 TEMP 目录里动手，
    删不掉就跳过——任何异常都吞掉，不能因为清理把程序拖挂。
    """
    def work():
        try:
            import glob
            import shutil
            import threading  # noqa: F401

            cur = ""
            meipass = getattr(sys, "_MEIPASS", "")
            if meipass:
                cur = os.path.normcase(os.path.abspath(meipass))

            bases = []
            for key in ("TEMP", "TMP"):
                v = os.environ.get(key)
                if v and os.path.isdir(v):
                    bases.append(v)
            real = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp")
            if os.path.isdir(real):
                bases.append(real)

            seen = set()

            def sweep(base):
                """清 base 下的 _MEI*，再扫一层重定向子 TEMP。"""
                nb = os.path.normcase(os.path.abspath(base))
                if nb in seen or not os.path.isdir(base):
                    return
                seen.add(nb)
                for p in glob.glob(os.path.join(base, "_MEI*")):
                    if not os.path.isdir(p):
                        continue
                    if cur and os.path.normcase(os.path.abspath(p)) == cur:
                        continue          # 当前进程正在用，跳过
                    # 只清 6 小时以上的，避免误伤刚启动的另一个实例
                    try:
                        import time as _t
                        if _t.time() - os.path.getmtime(p) < 6 * 3600:
                            continue
                    except OSError:
                        continue
                    shutil.rmtree(p, ignore_errors=True)

            for base in bases:
                sweep(base)
            # 子 TEMP（终端/编排环境可能重定向 TEMP）也扫一层
            for base in list(bases):
                for sub in glob.glob(os.path.join(base, "*")):
                    if os.path.isdir(sub):
                        sweep(sub)
        except Exception:                 # noqa: BLE001
            pass

    try:
        import threading
        t = threading.Thread(target=work, daemon=True)
        t.start()
    except Exception:                     # noqa: BLE001
        pass


def main():
    root = tk.Tk()
    _lock_dpi_scaling(root)
    _set_app_icon(root)
    _sweep_old_mei()          # 后台清上次残留，不阻塞启动
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
