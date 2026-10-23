# -*- coding: utf-8 -*-
"""界面公共样式与小组件 —— 设计 token 集中定义。

设计参考（提炼自优秀开源产品，纯 ttk/canvas 复刻，零新依赖）：
  - ttkbootstrap (israel-dryer)：语义化意图色 primary/success/danger、扁平+圆角、
    8px 间距栅格、Meter 环形进度。
  - Sun Valley / Azure ttk (rdbende)：Win11 圆角按钮、主色高亮选中态、浅灰底+白卡。
  - 墨墨背单词 / 不背单词 / Anki：大字号单词卡、留白、进度环、胶囊标签。

落地约定：
  * 所有颜色/圆角/间距/字体只从这里取，页面里不再散落硬编码 hex。
  * 圆角用 tk.Canvas 画（ttk 无原生圆角），对外 API 保持向后兼容：
      card(parent)         -> (outer, inner)   # 圆角白卡
      hline(parent)        -> Frame           # 细分隔线
      scrollable(parent)   -> (outer, inner)  # 可滚动容器
      center_window(w,h)   -> None
  * 新增：
      button(parent, ...)  -> 圆角按钮（替代 ttk.Button）
      chip(parent, ...)    -> 胶囊标签
      meter(parent, ...)   -> 环形进度
      empty_state(...)     -> 统一空状态
"""

import tkinter as tk
from tkinter import ttk

# --------------------------------------------------------------------------- #
# ① 色板 —— 墨墨暖红主色体系（语义化，禁止页面里另写 hex）
# --------------------------------------------------------------------------- #
BG = "#F6F7F9"            # 页面底：极浅冷灰，让白卡浮起来
CARD = "#FFFFFF"          # 卡片白
CARD_SOFT = "#FBFBFC"     # 卡内次级底：输入区/结果区/表头
PRIMARY = "#E8455F"       # 主色：墨墨暖红（饱和但不刺眼）
PRIMARY_DARK = "#CF3752"  # hover / active
PRIMARY_DEEP = "#A82A42"  # 按下 / 强调描边
PRIMARY_SOFT = "#FDEEF1"  # 主色浅底：选中态、高亮 chip、进度环底
PRIMARY_TINT = "#FDF6F7"  # 更浅的一层，用于整块背景
TEXT = "#1F2933"          # 正文
TEXT_MUTED = "#6B7280"    # 次要文字
TEXT_FAINT = "#9CA3AF"    # 弱提示 / 占位
BORDER = "#E6E8EC"        # 细边框
BORDER_SOFT = "#F0F1F4"   # 更浅分隔线
OK = "#16A34A"            # 正确 / 成功
OK_SOFT = "#E7F7EC"       # 成功浅底
WARN = "#E8455F"          # 错误 / 危险（与主色同源，保持体系一致）
WARN_SOFT = "#FDEEF1"
AMBER = "#D97706"         # 提醒 / 一般
AMBER_SOFT = "#FEF4E7"
INFO = "#2563EB"          # 信息蓝（少量点缀，如听力）
INFO_SOFT = "#EAF1FF"

# 兼容旧命名（部分页面可能引用）
WHITE = "#FFFFFF"

# --------------------------------------------------------------------------- #
# ② 圆角 & 间距 —— 8px 栅格
# --------------------------------------------------------------------------- #
R_CARD = 12               # 卡片圆角
R_BTN = 8                 # 按钮圆角
R_INPUT = 8               # 输入框圆角
R_CHIP = 999              # 胶囊
R_METER = 999

S_XS = 4
S_SM = 8
S_MD = 12
S_LG = 16
S_XL = 24

PAGE_PAD = 16             # 页面外边距
CARD_PAD = 16             # 卡片内边距
GAP = 12                  # 卡片间距

BORDER_W = 1

# --------------------------------------------------------------------------- #
# ③ 字体
# --------------------------------------------------------------------------- #
FONT_FAMILY = "Microsoft YaHei UI"
FONT_UI = (FONT_FAMILY, 10)
FONT_UI_B = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_SUBTITLE = (FONT_FAMILY, 12, "bold")
FONT_TITLE = (FONT_FAMILY, 17, "bold")
FONT_HERO = (FONT_FAMILY, 26, "bold")          # 统计大数字
FONT_WORD = ("Georgia", 40, "bold")            # 单词卡主词
FONT_WORD_MD = ("Georgia", 28, "bold")
FONT_PHON = ("Consolas", 12)
FONT_MONO = ("Consolas", 11)
FONT_EX = ("Georgia", 12)


# --------------------------------------------------------------------------- #
# ④ 圆角图形基础工具
# --------------------------------------------------------------------------- #
def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    """在 canvas 上画圆角矩形。

    注意：不能用 create_polygon(smooth=True) —— Tk 的 smooth 是贝塞尔样条，
    会把直角边的顶点当控制点，圆角被"抹平"成矩形。这里改为在四个角上
    按角度插值出真实圆弧顶点，再用普通多边形连接，圆角才精确可控。
    """
    import math

    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    if r < 0.5:
        return canvas.create_rectangle(x1, y1, x2, y2, **kw)

    # 每个角用 6 段折线近似 90° 圆弧，96dpi 下肉眼看不出折角
    steps = 6
    pts = []
    corners = (
        (x2 - r, y1 + r, -90, 0),    # 右上
        (x2 - r, y2 - r, 0, 90),     # 右下
        (x1 + r, y2 - r, 90, 180),   # 左下
        (x1 + r, y1 + r, 180, 270),  # 左上
    )
    for cx, cy, a0, a1 in corners:
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            pts.append(cx + r * math.cos(a))
            pts.append(cy + r * math.sin(a))
    return canvas.create_polygon(pts, **kw)


