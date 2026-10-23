# -*- coding: utf-8 -*-
"""语法知识页：四六级常考语法点，左侧列表 + 右侧讲解

每条：标题 / 等级 / 规则说明 / 常见错句 / 正确写法 / 记忆点
"""

import tkinter as tk
import tkinter.font as tkfont

import ui_common as ui

try:
    from data_grammar import GRAMMAR
except Exception:  # noqa: BLE001
    GRAMMAR = []

# (显示名, 等级) —— 0 表示全部
LEVELS = (('全部', 0), ('四级基础', 1), ('四级进阶', 2), ('六级重点', 3))
LEVEL_NAME = {1: '四级基础', 2: '四级进阶', 3: '六级重点'}


from pages import Page


class GrammarPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.app = app
        self.store = app.store

        self.items = list(GRAMMAR)
        self.cur = 0
        self.level = tk.StringVar(value="0")

        self._build()
        self._reload()

    # ---------- 布局 ----------
    def _build(self):
        top = tk.Frame(self, bg=ui.BG)
        top.pack(fill="x", padx=ui.PAGE_PAD, pady=(ui.S_MD, ui.S_SM))

        tk.Label(top, text="等级", bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI).pack(side="left", padx=(0, ui.S_SM))
        seg = ui.segment(top, [(t, str(v)) for t, v in LEVELS],
                         value="0", command=self._on_level)
        seg.pack(side="left")

        self.stat_lbl = tk.Label(top, text="", bg=ui.BG, fg=ui.TEXT_MUTED,
                                 font=ui.FONT_SMALL)
        self.stat_lbl.pack(side="right")

        body = tk.Frame(self, bg=ui.BG)
        body.pack(fill="both", expand=True, padx=ui.PAGE_PAD,
                  pady=(0, ui.S_SM))

        # 左：知识点目录（固定宽）
        left_wrap = tk.Frame(body, bg=ui.BG, width=272)
        left_wrap.pack(side="left", fill="y")
        left_wrap.pack_propagate(False)
        left_outer, left = ui.card(left_wrap)
        left_outer.pack(fill="both", expand=True)

        lhead = tk.Frame(left, bg=ui.CARD)
        lhead.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.S_SM))
        ui.Icon(lhead, "doc", size=16, color=ui.TEXT_MUTED,
                bg=ui.CARD).pack(side="left")
        tk.Label(lhead, text="知识点", bg=ui.CARD, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI_B).pack(side="left", padx=(ui.S_SM, 0))

        listwrap = ui.scrollable(left, bg=ui.CARD)
        listwrap[0].pack(fill="both", expand=True, padx=ui.S_SM,
                         pady=(0, ui.S_MD))
        self.list_frame = listwrap[1]

        # 右：讲解
        right_wrap = tk.Frame(body, bg=ui.BG)
        right_wrap.pack(side="left", fill="both", expand=True,
                        padx=(ui.GAP, 0))
        right_outer, self.right = ui.card(right_wrap)
        right_outer.pack(fill="both", expand=True)

        self.mode = tk.StringVar(value="0")

    def _on_level(self, val):
        self.mode.set(val)
        self._reload()

    # ---------- 列表 ----------
    def _reload(self):
        lv = int(self.mode.get() or 0)
        shown = [g for g in self.items if lv == 0 or g.get("level") == lv]
        self.shown = shown

        log = self.store.question_log("grammar", "points")

        done_n = sum(
            1 for g in shown
            if log.get(self.items.index(g) + 1)
            and log.get(self.items.index(g) + 1).get("correct")
        )

        for w in self.list_frame.winfo_children():
            w.destroy()
        self.btns = []

        for i, g in enumerate(shown):
            gno = self.items.index(g) + 1
            done = log.get(gno)
            ok = bool(done and done.get("correct"))
            item = _Item(self.list_frame, gno, g.get("title", ""), ok,
                         lambda k=i: self._show(k), wrap_w=236)
            item.pack(fill="x", pady=1)
            self.btns.append(item)

        if shown:
            self.cur = max(0, min(self.cur, len(shown) - 1))
            self._show(self.cur)
        else:
            for w in self.right.winfo_children():
                w.destroy()
            ui.empty_state(self.right, icon="doc", title="这个等级还没有知识点",
                           desc="换个等级看看", bg=ui.CARD)

        self.stat_lbl.config(
            text="共 %d 个知识点　已掌握 %d 个" % (len(shown), done_n))

    # ---------- 详情 ----------
    def _show(self, k):
        if not self.shown:
            return
        self.cur = k
        g = self.shown[k]
        gno = self.items.index(g) + 1
        done = self.store.question_log("grammar", "points").get(gno)

        for i, b in enumerate(self.btns):
            b.set_active(i == k)

        for w in self.right.winfo_children():
            w.destroy()

        lvname = LEVEL_NAME.get(g.get("level"), "")

        # 可滚动的详情区 + 固定底部按钮
        bar = tk.Frame(self.right, bg=ui.CARD)
        bar.pack(side="bottom", fill="x", padx=ui.CARD_PAD,
                 pady=(ui.S_SM, ui.CARD_PAD))

        bodyw = ui.scrollable(self.right, bg=ui.CARD)
        bodyw[0].pack(fill="both", expand=True, padx=(ui.CARD_PAD, ui.S_SM),
                      pady=(ui.S_MD, 0))
        host = bodyw[1]

        head = tk.Frame(host, bg=ui.CARD)
        head.pack(fill="x", pady=(0, ui.S_MD))

        # 第一行：编号 + 等级标签
        meta = tk.Frame(head, bg=ui.CARD)
        meta.pack(fill="x")
        tk.Label(meta, text="第 %d 条" % gno, bg=ui.CARD, fg=ui.TEXT_FAINT,
                 font=ui.FONT_SMALL).pack(side="left")
        if lvname:
            chip_bg = {1: ui.INFO_SOFT, 2: ui.OK_SOFT, 3: ui.AMBER_SOFT}
            chip_fg = {1: ui.INFO, 2: ui.OK, 3: ui.AMBER}
            lb = ui.chip(meta, lvname, fg=chip_fg.get(g.get("level"), ui.INFO),
                         bg=chip_bg.get(g.get("level"), ui.INFO_SOFT))
            lb.pack(side="right")

        # 第二行：标题（占满整行宽度，自适应换行）
        ui.wrap_label(head, text=g.get("title", ""), fg=ui.TEXT,
                      bg=ui.CARD, font=(ui.FONT_FAMILY, 15, "bold"),
                      justify="left", anchor="w").pack(
            fill="x", pady=(ui.S_XS, 0), padx=(0, ui.S_MD))

        def block(title, text, fg, font, icon_name=None, bg_tint=None):
            wrap = tk.Frame(host, bg=bg_tint or ui.CARD)
            wrap.pack(fill="x", padx=(0, ui.CARD_PAD), pady=(0, ui.S_MD))
            th = tk.Frame(wrap, bg=bg_tint or ui.CARD)
            th.pack(fill="x", padx=(ui.S_MD if bg_tint else 0),
                    pady=(ui.S_SM if bg_tint else 0, 2))
            if icon_name:
                ui.Icon(th, icon_name, size=14, color=fg,
                        bg=bg_tint or ui.CARD).pack(side="left",
                                                    padx=(0, ui.S_XS))
            tk.Label(th, text=title, bg=bg_tint or ui.CARD, fg=fg,
                     font=ui.FONT_SMALL).pack(side="left")
            lb = ui.wrap_label(wrap, text=text, fg=fg, font=font,
                               bg=bg_tint or ui.CARD, justify="left",
                               anchor="w", pad=0)
            lb.pack(fill="x", anchor="w",
                    padx=(ui.S_MD if bg_tint else 0, ui.S_MD if bg_tint else 0),
                    pady=(0, ui.S_SM if bg_tint else 0))
            return wrap

        block("规则", g.get("point", ""), ui.TEXT,
              (ui.FONT_FAMILY, 11), icon_name="info")
        if g.get("wrong"):
            block("常见错句", g.get("wrong", ""), ui.WARN, ui.FONT_EX,
                  icon_name="close", bg_tint=ui.WARN_SOFT)
        if g.get("right"):
            block("正确写法", g.get("right", ""), ui.OK, ui.FONT_EX,
                  icon_name="check", bg_tint=ui.OK_SOFT)
        if g.get("note"):
            block("记忆点", g.get("note", ""), ui.AMBER,
                  (ui.FONT_FAMILY, 10), icon_name="light",
                  bg_tint=ui.AMBER_SOFT)

        ui.button(bar, text="记住了", kind="primary", icon="check",
                  command=lambda n=gno: self._mark(n, True)).pack(
            side="left", padx=(0, ui.S_SM))
        ui.button(bar, text="还要再看", kind="ghost", icon="undo",
                  command=lambda n=gno: self._mark(n, False)).pack(side="left")
        ui.button(bar, text="朗读例句", kind="ghost", icon="speaker",
                  command=lambda t=g.get("right", ""):
                  self.app.tts.speak(t, blocking=False)).pack(
            side="right")

        if done:
            ok = done.get("correct")
            ui.chip(bar, "已掌握" if ok else "待复习",
                    fg=ui.OK if ok else ui.WARN,
                    bg=ui.OK_SOFT if ok else ui.WARN_SOFT).pack(
                side="right", padx=(0, ui.S_SM))

    # ---------- 标记掌握 ----------
    def _mark(self, gno, ok):
        g = self.items[gno - 1]
        self.store.log_question(
            "grammar", "points", str(gno), g.get("title", ""), ok,
            g.get("right", ""), g.get("point", ""),
        )
        self.app.set_status(
            "语法：%s 已记为%s" % (g.get("title", ""), "掌握" if ok else "待复习"))
        self._reload()

    def on_show(self):
        self._reload()


