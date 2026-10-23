# -*- coding: utf-8 -*-
"""数据包（cet_pack.json）导入

程序启动时会找一个数据包并整包导入本地库：
  1. exe 同目录的 cet_pack.json / pack_data.zip
  2. 打包进 exe 内部的 cet_pack.zip（PyInstaller 单文件模式下在 sys._MEIPASS）
  3. 源码目录的 _build/pack_data.zip（开发时）

包结构：
{
  "vocab":    {"CET4": [[词,音标,词性,释义,例句,例句中文], ...], "CET6": [...], "GZ": [...]},
  "phrases":  [[短语, 中文], ...],
  "reading":  [{"title":..., "passage":..., "questions":[...]}, ...],
  "cloze":    [{"title":..., "text":..., "blanks":[[答案,[选项],解析], ...]}, ...],
  "translate":[[中文, 译文, 难度], ...],
  "sentences":[[句子, 译文, 难度, 主题], ...]
}

每条记录带稳定 id，重复导入不会重复堆积，词库内容升级会自动覆盖。
"""

import json
import os
import shutil
import sys
import zipfile

PACK_VERSION = "2024-11-v1"
PACK_NAMES = ("cet_pack.json", "pack_data.zip")


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _find_pack():
    """返回 (来源描述, 读取函数) 或 None。"""
    base = _app_dir()

    # 1) 外置包
    for name in PACK_NAMES:
        for folder in (base, os.path.join(base, "data")):
            p = os.path.join(folder, name)
            if os.path.isfile(p) and os.path.getsize(p) > 1000:
                return (p, _loader_for(p))

    # 2) 打进 exe 内部的包
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        for name in ("cet_pack.zip", "cet_pack.json"):
            p = os.path.join(meipass, name)
            if os.path.isfile(p):
                return ("内置:" + name, _loader_for(p))

    # 3) 开发目录
    for name in ("pack_data.zip", "cet_pack.json"):
        p = os.path.join(base, "_build", name)
        if os.path.isfile(p) and os.path.getsize(p) > 1000:
            return (p, _loader_for(p))
    return None


def _loader_for(path):
    def load():
        if path.lower().endswith(".zip"):
            with zipfile.ZipFile(path) as z:
                names = [n for n in z.namelist() if n.lower().endswith(".json")]
                if not names:
                    return {}
                return json.loads(z.read(names[0]).decode("utf-8"))
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return load


def _phrase_title(level):
    return {"GZ": "高中短语", "CET4": "四级短语", "CET6": "六级短语"}.get(level, "短语")


def import_pack(store, force=False):
    """把数据包导入本地库。已导入同一版本则跳过。

    返回 dict：{"ok": bool, "source": 来源, "msg": 说明, "counts": {...}}
    """
    found = _find_pack()
    if not found:
        return {"ok": False, "source": "", "msg": "没有找到数据包", "counts": {}}

    source, reader = found
    try:
        payload = reader()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "source": str(source), "msg": f"数据包读不出来：{e}", "counts": {}}
    if not isinstance(payload, dict):
        return {"ok": False, "source": str(source), "msg": "数据包格式不对", "counts": {}}

    ver = str(payload.get("version") or PACK_VERSION)
    if not force and store.get_setting("cet_pack_version") == ver:
        return {"ok": True, "source": str(source), "msg": "数据包已是最新", "counts": {}}

    counts = {}

    # 先清掉上一版包导入的题，避免改名后新旧两套都留着
    try:
        store.drop_pack_content()
    except Exception:  # noqa: BLE001
        pass

    # ---------- 词汇 ----------
    vocab = payload.get("vocab") or {}
    for level, rows in vocab.items():
        if not rows:
            continue
        try:
            store.bulk_vocab(level, rows)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "source": str(source), "msg": f"词汇导入失败：{e}", "counts": {}}
        counts[f"vocab_{level}"] = len(rows)

    # ---------- 短语 ----------
    phrases = payload.get("phrases") or []
    if phrases:
        items = [{"en": p[0], "cn": p[1]} for p in phrases if len(p) >= 2 and p[0]]
        by_level = {"CET4": [], "CET6": []}
        # 短语按原顺序切成两半：前一半归四级，后一半归六级（词书本身按难度排过）
        half = len(items) // 2
        by_level["CET4"] = items[:half]
        by_level["CET6"] = items[half:]
        for level, lst in by_level.items():
            if not lst:
                continue
            title = f"data:{_phrase_title(level)}"
            store.add_user_content("phrase", title, lst, level, source=str(source))
            store.mark_pack_title("phrase", title, level)
            counts[f"phrase_{level}"] = len(lst)

    # ---------- 阅读 / 选词填空：一篇一条 ----------
    for kind in ("reading", "cloze"):
        for i, rec in enumerate(payload.get(kind) or []):
            title = "data:" + (rec.get("title") or f"{kind}-{i + 1}")
            store.add_user_content(kind, title, rec, rec.get("level", ""), source=str(source))
            store.mark_pack_title(kind, title, rec.get("level", ""))

    # 翻译 / 听写句子统一按批次存两条，避免几千条标题
    trans = payload.get("translate") or []
    if trans:
        half = len(trans) // 2
        for level, lst in (("CET4", trans[:half]), ("CET6", trans[half:])):
            if not lst:
                continue
            title = "data:" + ("四级翻译" if level == "CET4" else "六级翻译")
            store.add_user_content(
                "translate", title, [{"trans": list(r)} for r in lst], level, source=str(source))
            store.mark_pack_title("translate", title, level)

    sents = payload.get("sentences") or []
    if sents:
        title = "data:真题句库"
        store.add_user_content("sentences", title,
                               [{"sent": list(r)} for r in sents], "", source=str(source))
        store.mark_pack_title("sentences", title, "")

    # 导入页「导入数据包」是按 kind 统计的，这里补一下总数，让提示看得出导入了什么
    extra = {k: len(v) for k, v in (("reading", payload.get("reading") or []),
                                     ("cloze", payload.get("cloze") or []))}
    for title_kind, cnt in (("translate", len(payload.get("translate") or [])),
                            ("sentences", len(sents))):
        if cnt:
            extra[title_kind] = cnt
    counts.update(extra)

    store.set_setting("cet_pack_version", ver)
    store.set_setting("cet_pack_source", str(source))
    total = sum(v for k, v in counts.items() if k.startswith("vocab_"))
    phrase_n = counts.get("phrase_CET4", 0) + counts.get("phrase_CET6", 0)
    parts = []
    if total:
        parts.append(f"词汇 {total} 条")
    if phrase_n:
        parts.append(f"短语 {phrase_n} 条")
    for kind, label in (("reading", "阅读"), ("cloze", "选词填空"),
                        ("translate", "翻译"), ("sentences", "听写句子")):
        if counts.get(kind):
            parts.append(f"{label} {counts[kind]} 条")
    msg = "数据包已导入：" + ("，".join(parts) if parts else "没有可识别的题目")
    return {
        "ok": True,
        "source": str(source),
        "msg": msg,
        "counts": counts,
    }


def install_pack(src_path, dest_dir=None):
    """把用户给的包拷到程序目录（供“题库导入”页使用）。"""
    dest_dir = dest_dir or _app_dir()
    name = "cet_pack.json" if src_path.lower().endswith(".json") else "pack_data.zip"
    dst = os.path.join(dest_dir, name)
    shutil.copyfile(src_path, dst)
    return dst
