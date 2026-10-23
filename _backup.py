# -*- coding: utf-8 -*-
"""源码快照备份 —— 每次改完代码跑一次，生成带时间戳的 zip。

用法：
    E:\\Python315\\python.exe _backup.py            # 生成快照
    E:\\Python315\\python.exe _backup.py --list     # 列出已有快照

快照位置：
    C:\\Temp\\cet_src_snapshots\\cet_src_<时间戳>.zip
    E:\\CETTrainer_src_backup\\cet_src_<时间戳>.zip    （与源码盘分开，防单盘故障）

排除：__pycache__ / _rt / build / dist / cet_tts_* / cet_data / shots / *.pyc
不排除：data_*.py（题库源码）、cet_pack.json 不打进去（可由 build_pack.py 重建）
"""
import os
import shutil
import sys
import zipfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
NAME = "cet_src_%s" % STAMP

DEST_DIRS = [
    r"C:\Temp\cet_src_snapshots",
    r"E:\CETTrainer_src_backup",
]

# 目录名 / 文件名片段，命中即跳过
SKIP_DIRS = {"__pycache__", "_rt", "build", "dist", "cet_data", "shots",
             ".git", ".idea", ".vscode"}
SKIP_PREFIX = ("cet_tts_", "shot_", "z_")
SKIP_FILES = {"cet_pack.json"}
SKIP_EXT = {".pyc", ".pyo", ".log", ".tmp"}

# 这些必须存在，缺一个就报错（防止备份了一个残废版本）
MUST_HAVE = [
    "app.py", "ui_common.py", "tts.py", "tts_edge.py", "store.py",
    "cetpack.py", "importer.py", "build_pack.py", "build.bat",
    "pages/__init__.py", "pages/page_vocab.py", "pages/page_stats.py",
    "cet.ico", "icon_app.png",
]


def _skip(name, is_dir):
    if is_dir:
        return name in SKIP_DIRS
    if name in SKIP_FILES or os.path.splitext(name)[1].lower() in SKIP_EXT:
        return True
    return any(name.startswith(p) for p in SKIP_PREFIX)


def collect():
    """返回 [(相对路径, 绝对路径)]。"""
    out = []
    for root, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs if not _skip(d, True)]
        for f in files:
            if _skip(f, False):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, HERE)
            out.append((rel, full))
    return out


def check_must_have(files):
    have = {r.replace("\\", "/") for r, _ in files}
    missing = [m for m in MUST_HAVE if m not in have]
    return missing


def make_zip(files, target):
    os.makedirs(os.path.dirname(target), exist_ok=True)
    tmp = target + ".part"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel, full in sorted(files):
            z.write(full, os.path.join(NAME, rel))
    # 自检：能读回来且无坏项
    with zipfile.ZipFile(tmp) as z:
        bad = z.testzip()
        if bad:
            os.remove(tmp)
            raise RuntimeError("快照损坏，坏项：%s" % bad)
        n = len(z.namelist())
    os.replace(tmp, target)
    return n


def list_snapshots():
    seen = []
    for d in DEST_DIRS:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.startswith("cet_src_") and f.endswith(".zip"):
                p = os.path.join(d, f)
                seen.append((os.path.getmtime(p), p, os.path.getsize(p)))
    for mt, p, sz in sorted(seen, reverse=True):
        print("%-60s %8.1f KB  %s" % (
            p, sz / 1024.0,
            datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M:%S")))
    if not seen:
        print("（还没有快照）")


def main():
    if "--list" in sys.argv:
        list_snapshots()
        return 0

    files = collect()
    missing = check_must_have(files)
    if missing:
        print("[错误] 关键文件缺失，拒绝生成快照：")
        for m in missing:
            print("   -", m)
        return 1

    pys = [f for f, _ in files if f.endswith(".py")]
    pages = [f for f in pys if f.replace("\\", "/").startswith("pages/page_")]
    print("待备份：%d 个文件（其中 .py %d 个，页面 %d 个）"
          % (len(files), len(pys), len(pages)))

    ok = 0
    for d in DEST_DIRS:
        target = os.path.join(d, NAME + ".zip")
        try:
            n = make_zip(files, target)
            print("  ->", target, "(%.1f KB, %d 项)" % (
                os.path.getsize(target) / 1024.0, n))
            ok += 1
        except Exception as e:                     # noqa: BLE001
            print("  !! 写入失败", target, ":", e)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
