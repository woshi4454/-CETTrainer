# -*- coding: utf-8 -*-
"""题库导入页

把从网络/教辅/自己整理的内容粘进来，解析后存进本地库，
立刻出现在对应的练习页里（阅读/选词填空/翻译/词汇/听写）。

布局：
    ┌ 题型 分段 ─────────────── 等级 分段 ┐
    │ 从文件导入  载入格式示例  导入数据包  备份/恢复 │
    │ ┌ 粘贴内容（左，可滚 Text）──────┐ ┌ 已导入题库（右）┐ │
    │ │ 格式提示                       │ │ Treeview        │ │
    │ │ 解析并保存  清空                │ │ 删除选中        │ │
    │ └────────────────────────────────┘ └─────────────────┘ │
"""

import os
import shutil
import time

import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from tkinter import ttk

import ui_common as ui

from pages import Page

import importer

try:
    import cetpack
except Exception:  # noqa: BLE001
    cetpack = None

KINDS = ("reading", "cloze", "translate", "vocab", "sentences")
# 表格列里用短标签（长标签 4 个字塞不进窄列）
SHORT = {"reading": "阅读", "cloze": "选词", "translate": "翻译",
         "vocab": "词汇", "sentences": "听写"}
LEVELS = (("高中", "GZ"), ("四级", "CET4"), ("六级", "CET6"))

TIPS = {
    "reading": "# 标题 / ## 文章 / ## 题目（1. 题干、A-D 选项、答案：X、解析：…）",
    "cloze": "# 标题 / ## 词库 / ## 文章（空位写 ___1___）/ ## 答案（1. D 解析）",
    "translate": "一行一题　中文原句 | 参考译文 | 难度(可省)",
    "vocab": "一行一词　单词 | 音标 | 词性 | 释义 | 例句(可省) | 例句翻译(可省)",
    "sentences": "一行一句　英文句子 | 参考译文 | 难度(可省) | 主题(可省)",
}


class ImportPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.kind_var = tk.StringVar(value="reading")
        self.level_var = tk.StringVar(value="CET4")
        self._build()
        self._refresh_list()

    # ---------------------------------------------------------------- 构建界面
    def _build(self):
        top = tk.Frame(self, bg=ui.BG)
        top.pack(side="top", fill="x", padx=ui.PAGE_PAD, pady=(ui.S_MD, ui.S_SM))

        tk.Label(top, text="题型", bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI).pack(side="left", padx=(0, ui.S_SM))
        self.kind_seg = ui.segment(
            top, [(importer.KIND_LABELS[k], k) for k in KINDS],
            value="reading", command=self._on_kind_pick)
        self.kind_seg.pack(side="left")

        self.level_seg = ui.segment(top, LEVELS, value="CET4",
                                    command=self._on_level)
        self.level_seg.pack(side="right")
        tk.Label(top, text="等级", bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=ui.FONT_UI).pack(side="right", padx=(0, ui.S_SM))

        bar = tk.Frame(self, bg=ui.BG)
        bar.pack(side="top", fill="x", padx=ui.PAGE_PAD, pady=(0, ui.S_SM))

        ui.button(bar, text="从文件导入", kind="ghost", icon="doc",
                  command=self._from_file).pack(side="left")
        ui.button(bar, text="载入格式示例", kind="ghost", icon="sheet",
                  command=self._load_template).pack(side="left",
                                                   padx=(ui.S_SM, 0))
        ui.button(bar, text="导入数据包", kind="ghost", icon="import",
                  command=self._import_pack).pack(side="left",
                                                 padx=(ui.S_SM, 0))
        ui.button(bar, text="备份 / 恢复", kind="ghost", icon="bookmark",
                  command=self._backup).pack(side="left", padx=(ui.S_SM, 0))

        self.status_lbl = tk.Label(bar, text="", bg=ui.BG, fg=ui.TEXT_MUTED,
                                   font=ui.FONT_SMALL)
        self.status_lbl.pack(side="right")

        body = tk.Frame(self, bg=ui.BG)
        body.pack(side="top", fill="both", expand=True, padx=ui.PAGE_PAD,
                  pady=(0, ui.S_SM))

        # ---------------- 左：粘贴区 ----------------
        # 先 pack 右侧固定宽，再 pack 左侧 expand，否则左侧会吃掉全部宽度
        self.left_wrap = tk.Frame(body, bg=ui.BG)
        louter, linner = ui.card(self.left_wrap)
        louter.pack(fill="both", expand=True)

        head = tk.Frame(linner, bg=ui.CARD)
        head.pack(side="top", fill="x", padx=ui.CARD_PAD,
                  pady=(ui.S_MD, ui.S_XS))
        ui.Icon(head, "edit", size=15, color=ui.PRIMARY,
                bg=ui.CARD).pack(side="left")
        tk.Label(head, text="粘贴内容", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_UI_B).pack(side="left", padx=(ui.S_XS, 0))

        self.hint_lbl = ui.wrap_label(linner, text="", fg=ui.TEXT_MUTED,
                                     bg=ui.CARD_SOFT, font=ui.FONT_SMALL,
                                     justify="left", pad=10)
        self.hint_lbl.pack(side="top", fill="x", padx=ui.CARD_PAD,
                           pady=(0, ui.S_SM))

        bbar = tk.Frame(linner, bg=ui.CARD)
        bbar.pack(side="bottom", fill="x", padx=ui.CARD_PAD,
                  pady=(ui.S_SM, ui.CARD_PAD))

        ui.button(bbar, text="解析并保存", kind="primary", icon="check",
                  command=self._do_import).pack(side="left", padx=(0, ui.S_SM))
        ui.button(bbar, text="清空", kind="text", icon="trash",
                  command=lambda: self.text.delete("1.0", "end")).pack(
            side="left")

        wrap = tk.Frame(linner, bg=ui.CARD)
        wrap.pack(side="top", fill="both", expand=True, padx=ui.CARD_PAD,
                  pady=(0, 0))

        self.text = tk.Text(wrap, wrap="word", font=("Consolas", 11),
                            relief="flat", bg=ui.CARD_SOFT, fg=ui.TEXT,
                            undo=True, padx=12, pady=10, insertbackground=ui.PRIMARY,
                            highlightthickness=1,
                            highlightbackground=ui.BORDER,
                            highlightcolor=ui.PRIMARY)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(ui.S_XS, 0))
        self.text.pack(side="left", fill="both", expand=True)

        # ---------------- 右：已导入列表 ----------------
        self.right_wrap = tk.Frame(body, bg=ui.BG, width=520)
        self.right_wrap.pack(side="right", fill="y", padx=(ui.GAP, 0))
        self.right_wrap.pack_propagate(False)
        router, rinner = ui.card(self.right_wrap)
        router.pack(fill="both", expand=True)

        rhead = tk.Frame(rinner, bg=ui.CARD)
        rhead.pack(side="top", fill="x", padx=ui.CARD_PAD,
                   pady=(ui.S_MD, ui.S_SM))
        ui.Icon(rhead, "book", size=15, color=ui.TEXT_MUTED,
                bg=ui.CARD).pack(side="left")
        tk.Label(rhead, text="已导入题库", bg=ui.CARD, fg=ui.TEXT,
                 font=ui.FONT_UI_B).pack(side="left", padx=(ui.S_XS, 0))
        self.count_chip = tk.Frame(rhead, bg=ui.CARD)
        self.count_chip.pack(side="right")

        rbar = tk.Frame(rinner, bg=ui.CARD)
        rbar.pack(side="bottom", fill="x", padx=ui.CARD_PAD,
                  pady=(ui.S_SM, ui.CARD_PAD))
        ui.button(rbar, text="删除选中", kind="ghost", icon="trash",
                  command=self._delete_sel).pack(side="left")

        treewrap = tk.Frame(rinner, bg=ui.CARD)
        treewrap.pack(side="top", fill="both", expand=True,
                      padx=(ui.CARD_PAD, 0))

        cols = ("title", "kind", "n", "time")
        self.tree = ttk.Treeview(treewrap, columns=cols, show="headings",
                                 height=14)
        for c, t, w, st, anc in (
            ("title", "标题", 152, True, "w"),
            ("kind", "题型", 62, False, "center"),
            ("n", "题数", 56, False, "center"),
            ("time", "导入", 70, False, "center"),
        ):
            self.tree.heading(c, text=t, anchor=anc)
            self.tree.column(c, width=w, minwidth=w, anchor=anc, stretch=st)

        tsb = ttk.Scrollbar(treewrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tsb.set)
        tsb.pack(side="right", fill="y", padx=(ui.S_XS, ui.S_XS))
        self.tree.pack(side="left", fill="both", expand=True)

        self.empty_layer = tk.Frame(rinner, bg=ui.CARD)
        ui.empty_state(self.empty_layer, icon="book", title="还没有导入过题目",
                       desc="左边粘好内容点「解析并保存」",
                       bg=ui.CARD, pady=24).pack(fill="both", expand=True)

        self.left_wrap.pack(side="left", fill="both", expand=True)

        self._on_kind()

    # ---------------------------------------------------------------- 交互
    def _set_status(self, text, fg=None):
        self.status_lbl.config(text=text, fg=fg or ui.TEXT_MUTED)

    def _cur_kind(self):
        return self.kind_var.get() or "reading"

    def _on_kind_pick(self, val):
        self.kind_var.set(val)
        self._on_kind()

    def _on_level(self, val):
        self.level_var.set(val)

    def _on_kind(self, _e=None):
        self.hint_lbl.config(text=TIPS.get(self._cur_kind(), ""))

    # ---------------------------------------------------------------- 模板/文件
    def _load_template(self):
        k = self._cur_kind()
        self.text.delete("1.0", "end")
        self.text.insert("1.0", importer.TEMPLATES.get(k, ""))
        self._set_status("已载入示例，改完点「解析并保存」")

    def _from_file(self):
        path = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("文本文件", "*.txt *.md"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as e:
            self._set_status("读取失败：" + str(e), ui.WARN)
            return
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self._set_status("已载入 " + os.path.basename(path))

    # ---------------------------------------------------------------- 备份/恢复
    def _backup(self):
        import store as store_mod

        db = getattr(store_mod, "DB_PATH", "")
        win = tk.Toplevel(self)
        win.title("备份 / 恢复学习进度")
        win.configure(bg=ui.BG)
        win.transient(self.winfo_toplevel())
        win.geometry("560x250")
        win.resizable(False, False)

        tk.Label(win, text="学习进度存在下面这个文件里，复制走就等于备份。",
                 bg=ui.BG, fg=ui.TEXT, font=ui.FONT_UI).pack(
            anchor="w", padx=ui.S_LG, pady=(ui.S_LG, ui.S_XS))
        tk.Label(win, text=db, bg=ui.BG, fg=ui.TEXT_MUTED,
                 font=("Consolas", 9), wraplength=520, justify="left").pack(
            anchor="w", padx=ui.S_LG)
        tk.Label(win,
                 text="· 换电脑：把备份文件放到新机器的 cet_data\\progress.db 即可\n"
                      "· 恢复前请先关掉本程序，否则会被占用",
                 bg=ui.BG, fg=ui.TEXT_MUTED, font=ui.FONT_SMALL,
                 justify="left").pack(anchor="w", padx=ui.S_LG,
                                      pady=(ui.S_SM, 0))

        bar = tk.Frame(win, bg=ui.BG)
        bar.pack(side="bottom", fill="x", padx=ui.S_LG, pady=ui.S_LG)

        def do_backup():
            dst = filedialog.asksaveasfilename(
                parent=win, title="备份到", defaultextension=".db",
                initialfile=time.strftime("progress_%Y%m%d_%H%M.db"),
                filetypes=[("数据库文件", "*.db"), ("所有文件", "*.*")])
            if not dst:
                return
            try:
                self.store.conn.commit()
                shutil.copy2(db, dst)
            except OSError as exc:
                messagebox.showerror("备份失败", str(exc), parent=win)
                return
            self.app.set_status("已备份到 " + dst)
            self._set_status("备份完成", ui.OK)

        def do_restore():
            src = filedialog.askopenfilename(
                parent=win, title="选择备份文件",
                filetypes=[("数据库文件", "*.db"), ("所有文件", "*.*")])
            if not src:
                return
            if not messagebox.askyesno(
                    "确认恢复",
                    "恢复会用备份文件覆盖当前进度，现在的记录会丢。\n确定继续吗？",
                    parent=win):
                return
            try:
                self.store.close()
                shutil.copy2(src, db)
            except OSError as exc:
                messagebox.showerror(
                    "恢复失败", str(exc) + "\n请先完全关闭程序再试。", parent=win)
                return
            messagebox.showinfo("恢复完成", "进度已恢复，请重启程序让它生效。",
                                parent=win)
            self.app.set_status("进度已恢复，重启后生效")

        ui.button(bar, text="备份到…", kind="primary", icon="bookmark",
                  command=do_backup).pack(side="left")
        ui.button(bar, text="从备份恢复…", kind="ghost", icon="undo",
                  command=do_restore).pack(side="left", padx=(ui.S_SM, 0))
        ui.button(bar, text="关闭", kind="text", command=win.destroy).pack(
            side="right")

    # ---------------------------------------------------------------- 导入数据包
    def _import_pack(self):
        if cetpack is None:
            self._set_status("数据包模块缺失，无法导入", ui.WARN)
            return
        path = filedialog.askopenfilename(
            title="选择题库数据包",
            filetypes=[("题库数据包", "*.json *.zip"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            dst = cetpack.install_pack(path)
        except Exception as e:  # noqa: BLE001
            self._set_status("拷贝失败：" + str(e), ui.WARN)
            return
        res = cetpack.import_pack(self.store, force=True)
        if not res.get("ok"):
            self._set_status("导入失败：" + res.get("msg", ""), ui.WARN)
            return
        self._set_status(res["msg"] + "（来源 " + os.path.basename(dst) + "）",
                        ui.OK)
        self.app.set_status(res["msg"])
        self._reload_pages()
        self._refresh_list()

    # ---------------------------------------------------------------- 解析并保存
    def _do_import(self):
        k = self._cur_kind()
        raw = self.text.get("1.0", "end").strip()
        if not raw:
            self._set_status("先粘贴点内容吧", ui.AMBER)
            return
        ok, result = importer.parse_all(k, raw, self.level_var.get())
        if not ok:
            self._set_status(str(result), ui.WARN)
            self.app.set_status("导入失败：" + str(result))
            return

        added = 0
        skipped = 0
        for item in result:
            try:
                if k == "reading":
                    self._save(k, item["title"], item,
                               len(item["questions"]))
                elif k == "cloze":
                    self._save(k, item["title"], item,
                               len(item["blanks"]))
                elif k == "vocab":
                    self._save(k, item[0], {"word": item}, 1)
                elif k == "sentences":
                    self._save(k, item[0][:60], {"sent": item}, 1)
                elif k == "translate":
                    self._save(k, item[0][:60], {"trans": item}, 1)
            except Exception:  # noqa: BLE001
                skipped += 1
                continue
            added += 1

        msg = "已导入 %d 条" % added
        if skipped:
            msg += "，跳过 %d 条" % skipped
        self._set_status(msg, ui.OK)
        self.app.set_status(msg)
        self._refresh_list()
        self._reload_pages()

    def _save(self, kind, title, data, n):
        self.store.add_user_content(kind, title, data, self.level_var.get(),
                                    source="手动导入")

    def _reload_pages(self):
        for key in ("read", "cloze", "trans", "vocab", "dict"):
            page = self.app.pages.get(key)
            if page is not None and hasattr(page, "reload_data"):
                page.reload_data()

    # ---------------------------------------------------------------- 列表管理
    def _refresh_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        counts = self.store.user_content_count() or {}
        total = 0
        for kind in KINDS:
            if kind not in counts:
                continue
            for rec in self.store.user_content(kind):
                total += 1
                t = time.strftime("%m-%d",
                                  time.localtime(rec.get("created_at")))
                title = str(rec.get("title", ""))
                for pre in ("data:", "【导入】"):
                    if title.startswith(pre):
                        title = title[len(pre):]
                self.tree.insert(
                    "", "end", iid=str(rec["id"]),
                    values=(title,
                            SHORT.get(kind, kind),
                            counts.get(kind, ""), t),
                    tags=("odd" if total % 2 else "even",))

        self.tree.tag_configure("odd", background=ui.CARD_SOFT)

        # 给阅读/选词那两类的每一行补上该题数
        for iid in self.tree.get_children():
            cid = int(iid)
            for rec in (self.store.user_content("reading")
                        + self.store.user_content("cloze")):
                if rec["id"] == cid:
                    d = rec.get("data") or {}
                    n = len(d.get("questions", d.get("blanks", [])))
                    vals = list(self.tree.item(iid, "values"))
                    vals[2] = n
                    self.tree.item(iid, values=vals)
                    break

        for w in self.count_chip.winfo_children():
            w.destroy()
        ui.chip(self.count_chip, "%d 条" % total).pack()

        if total:
            self.empty_layer.pack_forget()
        else:
            self.empty_layer.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.empty_layer.lift()

    def _delete_sel(self):
        sel = self.tree.selection()
        if not sel:
            self._set_status("先在上表选一行", ui.AMBER)
            return
        for iid in sel:
            self.store.delete_user_content(int(iid))
        self._set_status("已删除 %d 条" % len(sel))
        self._refresh_list()
        self._reload_pages()

    # ---------------------------------------------------------------- 切页刷新
    def on_show(self):
        self._refresh_list()
