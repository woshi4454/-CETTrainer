# -*- coding: utf-8 -*-
"""短语 / 固定搭配页（1800 条，来自四六级词书的短语字段）

用法：
- 顶部分段控件切换「顺序 / 随机 / 只练不熟的」三种刷法
- 点「显示释义」看中文，再点「认识 / 不认识」记录掌握情况
- 点「朗读」听发音；键盘 ← → 切词条，空格翻释义
- 标记过「不认识」的，可在「只练不熟的」模式里集中巩固
"""

import random
import tkinter as tk
import tkinter.ttk as ttk

import ui_common as ui
from pages import Page

try:
    from data_phrases import PHRASE_BANK
except Exception:  # noqa: BLE001
    PHRASE_BANK = []

MODE_ALL = "顺序（全部）"
MODE_RANDOM = "随机（全部）"
MODE_WRONG = "只练不熟的"

MODES = [("顺序", MODE_ALL), ("随机", MODE_RANDOM), ("只练不熟", MODE_WRONG)]


class PhrasePage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.items = list(PHRASE_BANK)
        self.queue = []
        self.idx = 0
        self.revealed = False
        self.mode = tk.StringVar(value=MODE_ALL)
        self._build()
        self._reload()

    # ---------------------------------------------------------------- #
    # UI 构建
    # ---------------------------------------------------------------- #
    def _build(self):
        top = tk.Frame(self, bg=ui.BG)
        top.pack(fill="x", padx=ui.PAGE_PAD, pady=(ui.S_MD, ui.S_SM))

        self.stat_lbl = tk.Label(top, text="", bg=ui.BG, fg=ui.TEXT_FAINT,
                                 font=ui.FONT_SMALL)
        self.stat_lbl.pack(side="right")

        ui.segment(top, MODES, value=MODE_ALL, command=self._on_mode
                   ).pack(side="left")

        # ---- 主卡 ----
        outer, inner = ui.card(self)
        outer.pack(fill="both", expand=True, padx=ui.PAGE_PAD,
                   pady=(0, ui.S_SM))

        # 底部按钮栏先占位，避免被内容顶到中间
        foot = tk.Frame(inner, bg=ui.CARD)
        foot.pack(side="bottom", fill="x", padx=ui.CARD_PAD,
                  pady=(0, ui.S_MD))

        self.idx_lbl = tk.Label(foot, text="", bg=ui.CARD, fg=ui.TEXT_FAINT,
                                font=ui.FONT_SMALL)
        self.idx_lbl.pack(side="left")
        self.hint_lbl = tk.Label(foot, text="空格 显示释义　·　← → 切换",
                                 bg=ui.CARD, fg=ui.TEXT_FAINT,
                                 font=ui.FONT_SMALL)
        self.hint_lbl.pack(side="right")

        bar = tk.Frame(inner, bg=ui.CARD)
        bar.pack(side="bottom", fill="x", padx=ui.CARD_PAD,
                 pady=(0, ui.S_MD))

        self.btn_no = ui.button(bar, text="不认识", kind="danger", icon="close",
                                command=lambda: self._rate(False))
        self.btn_no.pack(side="right")
        self.btn_ok = ui.button(bar, text="认识", kind="primary", icon="check",
                                command=lambda: self._rate(True))
        self.btn_ok.pack(side="right", padx=(0, ui.S_SM))

        self.btn_speak = ui.button(bar, text="朗读", kind="ghost", icon="speaker",
                                   command=self._speak)
        self.btn_speak.pack(side="left", padx=(0, ui.S_SM))
        self.btn_reveal = ui.button(bar, text="显示释义", kind="primary",
                                    icon="eye", command=self._reveal)
        self.btn_reveal.pack(side="left")

        self.btn_prev = ui.button(bar, text="上一个", kind="ghost",
                                  icon="arrow-left",
                                  command=lambda: self._step(-1))
        self.btn_prev.pack(side="left", padx=(ui.S_MD, 0))
        self.btn_next = ui.button(bar, text="下一个", kind="ghost",
                                  icon="arrow-right",
                                  command=lambda: self._step(1))
        self.btn_next.pack(side="left", padx=(0, ui.S_SM))

        # ---- 内容：垂直居中 ----
        self.stage = tk.Frame(inner, bg=ui.CARD)
        self.stage.pack(fill="both", expand=True)

        center = tk.Frame(self.stage, bg=ui.CARD)
        center.pack(expand=True)

        self.no_lbl = tk.Label(center, text="", bg=ui.CARD, fg=ui.TEXT_FAINT,
                               font=ui.FONT_SMALL)
        self.no_lbl.pack()

        self.phrase_lbl = tk.Label(center, text="", bg=ui.CARD, fg=ui.TEXT,
                                   font=ui.FONT_WORD_MD, wraplength=760,
                                   justify="center")
        self.phrase_lbl.pack(pady=(ui.S_XS, ui.S_SM))

        self.mean_lbl = ui.wrap_label(
            center, text="（点「显示释义」看中文）", fg=ui.TEXT_FAINT,
            bg=ui.CARD, font=(ui.FONT_FAMILY, 13), justify="center",
            wraplength=720, min_w=300)
        self.mean_lbl.pack(pady=(0, ui.S_MD))

        self.mark_lbl = ui.chip(center, text="未标记", fg=ui.TEXT_MUTED,
                                bg=ui.CARD_SOFT, font=ui.FONT_SMALL)
        self.mark_lbl.pack()

        # ---- 空状态遮罩 ----
        self.empty_layer = tk.Frame(self.stage, bg=ui.CARD)
        ui.empty_state(
            self.empty_layer, icon="tag", title="这个模式里还没有词条",
            desc="先按「顺序」过一遍，标几个「不认识」再回到「只练不熟」",
            bg=ui.CARD, pady=30).pack(fill="both", expand=True)

        self.bind_all("<Left>", self._safe(lambda: self._step(-1)))
        self.bind_all("<Right>", self._safe(lambda: self._step(1)))
        self.bind_all("<space>", self._safe(self._space))

    # ---------------------------------------------------------------- #
    def _on_mode(self, val):
        self.mode.set(val)
        self._reload()

    # ---------- 安全回调（只在页面可见且聚焦时响应键盘） ----------
    def _safe(self, fn):
        def handler(_e=None):
            try:
                if not self.winfo_viewable():
                    return
                focus = str(tk.focus_get())
                if focus.startswith(str(self)):
                    fn()
            except Exception:  # noqa: BLE001
                pass
        return handler

    def _log(self):
        return self.store.question_log_full("phrase", "bank")

    def reload_data(self):
        self.items = list(PHRASE_BANK)
        self._reload()

    # ---------------------------------------------------------------- #
    # 构建练习队列
    # ---------------------------------------------------------------- #
    def _reload(self):
        mode = self.mode.get()
        if mode == MODE_WRONG:
            log = self._log()
            queue = [x for i, x in enumerate(self.items)
                     if log.get(str(i)) and not log[str(i)].get("correct")]
        elif mode == MODE_RANDOM:
            queue = list(self.items)
            random.shuffle(queue)
        else:
            queue = list(self.items)
        self.queue = queue
        self.idx = 0
        self._render()

    def _total(self):
        return len(self.items)

    # ---------------------------------------------------------------- #
    # 渲染
    # ---------------------------------------------------------------- #
    def _show_empty(self, flag):
        if flag:
            self.empty_layer.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.empty_layer.place_forget()

    def _render(self):
        log = self._log()
        done = len(log)
        wrong = sum(1 for d in log.values() if not d.get("correct"))
        self.stat_lbl.config(
            text="共 %d 条　·　已过 %d　·　不熟 %d"
                 % (self._total(), done, wrong))

        if not self.queue:
            self.idx_lbl.config(text="")
            self._show_empty(True)
            for b in (self.btn_reveal, self.btn_ok, self.btn_no,
                      self.btn_speak, self.btn_prev, self.btn_next):
                b.set_enabled(False)
            return

        self._show_empty(False)
        for b in (self.btn_reveal, self.btn_ok, self.btn_no,
                  self.btn_speak, self.btn_prev, self.btn_next):
            b.set_enabled(True)

        self.idx = max(0, min(self.idx, len(self.queue) - 1))
        phrase, _mean = self.queue[self.idx]
        gno = next((i for i, x in enumerate(self.items, 1)
                    if x[0] == phrase), self.idx + 1)
        rec = log.get(str(gno), {})

        self.no_lbl.config(text="〔%d〕" % gno)
        self.phrase_lbl.config(text=phrase)
        self.idx_lbl.config(
            text="第 %d / %d 条　·　%s"
                 % (self.idx + 1, len(self.queue), self.mode.get()))
        self.revealed = False

        if rec.get("correct"):
            self.mark_lbl.config(text="✓ 认识", fg=ui.OK, bg=ui.OK_SOFT)
            self.mean_lbl.config(text=rec.get("answer") or "（看过释义）",
                                 fg=ui.TEXT)
            self.revealed = True
        else:
            if rec:
                self.mark_lbl.config(text="✗ 不熟", fg=ui.WARN, bg=ui.WARN_SOFT)
            else:
                self.mark_lbl.config(text="未标记", fg=ui.TEXT_MUTED,
                                     bg=ui.CARD_SOFT)
            self.mean_lbl.config(text="（点「显示释义」看中文）", fg=ui.TEXT_FAINT)

    def _show_meaning(self):
        if not self.queue:
            return
        phrase, mean = self.queue[self.idx]
        self.mean_lbl.config(text=mean, fg=ui.TEXT)
        self.revealed = True

    def _reveal(self):
        self._show_meaning()

    def _rate(self, ok):
        if not self.queue:
            return
        phrase, mean = self.queue[self.idx]
        gno = next((i for i, x in enumerate(self.items, 1)
                    if x[0] == phrase), self.idx + 1)
        self.store.log_question("phrase", "bank", str(gno), mean, ok)
        self._show_meaning()
        if ok:
            self.mark_lbl.config(text="✓ 认识", fg=ui.OK, bg=ui.OK_SOFT)
        else:
            self.mark_lbl.config(text="✗ 不熟", fg=ui.WARN, bg=ui.WARN_SOFT)
        self._step(1)

    def _step(self, d):
        if not self.queue:
            return
        nxt = self.idx + d
        if nxt >= len(self.queue):
            self.idx = 0
            self.app.set_status("这一轮到头了，从头再来一遍")
        elif nxt < 0:
            self.idx = len(self.queue) - 1
        else:
            self.idx = nxt
        self._render()

    def _space(self):
        if self.revealed:
            self._step(1)
        else:
            self._reveal()

    def _speak(self):
        if not self.queue:
            return
        phrase, _ = self.queue[self.idx]
        self.app.tts.speak(phrase, blocking=False)
        self.app.set_status("正在朗读短语…")

    def on_show(self):
        self._render()