class RoundedFrame(tk.Frame):
    """圆角卡片：外层 canvas 画底，内层 Frame 放内容。

    用法：rf = RoundedFrame(parent, bg=CARD, radius=R_CARD, ...)
          rf.inner  # 往里塞组件
    """

    def __init__(self, parent, bg=CARD, border=BORDER, radius=R_CARD,
                 border_w=BORDER_W, outer_bg=None, **kw):
        super().__init__(parent, bg=outer_bg or _bg_of(parent), highlightthickness=0, bd=0, **kw)
        self._bg = bg
        self._border = border
        self._radius = radius
        self._border_w = border_w
        self._outer_bg = outer_bg or _bg_of(parent)
        # 关键：Canvas 的默认请求尺寸是 382x268，若放任不管，每张卡片都会被
        # 撑到至少 268 高（这正是"卡内大片留白"的根因）。先压到 1x1，再由
        # 内容帧的真实请求尺寸回调修正，卡片就刚好裹住内容。
        self._bgc = tk.Canvas(self, bg=self._outer_bg, width=1, height=1,
                              highlightthickness=0, bd=0)
        self._bgc.pack(fill="both", expand=True)
        self.inner = tk.Frame(self._bgc, bg=bg, highlightthickness=0, bd=0)
        self._win = self._bgc.create_window(0, 0, window=self.inner, anchor="nw")
        self._bgc.bind("<Configure>", self._redraw)
        self.inner.bind("<Configure>", self._sync_scroll)
        self._req_cache = None
        self.after(10, self._fit_req)

    def _sync_scroll(self, _e=None):
        pass

    def _fit_req(self):
        """把内容帧的期望尺寸同步给 canvas，让卡片高度贴合内容。"""
        try:
            rw = max(1, self.inner.winfo_reqwidth())
            rh = max(1, self.inner.winfo_reqheight())
        except tk.TclError:
            return
        inset = min(max(2, self._radius), 6)
        if self._req_cache != (rw, rh):
            self._req_cache = (rw, rh)
            try:
                self._bgc.configure(width=rw + inset * 2, height=rh + inset * 2)
            except tk.TclError:
                pass
        self.after(120, self._fit_req)

    def _redraw(self, _e=None):
        c = self._bgc
        w, h = c.winfo_width(), c.winfo_height()
        if w <= 2 or h <= 2:
            return
        c.delete("bgshape")
        r = max(2, self._radius)
        bw = max(1, self._border_w)
        # 外框（边框色）+ 内底（卡片色），都是圆角
        round_rect(c, 0, 0, w, h, r, fill=self._border,
                   outline=self._border, tags="bgshape")
        round_rect(c, bw, bw, w - bw, h - bw, max(0, r - bw),
                   fill=self._bg, outline=self._bg, tags="bgshape")
        c.tag_lower("bgshape")
        # 内容仅沿四边内缩几像素：既不遮住圆角边框弧线，也不额外吃掉页面留白
        inset = min(r, 6)
        c.itemconfigure(self._win, width=max(1, w - inset * 2),
                        height=max(1, h - inset * 2))
        c.coords(self._win, inset, inset)


def _bg_of(widget):
    """取父容器背景色，保证圆角外部不露白。"""
    try:
        return widget.cget("bg")
    except tk.TclError:
        return BG


