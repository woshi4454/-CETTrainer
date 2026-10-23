# -*- coding: utf-8 -*-
"""CETTrainer 垃圾清理 —— 清掉运行和打包留下的临时文件。

为什么需要它：
  1. PyInstaller onefile 每次启动都会把自身解压到 _rt\\_MEIxxxxxx，退出后不自动删
     （每次约 29 MB）。本机因为用户名带单引号必须用 --runtime-tmpdir "_rt" 绕开
     TEMP 路径问题，所以这个残留是必然代价。
  2. tts.py 每次实例化 TTSEngine 都会 mkdtemp(prefix='cet_tts_')，正常退出会 cleanup()，
     但进程被强杀/崩溃时会留下空目录。
  3. 打包过程会产生 build\\ 和 __pycache__\\。

安全原则（宁可少清，不能误删）：
  - 程序正在运行时，**绝不**动它正在用的 _MEI 目录（也只删 _MEI 前缀，不删 _rt 本身）。
  - 只删名字白名单匹配的目录，不做通配乱扫。
  - 被占用删不掉的，跳过并报告，不报错退出。

用法：
    python _clean.py                # 清理
    python _clean.py --dry          # 只看会删什么，不真删
    python _clean.py --all          # 连源码目录的 build/ __pycache__/ 一起清
    python _clean.py --keep-hours 6 # 只删 6 小时前的（默认 0 = 全部）
或者双击 _clean.bat。
"""
import glob
import os
import shutil
import sys
import time

HOME = os.path.dirname(os.path.abspath(__file__))
DEPLOY_DIR = r"E:\CETTrainer"
EXE_NAMES = ("CETTrainer.exe",)


# ---------------- 进程检测（纯 ctypes，不装 psutil） ----------------

def running_pids(names=EXE_NAMES):
    """返回正在运行的 exe 的 pid 列表。用 CreateToolhelp32Snapshot 枚举进程。"""
    import ctypes
    import ctypes.wintypes as wt

    TH32CS_SNAPPROCESS = 0x2

    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                    ("th32ProcessID", wt.DWORD), ("th32DefaultHeapID", ctypes.c_void_p),
                    ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                    ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wt.DWORD), ("szExeFile", ctypes.c_char * 260)]

    k32 = ctypes.windll.kernel32
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == -1:
        return []
    want = {n.lower() for n in names}
    pids = []
    try:
        e = PROCESSENTRY32()
        e.dwSize = ctypes.sizeof(PROCESSENTRY32)
        ok = k32.Process32First(snap, ctypes.byref(e))
        while ok:
            try:
                exe = e.szExeFile.decode("mbcs", "ignore").lower()
            except Exception:                      # noqa: BLE001
                exe = ""
            if exe in want:
                pids.append(int(e.th32ProcessID))
            ok = k32.Process32Next(snap, ctypes.byref(e))
    finally:
        k32.CloseHandle(snap)
    return pids


# ---------------- 清理目标 ----------------

