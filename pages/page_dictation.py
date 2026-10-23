# -*- coding: utf-8 -*-
"""听写训练页：听音 → 逐词播 → 慢速/换音色 → 写英文 → 智能判分。

UI 结构（三栏收成两栏，一屏装得下）：
    ┌ 难度分段 ───────────────── 练习 1/81 · 通过 0 · 准确率 0% ┐
    │   ┌ 听音卡（左，固定 320）┐  ┌ 作答卡（右，撑满）────────┐  │
    │   │ 喇叭大圆 + 4 个播放钮 │  │ 输入框                    │  │
    │   │ 提示文字              │  │ 提交/看答案/跳过           │  │
    │   │ 判分后：环形准确率      │  │ 逐词对错 + 原文/译文        │  │
    │   └───────────────────────┘  └───────────────────────────┘  │
"""

import random
import re

import tkinter as tk

import ui_common as ui

from data_sentences import SENTENCES
from pages import Page

DIFFS = [("全部", "全部"), ("短句", 1), ("中句", 2), ("长难句", 3)]


class DictationPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, bg=ui.BG)
        self.app = app
        self.store = app.store
        self.difficulty = tk.StringVar(value="全部")
        self.queue = []
        self.pos = 0
        self.cur = None
        self.checked = False
        self._build()
        self._load()

    # ------------------------------------------------------------------ #
    def _build(self):
        # 顶栏：难度分段 + 右侧统计
        top = tk.Frame(self, bg=ui.BG)
        top.pack(fill="x", padx=ui.PAGE_PAD, pady=(ui.S_MD, ui.S_SM))

        tk.Label(top, text="难度", bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI).pack(side="left", padx=(0, ui.S_SM))
        self.seg = ui.segment(top, DIFFS, value="全部",
                              command=self._on_diff)
        self.seg.pack(side="left")

        self.stat_lbl = tk.Label(top, text="", bg=ui.BG, fg=ui.TEXT_MUTED,
                                 font=ui.FONT_SMALL)
        self.stat_lbl.pack(side="right")

        body = tk.Frame(self, bg=ui.BG)
        body.pack(fill="both", expand=True, padx=ui.PAGE_PAD,
                  pady=(0, ui.S_SM))

        # ---------------- 左：听音卡 ----------------
        lw = tk.Frame(body, bg=ui.BG, width=326)
        lw.pack(side="left", fill="y")
        lw.pack_propagate(False)
        lo, lc = ui.card(lw)
        lo.pack(fill="both", expand=True)

        tk.Label(lc, text="先听，再写", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_SUBTITLE).pack(anchor="w",
                                             padx=ui.CARD_PAD,
                                             pady=(ui.CARD_PAD, 2))
        tk.Label(lc, text="听不清就多放几遍，逐词播放会一个一个念",
                 bg=ui.CARD, fg=ui.TEXT_FAINT, font=ui.FONT_SMALL,
                 wraplength=270, justify="left").pack(
            anchor="w", padx=ui.CARD_PAD, pady=(0, ui.S_MD))

        # 播放主钮（大圆）
        self.play_btn = ui.button(lc, text="播放整句", kind="primary",
                                  icon="speaker", command=self._play_all,
                                  height=44)
        self.play_btn.pack(fill="x", padx=ui.CARD_PAD, pady=(0, ui.S_SM))
        ui.button(lc, text="逐词播放", kind="soft", icon="play",
                  command=self._play_words).pack(fill="x",
                                                 padx=ui.CARD_PAD,
                                                 pady=(0, ui.S_SM))
        ui.button(lc, text="慢速播放", kind="ghost", icon="clock",
                  command=self._play_slow).pack(fill="x",
                                                padx=ui.CARD_PAD,
                                                pady=(0, ui.S_SM))
        ui.button(lc, text="换个音色", kind="ghost", icon="swap",
                  command=self._play_env).pack(fill="x",
                                               padx=ui.CARD_PAD)

        # 判分结果：环形准确率
        res = tk.Frame(lc, bg=ui.CARD)
        res.pack(fill="both", expand=True, padx=ui.CARD_PAD,
                 pady=(ui.S_LG, ui.CARD_PAD))
        self.meter_box = tk.Frame(res, bg=ui.CARD)
        self.meter_box.pack(expand=True)
        self.meter = None

        # ---------------- 右：作答卡 ----------------
        rw = tk.Frame(body, bg=ui.BG)
        rw.pack(side="left", fill="both", expand=True, padx=(ui.GAP, 0))
        ro, rc = ui.card(rw)
        ro.pack(fill="both", expand=True)

        head = tk.Frame(rc, bg=ui.CARD)
        head.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.CARD_PAD, ui.S_SM))
        ui.Icon(head, "edit", size=16, color=ui.PRIMARY,
                bg=ui.CARD).pack(side="left")
        tk.Label(head, text="把你听到的句子写下来", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_SUBTITLE).pack(side="left",
                                             padx=(ui.S_SM, 0))
        tk.Label(head, text="Ctrl + Enter 提交", bg=ui.CARD,
                 fg=ui.TEXT_FAINT, font=ui.FONT_SMALL).pack(side="right")

        self.text = tk.Text(rc, height=5, font=("Georgia", 15), wrap="word",
                            relief="flat", bg=ui.CARD_SOFT, fg=ui.TEXT,
                            insertbackground=ui.PRIMARY, padx=12, pady=10,
                            highlightthickness=1,
                            highlightbackground=ui.BORDER,
                            highlightcolor=ui.PRIMARY)
        self.text.pack(fill="x", padx=ui.CARD_PAD, pady=(0, ui.S_MD))
        self.text.bind("<Control-Return>", lambda e: (self._check(), "break"))

        bar = tk.Frame(rc, bg=ui.CARD)
        bar.pack(fill="x", padx=ui.CARD_PAD)
        ui.button(bar, text="提交判分", kind="primary", icon="check",
                  command=self._check).pack(side="left", padx=(0, ui.S_SM))
        ui.button(bar, text="看答案", kind="ghost", icon="eye",
                  command=self._show_answer).pack(side="left",
                                                  padx=(0, ui.S_SM))
        ui.button(bar, text="下一句", kind="text", icon="arrow-right",
                  command=self._next).pack(side="left")

        self.score_lbl = tk.Label(bar, text="", bg=ui.CARD, fg=ui.PRIMARY,
                                  font=(ui.FONT_FAMILY, 13, "bold"))
        self.score_lbl.pack(side="right")

        # 判分结果区（可滚动，避免撑爆）
        host = tk.Frame(rc, bg=ui.CARD)
        host.pack(fill="both", expand=True, padx=ui.CARD_PAD,
                  pady=(ui.S_MD, ui.CARD_PAD))
        self.res_scroll, self.res = ui.scrollable(host, bg=ui.CARD)
        self.res_scroll.pack(fill="both", expand=True)
        self.result_lbl = None
        self.ref_lbl = None

    # ------------------------------------------------------------------ #
    def _on_diff(self, val):
        self.difficulty.set(val)
        self._load()

    def reload_data(self):
        self._load()

    def on_show(self):
        self._render()

    # ------------------------------------------------------------------ #
    def _load(self):
        d = self.difficulty.get()
        pool = list(SENTENCES)
        try:
            for rec in self.store.user_content("sentences"):
                t = (rec.get("data") or {}).get("sent")
                if not t or len(t) < 2 or not t[0]:
                    continue
                diff = 2
                if len(t) > 2 and str(t[2]).isdigit():
                    diff = int(t[2])
                theme = t[3] if len(t) > 3 else "导入"
                pool.append((t[0], t[1], max(1, min(3, diff)), theme))
        except Exception:  # noqa: BLE001
            pool = list(SENTENCES)

        seen, uniq = set(), []
        for s in pool:
            if s[0] in seen:
                continue
            seen.add(s[0])
            uniq.append(s)
        pool = uniq

        if d != "全部":
            pool = [s for s in pool if s[2] == d]

        random.shuffle(pool)
        self.queue = pool
        self.pos = 0
        self._render()

    def _render(self):
        st = self.store.dict_stats()
        self.stat_lbl.config(
            text="练习 %d / %d　·　一次通过 %d 句　·　平均准确率 %s%%"
            % (self.pos + 1 if self.queue else 0, len(self.queue),
               st["perfect"], st["avg_accuracy"]))

        self.score_lbl.config(text="")
        self._reset_result()

        if not self.queue:
            self.cur = None
            self._set_result_empty("这个难度还没有句子", "换个难度试试")
            return

        self.pos = max(0, min(self.pos, len(self.queue) - 1))
        self.cur = self.queue[self.pos]
        self.checked = False
        self.text.delete("1.0", "end")
        self.text.focus_set()
        self._hint()
        self.meter = ui.meter(self.meter_box, size=118, thickness=10,
                              value=0, text="—", caption="待判分",
                              color=ui.BORDER_SOFT, track=ui.BORDER_SOFT)
        self.meter.pack()
        try:
            self.app.tts.prewarm(self.cur[0])
        except Exception:  # noqa: BLE001
            pass

    def _hint(self):
        """未判分时右栏的提示块，别让下半屏空着。"""
        box = tk.Frame(self.res, bg=ui.CARD)
        box.pack(fill="x", pady=(ui.S_LG, 0))
        for icon_name, text in (
            ("headphone", "点左边「播放整句」先听一遍，别急着看文字"),
            ("play", "跟不上就「逐词播放」，一个词一个词拆开听"),
            ("check", "写完按 Ctrl + Enter 提交，系统逐词给对错"),
        ):
            row = tk.Frame(box, bg=ui.CARD)
            row.pack(fill="x", pady=(0, ui.S_SM))
            ui.Icon(row, icon_name, size=15, color=ui.PRIMARY,
                    bg=ui.CARD).pack(side="left", padx=(0, ui.S_SM))
            ui.wrap_label(row, text=text, fg=ui.TEXT_MUTED, bg=ui.CARD,
                          font=ui.FONT_UI).pack(side="left", fill="x",
                                                 expand=True)

    # ------------------------------------------------------------------ #
    def _reset_result(self):
        for w in self.res.winfo_children():
            w.destroy()
        if self.meter is not None:
            self.meter.destroy()
            self.meter = None
        for w in self.meter_box.winfo_children():
            w.destroy()
        self.result_lbl = None
        self.ref_lbl = None

    def _set_result_empty(self, title, desc):
        ui.empty_state(self.res, icon="headphone", title=title, desc=desc,
                       bg=ui.CARD, pady=40)

    # ------------------------------------------------------------------ #
    def _play_all(self):
        if not self.cur:
            return
        self.app.tts.speak(self.cur[0], blocking=False)
        self.app.set_status("正在播放整句…")

    def _play_env(self):
        if not self.cur:
            return
        eng = self.app.tts
        old = getattr(eng, "pitch", 0)
        if hasattr(eng, "set_pitch"):
            eng.set_pitch(max(-50, old - 20))
            eng.speak(self.cur[0], blocking=False)
            eng.set_pitch(old)
        else:
            eng.speak(self.cur[0], blocking=False)
        self.app.set_status("换了个音色再播一遍…")

    def _play_slow(self):
        if not self.cur:
            return
        eng = self.app.tts
        old = getattr(eng, "rate", 0)
        eng.rate = max(-10, min(10, old - 6))
        eng.speak(self.cur[0], blocking=False)
        eng.rate = old
        self.app.set_status("慢速播放中…")

    def _play_words(self):
        if not self.cur:
            return
        words = [w for w in re.split(r"\s+", self.cur[0].strip()) if w]
        self.app.set_status("逐词播放…")

        def step(i):
            if i >= len(words):
                self.app.set_status("逐词播放结束")
                return
            self.app.tts.speak(words[i], blocking=False)
            self.after(950, lambda: step(i + 1))

        step(0)

    # ------------------------------------------------------------------ #
    def _check(self):
        if not self.cur or self.checked:
            return
        user = self.text.get("1.0", "end").strip()
        if not user:
            self.app.set_status("先写点什么再提交吧")
            self.text.focus_set()
            return

        answer = self.cur[0]
        acc = ui.accuracy(user, answer)
        self.store.record_dictation(answer, acc)
        self.checked = True

        color = ui.OK if acc >= 90 else (ui.AMBER if acc >= 70 else ui.WARN)
        self.score_lbl.config(text="准确率 %s%%" % acc, fg=color)

        self._reset_result()

        # 左栏环形
        self.meter = ui.meter(self.meter_box, size=118, thickness=10,
                              value=acc, caption="准确率", color=color)
        self.meter.pack()

        # 右栏逐词对比
        cap = tk.Frame(self.res, bg=ui.CARD)
        cap.pack(fill="x", pady=(0, ui.S_SM))
        tk.Label(cap, text="逐词对比", bg=ui.CARD, fg=ui.TEXT_MUTED,
                 font=ui.FONT_SMALL).pack(anchor="w")

        flow = tk.Frame(self.res, bg=ui.CARD)
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
            tk.Label(row, text=word, bg=bg, fg=fg,
                     font=(ui.FONT_FAMILY, 10), padx=6, pady=2).pack(
                side="left", padx=(0, 6))
            used += w

        self.ref_lbl = ui.wrap_label(
            self.res,
            text="原文：%s\n参考译文：%s" % (answer, self.cur[1]),
            fg=ui.TEXT_MUTED, bg=ui.CARD, font=ui.FONT_UI, justify="left")
        self.ref_lbl.pack(fill="x", pady=(ui.S_MD, 0))

        st = self.store.dict_stats()
        self.stat_lbl.config(
            text="练习 %d / %d　·　一次通过 %d 句　·　平均准确率 %s%%"
            % (self.pos + 1, len(self.queue), st["perfect"],
               st["avg_accuracy"]))
        self.app.set_status("判分完成：%s%%" % acc)

    def _show_answer(self):
        if not self.cur:
            return
        self.checked = True
        self._reset_result()
        self.score_lbl.config(text="")
        ui.wrap_label(self.res, text="原文：%s" % self.cur[0], fg=ui.TEXT,
                      bg=ui.CARD, font=(ui.FONT_FAMILY, 12, "bold"),
                      justify="left").pack(fill="x")
        ui.wrap_label(self.res, text="参考译文：%s" % self.cur[1],
                      fg=ui.TEXT_MUTED, bg=ui.CARD, font=ui.FONT_UI,
                      justify="left").pack(fill="x", pady=(ui.S_SM, 0))
        tk.Label(self.res, text="（已显示答案，本次不计入统计）",
                 bg=ui.CARD, fg=ui.TEXT_FAINT,
                 font=ui.FONT_SMALL).pack(anchor="w", pady=(ui.S_SM, 0))

    def _next(self):
        if self.pos < len(self.queue) - 1:
            self.pos += 1
        else:
            self.app.set_status("这一轮读完啦，换个难度或点开别的页签")
            return
        self._render()