# --------------------------------------------------------------------------- #
# ⑤ 样式表
# --------------------------------------------------------------------------- #
def setup_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", font=FONT_UI, background=BG, foreground=TEXT)
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD, relief="flat", borderwidth=0)
    style.configure("Soft.TFrame", background=CARD_SOFT, borderwidth=0)

    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Card.TLabel", background=CARD, foreground=TEXT)
    style.configure("Muted.TLabel", background=BG, foreground=TEXT_MUTED)
    style.configure("CardMuted.TLabel", background=CARD, foreground=TEXT_MUTED)
    style.configure("Faint.TLabel", background=CARD, foreground=TEXT_FAINT, font=FONT_SMALL)
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=FONT_TITLE)
    style.configure("Sub.TLabel", background=BG, foreground=TEXT, font=FONT_SUBTITLE)
    style.configure("CardSub.TLabel", background=CARD, foreground=TEXT, font=FONT_SUBTITLE)
    style.configure("Word.TLabel", background=CARD, foreground=TEXT, font=FONT_WORD)
    style.configure("Phon.TLabel", background=CARD, foreground=TEXT_MUTED, font=FONT_PHON)
    style.configure("Big.TLabel", background=CARD, foreground=PRIMARY, font=FONT_HERO)
    style.configure("OK.TLabel", background=CARD, foreground=OK, font=FONT_UI_B)
    style.configure("Warn.TLabel", background=CARD, foreground=WARN, font=FONT_UI_B)
    style.configure("Amber.TLabel", background=CARD, foreground=AMBER, font=FONT_UI_B)

    # 侧边栏 / 顶栏（自绘 Frame + Label，这里只给 ttk 控件留兜底）
    style.configure("Nav.TFrame", background=CARD)

    # Notebook：保留兜底样式（主界面已改用侧边导航）
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(18, 9), font=FONT_UI,
                    background=BG, borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", CARD)],
              foreground=[("selected", PRIMARY)])

    # ttk 按钮：作为兜底（页面统一改用 ui.button）
    style.configure("TButton", font=FONT_UI, padding=(12, 6))
    style.configure("Primary.TButton", font=FONT_UI_B, padding=(14, 7))
    style.map("Primary.TButton",
              background=[("active", PRIMARY_DARK), ("!disabled", PRIMARY)],
              foreground=[("!disabled", WHITE)])
    style.configure("Ghost.TButton", font=FONT_UI, padding=(12, 7))
    style.map("Ghost.TButton",
              background=[("active", PRIMARY_SOFT), ("!disabled", CARD)],
              foreground=[("active", PRIMARY), ("!disabled", TEXT)])
    style.configure("Danger.TButton", font=FONT_UI, padding=(12, 7))
    style.map("Danger.TButton",
              background=[("active", WARN_SOFT), ("!disabled", CARD)],
              foreground=[("!disabled", WARN)])

    # 输入类
    style.configure("TEntry", padding=7, fieldbackground=WHITE, borderwidth=1,
                    relief="flat", bordercolor=BORDER, lightcolor=BORDER,
                    darkcolor=BORDER, insertcolor=PRIMARY)
    style.map("TEntry",
              bordercolor=[("focus", PRIMARY)],
              lightcolor=[("focus", PRIMARY)],
              darkcolor=[("focus", PRIMARY)])
    style.configure("TCombobox", padding=6, fieldbackground=WHITE, borderwidth=1,
                    arrowsize=14, relief="flat", bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, background=WHITE)
    style.map("TCombobox",
              fieldbackground=[("readonly", WHITE)],
              bordercolor=[("focus", PRIMARY)],
              lightcolor=[("focus", PRIMARY)],
              darkcolor=[("focus", PRIMARY)])
    style.configure("TSpinbox", padding=5, borderwidth=1, relief="flat",
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
    style.map("TSpinbox",
              bordercolor=[("focus", PRIMARY)],
              lightcolor=[("focus", PRIMARY)],
              darkcolor=[("focus", PRIMARY)])

    style.configure("Horizontal.TProgressbar", background=PRIMARY,
                    troughcolor=BORDER_SOFT, borderwidth=0, thickness=8)
    style.configure("TRadiobutton", background=CARD, font=FONT_UI, focuscolor=PRIMARY)
    style.map("TRadiobutton",
              foreground=[("active", PRIMARY)],
              background=[("active", CARD)])
    style.configure("TCheckbutton", background=CARD, font=FONT_UI, focuscolor=PRIMARY)
    style.map("TCheckbutton",
              foreground=[("active", PRIMARY)],
              background=[("active", CARD)])

    # Treeview：表头浅底、行选中主色浅底 + 主色字
    style.configure("Treeview",
                    background=WHITE, fieldbackground=WHITE, foreground=TEXT,
                    rowheight=30, font=FONT_UI, borderwidth=0, relief="flat")
    style.configure("Treeview.Heading",
                    background=CARD_SOFT, foreground=TEXT_MUTED,
                    font=FONT_UI_B, relief="flat", borderwidth=0, padding=(8, 7))
    style.map("Treeview.Heading", background=[("active", PRIMARY_SOFT)],
              foreground=[("active", PRIMARY)])
    style.map("Treeview",
              background=[("selected", PRIMARY_SOFT)],
              foreground=[("selected", PRIMARY_DEEP)])
    style.configure("Vertical.TScrollbar", background=BORDER, troughcolor=CARD,
                    bordercolor=CARD, lightcolor=BORDER, darkcolor=BORDER,
                    width=11, borderwidth=0, arrowsize=0, relief="flat")
    style.map("Vertical.TScrollbar",
              background=[("active", TEXT_FAINT), ("!disabled", BORDER)])
    style.configure("Horizontal.TScrollbar", background=BORDER,
                    troughcolor=CARD, bordercolor=CARD, borderwidth=0,
                    arrowsize=0, relief="flat")

    try:
        root.option_add("*Font", FONT_UI)
        root.configure(bg=BG)
    except tk.TclError:
        pass
    return style


# --------------------------------------------------------------------------- #
# ⑥ 卡片 / 分隔 / 滚动容器
# --------------------------------------------------------------------------- #
def card(parent, bg=None, radius=R_CARD, border=BORDER, **kw):
    """圆角白卡。返回 (outer, inner)。

    向后兼容：旧调用 `outer, inner = ui.card(parent)`、
    `ui.card(parent, bg=None)` 均可用；inner 是普通 Frame，可直接 pack 子组件。
    """
    bg = bg or CARD
    rf = RoundedFrame(parent, bg=bg, border=border, radius=radius, **kw)
    return rf, rf.inner


def hline(parent, bg=BORDER_SOFT, pady=(S_SM, S_SM)):
    f = tk.Frame(parent, bg=bg, height=1)
    f.pack(fill="x", pady=pady)
    return f


def scrollable(parent, bg=BG, autohide=True):
    """返回 (外层frame, 内部可放内容的frame)。

    autohide=True 时滚动条只在内容超出可视区时才出现，
    避免短内容页右侧挂一条永远不动的灰条。
    """
    outer = tk.Frame(parent, bg=bg, highlightthickness=0, bd=0)
    # Canvas 默认请求尺寸是 382x268，会把父容器 req 撑大、破坏 PanedWindow
    # 的比例分配，这里压到 1x1，实际尺寸交给 pack(fill/expand) 决定。
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0,
                       width=1, height=1)
    vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=bg)
    win = canvas.create_window((0, 0), window=inner, anchor="nw")

    state = {"shown": True}

    def _sync_bar():
        if not autohide:
            return
        try:
            need = inner.winfo_reqheight() > canvas.winfo_height() + 1
        except tk.TclError:
            return
        if need and not state["shown"]:
            state["shown"] = True
            vsb.pack(side="right", fill="y")
        elif not need and state["shown"]:
            state["shown"] = False
            vsb.pack_forget()

    def _on_config(_e):
        canvas.configure(scrollregion=canvas.bbox("all"))
        _sync_bar()

    inner.bind("<Configure>", _on_config)
    canvas.bind("<Configure>", lambda e: (
        canvas.itemconfigure(win, width=e.width), _sync_bar()))
    canvas.configure(yscrollcommand=vsb.set)
    canvas.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    def _wheel(e):
        try:
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        except tk.TclError:
            pass

    canvas.bind("<MouseWheel>", _wheel)
    return outer, inner


