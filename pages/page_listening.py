# -*- coding: utf-8 -*-
"""听力训练页：听音频 → 做题 → 交卷判分 → 看解析。

布局：
    ┌ 换一篇 · 标题 · 等级 ──────────────── 已答 1/3 ┐
    │ ┌ 听力原文（左，360）──┐ ┌ 题目（右，撑满）─────┐ │
    │ │ 连播整段             │ │ 第 1/3 题            │ │
    │ │ 第1段 / 第2段 …      │ │ 题干                  │ │
    │ │ （原文默认折叠）      │ │ ○ A … ○ B …          │ │
    │ └──────────────────────┘ │ 上一题 下一题   交卷  │ │
    │                          └──────────────────────┘ │
"""

import random

import tkinter as tk
import tkinter.ttk as ttk

import ui_common as ui

from data_listening import LISTENING_ITEMS
from pages import Page


class ListeningPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, bg=ui.BG)
        self.app = app
        self.store = app.store
        self.item = None
        self.q = 0
        self.answers = {}
        self.submitted = False
        self.audio_controls = {}
        self.show_script = tk.BooleanVar(value=False)
        self._build()
        self._load()

    # ------------------------------------------------------------------ #
    def _build(self):
        top = tk.Frame(self, bg=ui.BG)
        top.pack(fill="x", padx=ui.PAGE_PAD, pady=(ui.S_MD, ui.S_SM))

        ui.button(top, text="换一篇", kind="ghost", icon="refresh",
                  command=self._load).pack(side="left", padx=(0, ui.S_MD))

        self.title_lbl = tk.Label(top, text="", bg=ui.BG, fg=ui.TEXT,
                                  font=ui.FONT_SUBTITLE)
        self.title_lbl.pack(side="left")

        self.prog_lbl = tk.Label(top, text="", bg=ui.BG, fg=ui.TEXT_MUTED,
                                 font=ui.FONT_SMALL)
        self.prog_lbl.pack(side="right")

        body = tk.Frame(self, bg=ui.BG)
        body.pack(fill="both", expand=True, padx=ui.PAGE_PAD,
                  pady=(0, ui.S_SM))

        # ---------------- 左：音频 / 原文 ----------------
        lw = tk.Frame(body, bg=ui.BG, width=368)
        lw.pack(side="left", fill="y")
        lw.pack_propagate(False)
        lo, lc = ui.card(lw)
        lo.pack(fill="both", expand=True)

        lhead = tk.Frame(lc, bg=ui.CARD)
        lhead.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.CARD_PAD, ui.S_SM))
        ui.Icon(lhead, "headphone", size=16, color=ui.PRIMARY,
                bg=ui.CARD).pack(side="left")
        tk.Label(lhead, text="听力音频", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_SUBTITLE).pack(side="left",
                                             padx=(ui.S_SM, 0))

        ui.button(lc, text="连播整段", kind="primary", icon="speaker",
                  command=self._play_all).pack(fill="x", padx=ui.CARD_PAD,
                                               pady=(0, ui.S_SM))

        self.script_toggle = ui.button(lc, text="显示原文", kind="ghost",
                                       icon="eye",
                                       command=self._toggle_script)
        self.script_toggle.pack(fill="x", padx=ui.CARD_PAD,
                                pady=(0, ui.S_SM))

        self.audio_frame = tk.Frame(lc, bg=ui.CARD)
        self.audio_frame.pack(fill="both", expand=True,
                              padx=ui.CARD_PAD, pady=(0, ui.CARD_PAD))

        # ---------------- 右：题目 ----------------
        rw = tk.Frame(body, bg=ui.BG)
        rw.pack(side="left", fill="both", expand=True, padx=(ui.GAP, 0))
        ro, rc = ui.card(rw)
        ro.pack(fill="both", expand=True)

        self.qframe = tk.Frame(rc, bg=ui.CARD)
        self.qframe.pack(fill="both", expand=True, padx=ui.CARD_PAD,
                         pady=(ui.CARD_PAD, ui.S_SM))

        bar = tk.Frame(rc, bg=ui.CARD)
        bar.pack(fill="x", padx=ui.CARD_PAD, pady=(0, ui.CARD_PAD))

        ui.button(bar, text="上一题", kind="ghost", icon="arrow-left",
                  command=lambda: self._goto(-1)).pack(side="left",
                                                       padx=(0, ui.S_SM))
        ui.button(bar, text="下一题", kind="ghost", icon="arrow-right",
                  command=lambda: self._goto(1)).pack(side="left")

        self.score_lbl = tk.Label(bar, text="", bg=ui.CARD, fg=ui.PRIMARY,
                                  font=(ui.FONT_FAMILY, 13, "bold"))
        self.score_lbl.pack(side="left", padx=(ui.S_LG, 0))

        self.submit_btn = ui.button(bar, text="交卷", kind="primary",
                                    icon="check", command=self._submit)
        self.submit_btn.pack(side="right")

    # ------------------------------------------------------------------ #
    def reload_data(self):
        self._load()

    def on_show(self):
        pass

    def _load(self):
        self.item = random.choice(LISTENING_ITEMS)
        self.q = 0
        self.answers = {}
        self.submitted = False
        self.score_lbl.config(text="")
        self.show_script.set(False)
        self.script_toggle.set_text("显示原文")
        self.script_toggle.set_icon("eye")
        self._render_audio()
        self._render_questions()

    def _toggle_script(self):
        on = not self.show_script.get()
        self.show_script.set(on)
        self.script_toggle.set_text("隐藏原文" if on else "显示原文")
        self.script_toggle.set_icon("eye" if not on else "close")
        self._render_audio()

    # ------------------------------------------------------------------ #
    def _render_audio(self):
        for w in self.audio_frame.winfo_children():
            w.destroy()
        self.audio_controls.clear()

        script = (self.item or {}).get("script") or []
        if not script:
            ui.empty_state(self.audio_frame, icon="headphone",
                           title="这段没有音频脚本",
                           desc="换一篇试试", bg=ui.CARD, pady=30)
            return

        for idx, line in enumerate(script):
            row = tk.Frame(self.audio_frame, bg=ui.CARD)
            row.pack(fill="x", pady=(0, ui.S_XS))
            ui.button(row, text="第 %d 段" % (idx + 1), kind="text",
                      icon="play", height=30,
                      command=lambda i=idx: self._play(i)).pack(side="left")
            self.audio_controls[idx] = line
            if self.show_script.get():
                ui.wrap_label(row, text=line, fg=ui.TEXT_MUTED, bg=ui.CARD,
                              font=ui.FONT_SMALL, justify="left").pack(
                    side="left", fill="x", expand=True, padx=(ui.S_SM, 0))

        if not self.show_script.get():
            tk.Label(self.audio_frame,
                     text="原文先藏着，先认真听一遍，实在跟不上再点「显示原文」",
                     bg=ui.CARD, fg=ui.TEXT_FAINT, font=ui.FONT_SMALL,
                     wraplength=300, justify="left").pack(
                anchor="w", pady=(ui.S_MD, 0))

    def _play(self, idx):
        line = self.audio_controls.get(idx, "")
        if line:
            self.app.tts.speak(line, blocking=False)
            self.app.set_status("播放第 %d 段…" % (idx + 1))

    def _play_all(self):
        lines = [self.audio_controls[k] for k in sorted(self.audio_controls)]
        if not lines:
            return
        self.app.set_status("连播整段…")

        def step(i):
            if i >= len(lines):
                self.app.set_status("连播结束")
                return
            self.app.tts.speak(lines[i], blocking=False)
            self.after(2600, lambda: step(i + 1))

        step(0)

    # ------------------------------------------------------------------ #
    def _render_questions(self):
        for w in self.qframe.winfo_children():
            w.destroy()

        if not self.item or not self.item.get("questions"):
            ui.empty_state(self.qframe, icon="doc", title="这篇没有题目",
                           desc="换一篇试试", bg=ui.CARD, pady=40)
            return

        self.title_lbl.config(text=self.item.get("title", ""))

        qs = self.item["questions"]
        n = len(qs)
        idx = max(0, min(self.q, n - 1))
        qd = qs[idx]

        self.prog_lbl.config(text="已答 %d / %d 题" % (
            len([k for k in self.answers if isinstance(k, int)]), n))

        head = tk.Frame(self.qframe, bg=ui.CARD)
        head.pack(fill="x", pady=(0, ui.S_MD))
        ui.chip(head, "第 %d / %d 题" % (idx + 1, n),
                fg=ui.PRIMARY_DEEP, bg=ui.PRIMARY_SOFT).pack(side="left")
        if self.item.get("level"):
            lv = str(self.item["level"])
            ui.chip(head, {"1": "基础", "2": "进阶", "3": "挑战"}.get(lv, lv),
                    fg=ui.TEXT_MUTED,
                    bg=ui.CARD_SOFT).pack(side="left", padx=(ui.S_SM, 0))

        ui.wrap_label(self.qframe, text=qd["q"], fg=ui.TEXT, bg=ui.CARD,
                      font=(ui.FONT_FAMILY, 12), justify="left").pack(
            fill="x", pady=(0, ui.S_MD))

        var = tk.StringVar(value=self.answers.get(idx, ""))
        self.answers["_var"] = (idx, var)

        for opt in qd["options"]:
            row = tk.Frame(self.qframe, bg=ui.CARD_SOFT,
                           highlightthickness=1,
                           highlightbackground=ui.BORDER_SOFT)
            row.pack(fill="x", pady=(0, ui.S_SM))
            rb = tk.Radiobutton(
                row, text=opt, value=opt, variable=var,
                bg=ui.CARD_SOFT, fg=ui.TEXT, selectcolor=ui.CARD,
                activebackground=ui.PRIMARY_SOFT,
                activeforeground=ui.PRIMARY_DEEP,
                font=ui.FONT_UI, anchor="w", justify="left",
                highlightthickness=0, bd=0, padx=8, pady=8,
                command=lambda i=idx, v=var: self._pick(i, v.get()))
            rb.pack(fill="x")
            row._rb = rb
            row.bind("<Button-1>", lambda e, v=var, o=opt, i=idx:
                     (v.set(o), self._pick(i, o)))
            if self.submitted and self.answers.get(idx) == opt:
                row.configure(highlightbackground=ui.PRIMARY)
            if self.submitted:
                qd_ok = (opt == qd["answer"])
                if opt == qd["answer"]:
                    row.configure(bg=ui.OK_SOFT,
                                  highlightbackground=ui.OK_SOFT)
                    rb.configure(bg=ui.OK_SOFT, fg=ui.OK, selectcolor=ui.OK_SOFT)
                elif self.answers.get(idx) == opt:
                    row.configure(bg=ui.WARN_SOFT,
                                  highlightbackground=ui.WARN_SOFT)
                    rb.configure(bg=ui.WARN_SOFT, fg=ui.WARN,
                                 selectcolor=ui.WARN_SOFT)

        if self.submitted:
            self._show_feedback(idx)

    def _pick(self, idx, val):
        self.answers[idx] = val
        n = len(self.item["questions"])
        self.prog_lbl.config(text="已答 %d / %d 题" % (
            len([k for k in self.answers if isinstance(k, int)]), n))
        self._render_questions()

    def _goto(self, delta):
        if not self.item:
            return
        var_info = self.answers.get("_var")
        if var_info:
            i, v = var_info
            self.answers[i] = v.get()
        n = len(self.item["questions"])
        self.q = max(0, min(self.q + delta, n - 1))
        self._render_questions()

    # ------------------------------------------------------------------ #
    def _submit(self):
        if not self.item:
            return
        var_info = self.answers.get("_var")
        if var_info:
            i, v = var_info
            self.answers[i] = v.get()
        self.submitted = True

        qs = self.item["questions"]
        correct = 0
        detail = []
        for i, qd in enumerate(qs):
            ans = self.answers.get(i, "")
            ok = (ans == qd["answer"])
            if ok:
                correct += 1
            detail.append({
                "q": qd["q"], "answer": ans, "standard": qd["answer"],
                "correct": ok, "explain": qd.get("explain", ""),
            })
            self.store.log_question("listening", self.item.get("title", ""),
                                    i, ans, ok, qd["answer"],
                                    qd.get("explain", ""))

        self.store.add_exam("listening", self.item.get("title", ""),
                            correct, len(qs), detail)
        self.score_lbl.config(text="得分 %d / %d" % (correct, len(qs)))
        self.submit_btn.set_text("重新交卷")
        self._render_questions()
        self.app.set_status("听力交卷：%d / %d" % (correct, len(qs)))

    def _show_feedback(self, idx):
        qd = self.item["questions"][idx]
        ans = self.answers.get(idx, "")
        ok = (ans == qd["answer"])
        color = ui.OK if ok else ui.WARN
        fb = tk.Frame(self.qframe, bg=ui.CARD_SOFT,
                      highlightthickness=1,
                      highlightbackground=ui.BORDER_SOFT)
        fb.pack(fill="x", pady=(ui.S_SM, 0))

        th = tk.Frame(fb, bg=ui.CARD_SOFT)
        th.pack(fill="x", padx=ui.S_MD, pady=(ui.S_SM, ui.S_XS))
        ui.Icon(th, "check" if ok else "close", size=14, color=color,
                bg=ui.CARD_SOFT).pack(side="left", padx=(0, ui.S_XS))
        tk.Label(th, text="答对了" if ok else "答错了", bg=ui.CARD_SOFT,
                 fg=color, font=ui.FONT_UI_B).pack(side="left")
        tk.Label(th, text="正确答案：%s" % qd["answer"], bg=ui.CARD_SOFT,
                 fg=ui.TEXT_MUTED, font=ui.FONT_SMALL).pack(side="right")

        if qd.get("explain"):
            ui.wrap_label(fb, text="解析：%s" % qd["explain"],
                          fg=ui.TEXT_MUTED, bg=ui.CARD_SOFT,
                          font=ui.FONT_UI, justify="left").pack(
                fill="x", padx=ui.S_MD, pady=(0, ui.S_SM))
