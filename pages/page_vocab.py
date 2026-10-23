# -*- coding: utf-8 -*-
"""词汇记忆页"""

import random
import tkinter as tk
import tkinter.ttk as ttk

import ui_common as ui

from data_vocab import CET4_WORDS, CET6_WORDS

try:
    from data_gaokao import GAOKAO_WORDS
except Exception:
    GAOKAO_WORDS = []

from pages import Page

LEVELS = (("高中", "GZ"), ("四级", "CET4"), ("六级", "CET6"))

# 词书：等级代码 -> 内置词表
_WORD_BOOK = {
    "CET4": CET4_WORDS,
    "CET6": CET6_WORDS,
    "GZ": GAOKAO_WORDS,
}


class VocabPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.app = app
        self.store = app.store

        self.level = tk.StringVar(value="CET4")
        self.words = []
        self.idx = 0
        self.revealed = False

        self._build()
        self._load()

    # ---------- 构建界面 ----------
    def _build(self):
        top = tk.Frame(self, bg=ui.BG)
        top.pack(fill="x", padx=ui.PAGE_PAD, pady=(ui.S_MD, ui.S_SM))

        self.level_seg = ui.segment(
            top, LEVELS, value=self.level.get(), command=self._on_level)
        self.level_seg.pack(side="left")

        tk.Label(top, text="顺序", bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=ui.FONT_SMALL).pack(side="left", padx=(ui.S_LG, ui.S_SM))

        self.order = tk.StringVar(value="顺序学")
        cb = ttk.Combobox(
            top, textvariable=self.order, width=9, state="readonly",
            values=("顺序学", "随机学", "只练生词"),
        )
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self._load())

        self.stat_lbl = tk.Label(top, text="", bg=ui.BG, fg=ui.TEXT_MUTED,
                                 font=ui.FONT_SMALL)
        self.stat_lbl.pack(side="right")

        outer, inner = ui.card(self)
        outer.pack(fill="both", expand=True, padx=ui.PAGE_PAD, pady=(0, ui.S_SM))
        self.card_inner = inner

        # 卡片底部信息条（左侧进度，右侧快捷键提示）
        foot = tk.Frame(inner, bg=ui.CARD)
        foot.pack(side="bottom", fill="x", padx=ui.CARD_PAD, pady=(0, ui.S_MD))
        self.idx_lbl = tk.Label(foot, text="", bg=ui.CARD, fg=ui.TEXT_FAINT,
                                font=ui.FONT_SMALL)
        self.idx_lbl.pack(side="left")
        self.hint_lbl = tk.Label(
            foot, text="空格 显示释义　·　← → 切换", bg=ui.CARD,
            fg=ui.TEXT_FAINT, font=ui.FONT_SMALL)
        self.hint_lbl.pack(side="right")

        box = tk.Frame(inner, bg=ui.CARD)
        box.pack(expand=True)

        self.word_lbl = tk.Label(
            box, text="", bg=ui.CARD, fg=ui.TEXT, font=ui.FONT_WORD)
        self.word_lbl.pack(pady=(4, 2))

        self.phon_lbl = tk.Label(
            box, text="", bg=ui.CARD, fg=ui.TEXT_FAINT, font=ui.FONT_PHON)
        self.phon_lbl.pack(pady=(0, 14))

        self.pos_lbl = tk.Label(
            box, text="", bg=ui.CARD, fg=ui.PRIMARY, font=ui.FONT_UI_B)
        self.pos_lbl.pack()

        self.mean_lbl = tk.Label(
            box, text="", bg=ui.CARD, fg=ui.TEXT,
            font=(ui.FONT_FAMILY, 14), wraplength=680, justify="center")
        self.mean_lbl.pack(pady=(10, 14))

        # 例句整块：未显示释义时整块隐藏，避免大片空白
        self.ex_box = tk.Frame(box, bg=ui.CARD)

        mid = tk.Frame(self.ex_box, bg=ui.CARD)
        mid.pack()
        tk.Frame(mid, bg=ui.BORDER_SOFT, height=1, width=200).pack(
            side="left", pady=8)
        tk.Label(mid, text="  例句  ", bg=ui.CARD, fg=ui.TEXT_FAINT,
                 font=ui.FONT_SMALL).pack(side="left")
        tk.Frame(mid, bg=ui.BORDER_SOFT, height=1, width=200).pack(
            side="left", pady=8)

        self.ex_lbl = tk.Label(
            self.ex_box, text="", bg=ui.CARD, fg=ui.TEXT,
            font=ui.FONT_EX, wraplength=680, justify="center")
        self.ex_lbl.pack(pady=(10, 2))

        self.ex_cn_lbl = tk.Label(
            self.ex_box, text="", bg=ui.CARD, fg=ui.TEXT_MUTED,
            font=ui.FONT_UI, wraplength=680, justify="center")
        self.ex_cn_lbl.pack(pady=(0, 4))

        bar = tk.Frame(self, bg=ui.BG)
        bar.pack(fill="x", padx=ui.PAGE_PAD, pady=(ui.S_XS, ui.S_MD))

        ui.button(bar, text="上一个", icon="arrow-left", kind="ghost",
                  command=self._prev, height=36).pack(
            side="left", padx=(0, ui.S_SM))
        ui.button(bar, text="下一个", icon="arrow-right", kind="ghost",
                  command=self._next, height=36).pack(
            side="left", padx=(0, ui.S_SM))

        self.reveal_btn = ui.button(
            bar, text="显示释义", icon="eye", kind="primary",
            command=self._reveal, height=36)
        self.reveal_btn.pack(side="left", padx=(ui.S_MD, ui.S_SM))

        self.speak_btn = ui.button(bar, text="发音", icon="speaker",
                                   kind="ghost", command=self._speak,
                                   height=36)
        self.speak_btn.pack(side="left", padx=(0, ui.S_SM))

        self.star_btn = ui.button(
            bar, text="收藏", icon="star", kind="ghost",
            command=self._toggle_star, height=36)
        self.star_btn.pack(side="left", padx=(0, ui.S_SM))

        self.ok_btn = ui.button(
            bar, text="认识", icon="check", kind="primary",
            command=lambda: self._mark(True), height=36)
        self.ok_btn.pack(side="right", padx=(ui.S_SM, 0))

        self.no_btn = ui.button(
            bar, text="不认识", icon="close", kind="danger",
            command=lambda: self._mark(False), height=36)
        self.no_btn.pack(side="right", padx=(ui.S_SM, 0))

        self.bind_all("<space>", self._on_space, "+")
        self.bind_all("<Left>", lambda e: self._prev(), "+")
        self.bind_all("<Right>", lambda e: self._next(), "+")

    def _on_level(self, val):
        self.level.set(val)
        self._load()

    # ---------- 组装词表 ----------
    def _all_words(self):
        level = self.level.get()
        base = list(_WORD_BOOK.get(level) or [])
        try:
            base = self.store.pack_vocab(level) + base
        except Exception:
            pass

        try:
            for rec in self.store.user_content("vocab", level=level):
                d = rec.get("data") if isinstance(rec, dict) else None
                if not isinstance(d, dict):
                    continue
                raw = d.get("word")
                t = tuple(raw) if raw else ()
                if len(t) == 6 and t[0]:
                    base.append(t)
        except Exception:
            pass

        seen = set()
        out = []
        for w in base:
            try:
                k = str(w[0]).lower()
            except Exception:
                continue
            if k in seen:
                continue
            seen.add(k)
            out.append(w)
        return out

    # ---------- 全局刷新 ----------
    def reload_data(self):
        self._load()

    # ---------- 加载当前词书 ----------
    def _load(self):
        level = self.level.get()
        pool = list(self._all_words())

        mode = self.order.get()
        if mode == "随机学":
            random.shuffle(pool)
        elif mode == "只练生词":
            try:
                w = self.store.weak_words(level, 500)
                weak = {x["word"] for x in w}
            except Exception:
                weak = set()
            filtered = [x for x in pool if x[0] in weak]
            pool = filtered if filtered else pool

        self.words = pool
        self.idx = 0
        self._render()

    # ---------- 取当前词 ----------
    def _cur(self):
        if not self.words:
            return None
        self.idx = max(0, min(self.idx, len(self.words) - 1))
        return self.words[self.idx]

    # ---------- 渲染当前词 ----------
    def _render(self):
        w = self._cur()

        stats = self.store.word_stats(self.level.get())
        self.stat_lbl.config(
            text="已学 {} / {}　·　已掌握 {}".format(
                stats.get("touched", 0), len(self.words),
                stats.get("mastered", 0)))

        if not w:
            self.word_lbl.config(text="没有可用的单词", font=ui.FONT_TITLE,
                                 fg=ui.TEXT_MUTED)
            self.phon_lbl.config(text="换个词库试试")
            self.pos_lbl.config(text="")
            self.mean_lbl.config(text="")
            self._set_ex_visible(False)
            self.hint_lbl.config(text="")
            self.idx_lbl.config(text="")
            for b in (self.reveal_btn, self.ok_btn, self.no_btn,
                      self.star_btn, self.speak_btn):
                try:
                    b.set_enabled(False)
                except AttributeError:
                    b.config(state="disabled")
            return

        self.word_lbl.config(font=ui.FONT_WORD, fg=ui.TEXT)
        for b in (self.reveal_btn, self.ok_btn, self.no_btn,
                  self.star_btn, self.speak_btn):
            try:
                b.set_enabled(True)
            except AttributeError:
                b.config(state="normal")

        word, phon, pos, mean, ex, ex_cn = w

        self.word_lbl.config(text=word)
        self.phon_lbl.config(text=phon)
        self.revealed = False
        self._hide_meaning()

        self.pos_lbl.config(text="")
        self.mean_lbl.config(text="")
        self.ex_lbl.config(text="")
        self.ex_cn_lbl.config(text="")
        self._set_ex_visible(False)

        self.hint_lbl.config(text="点击「显示释义」或按空格查看答案")

        self.idx_lbl.config(
            text="第 {} / {} 个".format(self.idx + 1, len(self.words)))
        self._current = (pos, mean, ex, ex_cn)
        self._full = w
        self._update_buttons()

    def _set_ex_visible(self, flag):
        """例句区在未揭示时整块隐藏，避免大片空白。"""
        if flag:
            if not self.ex_box.winfo_ismapped():
                self.ex_box.pack(pady=(6, 0))
        else:
            self.ex_box.pack_forget()

    # ---------- 隐藏释义 ----------
    def _hide_meaning(self):
        self.pos_lbl.config(text="")
        self.mean_lbl.config(text="· · ·　· · ·　· · ·")

    # ---------- 显示释义 ----------
    def _reveal(self):
        if not hasattr(self, "_current"):
            return
        pos, mean, ex, ex_cn = self._current
        # 释义本身常已带词性（"n. 非洲"），此时不再重复显示词性
        show_pos = bool(pos) and not str(mean).strip().lower().startswith(
            str(pos).strip().lower())
        self.pos_lbl.config(text=pos if show_pos else "")
        self.mean_lbl.config(text=mean)
        self.ex_lbl.config(text=ex)
        self.ex_cn_lbl.config(text=ex_cn)
        self._set_ex_visible(bool(ex or ex_cn))
        self.hint_lbl.config(text="")
        self.revealed = True
        self._update_buttons()

    # ---------- 更新收藏按钮 ----------
    def _update_buttons(self):
        w = self._cur()
        if not w or not hasattr(self, "star_btn"):
            return
        try:
            starred = self.store.in_wordbook(w[0])
        except Exception:
            starred = False
        self.star_btn.set_text("已收藏" if starred else "收藏")
        if starred:
            self.star_btn.set_kind("soft")
        else:
            self.star_btn.set_kind("ghost")

    # ---------- 收藏 / 取消收藏 ----------
    def _toggle_star(self):
        w = self._cur()
        if not w:
            return
        try:
            if self.store.in_wordbook(w[0]):
                self.store.remove_wordbook(w[0])
                self.app.set_status("已从单词本移出：" + w[0])
            else:
                self.store.add_wordbook(w[0], self.level.get(), list(w))
                self.app.set_status("★ 已收藏到单词本：" + w[0])
        except Exception as e:
            self.app.set_status("收藏失败：" + str(e))
            return
        try:
            self._update_buttons()
            self.app.pages["wordbook"].reload_data()
        except Exception:
            pass

    # ---------- 发音 ----------
    def _speak(self):
        w = self._cur()
        if not w:
            return
        self.app.tts.speak(w[0])
        self.app.set_status("正在朗读：" + w[0])

    # ---------- 认识 / 不认识 ----------
    def _mark(self, correct):
        w = self._cur()
        if not w:
            return
        if not self.revealed:
            self._reveal()
            return
        self.store.record_word(w[0], self.level.get(), correct)
        self.app.set_status(
            ("✓ 认识 " if correct else "✗ 不认识 ") + w[0])
        self._next()

    # ---------- 下一个 ----------
    def _next(self):
        if self.idx < len(self.words) - 1:
            self.idx += 1
            self._render()
        else:
            self.app.set_status("已经是最后一个啦，点「上一个」往回看")

    # ---------- 上一个 ----------
    def _prev(self):
        if self.idx > 0:
            self.idx -= 1
            self._render()

    # ---------- 空格键 ----------
    def _on_space(self, _e=None):
        try:
            if self.app.notebook.index("current") != 0:
                return
            if not self.revealed:
                self._reveal()
                return
            self._next()
        except (tk.TclError, AttributeError):
            return

    # ---------- 切到本页 ----------
    def on_show(self):
        self._render()