# --------------------------------------------------------------------------- #
# ⑦ 圆角按钮（自绘 canvas，支持 hover / primary / ghost / danger / soft）
# --------------------------------------------------------------------------- #
class RoundButton(tk.Canvas):
    """圆角按钮。ttk 无圆角，故用 Canvas 自绘。

    kind: "primary" 实心主色 | "ghost" 白底细边 | "danger" 红字白底 |
          "soft" 主色浅底 | "text" 纯文字
    """

    _PAD_X = 16
    _PAD_Y = 8

    def __init__(self, parent, text="", command=None, kind="ghost",
                 width=None, height=36, font=None, bg=None, radius=R_BTN,
                 icon="", **kw):
        # 兼容 ttk.Button 传参：style="Primary.TButton" / state="disabled"
        style = kw.pop("style", None)
        state = kw.pop("state", None)
        padding = kw.pop("padding", None)
        takefocus = kw.pop("takefocus", None)
        if style:
            kind = self._STYLE_KIND.get(style, kind)
        self._bg = bg or _bg_of(parent)
        super().__init__(parent, bg=self._bg, highlightthickness=0, bd=0,
                         cursor="hand2" if command else "arrow", **kw)
        if state is not None:
            kw_state_enabled = str(state) not in ("disabled", "0", "False")
        else:
            kw_state_enabled = True
        self._text = text
        self._icon = icon
        self._command = command
        self._kind = kind
        self._radius = radius
        self._font = font or (FONT_UI_B if kind == "primary" else FONT_UI)
        self._h = height
        self._enabled = kw_state_enabled
        self._hover = False
        self._active = False

        # 先按文字估算宽度，父容器分配后再以 grid/pack 的固定宽为准
        self._fixed_w = width is not None
        w = width or self._estimate_width()
        self.configure(width=w, height=height)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda e: self._redraw())
        self.after(1, self._redraw)

    # ---- 尺寸 ----
    def _icon_name(self):
        """icon 若是线性图标名就返回名字，否则返回 None（当作 emoji/文字）。"""
        return self._icon if self._icon in _ICON_NAMES else None

    def _measure(self, text, font):
        """用 tkfont 精确测量文字宽度（比按字符数估算可靠）。"""
        try:
            from tkinter import font as tkfont
            f = tkfont.Font(root=self, font=font)
            return f.measure(text)
        except Exception:
            return sum(13 if ord(ch) > 127 else 7 for ch in text)

    def _estimate_width(self):
        if self._icon_name():
            icon_w = 17 + 7           # 图标 17px + 间距
            return max(64, self._measure(self._text, self._font)
                       + icon_w + self._PAD_X * 2)
        txt = (self._icon + " " if self._icon else "") + self._text
        # 末尾 +2 是给 emoji 回退字体的误差留余量
        return max(64, self._measure(txt, self._font) + self._PAD_X * 2 + 2)

    # ---- 兼容 ttk.Button 的 configure/config 调用习惯 ----
    _STYLE_KIND = {
        "Primary.TButton": "primary",
        "Ghost.TButton": "ghost",
        "Danger.TButton": "danger",
        "Soft.TButton": "soft",
    }

    def configure(self, cnf=None, **kw):
        text = kw.pop("text", None)
        state = kw.pop("state", None)
        style = kw.pop("style", None)
        if "command" in kw:
            self._command = kw.pop("command")
            self.configure(cursor="hand2" if self._command else "arrow")
        if style is not None:
            self._kind = self._STYLE_KIND.get(style, "ghost")
        if state is not None:
            self._enabled = str(state) not in ("disabled", "0", "False")
        if text is not None or state is not None or style is not None:
            self._redraw()
        if kw or cnf:
            super().configure(cnf, **kw)

    config = configure

    def set_text(self, text, icon=None):
        self._text = text
        if icon is not None:
            self._icon = icon
        if not self._fixed_w:
            try:
                super().configure(width=self._estimate_width())
            except tk.TclError:
                pass
        self._redraw()

    def set_icon(self, icon):
        self._icon = icon
        if not self._fixed_w:
            try:
                super().configure(width=self._estimate_width())
            except tk.TclError:
                pass
        self._redraw()

    def set_kind(self, kind):
        self._kind = kind
        self._redraw()

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        self.configure(cursor="hand2" if (self._enabled and self._command) else "arrow")
        self._redraw()

    # ---- 配色 ----
    def _palette(self):
        k = self._kind
        if not self._enabled:
            return dict(fill=BORDER_SOFT, outline=BORDER_SOFT, fg=TEXT_FAINT)
        if k == "primary":
            if self._active:
                return dict(fill=PRIMARY_DEEP, outline=PRIMARY_DEEP, fg=WHITE)
            return dict(fill=PRIMARY_DARK if self._hover else PRIMARY,
                        outline=PRIMARY_DARK if self._hover else PRIMARY, fg=WHITE)
        if k == "danger":
            if self._hover:
                return dict(fill=WARN_SOFT, outline=WARN, fg=WARN)
            return dict(fill=WHITE, outline=BORDER, fg=WARN)
        if k == "soft":
            return dict(fill=PRIMARY_SOFT, outline=PRIMARY_SOFT, fg=PRIMARY_DEEP)
        if k == "text":
            return dict(fill=self._bg, outline=self._bg,
                        fg=PRIMARY if self._hover else TEXT_MUTED)
        # ghost
        if self._hover:
            return dict(fill=PRIMARY_SOFT, outline=PRIMARY, fg=PRIMARY)
        return dict(fill=WHITE, outline=BORDER, fg=TEXT)

    # ---- 绘制 ----
    def _redraw(self, _e=None):
        c = self
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 2 or h <= 2:
            w, h = int(self.cget("width")), int(self.cget("height"))
        c.delete("all")
        pal = self._palette()
        round_rect(c, 0.5, 0.5, w - 0.5, h - 0.5, self._radius,
                   fill=pal["fill"], outline=pal["outline"])
        name = self._icon_name()
        if not name:
            txt = (self._icon + " " if self._icon else "") + self._text
            c.create_text(w / 2, h / 2, text=txt, fill=pal["fg"],
                          font=self._font)
            return
        # 线性图标 + 文字：整体水平居中
        gap = 7 if self._text else 0
        isz = 17
        tw = self._measure(self._text, self._font) if self._text else 0
        total = isz + gap + tw
        x0 = (w - total) / 2
        icon(c, name, x0, (h - isz) / 2, isz, pal["fg"],
             width=1.7 if h >= 30 else 1.5)
        if self._text:
            c.create_text(x0 + isz + gap, h / 2, text=self._text, anchor="w",
                          fill=pal["fg"], font=self._font)

    # ---- 事件 ----
    def _on_enter(self, _e):
        self._hover = True
        self._redraw()

    def _on_leave(self, _e):
        self._hover = False
        self._active = False
        self._redraw()

    def _on_press(self, _e):
        if not self._enabled:
            return
        self._active = True
        self._redraw()

    def _on_release(self, _e):
        was = self._active
        self._active = False
        self._redraw()
        if was and self._enabled and self._command:
            try:
                self._command()
            except Exception:  # noqa: BLE001  按钮回调异常不应炸掉整个界面
                import traceback
                traceback.print_exc()


def button(parent, text="", command=None, kind="ghost", **kw):
    """创建圆角按钮的快捷函数。"""
    return RoundButton(parent, text=text, command=command, kind=kind, **kw)