def _size_of(path):
    """目录或文件的字节大小。"""
    if os.path.isfile(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def _age_hours(path):
    try:
        return (time.time() - os.path.getmtime(path)) / 3600.0
    except OSError:
        return 1e9


def targets(keep_hours=0.0, include_build=False):
    """(描述, 路径) 列表。只包含确实存在的。"""
    out = []

    # 1) 部署目录的 _MEI 解压残留
    for base in (DEPLOY_DIR, HOME):
        rt = os.path.join(base, "_rt")
        if os.path.isdir(rt):
            for p in sorted(glob.glob(os.path.join(rt, "_MEI*"))):
                if os.path.isdir(p) and _age_hours(p) >= keep_hours:
                    out.append(("onefile 解压残留", p))

    # 2) 系统 TEMP 里的 TTS 临时目录
    #    注意：进程的 TEMP 可能被父进程重定向（比如在编排环境/终端里跑），
    #    所以除了当前的 TEMP，还要扫真实的用户 TEMP，否则会漏。
    temp_dirs = []
    for key in ("TEMP", "TMP"):
        v = os.environ.get(key)
        if v and os.path.isdir(v):
            temp_dirs.append(v)
    real_temp = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp")
    if os.path.isdir(real_temp):
        temp_dirs.append(real_temp)
    temp_dirs.append(os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Temp"))

    seen_temp = set()
    for temp in temp_dirs:
        t = os.path.normcase(os.path.abspath(temp))
        if t in seen_temp:
            continue
        seen_temp.add(t)
        for p in sorted(glob.glob(os.path.join(temp, "cet_tts_*"))):
            if os.path.isdir(p) and _age_hours(p) >= keep_hours:
                out.append(("TTS 临时音频", p))
        # onefile 用默认 TEMP 时，解压目录直接落在 TEMP 根下
        for p in sorted(glob.glob(os.path.join(temp, "_MEI*"))):
            if os.path.isdir(p) and _age_hours(p) >= keep_hours:
                out.append(("onefile 解压残留", p))
        # 被重定向的子 TEMP（如 dsh-win-bash-xxxx）也顺带扫一层
        for sub in sorted(glob.glob(os.path.join(temp, "*"))):
            if not os.path.isdir(sub):
                continue
            base = os.path.basename(sub).lower()
            if not (base.startswith("dsh-") or base.startswith("tmp")):
                continue
            for p in sorted(glob.glob(os.path.join(sub, "cet_tts_*"))):
                if os.path.isdir(p) and _age_hours(p) >= keep_hours:
                    out.append(("TTS 临时音频", p))
            for p in sorted(glob.glob(os.path.join(sub, "_MEI*"))):
                if os.path.isdir(p) and _age_hours(p) >= keep_hours:
                    out.append(("onefile 解压残留", p))

    # 3) 源码目录的打包中间产物（可选）
    if include_build:
        for name in ("build", "dist_tmp"):
            p = os.path.join(HOME, name)
            if os.path.isdir(p):
                out.append(("打包中间产物", p))
        for p in sorted(glob.glob(os.path.join(HOME, "__pycache__"))):
            out.append(("字节码缓存", p))
        for p in sorted(glob.glob(os.path.join(HOME, "pages", "__pycache__"))):
            out.append(("字节码缓存", p))
        for p in sorted(glob.glob(os.path.join(HOME, "cet_tts_*"))):
            if os.path.isdir(p):
                out.append(("TTS 临时音频", p))

    # 去重：同一个目录可能被多条扫描路径命中（TEMP 与子 TEMP 重叠时）
    dedup = {}
    for kind, path in out:
        key = os.path.normcase(os.path.abspath(path))
        if key not in dedup:
            dedup[key] = (kind, path)
    return list(dedup.values())


def in_use_dirs(pids):
    """正在运行的进程实际加载的 _MEI 目录，绝对不能删。

    做法：枚举进程加载的模块 DLL 路径，取到路径里第一个以 _MEI 开头的
    目录段为止，就是正在使用的解压目录。
    """
    if not pids:
        return set()
    import ctypes
    import ctypes.wintypes as wt

    TH32CS_SNAPMODULE = 0x8 | 0x10          # MODULE | MODULE32

    class MODULEENTRY32(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("th32ModuleID", wt.DWORD),
                    ("th32ProcessID", wt.DWORD), ("GlblcntUsage", wt.DWORD),
                    ("ProccntUsage", wt.DWORD), ("modBaseAddr", ctypes.c_void_p),
                    ("modBaseSize", wt.DWORD), ("hModule", ctypes.c_void_p),
                    ("szModule", ctypes.c_char * 256),
                    ("szExePath", ctypes.c_char * 260)]

    k32 = ctypes.windll.kernel32
    out = set()
    for pid in pids:
        snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pid)
        if snap == -1 or snap == 0xFFFFFFFF:
            continue
        try:
            e = MODULEENTRY32()
            e.dwSize = ctypes.sizeof(MODULEENTRY32)
            ok = k32.Module32First(snap, ctypes.byref(e))
            while ok:
                try:
                    path = e.szExePath.decode("mbcs", "ignore")
                except Exception:                # noqa: BLE001
                    path = ""
                if path:
                    parts = path.split("\\")
                    acc = []
                    for seg in parts:
                        acc.append(seg)
                        if seg.upper().startswith("_MEI"):
                            out.add(os.path.normcase("\\".join(acc)))
                            break
                ok = k32.Module32Next(snap, ctypes.byref(e))
        finally:
            k32.CloseHandle(snap)
    return out


def remove(path):
    """删目录/文件，返回 (成功?, 提示)。

    注意：目标已经不存在算成功（可能刚被程序自带的启动清理删掉了，
    两个清理器同时跑时很常见），不能当成失败。
    """
    if not os.path.exists(path):
        return True, ""
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return True, ""
    except FileNotFoundError:
        return True, ""                     # 已被别人清掉，目的已达到
    except PermissionError:
        return False, "被占用（程序可能正在运行）"
    except OSError as e:
        if getattr(e, "winerror", None) == 2:
            return True, ""
        return False, str(e)


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.1f %s" % (n, unit)
        n /= 1024.0
    return "%.1f GB" % n


def main():
    dry = "--dry" in sys.argv or "-n" in sys.argv
    include_build = "--all" in sys.argv
    keep_hours = 0.0
    for i, a in enumerate(sys.argv):
        if a == "--keep-hours" and i + 1 < len(sys.argv):
            try:
                keep_hours = float(sys.argv[i + 1])
            except ValueError:
                pass

    print("=" * 62)
    print(" CETTrainer 垃圾清理" + ("   [预览模式，不真删]" if dry else ""))
    print("=" * 62)

    pids = running_pids()
    if pids:
        print("! 检测到程序正在运行（pid: %s）" % ", ".join(map(str, pids)))
        print("  正在使用的 _MEI 目录会被跳过（Windows 也会拒绝删除）。")
        print("  建议先关掉程序再清理，能清得更干净。")
    else:
        print("程序未运行，可以安全清理。")
    print("")

    items = targets(keep_hours, include_build)

    # 正在使用的目录绝对不能碰
    busy = in_use_dirs(pids)
    if busy:
        before = len(items)
        items = [(k, p) for (k, p) in items
                 if os.path.normcase(os.path.abspath(p)) not in busy]
        skipped = before - len(items)
        if skipped:
            print("已排除 %d 个正在使用的解压目录（程序正在跑）。" % skipped)
            print("")

    if not items:
        print("没有需要清理的东西，很干净。")
        return 0

    freed = 0
    failed = []
    print("%-16s %-10s %s" % ("类型", "大小", "路径"))
    print("-" * 62)
    for kind, path in items:
        size = _size_of(path)
        if dry:
            print("%-16s %-10s %s" % (kind, human(size), path))
            freed += size
            continue
        ok, msg = remove(path)
        if ok:
            print("%-16s %-10s %s" % (kind, human(size), path))
            freed += size
        else:
            failed.append((path, msg))
            print("%-16s %-10s %s  <- 跳过：%s" % (kind, human(size), path, msg))
    print("-" * 62)
    verb = "可释放" if dry else "已释放"
    print("%s %d 项，共 %s" % (verb, len(items) - len(failed), human(freed)))
    if failed:
        print("跳过 %d 项（多半是程序还开着，关掉再跑一次）" % len(failed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
