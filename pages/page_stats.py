# -*- coding: utf-8 -*-
"""学习统计页 —— 概览卡片 + 环形进度 + 薄弱单词 + 练习记录。"""

import time

import tkinter as tk
from tkinter import ttk

import ui_common as ui

from data_vocab import CET4_WORDS, CET6_WORDS
from data_sentences import SENTENCES

try:
    from data_phrases import PHRASE_BANK
except Exception:
    PHRASE_BANK = []

try:
    from data_grammar import GRAMMAR
except Exception:
    GRAMMAR = []

try:
    from data_gaokao import GAOKAO_WORDS
except Exception:
    GAOKAO_WORDS = []


def _fmt_time(ts):
    try:
        return time.strftime("%m-%d %H:%M", time.localtime(ts))
    except (ValueError, OSError):
        return "-"


class StatsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=ui.BG)
        self.app = app
        self.store = app.store
        self._weak_words = []
        self.ov_frame = None
        self.tree = None
        self.weak_frame = None
        self.meters = {}
        self._build()
        self.refresh()

    # ---------- 布局 ----------
    def _build(self):
        # 顶栏：说明 + 刷新
        top = tk.Frame(self, bg=ui.BG)
        top.pack(fill="x", padx=ui.PAGE_PAD, pady=(0, ui.S_SM))

        tk.Label(top, text="一眼看清每个模块的进度", bg=ui.BG,
                 fg=ui.TEXT_MUTED, font=ui.FONT_SMALL).pack(side="left")

        ui.button(top, text="刷新数据", icon="⟳", kind="ghost",
                  command=self.refresh, height=32).pack(side="right")

        # 可滚动主体
        self.scroll, body = ui.scrollable(self, bg=ui.BG)
        self.scroll.pack(fill="both", expand=True)

        # ---- 三块主进度环（词库掌握度）----
        ring_card, ring_inner = ui.card(body)
        ring_card.pack(fill="x", pady=(0, ui.GAP))

        tk.Label(ring_inner, text="词库掌握度", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_SUBTITLE).pack(anchor="w", padx=ui.CARD_PAD,
                                             pady=(ui.CARD_PAD, 2))
        tk.Label(ring_inner, text="每个词库的已掌握比例", bg=ui.CARD,
                 fg=ui.TEXT_FAINT, font=ui.FONT_SMALL).pack(
                     anchor="w", padx=ui.CARD_PAD)

        rings = tk.Frame(ring_inner, bg=ui.CARD)
        rings.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.CARD_PAD))

        for key, label in (("GZ", "高中词汇"), ("CET4", "四级词汇"),
                           ("CET6", "六级词汇")):
            cell = tk.Frame(rings, bg=ui.CARD)
            cell.pack(side="left", expand=True, fill="x")
            m = ui.Meter(cell, size=112, thickness=10, value=0,
                         caption="已掌握", color=ui.PRIMARY)
            m.pack(pady=(6, 4))
            tk.Label(cell, text=label, bg=ui.CARD, fg=ui.TEXT,
                     font=ui.FONT_UI_B).pack()
            sub = tk.Label(cell, text="", bg=ui.CARD, fg=ui.TEXT_MUTED,
                           font=ui.FONT_SMALL)
            sub.pack()
            self.meters[key] = (m, sub)

        # ---- 概览小卡网格 ----
        self.ov_frame = tk.Frame(body, bg=ui.BG)
        self.ov_frame.pack(fill="x")

        # ---- 薄弱单词 ----
        weak_card, weak_inner = ui.card(body)
        weak_card.pack(fill="x", pady=(ui.GAP, 0))

        head = tk.Frame(weak_inner, bg=ui.CARD)
        head.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.CARD_PAD, 4))
        tk.Label(head, text="需要加强的单词", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_SUBTITLE).pack(side="left")
        tk.Label(head, text="错得最多的那些", bg=ui.CARD, fg=ui.TEXT_FAINT,
                 font=ui.FONT_SMALL).pack(side="left", padx=(8, 0))
        ui.button(head, text="逐个朗读", icon="🔉", kind="ghost",
                  command=self._speak_weak, height=30).pack(side="right")

        self.weak_frame = tk.Frame(weak_inner, bg=ui.CARD)
        self.weak_frame.pack(fill="x", padx=ui.CARD_PAD,
                             pady=(0, ui.CARD_PAD))

        # ---- 练习记录 ----
        log_card, log_inner = ui.card(body)
        log_card.pack(fill="both", expand=True, pady=(ui.GAP, ui.S_SM))

        tk.Label(log_inner, text="练习记录", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_SUBTITLE).pack(anchor="w", padx=ui.CARD_PAD,
                                             pady=(ui.CARD_PAD, 6))

        table = tk.Frame(log_inner, bg=ui.CARD)
        table.pack(fill="both", expand=True, padx=ui.CARD_PAD,
                   pady=(0, ui.CARD_PAD))

        cols = ("time", "kind", "title", "score")
        self.tree = ttk.Treeview(table, columns=cols, show="headings", height=8)
        for c, t, w, anchor in (("time", "时间", 100, "center"),
                                ("kind", "类型", 90, "center"),
                                ("title", "题目", 460, "w"),
                                ("score", "成绩", 100, "center")):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor=anchor)

        vsb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    # ---------- 刷新 ----------
    def refresh(self):
        s4 = self.store.word_stats("CET4")
        s6 = self.store.word_stats("CET6")
        sg = self.store.word_stats("GZ")
        ds = self.store.dict_stats()
        wb = self.store.wordbook_count()
        wb_total = sum(wb.values())

        # 进度环
        for key, stats, total in (("GZ", sg, len(GAOKAO_WORDS)),
                                  ("CET4", s4, len(CET4_WORDS)),
                                  ("CET6", s6, len(CET6_WORDS))):
            if key not in self.meters:
                continue
            m, sub = self.meters[key]
            got = stats["mastered"]
            pct = (got * 100.0 / total) if total else 0
            m.set(pct)
            sub.config(text="%d / %d 词" % (got, total))

        items = [
            ("我的单词本", "%d" % wb_total, "收藏的重点词"),
            ("听写句子", "%d" % ds["perfect"], "一次通过的句子"),
            ("听写准确率", "%d%%" % ds["avg_accuracy"], "历史平均"),
            ("短语搭配", "%d" % len(PHRASE_BANK), "短语题库总量"),
            ("语法知识点", "%d" % len(GRAMMAR), "语法题库总量"),
            ("阅读+选词", "%d" % (self._question_total("reading")
                                 + self._question_total("cloze")), "已做题数"),
            ("答对率", self._accuracy_text(), "阅读 / 选词 / 翻译合计"),
            ("错题本", "%d" % sum(self.store.wrong_stats().values()), "待重做"),
        ]

        for w in self.ov_frame.winfo_children():
            w.destroy()

        per_row = 4
        row = None
        for i, (name, val, sub) in enumerate(items):
            if i % per_row == 0:
                row = tk.Frame(self.ov_frame, bg=ui.BG)
                row.pack(fill="x", pady=(0, ui.S_SM))
            cell_outer, cell = ui.card(row)
            cell_outer.pack(side="left", expand=True, fill="both",
                            padx=(0 if i % per_row == 0 else ui.S_SM, 0))
            cell.configure(height=96)
            cell.pack_propagate(False)

            tk.Label(cell, text=name, bg=ui.CARD, fg=ui.TEXT_MUTED,
                     font=ui.FONT_SMALL, anchor="w").pack(
                         fill="x", padx=14, pady=(12, 0))
            tk.Label(cell, text=val, bg=ui.CARD, fg=ui.TEXT,
                     font=(ui.FONT_FAMILY, 21, "bold"), anchor="w").pack(
                         fill="x", padx=14)
            tk.Label(cell, text=sub, bg=ui.CARD, fg=ui.TEXT_FAINT,
                     font=(ui.FONT_FAMILY, 8), anchor="w").pack(
                         fill="x", padx=14, pady=(0, 10))

        # 薄弱单词
        weak = self.store.weak_words(limit=18)
        self._weak_words = weak

        for w in self.weak_frame.winfo_children():
            w.destroy()

        if not weak:
            ui.empty_state(self.weak_frame, icon="🌱", title="还没有错词记录",
                           desc="背词时标「不认识」的词会出现在这里，方便集中复习",
                           pady=18)
        else:
            wrap = tk.Frame(self.weak_frame, bg=ui.CARD)
            wrap.pack(fill="x", anchor="w")
            for i, item in enumerate(weak):
                if i and i % 6 == 0:
                    wrap = tk.Frame(self.weak_frame, bg=ui.CARD)
                    wrap.pack(fill="x", anchor="w", pady=(6, 0))
                txt = "%s · %d次" % (item["word"], item["wrong"])
                ui.chip(wrap, txt, fg=ui.WARN, bg=ui.WARN_SOFT,
                        font=(ui.FONT_FAMILY, 9)).pack(
                            side="left", padx=(0, 6), pady=2)

        # 练习记录
        for i in self.tree.get_children():
            self.tree.delete(i)

        kind_map = {
            "reading": "阅读",
            "cloze": "选词填空",
            "translate": "翻译",
            "listening": "听力",
        }

        for h in self.store.exam_history(60):
            kind = kind_map.get(h["kind"], h["kind"])
            if h["kind"] == "translate":
                score = "%.1f%%" % h["score"]
            else:
                score = "%d / %d" % (int(h["score"]), int(h["total"]))
            self.tree.insert(
                "", "end",
                values=(_fmt_time(h["created_at"]), kind,
                        h["title"][:60], score),
            )

    # ---------- 各题型题量 ----------
    def _question_total(self, kind):
        try:
            return self.store.done_stats(kind)["questions"]
        except Exception:
            return 0

    # ---------- 汇总正确率文字 ----------
    def _accuracy_text(self):
        q = c = 0
        for kind in ("reading", "cloze", "translate"):
            st = self.store.done_stats(kind)
            q += st["questions"]
            c += st["correct"]
        if q:
            return "%d%%" % round(c * 100 / q)
        return "—"

    # ---------- 朗读薄弱项 ----------
    def _speak_weak(self):
        weak = getattr(self, "_weak_words", [])
        if not weak:
            self.app.set_status("暂时没有错词")
            return
        words = [item["word"] for item in weak[:12]]
        self.app.set_status("正在朗读错词…")

        def step(i):
            if i >= len(words):
                self.app.set_status("朗读结束")
                return
            self.app.tts.speak(words[i], blocking=False)
            self.after(1300, lambda: step(i + 1))

        step(0)

    # ---------- 切到本页 ----------
    def on_show(self):
        self.refresh()