class _Item(tk.Canvas):
    """左侧知识点行：圆角选中态 + 左侧指示条。

    行高在构造时按可用宽度算好（不在 <Configure> 里改高度，
    否则 pack 重排会和重绘打架，出现行与行重叠）。
    """

    def __init__(self, parent, no, title, done, command, wrap_w=230):
        self._bg = ui.CARD
        self.no = no
        self.title = title
        self.done = done
        self.command = command
        self._active = False
        self._hover = False
        self._wrap_w = max(120, wrap_w)
        self._font = ui.FONT_SMALL
        super().__init__(parent, bg=self._bg, highlightthickness=0, bd=0,
                         height=46, width=self._wrap_w, cursor="hand2")
        # 最多两行；行数在构造时定死，避免 <Configure> 里改高度导致重排打架
        self._lines = self._wrap(title, self._font,
                                 self._wrap_w - 26 - 30)[:2]
        self._h = 40 if len(self._lines) <= 1 else 54
        self.configure(height=self._h)
        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", lambda e: self.command())

    def set_active(self, flag):
        if flag != self._active:
            self._active = flag
            self._redraw()

    def _enter(self, _e=None):
        self._hover = True
        self._redraw()

    def _leave(self, _e=None):
        self._hover = False
        self._redraw()

    def _wrap(self, text, font, width):
        """优先按空格断行，避免把英文单词劈成两截。"""
        if width <= 10:
            return [text]
        try:
            f = tkfont.Font(root=self, font=font)
        except tk.TclError:
            return [text]
        lines, cur = [], ""
        for token in text.split(" "):
            trial = token if not cur else cur + " " + token
            if f.measure(trial) <= width:
                cur = trial
                continue
            if cur:
                lines.append(cur)
            if f.measure(token) > width:
                piece = ""
                for ch in token:
                    if f.measure(piece + ch) > width and piece:
                        lines.append(piece)
                        piece = ch
                    else:
                        piece += ch
                cur = piece
            else:
                cur = token
        if cur:
            lines.append(cur)
        return lines[:3]

    def _redraw(self, _e=None):
        self.delete("all")
        w = self.winfo_width()
        if w <= 1:
            w = self._wrap_w
        h = self._h
        x0 = 12 if not self._active else 15
        fg = ui.PRIMARY_DEEP if self._active else ui.TEXT
        font = self._font
        fill = (ui.PRIMARY_SOFT if self._active else
                (ui.CARD_SOFT if self._hover else ui.CARD))
        if self._active or self._hover:
            ui.round_rect(self, 0, 1, w - 1, h - 1, 8, fill=fill, outline="")
        if self._active:
            ui.round_rect(self, 0, 7, 3, h - 7, 2, fill=ui.PRIMARY, outline="")
        self.create_text(x0, h // 2, anchor="w", text="%02d" % self.no,
                         fill=ui.TEXT_FAINT, font=ui.FONT_MONO)
        self.create_text(x0 + 34, h // 2, anchor="w",
                         text="\n".join(self._lines), fill=fg, font=font)
        if self.done:
            self.create_text(w - 12, h // 2, anchor="e", text="✓",
                             fill=ui.OK, font=ui.FONT_UI_B)
