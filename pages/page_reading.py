# -*- coding: utf-8 -*-
"""阅读理解页：选篇目 → 读文章 → 做单选 → 提交判分 → 看解析。

布局：
    ┌ 篇目 下拉  ‹ ›   第 3/10 篇 · 本篇 5 题 · 全库 50 题   完成 12/50 ┐
    │ ┌ 文章（上，weight 3）────────────────────────────────────┐        │
    │ │ 文章标签 + 朗读全文                                      │        │
    │ │ Georgia 正文，行距放宽                                   │        │
    │ └─────────────────────────────────────────────────────────┘        │
    │ ┌ 题目（下，weight 4）────────────────────────────────────┐        │
    │ │ [1] 题干                                                │        │
    │ │  ○ A …  （灰底行，选中变主色底）                          │        │
    │ └─────────────────────────────────────────────────────────┘        │
    │  提交答案  重做本篇  跳题                 ‹ 上一篇  下一篇 ›          │
"""

import hashlib

import tkinter as tk
import tkinter.ttk as ttk

import ui_common as ui

from data_sentences import READING_PASSAGES
from pages import Page


class ReadingPage(Page):
    """阅读理解：选文章 → 展示文章（可朗读）+ 题目（单选）；提交判分 → 显示对错与解析。"""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.passages = list(READING_PASSAGES)
        self.pi = 0
        self.submitted = False
        self.q_vars = []
        self.exam_mode = False
        self._cur_key = ""
        self._inner_no = []
        self._done = {}
        self._build()
        self.reload_data()

    # ------------------------------------------------------------------ #
    def reload_data(self, keep_index=False):
        """重新装配题库（导入/删除后调用）。"""
        old_title = None
        if self.passages and 0 <= self.pi < len(self.passages):
            old_title = self.passages[self.pi].get("title")

        items = list(READING_PASSAGES)
        for rec in self.store.user_content("reading"):
            d = rec["data"]
            if not d.get("questions"):
                continue
            d = dict(d)
            d["title"] = "【导入】" + d.get("title", "未命名")
            items.append(d)

        self.passages = items

        if keep_index and old_title:
            for i, p in enumerate(self.passages):
                if p.get("title") == old_title:
                    self.pi = i
                    break

        self.pi = max(0, min(self.pi, len(self.passages) - 1))
        self._apply_labels()
        self._load_passage()

    @staticmethod
    def _item_key(p):
        """套题的稳定标识：同一篇文章永远对应同一个 key。"""
        raw = (p.get("title", "") + "|" + p.get("passage", "")[:200]).encode(
            "utf-8")
        return hashlib.md5(raw).hexdigest()[:12]

    def _apply_labels(self):
        """给每篇文章加「第 N 篇」和完成标记，下拉框里直接看得出做到哪儿了。"""
        labels = []
        for i, p in enumerate(self.passages):
            key = self._item_key(p)
            name = p["title"].replace("【导入】", "")
            done = self.store.question_log("reading", key)
            total = len(p.get("questions") or [])
            hist = self.store.last_exam("reading", p["title"])

            if hist:
                mark = "（已做 %d/%d）" % (int(hist["score"]),
                                          int(hist["total"]))
            elif done:
                mark = "（进行中 %d/%d）" % (len(done), total)
            else:
                mark = ""

            labels.append("%02d. %s%s" % (i + 1, name, mark))
            p["_label"] = labels[-1]

        self.cb.configure(values=labels)

    def _load_passage(self):
        p = self.passages[self.pi]
        self.passage_var.set(p.get("_label") or p["title"])
        self._cur_key = self._item_key(p)
        self._done = self.store.question_log_full("reading", self._cur_key)
        self._inner_no = self._global_numbers()

        self.passage_text.configure(state="normal")
        self.passage_text.delete("1.0", "end")
        self.passage_text.insert("1.0", p["passage"])
        self.passage_text.configure(state="disabled")

        last = None
        if not self.exam_mode:
            last = self.store.last_exam("reading", p["title"])

        if self._done and last and last.get("detail"):
            self.submitted = True
            self._show_grading(last["detail"])
        else:
            self.result_lbl.config(text="")
            self.submitted = False
            self._build_questions()

        self._update_stat()

    def _global_numbers(self):
        """本篇题目在整个阅读题库里的连续题号（跨篇累加）。"""
        out = []
        base = 0
        for i, p in enumerate(self.passages):
            n = len(p.get("questions") or [])
            if i == self.pi:
                out = [base + k + 1 for k in range(n)]
                break
            base += n
        return out

    def _header_text(self):
        p = self.passages[self.pi]
        total_q = sum(len(x.get("questions") or []) for x in self.passages)
        return "第 %d / %d 篇　·　本篇 %d 题　·　全库 %d 题" % (
            self.pi + 1, len(self.passages),
            len(p.get("questions") or []), total_q,
        )

    # ------------------------------------------------------------------ #
    def _build(self):
        top = tk.Frame(self, bg=ui.BG)
        top.pack(fill="x", padx=ui.PAGE_PAD, pady=(ui.S_MD, ui.S_SM))

        tk.Label(top, text="篇目", bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI).pack(side="left", padx=(0, ui.S_SM))

        self.passage_var = tk.StringVar()
        self.cb = ttk.Combobox(top, textvariable=self.passage_var,
                               width=40, state="readonly",
                               values=[p["title"] for p in self.passages])
        self.cb.pack(side="left")
        self.cb.bind("<<ComboboxSelected>>", self._on_pick)

        ui.button(top, text="", kind="ghost", icon="arrow-left",
                  width=38, command=lambda: self._step(-1)).pack(
            side="left", padx=(ui.S_SM, 0))
        ui.button(top, text="", kind="ghost", icon="arrow-right",
                  width=38, command=lambda: self._step(1)).pack(
            side="left", padx=(ui.S_XS, 0))

        self.stat_lbl = tk.Label(top, text="", bg=ui.BG, fg=ui.TEXT_MUTED,
                                 font=ui.FONT_SMALL)
        self.stat_lbl.pack(side="right")

        self.pos_lbl = tk.Label(self, text="", bg=ui.BG, fg=ui.TEXT_FAINT,
                                font=ui.FONT_SMALL)
        self.pos_lbl.pack(anchor="w", padx=ui.PAGE_PAD + 2)

        # 底部按钮条先占位：pack 按顺序分配空间，晚于 body 会拿不到高度
        bar = tk.Frame(self, bg=ui.BG)
        bar.pack(side="bottom", fill="x", padx=ui.PAGE_PAD,
                 pady=(0, ui.S_MD))

        ui.button(bar, text="提交答案", kind="primary", icon="check",
                  command=self._submit).pack(side="left", padx=(0, ui.S_SM))
        ui.button(bar, text="重做本篇", kind="ghost", icon="undo",
                  command=self._reset).pack(side="left", padx=(0, ui.S_SM))
        ui.button(bar, text="跳题", kind="text", icon="arrow-right",
                  command=self._jump_ask).pack(side="left")

        body = tk.Frame(self, bg=ui.BG)
        body.pack(fill="both", expand=True, padx=ui.PAGE_PAD,
                  pady=(ui.S_XS, ui.S_XS))

        pane = ttk.PanedWindow(body, orient="vertical")
        pane.pack(fill="both", expand=True)

        # PanedWindow 的初始分割位置按子件 req 高度分配，而文章 Text 的
        # req 高度远大于题目区，会让题目卡只剩一条缝。首次布局完成后
        # 强制把 sash 拉到 46%，之后用户拖动不再干预。
        _sash = {"done": False}

        def _init_sash(_e=None):
            if _sash["done"]:
                return
            try:
                total = pane.winfo_height()
                if total > 240:
                    pane.sashpos(0, int(total * 0.46))
                    _sash["done"] = True
            except tk.TclError:
                pass

        pane.bind("<Configure>", _init_sash)

        # ---------------- 上：文章 ----------------
        louter, linner = ui.card(pane)
        pane.add(louter, weight=3)

        head = tk.Frame(linner, bg=ui.CARD)
        head.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.S_XS))
        ui.Icon(head, "doc", size=15, color=ui.TEXT_MUTED,
                bg=ui.CARD).pack(side="left")
        tk.Label(head, text="文章", bg=ui.CARD, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI_B).pack(side="left", padx=(ui.S_XS, 0))
        ui.button(head, text="朗读全文", kind="soft", icon="speaker",
                  command=self._speak_passage).pack(side="right")

        txtwrap = tk.Frame(linner, bg=ui.CARD)
        txtwrap.pack(fill="both", expand=True, padx=(ui.CARD_PAD, ui.S_SM),
                     pady=(0, ui.S_SM))

        self.passage_text = tk.Text(
            txtwrap, wrap="word", font=("Georgia", 12), relief="flat",
            bg=ui.CARD, fg=ui.TEXT, padx=2, pady=2, borderwidth=0,
            spacing1=3, spacing2=4, spacing3=10, width=20, height=6,
            selectbackground=ui.PRIMARY_SOFT, selectforeground=ui.PRIMARY_DEEP,
        )
        psb = ttk.Scrollbar(txtwrap, orient="vertical",
                            command=self.passage_text.yview)
        self.passage_text.configure(yscrollcommand=psb.set)
        psb.pack(side="right", fill="y")
        self.passage_text.pack(side="left", fill="both", expand=True)

        # ---------------- 下：题目 ----------------
        router, rinner = ui.card(pane)
        pane.add(router, weight=4)

        qhead = tk.Frame(rinner, bg=ui.CARD)
        qhead.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.S_XS))
        ui.Icon(qhead, "grid", size=15, color=ui.TEXT_MUTED,
                bg=ui.CARD).pack(side="left")
        tk.Label(qhead, text="题目", bg=ui.CARD, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI_B).pack(side="left", padx=(ui.S_XS, 0))

        self.result_lbl = tk.Label(qhead, text="", bg=ui.CARD, fg=ui.PRIMARY,
                                   font=(ui.FONT_FAMILY, 12, "bold"))
        self.result_lbl.pack(side="right")

        qwrap = ui.scrollable(rinner, bg=ui.CARD)
        qwrap[0].pack(fill="both", expand=True,
                      padx=(ui.CARD_PAD, ui.S_XS), pady=(0, ui.S_SM))
        self.q_frame = qwrap[1]

    # ------------------------------------------------------------------ #
    @staticmethod
    def _opt_row(parent, text, var, value, command, fg=None, bg=ui.CARD_SOFT,
                 border=ui.BORDER_SOFT):
        row = tk.Frame(parent, bg=bg, highlightthickness=1,
                       highlightbackground=border)
        rb = tk.Radiobutton(
            row, text=text, value=value, variable=var,
            bg=bg, fg=fg or ui.TEXT, selectcolor=bg,
            activebackground=ui.PRIMARY_SOFT,
            activeforeground=ui.PRIMARY_DEEP,
            font=ui.FONT_UI, anchor="w", justify="left",
            highlightthickness=0, bd=0, padx=10, pady=7,
            command=command)
        rb.pack(fill="x")
        row.bind("<Button-1>",
                 lambda e: (var.set(value), command()))
        row._rb = rb
        return row

    def _build_questions(self):
        for w in self.q_frame.winfo_children():
            w.destroy()

        p = self.passages[self.pi]
        self.q_vars = []

        for i, q in enumerate(p["questions"]):
            gno = self._inner_no[i] if i < len(self._inner_no) else i + 1
            box = tk.Frame(self.q_frame, bg=ui.CARD)
            box.pack(fill="x", pady=(0, ui.S_MD))

            qrow = tk.Frame(box, bg=ui.CARD)
            qrow.pack(fill="x", pady=(0, ui.S_SM))

            done = self._done.get(str(gno)) or {}
            flag = ""
            if done:
                flag = "  ✓" if done.get("correct") else "  ✗"

            fg = ui.TEXT_FAINT
            if done:
                fg = ui.OK if done.get("correct") else ui.WARN

            tk.Label(qrow, text="%02d" % gno, bg=ui.CARD, fg=fg,
                     font=("Consolas", 11, "bold")).pack(side="left")
            tk.Label(qrow, text=flag, bg=ui.CARD, fg=fg,
                     font=ui.FONT_SMALL).pack(side="left")

            v = tk.StringVar()
            if done and done.get("got"):
                v.set(done["got"])
            self.q_vars.append(v)

            ui.wrap_label(qrow, text=q["q"], fg=ui.TEXT, bg=ui.CARD,
                          font=ui.FONT_UI_B, justify="left").pack(
                side="left", fill="x", expand=True, padx=(ui.S_SM, 0))

            for opt in q["options"]:
                letter = opt[:1]
                self._opt_row(
                    box, opt, v, letter,
                    lambda g=gno, qq=q, vv=v: self._mark_one(g, qq, vv),
                ).pack(fill="x", pady=(0, ui.S_XS))

            ui.hline(box, pady=(ui.S_SM, ui.S_SM))

    # ------------------------------------------------------------------ #
    def _update_stat(self):
        total = sum(len(x.get("questions") or []) for x in self.passages)
        done = sum(
            len(self.store.question_log("reading", self._item_key(x)))
            for x in self.passages
        )

        hist = [h for h in self.store.exam_history(200)
                if h.get("kind") == "reading"]

        part = "完成 %d / %d 题" % (done, total)
        if hist:
            avg = sum(h["score"] / h["total"] for h in hist if h["total"]) \
                / len(hist)
            part += "　·　练习 %d 次　·　均分 %.0f%%" % (len(hist),
                                                      avg * 100)

        self.stat_lbl.config(text=part)
        self.pos_lbl.config(text=self._header_text())

    def _speak_passage(self):
        if not self.passages:
            return
        self.app.tts.speak(self.passages[self.pi]["passage"])
        self.app.set_status("正在朗读全文…")

    def _on_pick(self, _e=None):
        idx = self.cb.current()
        if idx >= 0:
            self.pi = idx
            self._load_passage()

    def _jump_to(self, gidx):
        """按全库题号定位到对应篇目。"""
        base = 0
        for i, p in enumerate(self.passages):
            n = len(p.get("questions") or [])
            if base < gidx <= base + n:
                if i != self.pi:
                    self.pi = i
                    self._load_passage()
                return
            base += n

    @staticmethod
    def _std_of(q):
        """标准答案统一成「B. 选项原文」这种形式，错题本里才看得懂。"""
        letter = q.get("answer", "")
        opts = q.get("options") or []
        for opt in opts:
            if opt[:1] == letter:
                if len(opt) > 2:
                    return "%s. %s" % (letter, opt[2:].strip())
                return letter
        return letter

    def _mark_one(self, gno, q, var):
        """选中一个选项就立刻记进「完成情况」，不用等整篇提交。"""
        got = var.get()
        if not got:
            return
        ok = (got == q["answer"])
        self.store.log_question(
            "reading", self._cur_key, str(gno), got, ok,
            self._std_of(q), q.get("explain", ""),
        )

        self._done[str(gno)] = {
            "got": got, "correct": ok,
            "answer": q["answer"], "explain": q.get("explain", ""),
        }
        self._apply_labels()
        self._update_stat()

    def _reset(self):
        self.result_lbl.config(text="")
        self.submitted = False
        self.store.clear_question_log("reading", self._cur_key)
        self._done = {}
        self._build_questions()

    def _submit(self):
        p = self.passages[self.pi]
        qs = p["questions"]
        total = len(qs)
        answered = sum(1 for v in self.q_vars if v.get())

        if answered < total:
            self.app.set_status(
                "还有 %d 题没选，先把空的做掉再提交吧" % (total - answered))
            self.result_lbl.config(text="已答 %d/%d，还有空题" % (answered, total),
                                   fg=ui.AMBER)
            return

        correct = 0
        detail = []
        for i, q in enumerate(qs):
            got = self.q_vars[i].get()
            ok = (got == q["answer"])
            gno = self._inner_no[i] if i < len(self._inner_no) else i + 1

            self.store.log_question(
                "reading", self._cur_key, str(gno), got, ok,
                self._std_of(q), q.get("explain", ""),
            )

            self._done[str(gno)] = {
                "got": got, "correct": ok,
                "answer": q["answer"], "explain": q.get("explain", ""),
            }

            if ok:
                correct += 1

            detail.append("%d.%s(%s->%s)" % (
                gno, "O" if ok else "X", got or "-", q["answer"],
            ))

        self.submitted = True
        self._apply_labels()
        self._show_grading(";".join(detail))

        self.store.add_exam("reading", p["title"], correct, total,
                            ";".join(detail))
        self._update_stat()
        self.app.set_status("阅读：答对 %d/%d" % (correct, total))

    def _show_grading(self, detail):
        p = self.passages[self.pi]
        qs = p["questions"]
        total = len(qs)
        right = sum(1 for d in self._done.values() if d.get("correct"))

        color = ui.OK if right == total else (
            ui.AMBER if right >= total * 0.6 else ui.WARN
        )
        self.result_lbl.config(text="答对 %d / %d" % (right, total), fg=color)

        self.submitted = True

        for w in self.q_frame.winfo_children():
            w.destroy()
        self.q_vars = []

        for i, q in enumerate(qs):
            gno = self._inner_no[i] if i < len(self._inner_no) else i + 1
            d = self._done.get(str(gno)) or {}
            got = d.get("got", "")
            ok = d.get("correct")

            box = tk.Frame(self.q_frame, bg=ui.CARD)
            box.pack(fill="x", pady=(0, ui.S_MD))

            qrow = tk.Frame(box, bg=ui.CARD)
            qrow.pack(fill="x", pady=(0, ui.S_SM))
            ui.Icon(qrow, "check" if ok else "close", size=15,
                    color=ui.OK if ok else ui.WARN,
                    bg=ui.CARD).pack(side="left", padx=(0, ui.S_XS))
            tk.Label(qrow, text="%02d" % gno, bg=ui.CARD, fg=ui.TEXT_FAINT,
                     font=("Consolas", 11, "bold")).pack(side="left")
            tk.Label(qrow, text=q["q"], bg=ui.CARD, fg=ui.TEXT,
                     font=ui.FONT_UI_B, justify="left").pack(
                side="left", fill="x", expand=True, padx=(ui.S_SM, 0))

            for opt in q["options"]:
                letter = opt[:1]
                if letter == q["answer"]:
                    bg, fg, mark = ui.OK_SOFT, ui.OK, "　← 标准答案"
                elif letter == got:
                    bg, fg, mark = ui.WARN_SOFT, ui.WARN, "　← 你选的"
                else:
                    bg, fg, mark = ui.CARD_SOFT, ui.TEXT_MUTED, ""
                tk.Label(box, text=opt + mark, bg=bg, fg=fg, font=ui.FONT_UI,
                         justify="left", anchor="w", padx=10, pady=6).pack(
                    fill="x", pady=(0, ui.S_XS))

            if q.get("explain"):
                ui.wrap_label(box, text="解析：" + q["explain"],
                              fg=ui.TEXT_MUTED, bg=ui.CARD,
                              font=ui.FONT_SMALL, justify="left").pack(
                    fill="x", pady=(ui.S_XS, 0))

            ui.hline(box)

    def _jump_ask(self):
        from tkinter import simpledialog

        total = sum(len(x.get("questions") or []) for x in self.passages)
        n = simpledialog.askinteger(
            "跳题", "输入题号（1-%d）" % total, parent=self,
            minvalue=1, maxvalue=max(1, total),
        )
        if n:
            self._jump_to(n)

    def _step(self, d):
        nxt = self.pi + d
        if 0 <= nxt < len(self.passages):
            self.pi = nxt
            self._load_passage()

    def on_show(self):
        self._apply_labels()
        self._update_stat()