# --------------------------------------------------------------------------- #
# ⑦.5 线性图标（纯 Canvas 自绘，零依赖、可随主色变化）
#
# 为什么不用 emoji：Windows 上 emoji 是彩色位图，无法跟随主题色，且在
# tk.Label 里基线偏移明显。这里统一用 24×24 网格 + 圆头描边手绘，
# 和 ttkbootstrap / Lucide 的视觉重量接近。
# --------------------------------------------------------------------------- #
_ICON_NAMES = {
    "book", "star", "pen", "headphone", "music", "doc", "grid", "swap",
    "sheet", "tag", "brace", "clock", "import", "chart", "search", "check",
    "close", "speaker", "plus", "arrow-left", "arrow-right", "trash", "eye",
    "bookmark", "info", "light", "undo", "refresh", "play", "edit", "folder",
    "save",
}

_ICON_GRID = 24.0


def _ip(x, y, s, pts):
    k = s / _ICON_GRID
    return [v for pt in pts for v in (x + pt[0] * k, y + pt[1] * k)]


def _iline(c, x, y, s, pts, col, w, closed=False):
    p = _ip(x, y, s, pts)
    if closed:
        p = p + [p[0], p[1]]
    return c.create_line(*p, fill=col, width=w,
                         capstyle="round", joinstyle="round")


def _icirc(c, x, y, s, cx, cy, r, col, w):
    k = s / _ICON_GRID
    return c.create_oval(x + (cx - r) * k, y + (cy - r) * k,
                         x + (cx + r) * k, y + (cy + r) * k,
                         outline=col, width=w)


