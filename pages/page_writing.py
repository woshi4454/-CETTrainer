# -*- coding: utf-8 -*-
"""作文页：真题话题 + 模板填空 + 实时词数统计 + 自我检查清单

左侧：选一个真题话题 + 写正文（实时统计词数、到点计时、自检）；
右侧：万能模板、高分替换词、连接词，点「插入」即可填进正文。
"""

import re
import tkinter as tk
import tkinter.ttk as ttk

import ui_common as ui
from data_writing import WRITING_TOPICS, TEMPLATES, UPGRADE_WORDS, CONNECTORS
from pages import Page

CET4_MIN = 120
CET6_MIN = 150

LEVELS = [("四级 120", "CET4"), ("六级 150", "CET6")]


def count_words(text):
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]*", text))


class WritingPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.topic_i = 0
        self.tpl_i = 0
        self.level = tk.StringVar(value="CET4")
        self._timer_on = False
        self._timer_left = 1800
        self._timer_job = None
        self._build()
        self._load_topic()
        self._load_template()

    # ---------------------------------------------------------------- #
    # UI 构建
    # ---------------------------------------------------------------- #
    def _build(self):
        # ---- 顶部工具条 ----
        top = tk.Frame(self, bg=ui.BG)
        top.pack(fill="x", padx=ui.PAGE_PAD, pady=(ui.S_MD, ui.S_SM))

        self.btn_clear = ui.button(top, text="清空重写", kind="ghost",
                                   icon="trash", command=self._clear)
        self.btn_clear.pack(side="right")

        tk.Label(top, text="目标字数", bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI).pack(side="left", padx=(ui.S_LG, ui.S_SM))
        ui.segment(top, LEVELS, value="CET4", command=self._on_level_pick
                   ).pack(side="left")

        tk.Label(top, text="真题话题", bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI).pack(side="left")
        self.topic_cb = ttk.Combobox(
            top, state="readonly", width=40,
            values=["%02d. %s" % (i + 1, t[0])
                    for i, t in enumerate(WRITING_TOPICS)])
        self.topic_cb.current(0)
        self.topic_cb.pack(side="left", padx=(ui.S_SM, 0))
        self.topic_cb.bind("<<ComboboxSelected>>", lambda _e: self._pick_topic())

        # ---- 主体：左写作 / 右模板 ----
        body = tk.Frame(self, bg=ui.BG)
        body.pack(fill="both", expand=True, padx=ui.PAGE_PAD,
                  pady=(0, ui.S_SM))

        # 右侧先占位（固定宽）
        right_wrap = tk.Frame(body, bg=ui.BG, width=392)
        right_wrap.pack(side="right", fill="y")
        right_wrap.pack_propagate(False)

        left_wrap = tk.Frame(body, bg=ui.BG)
        left_wrap.pack(side="left", fill="both", expand=True,
                       padx=(0, ui.GAP))

        # ---- 左：题干卡 ----
        stem_outer, stem_in = ui.card(left_wrap)
        stem_outer.pack(fill="x", pady=(0, ui.S_SM))

        sh = tk.Frame(stem_in, bg=ui.CARD)
        sh.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, 0))
        self.source_chip = ui.chip(sh, "四级", fg=ui.INFO, bg=ui.INFO_SOFT)
        self.source_chip.pack(side="left")

        self.stem = ui.wrap_label(
            stem_in, text="", fg=ui.TEXT, bg=ui.CARD,
            font=(ui.FONT_FAMILY, 11), justify="left", anchor="w")
        self.stem.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_SM, ui.S_XS))

        self.kw_lbl = ui.wrap_label(
            stem_in, text="", fg=ui.TEXT_FAINT, bg=ui.CARD,
            font=ui.FONT_SMALL, justify="left", anchor="w")
        self.kw_lbl.pack(fill="x", padx=ui.CARD_PAD, pady=(0, ui.S_MD))

        # ---- 左：写作区 ----
        w_outer, w_in = ui.card(left_wrap)
        w_outer.pack(fill="both", expand=True)

        wbar = tk.Frame(w_in, bg=ui.CARD)
        wbar.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.S_SM))

        self.timer_lbl = tk.Label(wbar, text="", bg=ui.CARD, fg=ui.TEXT_MUTED,
                                  font=("Consolas", 12, "bold"))
        self.timer_lbl.pack(side="right")
        self.btn_timer = ui.button(wbar, text="计时 30 分钟", kind="ghost",
                                   icon="clock", command=self._toggle_timer)
        self.btn_timer.pack(side="right", padx=(0, ui.S_SM))
        self.btn_check = ui.button(wbar, text="检查", kind="soft", icon="search",
                                   command=self._check)
        self.btn_check.pack(side="right", padx=(0, ui.S_SM))

        self.count_lbl = tk.Label(wbar, text="0 词 / 目标 120", bg=ui.CARD,
                                  fg=ui.TEXT_MUTED, font=ui.FONT_UI_B)
        self.count_lbl.pack(side="left")

        # 正文输入区（带细边）
        box = tk.Frame(w_in, bg=ui.CARD, highlightthickness=1,
                       highlightbackground=ui.BORDER,
                       highlightcolor=ui.PRIMARY)
        box.pack(fill="both", expand=True, padx=ui.CARD_PAD,
                 pady=(0, ui.S_SM))

        self.text = tk.Text(box, wrap="word", relief="flat", bd=0,
                            bg=ui.CARD, fg=ui.TEXT,
                            font=("Consolas", 12), padx=14, pady=12,
                            undo=True, insertbackground=ui.TEXT,
                            spacing3=6, highlightthickness=0)
        self.text.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(box, orient="vertical", command=self.text.yview)
        sb.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=sb.set)
        self.text.bind("<<Modified>>", self._on_modified)

        self.result = ui.wrap_label(
            w_in, text="", fg=ui.TEXT_MUTED, bg=ui.CARD,
            font=ui.FONT_SMALL, justify="left", anchor="w")
        self.result.pack(fill="x", padx=ui.CARD_PAD, pady=(0, ui.S_MD))

        # ---- 右：模板卡 ----
        r_outer, r_in = ui.card(right_wrap)
        r_outer.pack(fill="both", expand=True)

        rh = tk.Frame(r_in, bg=ui.CARD)
        rh.pack(fill="x", padx=ui.CARD_PAD, pady=(ui.S_MD, ui.S_SM))
        ui.Icon(rh, "sheet", size=16, color=ui.TEXT_MUTED,
                bg=ui.CARD).pack(side="left")
        tk.Label(rh, text="模板", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_UI_B).pack(side="left", padx=(ui.S_SM, 0))
        ttk.Style()
        self.tpl_cb = ttk.Combobox(rh, state="readonly", width=18,
                                   values=[t["name"] for t in TEMPLATES],
                                   font=ui.FONT_SMALL)
        self.tpl_cb.current(0)
        self.tpl_cb.pack(side="right")
        self.tpl_cb.bind("<<ComboboxSelected>>", lambda _e: self._pick_tpl())

        tpl_scroll, self.tpl_frame = ui.scrollable(r_in, bg=ui.CARD)
        tpl_scroll.pack(fill="both", expand=True,
                        padx=(ui.CARD_PAD, ui.S_SM), pady=(0, ui.S_MD))

    # ---------------------------------------------------------------- #
    # 话题
    # ---------------------------------------------------------------- #
    def _pick_topic(self):
        self.topic_i = self.topic_cb.current()
        self._load_topic()

    def _load_topic(self):
        t = WRITING_TOPICS[self.topic_i]
        title, source, kind, cn, en, keys = t
        self.source_chip.config(text="%s·%s" % (source, kind))
        self.stem.config(text="%s\n%s" % (cn, en))
        self.kw_lbl.config(text="可用关键词：" + " / ".join(keys))

    def _on_level_pick(self, val):
        self.level.set(val)
        self._update_count(force=True)

    def _on_level(self):
        self._update_count(force=True)

    # ---------------------------------------------------------------- #
    # 模板
    # ---------------------------------------------------------------- #
    def _pick_tpl(self):
        self.tpl_i = self.tpl_cb.current()
        self._load_template()

    def _load_template(self):
        for w in self.tpl_frame.winfo_children():
            w.destroy()
        t = TEMPLATES[self.tpl_i]

        tk.Label(self.tpl_frame, text=t["name"], bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_SUBTITLE, anchor="w",
                 justify="left").pack(anchor="w", fill="x")
        tk.Label(self.tpl_frame,
                 text="%s　难度 %s" % (t["scene"], "★" * t["level"]),
                 bg=ui.CARD, fg=ui.TEXT_FAINT, font=ui.FONT_SMALL,
                 anchor="w").pack(anchor="w", fill="x", pady=(2, ui.S_SM))

        for label, key in (("开头", "opening"), ("中间", "body"),
                           ("结尾", "closing")):
            seg = tk.Frame(self.tpl_frame, bg=ui.CARD_SOFT)
            seg.pack(anchor="w", fill="x", pady=(0, ui.S_SM))

            head = tk.Frame(seg, bg=ui.CARD_SOFT)
            head.pack(fill="x", padx=ui.S_SM, pady=(ui.S_SM, 0))
            tk.Label(head, text=label, bg=ui.CARD_SOFT, fg=ui.PRIMARY_DEEP,
                     font=ui.FONT_SMALL).pack(side="left")
            ui.button(head, text="插入", kind="soft", height=26,
                      command=lambda k=key: self._insert(t[k])).pack(side="right")

            txt = tk.Text(seg, wrap="word", relief="flat", bd=0,
                          highlightthickness=0, bg=ui.CARD_SOFT,
                          fg=ui.TEXT_MUTED, font=("Consolas", 10),
                          height=self._lines(t[key]), cursor="arrow",
                          padx=ui.S_SM, pady=4, spacing3=3)
            txt.insert("1.0", t[key])
            txt.config(state="disabled")
            txt.pack(fill="x", padx=(ui.S_SM, 2))

        tk.Label(self.tpl_frame, text="※ " + t["tips"], bg=ui.CARD,
                 fg=ui.AMBER, font=ui.FONT_SMALL, anchor="w",
                 justify="left").pack(anchor="w", fill="x",
                                      pady=(0, ui.S_MD))

        tk.Label(self.tpl_frame, text="高分替换词", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_UI_B, anchor="w").pack(
            anchor="w", fill="x", pady=(ui.S_SM, ui.S_XS))
        for bad, good in UPGRADE_WORDS:
            ui.wrap_label(self.tpl_frame, text="%s → %s" % (bad, good),
                          fg=ui.TEXT_MUTED, bg=ui.CARD, font=ui.FONT_SMALL,
                          justify="left", anchor="w").pack(
                anchor="w", fill="x", pady=1)

        tk.Label(self.tpl_frame, text="连接词", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_UI_B, anchor="w").pack(
            anchor="w", fill="x", pady=(ui.S_MD, ui.S_XS))
        for tag, words in CONNECTORS:
            ui.wrap_label(self.tpl_frame, text="%s：%s" % (tag, words),
                          fg=ui.TEXT_MUTED, bg=ui.CARD, font=ui.FONT_SMALL,
                          justify="left", anchor="w").pack(
                anchor="w", fill="x", pady=1)

    @staticmethod
    def _lines(text):
        return max(2, min(9, text.count("\n") + len(text) // 34 + 1))

    def _insert(self, snippet):
        self.text.insert("insert", snippet + " ")
        self.text.focus_set()
        self._update_count(force=True)

    # ---------------------------------------------------------------- #
    # 正文操作
    # ---------------------------------------------------------------- #
    def _clear(self):
        self.text.delete("1.0", "end")
        self.result.config(text="")
        self._update_count(force=True)

    def _on_modified(self, _e=None):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            self._update_count()

    def _update_count(self, force=False):
        txt = self.text.get("1.0", "end")
        n = count_words(txt)
        need = CET4_MIN if self.level.get() == "CET4" else CET6_MIN
        if n >= need:
            color = ui.OK
        elif n >= need * 0.7:
            color = ui.AMBER
        else:
            color = ui.TEXT_MUTED
        self.count_lbl.config(text="%d 词 / 目标 %d" % (n, need), fg=color)
        if force:
            self.text.edit_modified(False)

    # ---------------------------------------------------------------- #
    # 计时
    # ---------------------------------------------------------------- #
    def _toggle_timer(self):
        if self._timer_on:
            self._timer_on = False
            if self._timer_job:
                self.after_cancel(self._timer_job)
                self._timer_job = None
            self.timer_lbl.config(text="", fg=ui.TEXT_MUTED)
            self.btn_timer.set_text("计时 30 分钟")
            self.btn_timer.set_kind("ghost")
            return
        self._timer_on = True
        self._timer_left = 1800
        self.btn_timer.set_text("暂停计时")
        self.btn_timer.set_kind("soft")
        self._tick()

    def _tick(self):
        if not self._timer_on:
            return
        m, s = divmod(self._timer_left, 60)
        color = ui.WARN if self._timer_left <= 300 else ui.TEXT_MUTED
        self.timer_lbl.config(text="%02d:%02d" % (m, s), fg=color)
        if self._timer_left <= 0:
            self._timer_on = False
            self.timer_lbl.config(text="时间到", fg=ui.WARN)
            self.app.set_status("作文计时结束，可以对照模板自查一下")
            return
        self._timer_left -= 1
        self._timer_job = self.after(1000, self._tick)

    # ---------------------------------------------------------------- #
    # 自检
    # ---------------------------------------------------------------- #
    def _check(self):
        txt = self.text.get("1.0", "end").strip()
        if not txt:
            self.result.config(text="先写点东西再检查吧", fg=ui.AMBER)
            return

        n = count_words(txt)
        need = CET4_MIN if self.level.get() == "CET4" else CET6_MIN
        issues = []
        if n < need:
            issues.append("字数 %d，还差 %d 词" % (n, need - n))

        low = txt.lower()
        paras = [p for p in re.split(r"\n\s*\n|\n", txt) if p.strip()]
        if len(paras) < 3:
            issues.append("只分了 %d 段，建议三段：观点 / 理由 / 总结" % len(paras))

        conn_hit = sum(1 for _t, w in CONNECTORS
                       if any(x.strip().lower() in low for x in w.split(" / ")))
        if conn_hit < 3:
            issues.append("连接词用得少（%d/6 类），考试里分段靠它拿分" % conn_hit)
        if "in conclusion" not in low and "to sum up" not in low:
            issues.append("结尾没有总结句（可加 In conclusion / To sum up）")

        words = re.findall(r"[A-Za-z][A-Za-z'\-]*", txt)
        freq = {}
        for w in words:
            w = w.lower()
            freq[w] = freq.get(w, 0) + 1
        rep = ["%s×%d" % (w, c) for w, c in
               sorted(freq.items(), key=lambda x: -x[1])[:3] if c >= 4]
        if rep:
            issues.append("有词重复太多：" + "、".join(rep) + "（可换同义词）")

        if re.search(r"\bi\s", txt):
            issues.append("注意第一人称 I 要大写")

        if not issues:
            self.result.config(
                text="✓ 字数、结构、连接词都还像样，检查一下拼写就可以交卷了",
                fg=ui.OK)
        else:
            self.result.config(text="待改进：" + "；".join(issues), fg=ui.WARN)

        self._update_count(force=True)
        self.store.set_setting("writing_last", txt[:4000])

    def on_show(self):
        self._update_count(force=True)

    def reload_data(self):
        pass
