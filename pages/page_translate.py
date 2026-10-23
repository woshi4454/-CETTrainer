# -*- coding: utf-8 -*-
"""中译英翻译页：看中文 → 写英文 → 智能判分 → 看参考译文。

布局：
    ┌ 难度 分段 ──────────────────── 练习 3 / 30 ┐
    │ ┌ 中文（上）──────────────────────────────┐ │
    │ │ ① 题号 · 难度胶囊                         │ │
    │ │ 中文原句（16 号加粗）                      │ │
    │ └──────────────────────────────────────────┘ │
    │ ┌ 我的译文（中）──────────────────────────┐ │
    │ │ Text 输入                                 │ │
    │ │ 提交判分  看参考译文  下一句    准确率       │ │
    │ └──────────────────────────────────────────┘ │
    │ ┌ 判分结果（下，判分后展开）──────────────┐ │
    │ │ 逐词对错 + 参考译文                        │ │
    │ └──────────────────────────────────────────┘ │
"""

import random

import tkinter as tk

import ui_common as ui

from data_sentences import TRANSLATIONS
from pages import Page

LEVELS = [("全部", "全部"), ("基础", "基础"), ("进阶", "进阶"), ("高阶", "高阶")]


class TranslatePage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, bg=ui.BG)
        self.app = app
        self.store = app.store
        self.level = tk.StringVar(value="全部")
        self.queue = []
        self.pos = 0
        self.cur = None
        self.checked = False
        self._build()
        self._load()

    # ------------------------------------------------------------------ #
    def _build(self):
        top = tk.Frame(self, bg=ui.BG)
        top.pack(fill="x", padx=ui.PAGE_PAD, pady=(ui.S_MD, ui.S_SM))

        tk.Label(top, text="难度", bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI).pack(side="left", padx=(0, ui.S_SM))
        self.seg = ui.segment(top, LEVELS, value="全部", command=self._on_level)
        self.seg.pack(side="left")

        self.stat_lbl = tk.Label(top, text="", bg=ui.BG, fg=ui.TEXT_MUTED,
                                 font=ui.FONT_SMALL)
        self.stat_lbl.pack(side="right")

        body = tk.Frame(self, bg=ui.BG)
        body.pack(fill="both", expand=True, padx=ui.PAGE_PAD,
                  pady=(0, ui.S_SM))

        # ---------------- 上：中文原句 ----------------
        co, cc = ui.card(body)
        co.pack(fill="x", pady=(0, ui.GAP))

        chead = tk.Frame(cc, bg=ui.CARD)
        chead.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.S_XS))
        ui.Icon(chead, "doc", size=15, color=ui.PRIMARY,
                bg=ui.CARD).pack(side="left")
        tk.Label(chead, text="把这句中文译成英文", bg=ui.CARD, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI_B).pack(side="left", padx=(ui.S_XS, 0))
        self.level_chip_box = tk.Frame(chead, bg=ui.CARD)
        self.level_chip_box.pack(side="right")

        self.cn_lbl = ui.wrap_label(cc, text="", fg=ui.TEXT, bg=ui.CARD,
                                    font=(ui.FONT_FAMILY, 15, "bold"),
                                    justify="left")
        self.cn_lbl.pack(fill="x", padx=ui.CARD_PAD, pady=(0, ui.CARD_PAD))

        # ---------------- 中：我的译文 ----------------
        eo, ec = ui.card(body)
        eo.pack(fill="both", expand=True, pady=(0, ui.GAP))

        ehead = tk.Frame(ec, bg=ui.CARD)
        ehead.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.S_XS))
        ui.Icon(ehead, "edit", size=15, color=ui.TEXT_MUTED,
                bg=ui.CARD).pack(side="left")
        tk.Label(ehead, text="我的译文", bg=ui.CARD, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI_B).pack(side="left", padx=(ui.S_XS, 0))
        tk.Label(ehead, text="Ctrl + Enter 提交", bg=ui.CARD,
                 fg=ui.TEXT_FAINT, font=ui.FONT_SMALL).pack(side="right")

        self.text = tk.Text(ec, height=5, font=("Georgia", 14), wrap="word",
                            relief="flat", bg=ui.CARD_SOFT, fg=ui.TEXT,
                            insertbackground=ui.PRIMARY, padx=12, pady=10,
                            highlightthickness=1,
                            highlightbackground=ui.BORDER,
                            highlightcolor=ui.PRIMARY,
                            spacing2=3)
        self.text.pack(fill="both", expand=True, padx=ui.CARD_PAD,
                       pady=(0, ui.S_MD))
        self.text.bind("<Control-Return>", lambda e: (self._check(), "break"))

        bar = tk.Frame(ec, bg=ui.CARD)
        bar.pack(fill="x", padx=ui.CARD_PAD, pady=(0, ui.CARD_PAD))

        ui.button(bar, text="提交判分", kind="primary", icon="check",
                  command=self._check).pack(side="left", padx=(0, ui.S_SM))
        ui.button(bar, text="看参考译文", kind="ghost", icon="eye",
                  command=self._show_answer).pack(side="left",
                                                  padx=(0, ui.S_SM))
        ui.button(bar, text="下一句", kind="text", icon="arrow-right",
                  command=self._next).pack(side="left")

        self.score_lbl = tk.Label(bar, text="", bg=ui.CARD, fg=ui.PRIMARY,
                                  font=(ui.FONT_FAMILY, 13, "bold"))
        self.score_lbl.pack(side="right")

        # ---------------- 下：判分结果（判分后才出现） ----------------
        self.bo, self.result_box = ui.card(body)
        self._result_shown = False
        self.result_head = tk.Frame(self.result_box, bg=ui.CARD)
        self.result_head.pack(fill="x", padx=ui.CARD_PAD,
                              pady=(ui.S_MD, ui.S_XS))
        ui.Icon(self.result_head, "chart", size=15, color=ui.TEXT_MUTED,
                bg=ui.CARD).pack(side="left")
        tk.Label(self.result_head, text="判分结果", bg=ui.CARD,
                 fg=ui.TEXT_MUTED, font=ui.FONT_UI_B).pack(
            side="left", padx=(ui.S_XS, 0))

        rhost = tk.Frame(self.result_box, bg=ui.CARD)
        rhost.pack(fill="both", expand=True,
                   padx=(ui.CARD_PAD, ui.S_XS), pady=(0, ui.S_MD))
        self.rscroll, self.rframe = ui.scrollable(rhost, bg=ui.CARD)
        self.rscroll.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    def _on_level(self, val):
        self.level.set(val)
        self._load()

    def reload_data(self):
        self._load()

    def on_show(self):
        self._render()

    def _level_of(self, item):
        d = item[2] if len(item) > 2 else 1
        return {1: "基础", 2: "进阶", 3: "高阶"}.get(int(d), "进阶")

    def _load(self):
        lv = self.level.get()
        pool = list(TRANSLATIONS)
        if lv != "全部":
            pool = [it for it in pool if self._level_of(it) == lv]
        random.shuffle(pool)
        self.queue = pool
        self.pos = 0
        self._render()

    # ------------------------------------------------------------------ #
    def _render(self):
        self.stat_lbl.config(text="练习 %d / %d" % (
            self.pos + 1 if self.queue else 0, len(self.queue)))

        for w in self.level_chip_box.winfo_children():
            w.destroy()
        self.score_lbl.config(text="")
        self.text.delete("1.0", "end")
        self._clear_result()

        if not self.queue:
            self.cur = None
            self.cn_lbl.config(text="这个难度下还没有题目")
            return

        self.pos = max(0, min(self.pos, len(self.queue) - 1))
        self.cur = self.queue[self.pos]
        self.checked = False
        self.cn_lbl.config(text=self.cur[0])
        ui.chip(self.level_chip_box, self._level_of(self.cur),
                fg=ui.TEXT_MUTED, bg=ui.CARD_SOFT).pack()
        self.text.focus_set()

    def _clear_result(self):
        for w in self.rframe.winfo_children():
            w.destroy()

    # ------------------------------------------------------------------ #
    def _word_chips(self, parent, user, answer):
        flow = tk.Frame(parent, bg=ui.CARD)
        flow.pack(fill="x")
        row = tk.Frame(flow, bg=ui.CARD)
        row.pack(anchor="w")
        used = 0
        for word, ok in ui.diff_words(user, answer):
            fg = ui.OK if ok else ui.WARN
            bg = ui.OK_SOFT if ok else ui.WARN_SOFT
            w = len(word) * 8 + 16
            if used + w > 520 and used > 0:
                row = tk.Frame(flow, bg=ui.CARD)
                row.pack(anchor="w", pady=(6, 0))
                used = 0
            tk.Label(row, text=word, bg=bg, fg=fg, font=(ui.FONT_FAMILY, 10),
                     padx=6, pady=2).pack(side="left", padx=(0, 6))
            used += w

    def _check(self):
        if not self.cur or self.checked:
            return
        user = self.text.get("1.0", "end").strip()
        if not user:
            self.app.set_status("先写点英文再提交吧")
            self.text.focus_set()
            return
        answer = self.cur[1]
        acc = ui.accuracy(user, answer)
        self.store.log_question("translate", self.cur[0], 0, user, acc >= 90,
                                answer, "")
        self.checked = True

        color = ui.OK if acc >= 90 else (ui.AMBER if acc >= 70 else ui.WARN)
        self.score_lbl.config(text="准确率 %s%%" % acc, fg=color)

        self._clear_result()
        self._word_chips(self.rframe, user, answer)
        ui.hline(self.rframe)
        ui.wrap_label(self.rframe, text="参考译文：%s" % answer,
                      fg=ui.TEXT, bg=ui.CARD, font=ui.FONT_UI,
                      justify="left").pack(fill="x")
        self.app.set_status("翻译判分：%s%%" % acc)

    def _show_answer(self):
        if not self.cur:
            return
        self.checked = True
        self.score_lbl.config(text="")
        self._clear_result()
        ui.wrap_label(self.rframe, text="参考译文：%s" % self.cur[1],
                      fg=ui.TEXT, bg=ui.CARD, font=ui.FONT_UI,
                      justify="left").pack(fill="x")
        tk.Label(self.rframe, text="（已显示参考译文，本次不计入统计）",
                 bg=ui.CARD, fg=ui.TEXT_FAINT,
                 font=ui.FONT_SMALL).pack(anchor="w", pady=(ui.S_SM, 0))

    def _next(self):
        if self.pos < len(self.queue) - 1:
            self.pos += 1
        else:
            self.app.set_status("这一轮读完啦，换个难度再练")
            return
        self._render()
