# -*- coding: utf-8 -*-
"""单词本页：收藏 + 重点记忆"""

import time

import tkinter as tk
import tkinter.ttk as ttk

import ui_common as ui
from pages import Page

# level 代码 -> 中文名（含空串兜底）
LEVEL_LABEL = {"GZ": "高中", "CET4": "四级", "CET6": "六级", "": "—"}

# 排序选项：显示名 -> 存储 order 键
ORDER_ITEMS = (
    ("收藏时间（新→旧）", "added"),
    ("错得多的排前面", "wrong"),
    ("字母顺序", "alpha"),
)

LEVELS = (("全部", "ALL"), ("高中", "GZ"), ("四级", "CET4"), ("六级", "CET6"))


def _fmt(ts):
    """把时间戳格式化成 'MM-DD HH:MM'，异常时返回 '-'。"""
    try:
        return time.strftime("%m-%d %H:%M", time.localtime(ts))
    except (ValueError, OSError):
        return "-"


def _tuples_from(rec):
    """把单词本记录还原成 6 元组 (词, 音标, 词性, 释义, 例句, 例句翻译)。"""
    d = rec.get("data") or []
    if isinstance(d, (list, tuple)) and len(d) >= 6:
        return tuple(d[:6])
    if isinstance(d, dict):
        t = d.get("word") or ()
        if len(t) >= 6:
            return tuple(t[:6])
    return (rec.get("word", ""), "", "", "", "", "")


class WordbookPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.configure(bg=ui.BG)

        self.app = app
        self.store = app.store

        self.level = tk.StringVar(value="ALL")
        self.order = tk.StringVar(value=ORDER_ITEMS[0][0])
        self.kw = tk.StringVar(value="")

        self.items = []
        self.idx = 0
        self.revealed = False
        self._current = None

        self._build()
        self.reload_data()

    # ------------------------------------------------------------------ #
    # 界面构建
    # ------------------------------------------------------------------ #
    def _build(self):
        top = tk.Frame(self, bg=ui.BG)
        top.pack(fill="x", padx=ui.PAGE_PAD, pady=(ui.S_MD, ui.S_SM))

        self.level_seg = ui.segment(top, LEVELS, value=self.level.get(),
                                    command=self._on_level)
        self.level_seg.pack(side="left")

        tk.Label(top, text="排序", bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=ui.FONT_SMALL).pack(side="left", padx=(ui.S_LG, ui.S_SM))
        cb = ttk.Combobox(top, textvariable=self.order, width=16,
                          state="readonly", values=[t for t, _ in ORDER_ITEMS])
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self._reload())

        search_box = tk.Frame(top, bg=ui.CARD, highlightthickness=1,
                              highlightbackground=ui.BORDER,
                              highlightcolor=ui.PRIMARY)
        search_box.pack(side="left", padx=(ui.S_LG, 0))
        ui.Icon(search_box, "search", size=14, color=ui.TEXT_FAINT,
                bg=ui.CARD).pack(side="left", padx=(8, 2), pady=4)
        ent = ttk.Entry(search_box, textvariable=self.kw, width=14,
                        style="Search.TEntry")
        ent.pack(side="left", padx=(0, 6), pady=2)
        ent.bind("<KeyRelease>", lambda e: self._refresh_list())
        self.search_entry = ent

        self.stat_lbl = tk.Label(top, text="", bg=ui.BG, fg=ui.TEXT_MUTED,
                                 font=ui.FONT_SMALL)
        self.stat_lbl.pack(side="right")

        body = tk.Frame(self, bg=ui.BG)
        body.pack(fill="both", expand=True, padx=ui.PAGE_PAD,
                  pady=(0, ui.S_SM))

        self.pane = ttk.PanedWindow(body, orient="horizontal")
        self.pane.pack(fill="both", expand=True)

        # 左：收藏列表
        left = tk.Frame(self.pane, bg=ui.BG)
        card_o, card_i = ui.card(left)
        card_o.pack(fill="both", expand=True)

        head = tk.Frame(card_i, bg=ui.CARD)
        head.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.S_SM))
        tk.Label(head, text="我的单词本", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_SUBTITLE).pack(side="left")
        ui.button(head, text="移出", icon="trash", kind="danger", height=30,
                  command=self._remove_sel).pack(side="right",
                                                 padx=(ui.S_SM, 0))
        ui.button(head, text="朗读", icon="speaker", kind="ghost", height=30,
                  command=self._speak_sel).pack(side="right")

        self.list_stage = tk.Frame(card_i, bg=ui.CARD)
        self.list_stage.pack(fill="both", expand=True)

        cols = ("word", "level", "state", "rev")
        self.tree = ttk.Treeview(self.list_stage, columns=cols,
                                 show="headings", height=16)
        for c, t, w, anchor in (("word", "单词", 150, "w"),
                                ("level", "词库", 60, "center"),
                                ("state", "掌握情况", 110, "w"),
                                ("rev", "复习", 50, "center")):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, minwidth=40, anchor=anchor)

        vsb = ttk.Scrollbar(self.list_stage, orient="vertical",
                            command=self.tree.yview)
        self.vsb = vsb
        self.tree.configure(yscrollcommand=vsb.set)
        self._list_bar_shown = True
        # 注意 pack 顺序：先 vsb(side=right) 再 tree(side=left, expand)，
        # 否则 tree 会把宽度吃光、vsb 分不到空间。
        vsb.pack(side="right", fill="y", padx=(0, ui.S_SM),
                 pady=(0, ui.CARD_PAD))
        self.tree.pack(side="left", fill="both", expand=True,
                       padx=(ui.CARD_PAD, 0), pady=(0, ui.CARD_PAD))

        self.tree.tag_configure("odd", background=ui.CARD_SOFT)
        self.tree.bind("<<TreeviewSelect>>", self._on_pick)
        self.pane.add(left, weight=3)

        # 左栏空状态覆盖层（place 覆盖，不参与 pack 挤压）
        self.left_empty = tk.Frame(self.list_stage, bg=ui.CARD)
        le_in = tk.Frame(self.left_empty, bg=ui.CARD)
        le_in.pack(expand=True)
        ui.Icon(le_in, "book", size=30, color=ui.TEXT_FAINT,
                bg=ui.CARD, width=1.5).pack(pady=(0, 8))
        tk.Label(le_in, text="还没有收藏的单词", bg=ui.CARD,
                 fg=ui.TEXT, font=ui.FONT_UI_B).pack()
        tk.Label(le_in, text="去「词汇记忆」点 ☆ 收藏", bg=ui.CARD,
                 fg=ui.TEXT_MUTED, font=ui.FONT_SMALL).pack(pady=(4, 0))

        # 右：重点记忆卡片
        right = tk.Frame(self.pane, bg=ui.BG)
        ro, ri = ui.card(right)
        ro.pack(fill="both", expand=True)
        self.card_inner = ri

        rhead = tk.Frame(ri, bg=ui.CARD)
        rhead.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, 0))
        tk.Label(rhead, text="重点记忆", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_SUBTITLE).pack(side="left")
        self.idx_lbl = tk.Label(rhead, text="", bg=ui.CARD,
                                fg=ui.TEXT_FAINT, font=ui.FONT_SMALL)
        self.idx_lbl.pack(side="right")

        # 底部操作栏先占位（pack 顺序决定优先级，否则会被中间内容挤到半空）
        rbar = tk.Frame(ri, bg=ui.CARD)
        rbar.pack(side="bottom", fill="x", padx=ui.CARD_PAD,
                  pady=(0, ui.S_MD))

        self.reveal_btn = ui.button(rbar, text="显示释义", icon="eye",
                                    kind="primary", height=34,
                                    command=self._reveal)
        self.reveal_btn.pack(side="left", padx=(0, ui.S_SM))
        self.speak_btn = ui.button(rbar, text="发音", icon="speaker",
                                   kind="ghost", height=34,
                                   command=self._speak_cur)
        self.speak_btn.pack(side="left", padx=(0, ui.S_SM))
        self.ok_btn = ui.button(rbar, text="认识", icon="check", kind="primary",
                                height=34, command=lambda: self._mark(True))
        self.ok_btn.pack(side="right", padx=(ui.S_SM, 0))
        self.no_btn = ui.button(rbar, text="不认识", icon="close",
                                kind="danger", height=34,
                                command=lambda: self._mark(False))
        self.no_btn.pack(side="right")

        box = tk.Frame(ri, bg=ui.CARD)
        box.pack(fill="both", expand=True, padx=ui.CARD_PAD, pady=ui.S_SM)

        # 词卡内容与空状态叠在同一舞台里，靠 place 切换，互不挤压
        self.stage = tk.Frame(box, bg=ui.CARD)
        self.stage.pack(fill="both", expand=True)
        content = tk.Frame(self.stage, bg=ui.CARD)
        content.place(x=0, y=0, relwidth=1, relheight=1)
        self._content = content
        center = tk.Frame(content, bg=ui.CARD)
        center.pack(expand=True)

        self.word_lbl = tk.Label(center, text="", bg=ui.CARD, fg=ui.TEXT,
                                 font=ui.FONT_WORD)
        self.word_lbl.pack(pady=(6, 2))
        self.phon_lbl = tk.Label(center, text="", bg=ui.CARD,
                                 fg=ui.TEXT_FAINT, font=ui.FONT_PHON)
        self.phon_lbl.pack(pady=(0, 12))
        self.pos_lbl = tk.Label(center, text="", bg=ui.CARD, fg=ui.PRIMARY,
                                font=ui.FONT_UI_B)
        self.pos_lbl.pack()
        self.mean_lbl = tk.Label(center, text="", bg=ui.CARD, fg=ui.TEXT,
                                 font=(ui.FONT_FAMILY, 14),
                                 wraplength=400, justify="center")
        self.mean_lbl.pack(pady=(8, 12))

        self.ex_box = tk.Frame(center, bg=ui.CARD)
        mid = tk.Frame(self.ex_box, bg=ui.CARD)
        mid.pack()
        tk.Frame(mid, bg=ui.BORDER_SOFT, height=1, width=110).pack(
            side="left", pady=8)
        tk.Label(mid, text="  例句  ", bg=ui.CARD, fg=ui.TEXT_FAINT,
                 font=ui.FONT_SMALL).pack(side="left")
        tk.Frame(mid, bg=ui.BORDER_SOFT, height=1, width=110).pack(
            side="left", pady=8)

        self.ex_lbl = tk.Label(self.ex_box, text="", bg=ui.CARD, fg=ui.TEXT,
                               font=ui.FONT_EX, wraplength=400,
                               justify="center")
        self.ex_lbl.pack(pady=(8, 2))
        self.ex_cn_lbl = tk.Label(self.ex_box, text="", bg=ui.CARD,
                                  fg=ui.TEXT_MUTED, font=ui.FONT_SMALL,
                                  wraplength=400, justify="center")
        self.ex_cn_lbl.pack(pady=(0, 4))

        self.hint_lbl = tk.Label(content, text="点「显示释义」或按空格查看",
                                 bg=ui.CARD, fg=ui.TEXT_FAINT,
                                 font=ui.FONT_SMALL)
        self.hint_lbl.pack(pady=(6, 4))

        # 空状态层
        self.empty_layer = tk.Frame(self.stage, bg=ui.CARD)
        el_in = tk.Frame(self.empty_layer, bg=ui.CARD)
        el_in.pack(expand=True)
        ui.Icon(el_in, "bookmark", size=34, color=ui.TEXT_FAINT,
                bg=ui.CARD, width=1.5).pack(pady=(0, 10))
        tk.Label(el_in, text="单词本是空的", bg=ui.CARD,
                 fg=ui.TEXT, font=ui.FONT_UI_B).pack()
        tk.Label(el_in,
                 text="在「词汇记忆」页点 ☆ 收藏单词，就会出现在这里",
                 bg=ui.CARD, fg=ui.TEXT_MUTED, font=ui.FONT_SMALL,
                 wraplength=380, justify="center").pack(pady=(6, 0))

        self.pane.add(right, weight=4)

        # 全局快捷键
        self.bind_all("<space>", self._on_space, "+")
        self.bind_all("<Left>", lambda e: self._prev(), "+")
        self.bind_all("<Right>", lambda e: self._next(), "+")

        self.after(60, self._place_sash)

    def _on_level(self, val):
        self.level.set(val)
        self._reload()

    def _place_sash(self):
        """左列表 : 右卡片 = 45 : 55，避免右栏过窄把释义挤变形。"""
        try:
            self.update_idletasks()
            total = self.pane.winfo_width()
            if total > 200:
                self.pane.sashpos(0, int(total * 0.45))
        except (tk.TclError, AttributeError):
            pass

    # ------------------------------------------------------------------ #
    # 数据加载与筛选
    # ------------------------------------------------------------------ #
    def _cur_order(self):
        for label, val in ORDER_ITEMS:
            if label == self.order.get():
                return val
        return "added"

    def _reload(self):
        self.idx = 0
        self.reload_data()

    def reload_data(self):
        lv = self.level.get()
        if lv == "ALL":
            lv = None
        self.items = self.store.wordbook(level=lv, order=self._cur_order())
        self.idx = min(self.idx, max(0, len(self.items) - 1))
        self._refresh_list()
        self._render()

    def _matched(self):
        kw = self.kw.get().strip().lower()
        if not kw:
            return list(self.items)
        out = []
        for rec in self.items:
            t = _tuples_from(rec)
            blob = " ".join(str(x) for x in t).lower()
            if kw in blob:
                out.append(rec)
        return out

    def _refresh_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = self._matched()
        for n, rec in enumerate(rows):
            word = rec.get("word")
            lv = LEVEL_LABEL.get(rec.get("level")) or rec.get("level") or "—"
            wrong = rec.get("wrong") or 0
            rev = rec.get("reviews") or 0
            if rev == 0:
                state = "未复习"
            elif wrong == 0:
                state = "都会"
            else:
                state = "错 %d 次" % wrong
            tag = "odd" if n % 2 else "even"
            self.tree.insert("", "end", iid=word,
                             values=(word, lv, state, rev), tags=(tag,))

        counts = self.store.wordbook_count()
        total = sum(counts.values())
        self.stat_lbl.config(text="共收藏 %d 词" % total)

        # 列表空 / 有内容的互斥显示
        if rows:
            self._show_list(True)
        else:
            self._show_list(False)

    def _show_list(self, flag):
        """列表为空时把 tree + 滚动条一起藏掉，只留空状态插图。"""
        if flag:
            if not getattr(self, "_list_bar_shown", True):
                self.vsb.pack(side="right", fill="y",
                              padx=(0, ui.S_SM), pady=(0, ui.CARD_PAD))
                self._list_bar_shown = True
            if not self.tree.winfo_ismapped():
                self.tree.pack(side="left", fill="both", expand=True,
                               padx=(ui.CARD_PAD, 0),
                               pady=(0, ui.CARD_PAD))
            self.left_empty.place_forget()
        else:
            if getattr(self, "_list_bar_shown", True):
                self.vsb.pack_forget()
                self._list_bar_shown = False
            self.tree.pack_forget()
            self.left_empty.place(relx=0, rely=0, relwidth=1, relheight=1)

    # ------------------------------------------------------------------ #
    # 卡片渲染
    # ------------------------------------------------------------------ #
    def _cur(self):
        rows = self._matched()
        if not rows:
            return None
        self.idx = max(0, min(self.idx, len(rows) - 1))
        return rows[self.idx]

    def _set_ex_visible(self, flag):
        if flag:
            if not self.ex_box.winfo_ismapped():
                self.ex_box.pack()
        else:
            self.ex_box.pack_forget()

    def _show_right_empty(self, flag):
        """空状态覆盖：用 place 把空状态层压在词卡上面，避免布局互相挤压。"""
        if flag:
            self.hint_lbl.pack_forget()
            self.empty_layer.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.empty_layer.place_forget()
            if not self.hint_lbl.winfo_ismapped():
                self.hint_lbl.pack(pady=(6, 4))

    def _render(self):
        rec = self._cur()
        self.revealed = False
        self.pos_lbl.config(text="")
        self.mean_lbl.config(text="")
        self._set_ex_visible(False)
        self.hint_lbl.config(text="点「显示释义」或按空格查看")

        if not rec:
            self.idx_lbl.config(text="")
            self._current = None
            self._show_right_empty(True)
            for b in (self.reveal_btn, self.ok_btn, self.no_btn,
                      self.speak_btn):
                try:
                    b.set_enabled(False)
                except AttributeError:
                    b.config(state="disabled")
            return

        self._show_right_empty(False)
        t = _tuples_from(rec)
        self._current = t
        self.word_lbl.config(font=ui.FONT_WORD, fg=ui.TEXT)
        for b in (self.reveal_btn, self.ok_btn, self.no_btn, self.speak_btn):
            try:
                b.set_enabled(True)
            except AttributeError:
                b.config(state="normal")

        rows = self._matched()
        self.idx_lbl.config(text="第 %d / %d 个" % (self.idx + 1, len(rows)))
        self.word_lbl.config(text=t[0] or "")
        self.phon_lbl.config(text=t[1] or "")
        self.pos_lbl.config(text="")
        self.mean_lbl.config(text="· · ·　· · ·　· · ·")

        if t[0] in self.tree.get_children():
            self.tree.selection_set(t[0])
            self.tree.see(t[0])
            return
        if self.tree.get_children():
            self.tree.selection_remove(self.tree.selection())
            return

    def _reveal(self):
        if not self._current:
            return
        _w, phon, pos, mean, ex, ex_cn = self._current
        self.phon_lbl.config(text=phon or "")
        show_pos = bool(pos) and not str(mean or "").strip().lower().startswith(
            str(pos).strip().lower())
        self.pos_lbl.config(text=pos if show_pos else "")
        self.mean_lbl.config(text=mean or "")
        self.ex_lbl.config(text=ex or "")
        self.ex_cn_lbl.config(text=ex_cn or "")
        self._set_ex_visible(bool(ex or ex_cn))
        self.hint_lbl.config(text="")
        self.revealed = True

    # ------------------------------------------------------------------ #
    # 交互
    # ------------------------------------------------------------------ #
    def _on_pick(self, _e=None):
        sel = self.tree.selection()
        if not sel:
            return
        word = sel[0]
        rows = self._matched()
        for i, rec in enumerate(rows):
            if rec.get("word") == word:
                if i != self.idx:
                    self.idx = i
                    self._render()
                return

    def _speak_cur(self):
        if self._current:
            self.app.tts.speak(self._current[0], blocking=False)
            self.app.set_status("正在朗读：" + self._current[0])

    def _speak_sel(self):
        sel = self.tree.selection()
        if not sel:
            self.app.set_status("先在列表里选一个单词")
            return
        self.app.tts.speak(sel[0], blocking=False)

    def _mark(self, correct):
        if not self._current:
            return
        if not self.revealed:
            self._reveal()
            return
        word = self._current[0]
        self.store.record_wordbook_review(word, correct)
        self.app.set_status(("✓ 认识 " if correct else "✗ 不认识 ") + word)

        for rec in self.items:
            if rec.get("word") == word:
                rec["reviews"] = (rec.get("reviews") or 0) + 1
                rec["wrong"] = (rec.get("wrong") or 0) + (0 if correct else 1)
                rec["last_review"] = int(time.time())
                break

        if self._cur_order() == "wrong":
            self.reload_data()
        else:
            self._refresh_list()
        self._next()

    def _remove_sel(self):
        sel = self.tree.selection()
        if not sel:
            self.app.set_status("先在列表里选一个单词")
            return
        for word in sel:
            self.store.remove_wordbook(word)
        self.app.set_status("已移出 %d 个单词" % len(sel))
        self.reload_data()
        self._notify_vocab()

    def _next(self):
        rows = self._matched()
        if self.idx < len(rows) - 1:
            self.idx += 1
            self._render()
        else:
            self.app.set_status("已经是最后一个啦")

    def _prev(self):
        if self.idx > 0:
            self.idx -= 1
            self._render()

    def _on_space(self, _e=None):
        try:
            if self.app.notebook.index("current") != self._page_index():
                return
        except (tk.TclError, AttributeError):
            return
        if not self.revealed:
            self._reveal()
            return
        self._next()

    def _page_index(self):
        try:
            return list(self.app.pages).index("wordbook")
        except ValueError:
            return -1

    def _notify_vocab(self):
        try:
            self.app.pages["vocab"].reload_data()
        except Exception:
            pass

    def on_show(self):
        self.reload_data()
        self.after(50, self._place_sash)
