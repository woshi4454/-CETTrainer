# -*- coding: utf-8 -*-
"""选词填空页：读一篇带空的文章 → 每个空从下拉选词 → 交卷判分 → 看解析。

布局：
    ┌ 换一篇 · 文章标题 ────────────────────────── 已填 2/5 ┐
    │ ┌ 文章（左，撑满）────────────┐ ┌ 填空（右，352）──────┐ │
    │ │ ① ② ③ 用主色圈在手文里标出  │ │ ① [下拉]            │ │
    │ │ 长文自动滚动                │ │ ② [下拉]            │ │
    │ └────────────────────────────┘ │ 交卷                 │ │
    │                                └─────────────────────┘ │
"""

import random
import re

import tkinter as tk
import tkinter.ttk as ttk

import ui_common as ui

from data_sentences import CLOZE_PASSAGES
from pages import Page

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"


def _num(i):
    return CIRCLED[i] if i < len(CIRCLED) else "(%d)" % (i + 1)


class ClozePage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, bg=ui.BG)
        self.app = app
        self.store = app.store
        self.passage = None
        self.selections = {}
        self.submitted = False
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

        # ---------------- 左：文章 ----------------
        # 先建好，pack 放到右栏之后（否则 expand 会吃掉全部宽度）
        lw = tk.Frame(body, bg=ui.BG)
        lo, lc = ui.card(lw)
        lo.pack(fill="both", expand=True)

        head = tk.Frame(lc, bg=ui.CARD)
        head.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.S_XS))
        ui.Icon(head, "doc", size=15, color=ui.TEXT_MUTED,
                bg=ui.CARD).pack(side="left")
        tk.Label(head, text="原文", bg=ui.CARD, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI_B).pack(side="left", padx=(ui.S_XS, 0))
        ui.button(head, text="朗读", kind="soft", icon="speaker",
                  command=self._speak).pack(side="right")

        wrap = tk.Frame(lc, bg=ui.CARD)
        wrap.pack(fill="both", expand=True,
                  padx=(ui.CARD_PAD, ui.S_SM), pady=(0, ui.S_MD))

        self.article = tk.Text(
            wrap, wrap="word", font=("Georgia", 13), relief="flat",
            bg=ui.CARD, fg=ui.TEXT, padx=2, pady=2, borderwidth=0,
            spacing1=3, spacing2=5, spacing3=12, height=10,
            selectbackground=ui.PRIMARY_SOFT,
            selectforeground=ui.PRIMARY_DEEP)
        sb = ttk.Scrollbar(wrap, orient="vertical",
                           command=self.article.yview)
        self.article.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.article.pack(side="left", fill="both", expand=True)
        self.article.tag_configure("blank", foreground=ui.PRIMARY,
                                   font=(ui.FONT_FAMILY, 13, "bold"))
        self.article.tag_configure("right", foreground=ui.OK,
                                   font=(ui.FONT_FAMILY, 13, "bold"))

        # ---------------- 右：填空 ----------------
        rw = tk.Frame(body, bg=ui.BG, width=356)
        rw.pack(side="right", fill="y", padx=(ui.GAP, 0))
        rw.pack_propagate(False)

        # 右栏固定宽就位后，左栏再 expand 占满剩余
        lw.pack(side="left", fill="both", expand=True)
        ro, rc = ui.card(rw)
        ro.pack(fill="both", expand=True)

        rhead = tk.Frame(rc, bg=ui.CARD)
        rhead.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.S_SM))
        ui.Icon(rhead, "sheet", size=15, color=ui.PRIMARY,
                bg=ui.CARD).pack(side="left")
        tk.Label(rhead, text="选词填空", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_SUBTITLE).pack(side="left",
                                             padx=(ui.S_SM, 0))

        self.submit_btn = ui.button(rc, text="交卷判分", kind="primary",
                                    icon="check", command=self._submit)
        self.submit_btn.pack(side="bottom", fill="x", padx=ui.CARD_PAD,
                             pady=(ui.S_SM, ui.CARD_PAD))

        self.score_lbl = tk.Label(rc, text="", bg=ui.CARD, fg=ui.PRIMARY,
                                  font=(ui.FONT_FAMILY, 13, "bold"))
        self.score_lbl.pack(side="bottom", anchor="w", padx=ui.CARD_PAD)

        host = tk.Frame(rc, bg=ui.CARD)
        host.pack(fill="both", expand=True, padx=(ui.CARD_PAD, ui.S_XS),
                  pady=(0, ui.S_SM))
        self.sc, self.blanks_frame = ui.scrollable(host, bg=ui.CARD)
        self.sc.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    def reload_data(self):
        self._load()

    def on_show(self):
        pass

    def _load(self):
        self.passage = random.choice(CLOZE_PASSAGES)
        self.selections = {}
        self.submitted = False
        self.score_lbl.config(text="")
        self.submit_btn.set_text("交卷判分")
        self._render()

    # ------------------------------------------------------------------ #
    def _render(self):
        self.title_lbl.config(text=self.passage.get("title", ""))
        for w in self.blanks_frame.winfo_children():
            w.destroy()

        blanks = self.passage.get("blanks", [])
        self._render_article(blanks)

        for i, blank in enumerate(blanks):
            answer, options, explain = blank[0], blank[1], (
                blank[2] if len(blank) > 2 else "")
            row = tk.Frame(self.blanks_frame, bg=ui.CARD)
            row.pack(fill="x", pady=(0, ui.S_MD))

            hd = tk.Frame(row, bg=ui.CARD)
            hd.pack(fill="x")
            badge = tk.Frame(hd, bg=ui.PRIMARY_SOFT, padx=7, pady=1)
            badge.pack(side="left")
            tk.Label(badge, text=_num(i), bg=ui.PRIMARY_SOFT, fg=ui.PRIMARY_DEEP,
                     font=(ui.FONT_FAMILY, 11, "bold")).pack()
            tk.Label(hd, text="第 %d 空" % (i + 1), bg=ui.CARD,
                     fg=ui.TEXT_FAINT, font=ui.FONT_SMALL).pack(
                side="left", padx=(ui.S_SM, 0))

            var = tk.StringVar()
            cb = ttk.Combobox(row, textvariable=var, values=options,
                              state="readonly", width=1, font=ui.FONT_UI)
            cb.pack(fill="x", pady=(ui.S_XS, 0))
            cb.bind("<<ComboboxSelected>>",
                    lambda e, i=i, v=var: self._pick(i, v.get()))

            self.selections[i] = {"var": var, "answer": answer,
                                  "explain": explain}
            if self.submitted:
                self._show_feedback(row, i)

        self._update_prog()

    def _render_article(self, blanks):
        text = self.passage.get("text", "")
        # 兼容 ___1___ / __1__ 两种标记
        parts = re.split(r"_{2,}\s*(\d+)\s*_{2,}", text)
        self.article.configure(state="normal")
        self.article.delete("1.0", "end")
        idx = 0
        for k, seg in enumerate(parts):
            if k % 2 == 0:
                self.article.insert("end", seg)
            else:
                n = int(seg) - 1
                got = ""
                if self.submitted:
                    got = self.selections.get(n, {}).get("picked", "")
                label = ("%s%s" % (_num(n), got)) if got else _num(n)
                self.article.insert("end", " %s " % label,
                                    "right" if self.submitted and
                                    got == blanks[n][0] else "blank")
                idx += 1
        self.article.configure(state="disabled")

    def _pick(self, idx, val):
        if idx in self.selections:
            self.selections[idx]["picked"] = val
        self._update_prog()

    def _update_prog(self):
        n = len(self.passage.get("blanks", [])) if self.passage else 0
        filled = len([1 for k, v in self.selections.items()
                      if isinstance(k, int) and v.get("picked")])
        self.prog_lbl.config(text="已填 %d / %d 空" % (filled, n))

    def _speak(self):
        if not self.passage:
            return
        self.app.tts.speak(self.passage.get("text", "").replace("_", " "))
        self.app.set_status("正在朗读原文…")

    # ------------------------------------------------------------------ #
    def _submit(self):
        if not self.passage:
            return
        self.submitted = True
        blanks = self.passage.get("blanks", [])
        correct = 0
        detail = []
        for i, blank in enumerate(blanks):
            answer = blank[0]
            picked = self.selections.get(i, {}).get("picked", "")
            ok = (picked == answer)
            if ok:
                correct += 1
            detail.append({
                "q": "第%d空" % (i + 1), "answer": picked,
                "standard": answer, "correct": ok,
                "explain": blank[2] if len(blank) > 2 else "",
            })
            self.store.log_question("cloze", self.passage.get("title", ""), i,
                                    picked, ok, answer,
                                    blank[2] if len(blank) > 2 else "")

        self.store.add_exam("cloze", self.passage.get("title", ""),
                            correct, len(blanks), detail)
        self.score_lbl.config(text="得分 %d / %d" % (correct, len(blanks)))
        self.submit_btn.set_text("重新交卷")
        self._render()
        self.app.set_status("选词填空交卷：%d / %d" % (correct, len(blanks)))

    def _show_feedback(self, row, idx):
        info = self.selections.get(idx, {})
        ok = (info.get("picked", "") == info.get("answer", ""))
        color = ui.OK if ok else ui.WARN
        bg = ui.OK_SOFT if ok else ui.WARN_SOFT

        fb = tk.Frame(row, bg=bg)
        fb.pack(fill="x", pady=(ui.S_XS, 0), padx=(0, ui.S_SM))
        th = tk.Frame(fb, bg=bg)
        th.pack(fill="x", padx=ui.S_SM, pady=(4, 2))
        ui.Icon(th, "check" if ok else "close", size=12, color=color,
                bg=bg).pack(side="left", padx=(0, 4))
        tk.Label(th, text="对" if ok else "正确答案：%s" % info.get("answer", ""),
                 bg=bg, fg=color, font=ui.FONT_SMALL).pack(side="left")
        if info.get("explain"):
            ui.wrap_label(fb, text=info["explain"], fg=ui.TEXT_MUTED, bg=bg,
                          font=ui.FONT_SMALL, justify="left").pack(
                fill="x", padx=ui.S_SM, pady=(0, 4))