def icon(canvas, name, x, y, s, color, width=1.7):
    """把图标 `name` 画到 canvas 的 (x, y) 处，边长 s 像素。"""
    if name == "book":
        _iline(canvas, x, y, s, [(12, 6), (4, 8), (4, 18), (12, 16),
                                 (20, 18), (20, 8), (12, 6)], color, width, True)
        _iline(canvas, x, y, s, [(12, 6), (12, 16)], color, width)
    elif name == "star":
        import math
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            r = 8.2 if i % 2 == 0 else 3.6
            pts.append((12 + r * math.cos(ang), 12.5 + r * math.sin(ang)))
        _iline(canvas, x, y, s, pts, color, width, True)
    elif name == "pen":
        _iline(canvas, x, y, s, [(5, 19), (7, 13), (16, 4), (20, 8),
                                 (11, 17), (5, 19)], color, width, True)
        _iline(canvas, x, y, s, [(16, 4), (20, 8)], color, width)
    elif name == "headphone":
        k = s / _ICON_GRID
        canvas.create_arc(x + 3 * k, y + 3 * k, x + 21 * k, y + 21 * k,
                          start=20, extent=140, style="arc",
                          outline=color, width=width)
        _iline(canvas, x, y, s, [(4, 14), (4, 19)], color, width + 1)
        _iline(canvas, x, y, s, [(20, 14), (20, 19)], color, width + 1)
    elif name == "music":
        _icirc(canvas, x, y, s, 8, 17, 3.2, color, width)
        _iline(canvas, x, y, s, [(11, 17), (11, 5), (19, 7), (19, 15)],
               color, width)
        _icirc(canvas, x, y, s, 16, 15, 3.0, color, width)
    elif name == "doc":
        _iline(canvas, x, y, s, [(6, 3), (14, 3), (19, 8), (19, 21),
                                 (6, 21), (6, 3)], color, width, True)
        _iline(canvas, x, y, s, [(14, 3), (14, 8), (19, 8)], color, width)
        _iline(canvas, x, y, s, [(9, 12), (16, 12)], color, width)
        _iline(canvas, x, y, s, [(9, 16), (16, 16)], color, width)
    elif name == "grid":
        _iline(canvas, x, y, s, [(4, 4), (20, 4), (20, 20), (4, 20), (4, 4)],
               color, width, True)
        _iline(canvas, x, y, s, [(12, 4), (12, 20)], color, width)
        _iline(canvas, x, y, s, [(4, 12), (20, 12)], color, width)
    elif name == "swap":
        _iline(canvas, x, y, s, [(4, 9), (18, 9)], color, width)
        _iline(canvas, x, y, s, [(15, 6), (18, 9), (15, 12)], color, width)
        _iline(canvas, x, y, s, [(20, 15), (6, 15)], color, width)
        _iline(canvas, x, y, s, [(9, 12), (6, 15), (9, 18)], color, width)
    elif name == "sheet":
        _iline(canvas, x, y, s, [(5, 3), (17, 3), (17, 21), (5, 21), (5, 3)],
               color, width, True)
        _iline(canvas, x, y, s, [(8, 8), (14, 8)], color, width)
        _iline(canvas, x, y, s, [(8, 12), (14, 12)], color, width)
        _iline(canvas, x, y, s, [(8, 16), (12, 16)], color, width)
        _iline(canvas, x, y, s, [(18, 9), (21, 12), (18, 15)], color, width)
    elif name == "tag":
        _iline(canvas, x, y, s, [(4, 11), (11, 4), (20, 4), (20, 13),
                                 (13, 20), (4, 11)], color, width, True)
        _icirc(canvas, x, y, s, 16.5, 7.5, 1.6, color, width)
    elif name == "brace":
        _iline(canvas, x, y, s, [(9, 3), (6, 5), (6, 10), (4, 12),
                                 (6, 14), (6, 19), (9, 21)], color, width)
        _iline(canvas, x, y, s, [(15, 3), (18, 5), (18, 10), (20, 12),
                                 (18, 14), (18, 19), (15, 21)], color, width)
    elif name == "clock":
        _icirc(canvas, x, y, s, 12, 13, 8.5, color, width)
        _iline(canvas, x, y, s, [(12, 13), (12, 8)], color, width)
        _iline(canvas, x, y, s, [(12, 13), (16, 15)], color, width)
        _iline(canvas, x, y, s, [(9, 2.5), (15, 2.5)], color, width)
    elif name == "import":
        _iline(canvas, x, y, s, [(12, 3), (12, 14)], color, width)
        _iline(canvas, x, y, s, [(8, 10), (12, 14), (16, 10)], color, width)
        _iline(canvas, x, y, s, [(4, 16), (4, 21), (20, 21), (20, 16)],
               color, width)
    elif name == "chart":
        _iline(canvas, x, y, s, [(4, 20), (20, 20)], color, width)
        _iline(canvas, x, y, s, [(7, 20), (7, 13)], color, width + 1)
        _iline(canvas, x, y, s, [(12, 20), (12, 8)], color, width + 1)
        _iline(canvas, x, y, s, [(17, 20), (17, 11)], color, width + 1)
    elif name == "search":
        _icirc(canvas, x, y, s, 10.5, 10.5, 6.5, color, width)
        _iline(canvas, x, y, s, [(15.5, 15.5), (20, 20)], color, width)
    elif name == "check":
        _iline(canvas, x, y, s, [(4, 13), (9.5, 19), (20, 5)], color, width)
    elif name == "close":
        _iline(canvas, x, y, s, [(6, 6), (18, 18)], color, width)
        _iline(canvas, x, y, s, [(18, 6), (6, 18)], color, width)
    elif name == "speaker":
        _iline(canvas, x, y, s, [(4, 9), (8, 9), (13, 4), (13, 20),
                                 (8, 15), (4, 15), (4, 9)], color, width, True)
        k = s / _ICON_GRID
        canvas.create_arc(x + 8 * k, y + 5 * k, x + 22 * k, y + 19 * k,
                          start=-55, extent=110, style="arc",
                          outline=color, width=width)
    elif name == "plus":
        _iline(canvas, x, y, s, [(12, 5), (12, 19)], color, width)
        _iline(canvas, x, y, s, [(5, 12), (19, 12)], color, width)
    elif name == "arrow-left":
        _iline(canvas, x, y, s, [(19, 12), (5, 12)], color, width)
        _iline(canvas, x, y, s, [(11, 6), (5, 12), (11, 18)], color, width)
    elif name == "arrow-right":
        _iline(canvas, x, y, s, [(5, 12), (19, 12)], color, width)
        _iline(canvas, x, y, s, [(13, 6), (19, 12), (13, 18)], color, width)
    elif name == "trash":
        _iline(canvas, x, y, s, [(4, 7), (20, 7)], color, width)
        _iline(canvas, x, y, s, [(9, 7), (9, 4), (15, 4), (15, 7)], color, width)
        _iline(canvas, x, y, s, [(6, 7), (7, 20), (17, 20), (18, 7)],
               color, width)
    elif name == "eye":
        _iline(canvas, x, y, s, [(3, 12), (7, 6.5), (12, 5), (17, 6.5),
                                 (21, 12), (17, 17.5), (12, 19), (7, 17.5),
                                 (3, 12)], color, width, True)
        _icirc(canvas, x, y, s, 12, 12, 3.2, color, width)
    elif name == "bookmark":
        _iline(canvas, x, y, s, [(6, 3), (18, 3), (18, 21), (12, 16),
                                 (6, 21), (6, 3)], color, width, True)
    elif name == "info":
        _icirc(canvas, x, y, s, 12, 12, 8.5, color, width)
        _icirc(canvas, x, y, s, 12, 7.5, 0.9, color, width + 0.6)
        _iline(canvas, x, y, s, [(12, 11), (12, 17)], color, width)
    elif name == "light":
        _icirc(canvas, x, y, s, 12, 10, 4.2, color, width)
        _iline(canvas, x, y, s, [(10, 15), (10, 18), (14, 18), (14, 15)],
               color, width)
        for a, b in (((12, 2.5), (12, 4.5)), ((4.8, 5.5), (6.2, 6.9)),
                     ((19.2, 5.5), (17.8, 6.9)),
                     ((3, 12), (5, 12)), ((21, 12), (19, 12))):
            _iline(canvas, x, y, s, [a, b], color, width)
    elif name == "undo":
        k = s / _ICON_GRID
        canvas.create_arc(x + 4 * k, y + 6 * k, x + 20 * k, y + 20 * k,
                          start=25, extent=185, style="arc",
                          outline=color, width=width)
        _iline(canvas, x, y, s, [(4, 10), (4, 16)], color, width)
        _iline(canvas, x, y, s, [(4, 10), (10, 10)], color, width)
    elif name == "refresh":
        k = s / _ICON_GRID
        canvas.create_arc(x + 4 * k, y + 4 * k, x + 20 * k, y + 20 * k,
                          start=35, extent=290, style="arc",
                          outline=color, width=width)
        _iline(canvas, x, y, s, [(17, 3.5), (19.5, 7.5), (15, 8.5)],
               color, width)
    elif name == "play":
        _iline(canvas, x, y, s, [(8, 4.5), (19, 12), (8, 19.5)], color,
               width, True)
    elif name == "edit":
        _iline(canvas, x, y, s, [(4, 20), (5, 15.5), (15.5, 5), (19, 8.5),
                                 (8.5, 19), (4, 20)], color, width, True)
    elif name == "folder":
        _iline(canvas, x, y, s, [(3, 6), (10, 6), (12, 8.5), (21, 8.5),
                                 (21, 20), (3, 20), (3, 6)], color, width,
               True)
    elif name == "save":
        _iline(canvas, x, y, s, [(4, 4), (17, 4), (20, 7), (20, 20),
                                 (4, 20), (4, 4)], color, width, True)
        _iline(canvas, x, y, s, [(8, 4), (8, 9), (15, 9), (15, 4)],
               color, width)
        _iline(canvas, x, y, s, [(7, 20), (7, 13), (17, 13), (17, 20)],
               color, width)


class Icon(tk.Canvas):
    """独立图标组件：Icon(parent, "star", size=20, color=TEXT_MUTED)。"""

    def __init__(self, parent, name="doc", size=20, color=TEXT_MUTED,
                 bg=None, width=1.7, pad=1, **kw):
        self._bg = bg or _bg_of(parent)
        super().__init__(parent, width=size + pad * 2, height=size + pad * 2,
                         bg=self._bg, highlightthickness=0, bd=0, **kw)
        self._name = name
        self._size = size
        self._color = color
        self._width = width
        self._pad = pad
        self._draw()

    def _draw(self):
        self.delete("all")
        icon(self, self._name, self._pad, self._pad, self._size,
             self._color, self._width)

    def set_color(self, color):
        self._color = color
        self.configure(bg=self._bg)
        self._draw()


