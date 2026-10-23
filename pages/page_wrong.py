# -*- coding: utf-8 -*-
"""错题本页：把做错的题集中起来重做，做对就自动出本。"""

import time

import tkinter as tk
from tkinter import ttk

import ui_common as ui

from pages import Page

# 题型代码 -> 中文标签
KIND_LABEL = {
    "reading": "阅读理解",
    "cloze": "选词填空",
    "translate": "翻译",
    "mock": "模拟考试",
}

# 顶部筛选：全部 + 可重做的题型
FILTERS = [
    ("全部", ""),
    ("阅读理解", "reading"),
    ("选词填空", "cloze"),
    ("翻译", "translate"),
]


def _fmt(ts):
    """把时间戳格式成 'MM-DD HH:MM'，异常时返回 '-'。"""
    try:
        return time.strftime("%m-%d %H:%M", time.localtime(ts))
    except (ValueError, OSError):
        return "-"


class WrongPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, bg=ui.BG)
        self.app = app
        self.store = app.store
        self.kind = tk.StringVar(value="")
        self.rows = []
        self._sel = None
        self._build()
        self.reload_data()

    def _build(self):
        # 顶部：题型筛选 + 统计 + 操作按钮
        top = tk.Frame(self, bg=ui.BG)
        top.pack(fill="x", padx=ui.PAGE_PAD, pady=(ui.S_MD, ui.S_SM))

        tk.Label(top, text="题型", bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI).pack(side="left", padx=(0, ui.S_SM))
        seg = ui.segment(top, FILTERS, value="", command=self._on_filter)
        seg.pack(side="left")

        self.stat_lbl = tk.Label(top, text="", bg=ui.BG, fg=ui.TEXT_MUTED,
                                 font=ui.FONT_SMALL)
        self.stat_lbl.pack(side="left", padx=(ui.S_LG, 0))

        ui.button(top, text="重做错题", kind="primary", icon="refresh",
                  command=self._retry).pack(side="right")
        ui.button(top, text="清空本类", kind="danger", icon="trash",
                  command=self._clear).pack(side="right", padx=(0, ui.S_SM))

        body = tk.Frame(self, bg=ui.BG)
        body.pack(fill="both", expand=True, padx=ui.PAGE_PAD,
                  pady=(0, ui.S_SM))

        # 左：错题列表（先建好，pack 放到右栏之后，否则 expand 会独占宽度）
        left_wrap = tk.Frame(body, bg=ui.BG)
        lcard_o, lcard = ui.card(left_wrap)
        lcard_o.pack(fill="both", expand=True)

        lhead = tk.Frame(lcard, bg=ui.CARD)
        lhead.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.S_SM))
        ui.Icon(lhead, "close", size=16, color=ui.WARN,
                bg=ui.CARD).pack(side="left")
        tk.Label(lhead, text="错题清单", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_SUBTITLE).pack(side="left", padx=(ui.S_SM, 0))
        tk.Label(lhead, text="双击一行可直接跳到对应题型重做",
                 bg=ui.CARD, fg=ui.TEXT_FAINT,
                 font=ui.FONT_SMALL).pack(side="right")

        self.stage = tk.Frame(lcard, bg=ui.CARD)
        self.stage.pack(fill="both", expand=True)

        cols = ("kind", "no", "mine", "std", "times", "at")
        self.tree = ttk.Treeview(self.stage, columns=cols, show="headings",
                                 height=18)
        for c, title, w, anchor in (
            ("kind", "题型", 96, "w"),
            ("no", "题号", 64, "center"),
            ("mine", "你的答案", 200, "w"),
            ("std", "标准答案", 210, "w"),
            ("times", "次数", 56, "center"),
            ("at", "最近作答", 104, "center"),
        ):
            self.tree.heading(c, text=title)
            self.tree.column(c, width=w, anchor=anchor)

        vs = ttk.Scrollbar(self.stage, orient="vertical",
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)
        vs.pack(side="right", fill="y", padx=(0, ui.S_SM),
                pady=(0, ui.CARD_PAD))
        self.tree.pack(side="left", fill="both", expand=True,
                       padx=(ui.CARD_PAD, 0), pady=(0, ui.CARD_PAD))

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._retry())
        self.tree.tag_configure("odd", background=ui.CARD_SOFT)

        # 列表空状态（place 覆盖，不参与 pack 挤压）
        self.empty = tk.Frame(self.stage, bg=ui.CARD)
        ein = tk.Frame(self.empty, bg=ui.CARD)
        ein.pack(expand=True)
        ui.Icon(ein, "check", size=34, color=ui.OK, bg=ui.CARD,
                width=1.8).pack(pady=(0, 10))
        tk.Label(ein, text="错题本是空的", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_UI_B).pack()
        tk.Label(ein, text="做错的阅读、选词填空会自动收进来，重做对了就出本",
                 bg=ui.CARD, fg=ui.TEXT_MUTED, font=ui.FONT_SMALL,
                 wraplength=320, justify="center").pack(pady=(6, 0))

        # 右：详情面板（固定宽度；先 pack 右侧，左栏再 expand）
        right_wrap = tk.Frame(body, bg=ui.BG, width=376)
        right_wrap.pack(side="right", fill="y", padx=(ui.GAP, 0))
        right_wrap.pack_propagate(False)
        left_wrap.pack(side="left", fill="both", expand=True)
        rcard_o, rcard = ui.card(right_wrap)
        rcard_o.pack(fill="both", expand=True)

        rhead = tk.Frame(rcard, bg=ui.CARD)
        rhead.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.S_SM))
        ui.Icon(rhead, "doc", size=16, color=ui.TEXT_MUTED,
                bg=ui.CARD).pack(side="left")
        tk.Label(rhead, text="这一题的详情", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_SUBTITLE).pack(side="left", padx=(ui.S_SM, 0))

        self.fix_btn = ui.button(rcard, text="这题我已经会了", kind="primary",
                                 icon="check", command=self._mark_fixed)
        self.fix_btn.pack(side="bottom", fill="x", padx=ui.CARD_PAD,
                          pady=(ui.S_SM, ui.CARD_PAD))
        self.fix_btn.set_enabled(False)

        self.detail = ui.scrollable(rcard, bg=ui.CARD)
        self.detail[0].pack(fill="both", expand=True,
                            padx=(ui.CARD_PAD, 0), pady=(0, ui.S_SM))
        self.detail_in = self.detail[1]
        self._sel = None

    # ------------------------------------------------------------------ #
    def _on_filter(self, val):
        self.kind.set(val)
        self.reload_data()

    def reload_data(self):
        self.rows = self.store.wrong_questions(self.kind.get() or None)

        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.rows):
            self.tree.insert(
                "", "end", str(i),
                values=(
                    KIND_LABEL.get(r["kind"], r["kind"]),
                    r["q_index"],
                    (r["answer"] or "（空）")[:40],
                    (r["standard"] or "-")[:50],
                    r["attempts"],
                    _fmt(r["created_at"]),
                ),
                tags=("odd",) if i % 2 else (),
            )

        total = len(self.rows)
        stats = self.store.wrong_stats()
        all_wrong = sum(stats.values())

        self.stat_lbl.config(
            text="共 %d 道错题" % all_wrong
            + ("，当前筛选 %d 道" % total if self.kind.get() else ""))

        if self.rows:
            self.empty.place_forget()
        else:
            self.empty.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._show_detail(None)

    def _on_select(self, _e=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.rows):
            self._show_detail(self.rows[idx])

    def _block(self, title, text, fg=None, bg_tint=None, icon_name=None,
               mono=False):
        wrap = tk.Frame(self.detail_in, bg=bg_tint or ui.CARD)
        wrap.pack(fill="x", padx=(0, ui.CARD_PAD), pady=(0, ui.S_MD))
        if title:
            th = tk.Frame(wrap, bg=bg_tint or ui.CARD)
            th.pack(fill="x", padx=(ui.S_MD if bg_tint else 0),
                    pady=(ui.S_SM if bg_tint else 0, ui.S_XS))
            if icon_name:
                ui.Icon(th, icon_name, size=13, color=fg or ui.TEXT_MUTED,
                        bg=bg_tint or ui.CARD).pack(side="left",
                                                    padx=(0, ui.S_XS))
            tk.Label(th, text=title, bg=bg_tint or ui.CARD,
                     fg=fg or ui.TEXT_MUTED,
                     font=ui.FONT_SMALL).pack(side="left")
        lbl = ui.wrap_label(wrap, text=text, fg=ui.TEXT if not fg else fg,
                            bg=bg_tint or ui.CARD,
                            font=ui.FONT_MONO if mono else ui.FONT_UI)
        lbl.pack(fill="x", anchor="w",
                 padx=((ui.S_MD, ui.S_MD) if bg_tint else 0),
                 pady=((0, ui.S_SM) if bg_tint else 0))
        return wrap

    def _show_detail(self, row):
        self._sel = row
        for w in self.detail_in.winfo_children():
            w.destroy()

        if row is None:
            self.fix_btn.set_enabled(False)
            ui.empty_state(
                self.detail_in, icon="eye", title="还没选题目",
                desc="在左边点一道错题，这里会显示你当时填了什么、"
                     "标准答案是什么", bg=ui.CARD, pady=48)
            return

        self.fix_btn.set_enabled(True)
        q = row["q_index"]
        head = tk.Frame(self.detail_in, bg=ui.CARD)
        head.pack(fill="x", padx=(0, ui.CARD_PAD), pady=(0, ui.S_MD))
        ui.chip(head, KIND_LABEL.get(row["kind"], row["kind"]),
                fg=ui.PRIMARY_DEEP, bg=ui.PRIMARY_SOFT).pack(side="left")
        tk.Label(head, text="第 %s 题" % q, bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_UI_B).pack(side="left", padx=(ui.S_SM, 0))
        tk.Label(head, text="作答 %d 次 · %s" % (row["attempts"],
                                              _fmt(row["created_at"])),
                 bg=ui.CARD, fg=ui.TEXT_FAINT,
                 font=ui.FONT_SMALL).pack(side="right")

        self._block("你的答案", row["answer"] or "（空）", fg=ui.WARN,
                    bg_tint=ui.WARN_SOFT, icon_name="close")
        self._block("标准答案", row["standard"] or "（无）", fg=ui.OK,
                    bg_tint=ui.OK_SOFT, icon_name="check")
        self._block("解析", row["explain"] or "（这题没有配解析）",
                    fg=ui.TEXT_MUTED)

    def _mark_fixed(self):
        if not self._sel:
            return
        self.store.mark_question_fixed(
            self._sel["kind"], self._sel["item_key"], self._sel["q_index"])
        self.app.set_status("已从错题本移除，继续加油")
        self.reload_data()

    def _clear(self):
        kind = self.kind.get()
        n = len(self.rows)
        if not n:
            self.app.set_status("这一栏没有错题，不用清了")
            return

        if kind:
            self.store.conn.execute(
                "DELETE FROM question_log WHERE kind=? AND correct=0",
                (kind,))
        else:
            self.store.conn.execute(
                "DELETE FROM question_log WHERE correct=0")
        self.store.conn.commit()

        self.app.set_status("已清掉 %d 道错题" % n)
        self.reload_data()

    def _retry(self):
        sel = self.tree.selection()
        row = self.rows[int(sel[0])] if sel else None
        if not row:
            self.app.set_status("先选一道错题再点重做")
            return

        key = {"reading": "read", "cloze": "cloze",
               "translate": "trans"}.get(row["kind"], row["kind"])
        if not key:
            self.app.set_status(
                KIND_LABEL.get(row["kind"], row["kind"]) + " 请到对应页签重做")
            return

        try:
            self.notebook_switch(key)
        except Exception:  # noqa: BLE001
            self.app.set_status("跳转失败，请手动点对应页签")

    def notebook_switch(self, key):
        nb = getattr(self.app, "notebook", None)
        page = self.app.pages.get(key)
        if nb is None or page is None:
            raise KeyError(key)
        nb.select(page)
        if hasattr(page, "on_show"):
            page.on_show()

    def on_show(self):
        self.reload_data()
