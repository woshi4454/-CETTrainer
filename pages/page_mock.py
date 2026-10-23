# -*- coding: utf-8 -*-
"""模拟考试页（从 page_mock.py.dis 反汇编蓝图还原）

功能：
  - 组卷：按所选套卷（CET4 / CET6 / mini）从阅读、选词填空题库抽题；
  - 计时：整卷倒计时（_tick），时间到自动交卷；
  - 作答：逐篇切换（_load_item / _show_item），答案存在 self.state 里；
  - 判分：交卷统一批改（_submit / _show_result），并记录最佳成绩（_refresh_best）。

说明：本页复用 ReadingPage / ClozePage 两个子页组件，组卷与判分逻辑来自蓝图；
子页内部接口（q_vars 为列表、cloze 用 selections）已做兼容适配。
"""

import time
import tkinter as tk
import tkinter.ttk as ttk

import ui_common as ui

from pages import Page
from pages.page_reading import ReadingPage
from pages.page_cloze import ClozePage


# 套卷定义：{key: {minutes, label}}
PLANS = {
    "CET4": {"minutes": 40, "label": "四级整卷（阅读2篇+选词填空1篇）"},
    "CET6": {"minutes": 40, "label": "六级整卷（阅读2篇+选词填空1篇）"},
    "mini": {"minutes": 15, "label": "小测（阅读1篇+选词填空1篇）"},
}


class MockPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.app = app
        self.store = app.store

        self.plan_var = tk.StringVar(value="CET4")
        self.plan_keys = list(PLANS.keys())
        self.level_var = tk.StringVar(value="CET4")

        self.running = False
        self.finished = False
        self.deadline = 0.0
        self.used_sec = 0
        self.paper = []
        self.state = {}
        self.sheet = []
        self._tick_job = None

        # 承载阅读 / 选词填空子页的容器
        self._area = tk.Frame(self, bg=ui.BG)
        self._reading = ReadingPage(self._area, app=app)
        self._cloze = ClozePage(self._area, app=app)
        self._reading.exam_mode = True
        self._cloze.exam_mode = True
        # 先都布局再隐藏，_start / _show_item 时再切显
        self._reading.pack(side="top", fill="both", expand=True)
        self._cloze.pack(side="top", fill="both", expand=True)
        self._reading.pack_forget()
        self._cloze.pack_forget()

        self._build()
        self._refresh_best()

    # ------------------------------------------------------------------ #
    # 时间格式化
    # ------------------------------------------------------------------ #
    def _fmt_clock(self, sec):
        return f"{max(0, int(sec)) // 60:02d}:{max(0, int(sec)) % 60:02d}"

    # ------------------------------------------------------------------ #
    # UI 构建
    # ------------------------------------------------------------------ #
    def _build(self):
        # 工具条（页面标题由顶栏统一给出，这里不再重复大标题）
        bar = tk.Frame(self, bg=ui.BG)
        bar.pack(fill="x", padx=ui.PAGE_PAD, pady=(ui.S_MD, ui.S_SM))

        # 先 pack 右侧固定区，再 pack 左侧，避免右侧被挤出可视区
        right = tk.Frame(bar, bg=ui.BG)
        right.pack(side="right", fill="y")

        clock_box = tk.Frame(right, bg=ui.BG)
        clock_box.pack(side="right")

        tk.Label(clock_box, text="剩余", bg=ui.BG, fg=ui.TEXT_FAINT,
                 font=ui.FONT_SMALL).pack(side="left", padx=(0, ui.S_XS))
        self.clock_lbl = tk.Label(clock_box, text="00:00", bg=ui.BG,
                                  fg=ui.TEXT,
                                  font=("Consolas", 17, "bold"))
        self.clock_lbl.pack(side="left")

        self.best_lbl = tk.Label(right, text="", bg=ui.BG,
                                 fg=ui.TEXT_FAINT, font=ui.FONT_SMALL)
        self.best_lbl.pack(side="right", padx=(0, ui.S_LG))

        left = tk.Frame(bar, bg=ui.BG)
        left.pack(side="left", fill="y")

        tk.Label(left, text="套卷", bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI).pack(side="left", padx=(0, ui.S_SM))
        self.cb_plan = ttk.Combobox(
            left, textvariable=self.plan_var, state="readonly", width=26,
            values=[PLANS[k]["label"] for k in self.plan_keys],
            font=ui.FONT_UI,
        )
        self.cb_plan.pack(side="left")
        if self.cb_plan["values"]:
            self.cb_plan.current(0)

        # 第二行：翻篇 + 当前位置 + 主操作按钮
        nav = tk.Frame(self, bg=ui.BG)
        nav.pack(fill="x", padx=ui.PAGE_PAD, pady=(0, ui.S_SM))

        self.btn_submit = ui.button(nav, text="交卷批改", kind="ghost",
                                    icon="save", state="disabled",
                                    command=self._submit)
        self.btn_submit.pack(side="right")

        self.btn_start = ui.button(nav, text="开始考试", kind="primary",
                                   icon="check", command=self._start)
        self.btn_start.pack(side="right", padx=(0, ui.S_SM))

        self.btn_prev = ui.button(nav, text="上一篇", kind="ghost",
                                  icon="arrow-left", state="disabled",
                                  command=lambda: self._load_item(self.cur - 1))
        self.btn_prev.pack(side="left", padx=(0, ui.S_SM))
        self.btn_next = ui.button(nav, text="下一篇", kind="ghost",
                                  icon="arrow-right", state="disabled",
                                  command=lambda: self._load_item(self.cur + 1))
        self.btn_next.pack(side="left")

        self.pos_lbl_bar = tk.Label(nav, text="", bg=ui.BG, fg=ui.PRIMARY,
                                    font=ui.FONT_UI_B)
        self.pos_lbl_bar.pack(side="left", padx=(ui.S_MD, 0))

        self.info_lbl = tk.Label(nav, text="", bg=ui.BG, fg=ui.TEXT_MUTED,
                                 font=ui.FONT_SMALL)
        self.info_lbl.pack(side="right", padx=(0, ui.S_LG))

        # 卡片容器：作业区 / 结果区互斥显示
        outer, inner = ui.card(self)
        outer.pack(fill="both", expand=True, padx=ui.PAGE_PAD,
                   pady=(0, ui.S_SM))
        self.paper_frame = inner

        # 作业区（子页容器）先寄到卡片内，初始隐藏
        self._area.pack(in_=inner, fill="both", expand=True)
        self._area.pack_forget()

        # 结果区（可滚动）
        res_wrap = ui.scrollable(inner, bg=ui.CARD)
        res_wrap[0].pack(fill="both", expand=True)
        self.result_frame = tk.Frame(res_wrap[1], bg=ui.CARD)
        self.result_frame.pack(fill="both", expand=True)
        self.result_host = res_wrap[0]
        self.result_host.pack_forget()

        # 未开考时的引导空状态
        self.idle_layer = tk.Frame(inner, bg=ui.CARD)
        ui.empty_state(
            self.idle_layer, icon="clock", title="还没开始，先选个套卷",
            desc="按考试节奏整卷计时，交卷后统一批改，并记录最好成绩",
            bg=ui.CARD, pady=40).pack(fill="both", expand=True)
        self.idle_layer.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    # 抽题
    # ------------------------------------------------------------------ #
    def _pick(self, kind, n, exclude_titles=None):
        exclude_titles = set(exclude_titles or [])
        if kind == "reading":
            pool = [p for p in self._reading.passages
                    if p.get("title", "") not in exclude_titles]
        else:
            pool = [p for p in self._cloze.passages
                    if p.get("title", "") not in exclude_titles]
        # 导入题排在后面
        pool.sort(key=lambda p: 1 if p.get("_imported") else 0)
        return pool[:n]

    def _build_paper(self, plan):
        self._reading.reload_data()
        self._cloze.reload_data()
        if plan == "mini":
            reads = self._pick("reading", 1)
            clozes = self._pick("cloze", 1)
        else:
            reads = self._pick("reading", 2)
            clozes = self._pick("cloze", 1)
        return [("reading", p) for p in reads] + [("cloze", p) for p in clozes]

    # ------------------------------------------------------------------ #
    # 开始考试
    # ------------------------------------------------------------------ #
    def _start(self):
        if self.running:
            return
        try:
            plan = self.plan_keys[self.cb_plan.current()]
        except Exception:
            plan = self.plan_keys[0]
        self.plan = plan
        self.paper = self._build_paper(plan)
        if not self.paper:
            self.app.set_status("题库是空的，先去其他页面添加一些题目吧～")
            return

        self.running = True
        self.finished = False
        self.start_ts = time.time()
        self.used_sec = 0
        self.deadline = self.start_ts + PLANS[plan]["minutes"] * 60

        self.btn_start.config(state="disabled")
        self.btn_submit.config(state="normal")
        self.cb_plan.config(state="disabled")

        for w in self.result_frame.winfo_children():
            w.destroy()
        self.result_host.pack_forget()

        self.cur = 0
        self.idle_layer.pack_forget()
        self._area.pack(fill="both", expand=True)
        self.update_idletasks()
        self._show_item(0)

        n_q = sum(len(p.get("questions", p.get("blanks", []))) for _, p in self.paper)
        self.info_lbl.config(
            text=("已开始：共 %d 篇 / %d 题，限时 %d 分钟。作答会一层层叠在纸上，"
                  "交卷后统一批改。") % (len(self.paper), n_q, PLANS[plan]["minutes"]),
            fg=ui.TEXT,
        )
        self._tick()
        self.app.set_status("模拟考试开始，加油")

    # ------------------------------------------------------------------ #
    # 篇目标签 / 题库池同步
    # ------------------------------------------------------------------ #
    def _item_label(self, i):
        kind, p = self.paper[i]
        tag = "阅读" if kind == "reading" else "选词填空"
        base = p.get("title", "").replace("【导入】", "").replace("data:", "")
        return f"第 {i + 1}/{len(self.paper)} 篇 · {tag} · {base}"

    def _sync_pools(self):
        # 子页题库可能被刷新，重新装配再组卷
        self._reading.reload_data()
        self._cloze.reload_data()

    # ------------------------------------------------------------------ #
    # 切换 / 显示题目
    # ------------------------------------------------------------------ #
    def _load_item(self, i):
        self._snapshot()
        self._show_item(i)

    def _show_item(self, i):
        if not self.paper or i < 0 or i >= len(self.paper):
            return
        if not (0 <= self.cur < len(self.paper)):
            return

        self._snapshot()
        self.cur = i
        kind, p = self.paper[i]

        if kind == "reading":
            page, other = self._reading, self._cloze
        else:
            page, other = self._cloze, self._reading

        other.pack_forget()
        page.pack(fill="both", expand=True)

        # 切到指定篇（只有带 cb 的子页才支持外部指定）
        cb = getattr(page, "cb", None)
        if cb is not None:
            try:
                vals = list(cb["values"] or [])
            except Exception:
                vals = []
            base = p.get("title", "").replace("【导入】", "")
            idx = -1
            for j, t in enumerate(vals):
                if str(t).endswith(base) or str(t).endswith(p.get("title", "")):
                    idx = j
                    break
            if idx >= 0 and getattr(page, "pi", -1) != idx:
                cb.current(idx)
                page.pi = idx
                if hasattr(page, "_load_passage"):
                    page._load_passage()

        # 把本篇已存答案灌回子页控件
        self._restore_answers(page, kind, i)

        self.pos_lbl_bar.config(text=self._item_label(i))
        self.btn_prev.config(state="normal" if i > 0 else "disabled")
        self.btn_next.config(state="normal" if i + 1 < len(self.paper) else "disabled")

    def _restore_answers(self, page, kind, i):
        snap = self.state.get(str(i), {}) or {}
        if kind == "reading":
            qvars = getattr(page, "q_vars", []) or []
            for qi, v in enumerate(qvars, 1):
                if hasattr(v, "set"):
                    v.set(snap.get(str(qi), snap.get(qi, "")))
        else:
            sels = getattr(page, "selections", {}) or {}
            for k in sorted(sels.keys()):
                node = sels[k]
                v = node.get("var") if isinstance(node, dict) else None
                if v is not None and hasattr(v, "set"):
                    v.set(snap.get(str(k + 1), snap.get(k + 1, "")))

    # ------------------------------------------------------------------ #
    # 答案存取
    # ------------------------------------------------------------------ #
    def _paper_index(self, kind, p):
        try:
            return self.paper.index((kind, p))
        except ValueError:
            return -1

    def _answers_for(self, kind, p):
        page = self._reading if kind == "reading" else self._cloze
        qvars = getattr(page, "q_vars", None)
        sels = getattr(page, "selections", None)
        passages = getattr(page, "passages", None)
        pi = getattr(page, "pi", -1)

        if kind == "reading" and qvars and passages \
                and 0 <= pi < len(passages) and passages[pi] is p:
            return {qi: (v.get() if hasattr(v, "get") else "")
                    for qi, v in enumerate(qvars, 1)}
        if kind == "cloze" and sels and passages \
                and 0 <= pi < len(passages) and passages[pi] is p:
            out = {}
            for k in sorted(sels.keys()):
                node = sels[k]
                v = node.get("var") if isinstance(node, dict) else None
                out[k + 1] = v.get() if v is not None and hasattr(v, "get") else ""
            return out

        # 回退：子页当前篇不是该篇时，用交卷前存好的快照
        idx = self._paper_index(kind, p)
        if idx >= 0:
            return dict(self.state.get(str(idx), {}))
        return {}

    def _snapshot(self):
        if not self.paper or not (0 <= self.cur < len(self.paper)):
            return {}
        if not (self.running or self.finished):
            return {}
        kind, p = self.paper[self.cur]
        page = self._reading if kind == "reading" else self._cloze

        if kind == "reading":
            qvars = getattr(page, "q_vars", []) or []
            snap = {qi: (v.get() if hasattr(v, "get") else "")
                    for qi, v in enumerate(qvars, 1)}
        else:
            sels = getattr(page, "selections", {}) or {}
            snap = {}
            for k in sorted(sels.keys()):
                node = sels[k]
                v = node.get("var") if isinstance(node, dict) else None
                snap[k + 1] = v.get() if v is not None and hasattr(v, "get") else ""

        self.state[str(self.cur)] = snap
        return snap

    # ------------------------------------------------------------------ #
    # 倒计时
    # ------------------------------------------------------------------ #
    def _tick(self):
        if not self.running:
            return
        left = self.deadline - time.time()
        self.clock_lbl.config(
            text=self._fmt_clock(left),
            fg=ui.WARN if left <= 60 else ui.TEXT,
        )
        if left <= 0:
            self.used_sec = int(time.time() - self.start_ts)
            self.app.set_status("时间到，自动交卷")
            self._submit(auto=True)
            return
        self._tick_job = self.after(500, self._tick)

    # ------------------------------------------------------------------ #
    # 交卷判分
    # ------------------------------------------------------------------ #
    def _submit(self, auto=False):
        if not self.running:
            return
        self.running = False
        if self._tick_job:
            self.after_cancel(self._tick_job)
            self._tick_job = None

        self.used_sec = int(time.time() - self.start_ts)
        correct = total = 0
        detail = []
        sheet = []

        for i, (kind, p) in enumerate(self.paper):
            got_map = self._answers_for(kind, p)
            subs = []

            if kind == "reading":
                qs = p.get("questions", [])
                for qi, q in enumerate(qs, 1):
                    got = got_map.get(qi, "")
                    std = str(q.get("answer", "")).upper()
                    ok = (got or "").upper() == std
                    total += 1
                    correct += 1 if ok else 0
                    detail.append("%d-%d:%s" % (i + 1, qi, "O" if ok else "X"))
                    subs.append({"got": got, "std": std, "ok": ok, "q": q})
                    self.store.log_question(
                        "reading", "mock:" + str(self.start_ts),
                        "%d-%d" % (i + 1, qi), got, ok, std, q.get("explain", ""),
                    )
            else:
                bl = p.get("blanks", [])
                for qi, b in enumerate(bl, 1):
                    got = got_map.get(qi, "")
                    std = b[0] if isinstance(b, (list, tuple)) else b
                    ok = str(got).strip().lower() == str(std).strip().lower()
                    total += 1
                    correct += 1 if ok else 0
                    detail.append("%d-%d:%s" % (i + 1, qi, "O" if ok else "X"))
                    expl = b[2] if isinstance(b, (list, tuple)) and len(b) > 2 else ""
                    subs.append({
                        "got": got, "std": std, "ok": ok,
                        "q": f"第 {qi} 空", "explain": expl,
                        "options": b[1] if isinstance(b, (list, tuple)) and len(b) > 1 else [],
                    })
                    self.store.log_question(
                        "cloze", "mock:" + str(self.start_ts),
                        "%d-%d" % (i + 1, qi), got, ok, std, expl,
                    )

            sheet.append({"kind": kind, "title": p.get("title", ""), "items": subs})

        title = "%s　%s" % (PLANS[self.plan]["label"], time.strftime("%m-%d %H:%M"))
        self.store.add_exam("mock", title, correct, total, ";".join(detail))

        self.finished = True
        self.btn_start.config(state="normal")
        self.btn_submit.config(state="disabled")
        self.cb_plan.config(state="readonly")

        self.clock_lbl.config(
            text=self._fmt_clock(0 if auto else self.deadline - time.time()),
            fg=ui.TEXT,
        )

        pct = round(correct * 100 / total) if total else 0
        if pct >= 85:
            tip = "答得漂亮！"
        elif pct >= 70:
            tip = "还不错，再冲一把就稳了。"
        else:
            tip = "短板还比较明显，针对性补一补吧。"
        self.info_lbl.config(
            text=("%s：%d/%d 题正确（%d%%），用时 %s。%s"
                  % ("时间到自动交卷" if auto else "已交卷",
                     correct, total, pct, self._fmt_clock(self.used_sec), tip)),
            fg=ui.OK if pct >= 70 else ui.WARN,
        )

        self.idle_layer.pack_forget()
        self._area.pack_forget()
        self.result_host.pack(fill="both", expand=True)
        self._show_result(correct, total, pct)
        self._refresh_best()
        self.app.set_status("模拟考试结束：%d/%d（%d%%）" % (correct, total, pct))

    # ------------------------------------------------------------------ #
    # 结果展示
    # ------------------------------------------------------------------ #
    def _show_result(self, correct, total, pct):
        for w in self.result_frame.winfo_children():
            w.destroy()

        head = tk.Frame(self.result_frame, bg=ui.CARD)
        head.pack(fill="x")

        tk.Label(head, text="%d / %d" % (correct, total), bg=ui.CARD,
                 fg=ui.OK if pct >= 70 else ui.WARN,
                 font=("Consolas", 26, "bold")).pack(side="left")
        tk.Label(head, text="　得分率 %d%%　用时 %s" % (pct, self._fmt_clock(self.used_sec)),
                 bg=ui.CARD, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI).pack(side="left", padx=(10, 0), pady=(6, 0))

        body = tk.Frame(self.result_frame, bg=ui.CARD)
        body.pack(fill="both", expand=True, pady=(6, 0))

        for i, part in enumerate(self.sheet):
            n = len(part["items"])
            ok_n = sum(1 for x in part["items"] if x["ok"])
            tag = "阅读" if part["kind"] == "reading" else "选词填空"
            base = part["title"].replace("【导入】", "").replace("data:", "")

            head2 = tk.Frame(body, bg=ui.CARD)
            head2.pack(fill="x", pady=(6, 1))
            tk.Label(head2, text="%d. [%s] %s　%d/%d" % (i + 1, tag, base, ok_n, n),
                     bg=ui.CARD, fg=ui.OK if ok_n == n else ui.TEXT,
                     font=ui.FONT_UI_B, anchor="w").pack(side="left")

            for qi, x in enumerate(part["items"], 1):
                mark = "✓" if x["ok"] else "✗"
                got = (x["got"] or "").strip() or "未作答"
                line = "　　%d. %s 你答 %s　标准答案 %s" % (qi, mark, got, x["std"])
                tk.Label(body, text=line, bg=ui.CARD,
                         fg=ui.OK if x["ok"] else ui.WARN,
                         font=ui.FONT_UI, anchor="w", justify="left").pack(fill="x")

                if not x["ok"]:
                    q = x.get("q", "")
                    qtext = ""
                    if isinstance(q, dict):
                        qtext = (q.get("q", "") or "").strip()
                    elif isinstance(q, str):
                        qtext = q.strip()
                    expl = x.get("explain", "") or ""
                    extra = []
                    if qtext:
                        extra.append(qtext)
                    if expl:
                        extra.append("解析：" + expl)
                    if extra:
                        tk.Label(body, text="　　" + " ".join(extra), bg=ui.CARD,
                                 fg=ui.TEXT_MUTED, font=("Microsoft YaHei UI", 8),
                                 anchor="w", justify="left", wraplength=980).pack(fill="x")

    # ------------------------------------------------------------------ #
    # 最佳成绩
    # ------------------------------------------------------------------ #
    def _refresh_best(self):
        best = self.store.exam_best("mock")
        if not best or not best.get("total"):
            self.best_lbl.config(text="还没有模考记录")
            return
        pct = round(best["score"] * 100 / best["total"])
        when = time.strftime("%m-%d", time.localtime(int(best["created_at"])))
        self.best_lbl.config(
            text="最好成绩 %d%%（%d/%d，%s）"
                 % (pct, int(best["score"]), int(best["total"]), when)
        )

    # ------------------------------------------------------------------ #
    # 切到本页时刷新
    # ------------------------------------------------------------------ #
    def on_show(self):
        if not self.running:
            self._refresh_best()