def icon_label(parent, name, text, fg=TEXT, icon_fg=None, size=18,
               font=None, bg=None, gap=8, **kw):
    """图标 + 文字的横排组合（返回容器 Frame，方便 pack/grid）。"""
    bg = bg or _bg_of(parent)
    box = tk.Frame(parent, bg=bg)
    ic = Icon(box, name, size=size, color=icon_fg or fg, bg=bg)
    ic.pack(side="left")
    lbl = tk.Label(box, text=text, bg=bg, fg=fg,
                   font=font or FONT_UI, padx=0)
    lbl.pack(side="left", padx=(gap, 0))
    box._icon = ic
    box._label = lbl
    return box


# --------------------------------------------------------------------------- #
# ⑧ 胶囊标签
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# ⑧.5 自适应换行文字（宽度跟着容器变，避免固定 wraplength 被裁）
# --------------------------------------------------------------------------- #
def wrap_label(parent, text="", fg=None, bg=None, font=None, pad=0,
               justify="left", anchor="w", min_w=120, **kw):
    """会跟着容器宽度自动重算 wraplength 的 Label。"""
    bg = bg or _bg_of(parent)
    lbl = tk.Label(parent, text=text, bg=bg, fg=fg or TEXT,
                   font=font or FONT_UI, justify=justify, anchor=anchor,
                   padx=pad, **kw)
    state = {"w": 0}

    def _fit(_e=None):
        try:
            w = parent.winfo_width() - 2 * pad
            if lbl.winfo_manager() == "pack":
                info = lbl.pack_info()
                for side in ("padx",):
                    v = info.get(side)
                    if isinstance(v, tuple) or isinstance(v, list):
                        w -= 2 * int(v[0] if len(v) < 2 else max(v))
                    elif v not in (None, ""):
                        w -= 2 * int(v)
        except (tk.TclError, ValueError, AttributeError):
            return
        w = max(min_w, w)
        if abs(w - state["w"]) > 2:
            state["w"] = w
            try:
                lbl.config(wraplength=w)
            except tk.TclError:
                pass

    parent.bind("<Configure>", _fit, add="+")
    lbl.after(30, _fit)
    lbl._fit = _fit
    return lbl


def chip(parent, text, fg=PRIMARY_DEEP, bg=PRIMARY_SOFT, font=None, padx=9, pady=3):
    lbl = tk.Label(parent, text=text, bg=bg, fg=fg,
                   font=font or FONT_SMALL, padx=padx, pady=pady)
    return lbl


# --------------------------------------------------------------------------- #
# ⑧.5 分段控件（替代一排 Radiobutton）
# --------------------------------------------------------------------------- #
class Segment(tk.Canvas):
    """分段控件：一组选项横向排列，选中项白底胶囊 + 细微边，容器浅灰底。

    用法：
        seg = Segment(parent, [("高中","GZ"),("四级","CET4"),("六级","CET6")],
                      value="CET4", command=on_change)
        seg.get()  /  seg.set("CET6")
    """

    H = 34
    PAD = 3

    def __init__(self, parent, options, value=None, command=None,
                 bg=None, font=None, height=34, min_w=0, **kw):
        self._bg = bg or _bg_of(parent)
        super().__init__(parent, bg=self._bg, highlightthickness=0, bd=0,
                         height=height, **kw)
        self._opts = [(str(text), str(val)) for text, val in options]
        self._value = value if value is not None else (
            self._opts[0][1] if self._opts else None)
        self._command = command
        self._font = font or FONT_UI
        self._h = height
        self._min_w = min_w
        self._hover_i = -1
        self._sum_w = 0
        self._tw = self._measure_widths()
        self.configure(width=max(min_w, sum(self._tw) + 2 * self.PAD + 2),
                       height=height, cursor="hand2")
        self.bind("<Button-1>", self._on_click)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", lambda e: self._set_hover(-1))
        self.bind("<Configure>", lambda e: self._redraw())
        self.after(1, self._redraw)

    def _measure_widths(self):
        from tkinter import font as tkfont
        try:
            f = tkfont.Font(root=self, font=self._font)
            return [f.measure(t) + 26 for t, _v in self._opts]
        except Exception:
            return [sum(13 if ord(c) > 127 else 7 for c in t) + 26
                    for t, _v in self._opts]

    def get(self):
        return self._value

    def set(self, value, fire=False):
        if value == self._value:
            return
        self._value = value
        self._redraw()
        if fire and self._command:
            self._command(value)

    def _seg_at(self, x):
        acc = self.PAD
        for i, w in enumerate(self._tw):
            if acc <= x <= acc + w:
                return i
            acc += w
        return -1

    def _set_hover(self, i):
        if i != self._hover_i:
            self._hover_i = i
            self._redraw()

    def _on_motion(self, e):
        self._set_hover(self._seg_at(e.x))

    def _on_click(self, e):
        i = self._seg_at(e.x)
        if i < 0:
            return
        val = self._opts[i][1]
        if val == self._value:
            return
        self._value = val
        self._redraw()
        if self._command:
            try:
                self._command(val)
            except Exception:  # noqa: BLE001
                import traceback
                traceback.print_exc()

    def _redraw(self, _e=None):
        w = self.winfo_width()
        if w <= 2:
            w = max(self._min_w, sum(self._tw) + 2 * self.PAD + 2)
        h = self._h
        self.delete("all")
        outer_bg = BORDER_SOFT if self._bg in (CARD, WHITE) else "#EDEEF1"
        round_rect(self, 0, 0, w, h, R_BTN, fill=outer_bg, outline=outer_bg)
        x = self.PAD
        pad = self.PAD
        for i, (text, val) in enumerate(self._opts):
            sw = self._tw[i]
            sel = (val == self._value)
            if sel:
                round_rect(self, x, pad, x + sw, h - pad, R_BTN - 2,
                           fill=WHITE, outline=BORDER)
                fg, font = PRIMARY_DEEP, (FONT_FAMILY, 10, "bold")
            elif i == self._hover_i:
                round_rect(self, x, pad, x + sw, h - pad, R_BTN - 2,
                           fill="#F4F5F7", outline="#F4F5F7")
                fg, font = TEXT, self._font
            else:
                fg, font = TEXT_MUTED, self._font
            self.create_text(x + sw / 2, h / 2, text=text, fill=fg, font=font)
            x += sw


def segment(parent, options, value=None, command=None, **kw):
    return Segment(parent, options, value=value, command=command, **kw)


# --------------------------------------------------------------------------- #
# ⑨ 环形进度（复刻 ttkbootstrap Meter）
# --------------------------------------------------------------------------- #
class Meter(tk.Canvas):
    """环形进度：中间显示百分比（或自定义文字），环用主色，底环浅色。

    用法：m = Meter(parent, size=96, value=42, caption="已掌握")
          m.set(60)  /  m.set(75, caption="听写准确率")
    """

    def __init__(self, parent, size=96, thickness=9, value=0, caption="",
                 bg=None, color=PRIMARY, track=None, font=None,
                 caption_font=None, text=None, **kw):
        self._bg = bg or _bg_of(parent)
        super().__init__(parent, width=size, height=size, bg=self._bg,
                         highlightthickness=0, bd=0, **kw)
        self._size = size
        self._th = thickness
        self._value = max(0, min(100, float(value)))
        self._caption = caption
        self._text = text
        self._color = color
        self._track = track or PRIMARY_SOFT
        self._font = font or (FONT_FAMILY, max(11, size // 6), "bold")
        self._cap_font = caption_font or (FONT_FAMILY, 9)
        self.bind("<Configure>", lambda e: self._redraw())
        self.after(1, self._redraw)

    def set(self, value, caption=None, text=None, color=None):
        self._value = max(0, min(100, float(value)))
        if caption is not None:
            self._caption = caption
        if text is not None:
            self._text = text
        if color is not None:
            self._color = color
        self._redraw()

    def _redraw(self, _e=None):
        c = self
        c.delete("all")
        s = self._size
        th = self._th
        pad = th / 2 + 2
        x1, y1, x2, y2 = pad, pad, s - pad, s - pad
        # 底环
        c.create_oval(x1, y1, x2, y2, outline=self._track, width=th)
        # 进度环（-90° 起，顺时针）
        extent = -360 * (self._value / 100.0)
        if abs(extent) > 0.01:
            c.create_arc(x1, y1, x2, y2, start=90, extent=extent,
                         style="arc", outline=self._color, width=th)
        # 中央文字
        center_txt = self._text if self._text is not None else "%d%%" % round(self._value)
        cy = s / 2 - (6 if self._caption else 0)
        c.create_text(s / 2, cy, text=center_txt, fill=TEXT, font=self._font)
        if self._caption:
            c.create_text(s / 2, cy + s * 0.20, text=self._caption,
                          fill=TEXT_MUTED, font=self._cap_font)


def meter(parent, **kw):
    return Meter(parent, **kw)


# --------------------------------------------------------------------------- #
# ⑩ 空状态
# --------------------------------------------------------------------------- #
def empty_state(parent, icon="doc", title="这里还空着", desc="",
                bg=None, action_text=None, action_command=None, pady=36):
    """统一空状态：图标 + 标题 + 说明 +（可选）主色按钮。返回容器 Frame。

    icon 传线性图标名（"doc"/"star"/"chart"...）；若传 emoji 则按 emoji 渲染，
    兼容老调用。
    """
    bg = bg or _bg_of(parent)
    box = tk.Frame(parent, bg=bg)
    box.pack(fill="both", expand=True, pady=pady)
    if icon in _ICON_NAMES:
        Icon(box, icon, size=34, color=TEXT_FAINT, bg=bg, width=1.5).pack(
            pady=(0, 8))
    else:
        tk.Label(box, text=icon, bg=bg, fg=TEXT_FAINT,
                 font=(FONT_FAMILY, 30)).pack(pady=(0, 6))
    tk.Label(box, text=title, bg=bg, fg=TEXT,
             font=FONT_UI_B).pack()
    if desc:
        dlbl = tk.Label(box, text=desc, bg=bg, fg=TEXT_MUTED,
                        font=FONT_SMALL, justify="center", wraplength=360)
        dlbl.pack(pady=(4, 0), padx=12)

        def _fit_desc(_e=None, _l=dlbl):
            try:
                avail = box.winfo_width()
            except tk.TclError:
                return
            if avail > 20:
                _l.configure(wraplength=max(120, avail - 48))

        box.bind("<Configure>", _fit_desc, add="+")
    if action_text and action_command:
        btn = RoundButton(box, text=action_text, command=action_command,
                          kind="soft", bg=bg, height=32)
        btn.pack(pady=(12, 0))
    return box


# --------------------------------------------------------------------------- #
# ⑪ 业务工具（原样保留）
# --------------------------------------------------------------------------- #
def accuracy(a, b):
    """计算两段文本的相似度百分比（用于听写判分）。"""
    import difflib
    import re

    def norm(s):
        s = s.lower().strip()
        s = re.sub(r"[^a-z0-9'\s]", " ", s)
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    na, nb = norm(a), norm(b)
    if not nb:
        return 0.0
    return round(difflib.SequenceMatcher(None, na, nb).ratio() * 100, 1)


def diff_words(user, answer):
    """逐词对比，返回 [(词, 是否正确)]。"""
    import re
    ua = [w for w in re.split(r"\s+", user.strip()) if w]
    ab = [w for w in re.split(r"\s+", answer.strip()) if w]
    import difflib
    sm = difflib.SequenceMatcher(None, [w.lower().strip(".,!?;:\"'") for w in ab],
                                 [w.lower().strip(".,!?;:\"'") for w in ua])
    res = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                res.append((ab[i1 + k], True))
        elif tag == "replace":
            for k in range(max(i2 - i1, j2 - j1)):
                if k < (j2 - j1):
                    res.append((ua[j1 + k], False))
        elif tag == "insert":
            for k in range(j2 - j1):
                res.append((ua[j1 + k], False))
        elif tag == "delete":
            for k in range(i2 - i1):
                res.append((ab[i1 + k], False))
    return res


def center_window(win, w, h):
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = max(0, (sw - w) // 2)
    y = max(0, (sh - h) // 3)
    win.geometry(f"{w}x{h}+{x}+{y}")
