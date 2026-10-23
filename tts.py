# -*- coding: utf-8 -*-
"""TTS 引擎封装

优先使用 pyttsx3 / win32com / PowerShell System.Speech。
为了让打包后的单 exe 稳定工作，这里直接用「调用 PowerShell 生成 wav 再用 winsound 播放」的方案，
不依赖任何第三方包。
"""

import os
import subprocess
import sys
import tempfile
import threading
import urllib.parse
import urllib.request
import winsound

try:
    import tts_edge
except ImportError:  # 打包后万一没带上，降级到「本机 + 百度在线」两条腿
    tts_edge = None

# 隐藏子进程窗口
if sys.platform == "win32":
    _CREATE_NO_WINDOW = 0x08000000
else:
    _CREATE_NO_WINDOW = 0


def _find_powershell():
    """找 powershell.exe 的绝对路径。"""
    candidates = [
        os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                     "System32", "WindowsPowerShell", "v1.0", "powershell.exe"),
        "powershell.exe",
    ]
    for c in candidates:
        if os.path.sep in c:
            if os.path.isfile(c):
                return c
        else:
            return c
    return "powershell.exe"


POWERSHELL = _find_powershell()

def _short_path(path):
    """路径转 8.3 短名：用户名带单引号时（如 g'z'x）PowerShell 会把路径字符串断掉。"""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(path, buf, 1024):
            return buf.value
    except Exception:  # noqa: BLE001
        pass
    return path



# 生成 wav 的 PowerShell 脚本模板（不带音高）
_SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {{ $s.SelectVoice('{voice}') }} catch {{ }}
$s.Rate = {rate}
$s.Volume = {volume}
$s.SetOutputToWaveFile('{out}')
$s.Speak([System.Net.WebUtility]::HtmlDecode('{ssml}'))
$s.Dispose()
"""

# 用 PromptBuilder + SSML 控制音高（比直接 SetOutputToWaveFile 灵活）
_PITCH_SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {{ $s.SelectVoice('{voice}') }} catch {{ }}
$s.Rate = {rate}
$s.Volume = {volume}
$s.SetOutputToWaveFile('{out}')
$b = New-Object System.Speech.Synthesis.PromptBuilder
$b.AppendSsmlMarkup('<prosody pitch="{pitch}">{text}</prosody>')
$s.Speak($b)
$s.Dispose()
"""

# 枚举已安装音色的 PS 脚本
_VOICE_SCRIPT = """
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.GetInstalledVoices() | ForEach-Object {{
  if ($_.Enabled) {{ Write-Output ($_.VoiceInfo.Name + '|' + $_.VoiceInfo.Culture.Name) }}
}}
$s.Dispose()
""".replace("{{", "{").replace("}}", "}")


def _ps_escape(text):
    """转义单引号，避免 PowerShell 字符串中断。"""
    return text.replace("'", "''")


def _xml_escape(text):
    """转义 XML 特殊字符，给 SSML 用。"""
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace("'", "&apos;")
                .replace('"', "&quot;"))


def looks_english(text):
    """粗略判断这段文字该用英文音色还是中文音色。"""
    latin = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return latin >= cjk


def list_voices():
    """列出本机所有可用音色：[(名称, 语言)]，失败返回空列表。"""
    try:
        proc = subprocess.run(
            [POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", _VOICE_SCRIPT],
            capture_output=True, timeout=20, creationflags=_CREATE_NO_WINDOW)
        out = (proc.stdout or b"").decode("utf-8", "ignore")
    except Exception:  # noqa: BLE001
        return []
    voices = []
    for line in out.splitlines():
        line = line.strip()
        if "|" in line:
            name, _, lang = line.partition("|")
            voices.append((name.strip(), lang.strip()))
    return voices


def pick_voice(voices, lang_prefix):
    """在音色列表里挑一个指定语言的，挑不到返回 None。"""
    for name, lang in voices:
        if lang.lower().startswith(lang_prefix):
            return name
    return None


# 在线真人音库：百度翻译的朗读接口，公开可用、不用登录，音质比 Windows 自带的清楚得多
_ONLINE_TTS = ("https://fanyi.baidu.com/gettts?lan={lang}&text={text}&spd={spd}&source=web")


def online_tts(text, lang="en", spd=3, timeout=12):
    """下载在线朗读 MP3，返回字节；失败返回 None。"""
    if not text or not text.strip():
        return None
    url = _ONLINE_TTS.format(lang=lang, text=urllib.parse.quote(text.strip()), spd=spd)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://fanyi.baidu.com/",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        # 正常返回的是 MP3，开头几个字节不是 mp3 帧头就当失败
        if len(data) > 4000 and data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3\x03"):
            return data
        return None
    except Exception:  # noqa: BLE001
        return None


def _save_mp3(data, path):
    with open(path, "wb") as f:
        f.write(data)
    return path


def play_mp3(path):
    """用系统自带的 MCI 播放 mp3，不引入第三方库。"""
    try:
        import ctypes
        mci = ctypes.windll.winmm.mciSendStringW
        alias = "cetmp3"
        mci(f'close {alias}', None, 0, None)
        if mci(f'open "{path}" type mpegvideo alias {alias}', None, 0, None) != 0:
            return False
        mci(f"play {alias} wait", None, 0, None)
        mci(f"close {alias}", None, 0, None)
        return True
    except Exception:  # noqa: BLE001
        return False


class TTSEngine:
    """把文本合成为 wav 并播放。"""

    def __init__(self, voice="", rate=0, volume=100, pitch=0, prefer_online=True):
        self.voices = list_voices()          # [(名称, 语言)]
        self.pitch = max(-50, min(50, int(pitch)))   # 音高，单位 %（SSML 的 x-low~x-high 不够细）
        self.voice_en = ""
        self.voice_zh = ""
        self._init_voices(voice)
        self.rate = max(-10, min(10, rate))
        self.volume = max(0, min(100, volume))
        self._tmpdir = tempfile.mkdtemp(prefix="cet_tts_")
        self._counter = 0
        self._lock = threading.Lock()
        self._last_error = ""
        # 缓存：文本+语速 -> wav 路径，反复播放同一句时省掉 2~3 秒合成时间
        self._cache = {}
        self.prefer_online = prefer_online
        self._last_source = ""
        # 界面上「语速 1~9」的原始档位，Edge 音色按它换算百分比
        self.speed_ui = 5
        # ---- Edge 神经音色（在线首选）----
        self.edge_ok = tts_edge is not None
        self.use_edge = self.edge_ok
        self.edge_voice_en = tts_edge.DEFAULT_EN if self.edge_ok else ""
        self.edge_voice_zh = tts_edge.DEFAULT_ZH if self.edge_ok else ""
        self._edge_fail = 0        # 连续失败次数，网络不通时及时让路，别每次都干等

    def _init_voices(self, preferred=""):
        """确定中英文各用哪个音色。用户指定的优先，否则自动挑。"""
        self.voice_en = pick_voice(self.voices, "en") or "Microsoft Zira Desktop"
        self.voice_zh = pick_voice(self.voices, "zh") or ""
        if preferred:
            low = preferred.lower()
            if "zh" in low or "chinese" in low or "huihui" in low:
                self.voice_zh = preferred
            else:
                self.voice_en = preferred
        if not self.voice_zh:
            self.voice_zh = self.voice_en

    # ---- Edge 神经音色相关 ----
    EDGES = list(tts_edge.VOICES) if tts_edge else []

    def edge_for(self, text):
        """按中英文挑对应的 Edge 音色 id。"""
        if not self.EDGES:
            return ""
        return self.edge_voice_zh if not looks_english(text) else self.edge_voice_en

    @staticmethod
    def _pct(value):
        """0 -> '+0%'，正数带加号，Edge 的 SSML 要求这种写法。"""
        v = int(value)
        return "%+d%%" % v

    def _rate_for_edge(self):
        """把内部语速 self.rate（-10 ~ 10）映射到 Edge 的百分比（-40% ~ +40%）。

        界面语速 1~9 对应 rate = level - 5（-4 ~ +4），慢速播放再减 6 到 -10。
        统一按 rate*10 换算，这样「慢速播放」对在线音色同样生效。
        """
        return self._pct(max(-40, min(40, int(self.rate) * 10)))

    def _synthesize_edge(self, text):
        """尝试用 Edge 神经音色合成 mp3，成功返回路径，失败返回 None。"""
        if not (self.use_edge and self.edge_ok and tts_edge):
            return None
        voice = self.edge_for(text)
        if not voice:
            return None
        try:
            data = tts_edge.synthesize(
                text, voice=voice, rate=self._rate_for_edge(),
                pitch=self._pct(self.pitch), volume="+0%", timeout=20.0)
        except Exception as e:  # noqa: BLE001
            self._last_error = "edge: %r" % (e,)
            data = None
        if data and len(data) > 1000:
            path = self._wav_path().replace(".wav", ".mp3")
            try:
                _save_mp3(data, path)
                self._edge_fail = 0
                return path
            except OSError:
                return None
        # 失败累计到 3 次就停用，后续直接走离线，避免每次操作都卡 20 秒
        self._edge_fail += 1
        if self._edge_fail >= 3:
            self.use_edge = False
        return None

    def set_voice(self, name):
        """切换音色。

        兼容三种写法：
          - Edge 内部 id（en-US-AvaNeural / zh-CN-XiaoxiaoNeural）
          - Edge 显示名（"Ava（美音·女）"）
          - 老式的本机音色名（"Microsoft Zira Desktop"）
        """
        if not name:
            return

        # 先看是不是 Edge 音色（按 id 或显示名匹配）
        hit = None
        for label, vid, lang, _desc in self.EDGES:
            if name == vid or name == label:
                hit = (vid, lang)
                break
        if hit:
            vid, lang = hit
            if lang == "zh":
                self.edge_voice_zh = vid
            else:
                self.edge_voice_en = vid
            # 用 Edge 音色时把在线开关打开：这里才是用户明确选的好音色
            self.use_edge = True
            self._edge_fail = 0
            self._cache.clear()
            return

        # 否则按老逻辑：本机音色只在自家人之间切
        low = name.lower()
        if any(k in low for k in ("zh", "chinese", "huihui", "yaoyao", "kangkang")):
            self.voice_zh = name
        else:
            self.voice_en = name
        self._cache.clear()

    def set_edge_enabled(self, flag):
        """开关 Edge 音色（界面上让用户手动切回离线时用）。"""
        self.use_edge = bool(flag) and self.edge_ok
        if self.use_edge:
            self._edge_fail = 0
        self._cache.clear()

    def set_pitch(self, value):
        self.pitch = max(-50, min(50, int(value)))
        self._cache.clear()

    def voice_for(self, text):
        return self.voice_zh if not looks_english(text) else self.voice_en

    def _cache_key(self, text):
        return (text.strip(), self.rate, self.volume, self.pitch, self.voice_for(text),
                self.prefer_online, self.edge_for(text) if self.use_edge else "")

    def _cached(self, text):
        key = self._cache_key(text)
        path = self._cache.get(key)
        if path and os.path.isfile(path):
            return path
        return None

    def _wav_path(self):
        with self._lock:
            self._counter += 1
            n = self._counter
        return os.path.join(self._tmpdir, f"tts_{n}.wav")

    def prewarm(self, text):
        """后台预生成 wav，让接下来的播放瞬时响应。"""
        if not text or not text.strip():
            return
        if self._cached(text):
            return
        threading.Thread(target=self.synthesize, args=(text,), daemon=True).start()

    def synthesize(self, text):
        """合成语音，返回文件路径；失败返回 None。已合成过的直接返回缓存。

        三级降级：Edge 神经音色 → 百度在线 → 本机 SAPI5。
        前面的失败不影响后面，保证断网也一定能出声。
        """
        if not text or not text.strip():
            return None
        hit = self._cached(text)
        if hit:
            return hit

        # ① Edge 神经网络音色（音质最好，需要联网）
        if self.use_edge and self.edge_ok:
            path = self._synthesize_edge(text)
            if path:
                self._cache[self._cache_key(text)] = path
                self._last_source = "edge"
                return path

        # ② 百度在线朗读接口（老方案，作备用）
        if self.prefer_online:
            lang = "en" if looks_english(text) else "zh"
            spd = max(1, min(5, 5 + round(self.rate / 5)))
            data = online_tts(text, lang=lang, spd=spd)
            if data:
                path = self._wav_path().replace(".wav", ".mp3")
                try:
                    _save_mp3(data, path)
                    if os.path.getsize(path) > 4000:
                        self._cache[self._cache_key(text)] = path
                        self._last_source = "online"
                        return path
                except OSError:
                    pass
            self._last_source = "local"
        else:
            self._last_source = "local"

        out = _short_path(self._wav_path())
        voice = self.voice_for(text)
        if self.pitch:
            # 正数抬高音高 → 更亮更清楚；负数压低
            sign = "+" if self.pitch > 0 else ""
            script = _PITCH_SCRIPT.format(
                voice=_ps_escape(voice),
                rate=self.rate,
                volume=self.volume,
                out=_ps_escape(out),
                pitch=f"{sign}{self.pitch}%",
                text=_xml_escape(text),
            )
        else:
            script = _SCRIPT.format(
                voice=_ps_escape(voice),
                rate=self.rate,
                volume=self.volume,
                out=_ps_escape(out),
                ssml=_ps_escape(text),
            )
        try:
            proc = subprocess.run(
                [POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True,
                timeout=60,
                creationflags=_CREATE_NO_WINDOW,
            )
            if os.path.isfile(out) and os.path.getsize(out) > 2000:
                self._cache[self._cache_key(text)] = out
                return out
            self._last_error = (proc.stderr or b"").decode("utf-8", "ignore")[:500]
            return None
        except Exception as e:  # noqa: BLE001
            self._last_error = repr(e)[:500]
            return None

    def save_wav(self, text, path):
        """把合成结果另存到指定路径（导出听力音频用），返回是否成功。"""
        wav = self.synthesize(text)
        if not wav:
            return False
        try:
            import shutil
            shutil.copyfile(wav, path)
            return True
        except OSError:
            return False

    def stop(self):
        """立刻停掉正在播放的声音（MCI 与 winsound 两条路径都停）。"""
        self._stopped = True
        try:
            import ctypes
            winmm = ctypes.windll.winmm
            winmm.mciSendStringW("close cetmp3", None, 0, None)
            winmm.mciSendStringW("stop cetmp3", None, 0, None)
        except Exception:  # noqa: BLE001
            pass
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:  # noqa: BLE001
            pass

    def speak(self, text, blocking=True):
        """合成并播放。blocking=False 时后台播放。"""
        def _job():
            wav = self.synthesize(text)
            if not wav:
                return
            try:
                if wav.lower().endswith(".mp3"):
                    if not play_mp3(wav):
                        self._last_error = "mp3 播放失败"
                else:
                    winsound.PlaySound(wav, winsound.SND_FILENAME)
            except Exception as e:  # noqa: BLE001
                self._last_error = repr(e)[:500]

        if blocking:
            _job()
        else:
            threading.Thread(target=_job, daemon=True).start()

    def last_error(self):
        return self._last_error

    # ------------------------------------------------------------------ #
    # 给界面用的音色清单
    # ------------------------------------------------------------------ #
    def voice_options(self):
        """返回界面下拉要用的音色列表，元素是 (显示文本, 传给 set_voice 的值, 说明)。

        分组：前面是 Edge 神经音色（标「在线」），后面是本机 SAPI5 音色（标「离线」）。
        本机只有 Huihui / Zira 两个老音色，默认不选它们，只在断网兜底时用。

        显示文本刻意精简（去掉中文括号、用单字符分隔），否则下拉框会把
        顶栏右侧的「语速」「试听」挤到窗口外。
        """
        import re as _re

        def short(label):
            # "Ava（美音·女）" -> "Ava 美音女"
            return _re.sub(r"（(.+?)）", lambda m: " " + m.group(1).replace("·", ""),
                           label).strip()

        opts = []
        if self.EDGES:
            online = self.edge_ok
            for label, vid, _lang, desc in self.EDGES:
                mark = "·在线" if online else "·离线"
                opts.append(("%s%s" % (short(label), mark), vid, desc))
        for name, _lang in self.voices:
            # "Microsoft Huihui Desktop" -> "Huihui"
            short_name = name.replace("Microsoft", "").replace("Desktop", "").strip()
            opts.append(("%s·离线" % short_name, name,
                         "Windows 自带音色，断网时使用"))
        return opts

    def current_voice_value(self):
        """当前选中的音色值，用于回填下拉框。"""
        if self.use_edge and self.edge_voice_en:
            return self.edge_voice_en
        return self.voice_en or (self.voices[0][0] if self.voices else "")

    def current_voice_desc(self):
        """当前音色的一句话说明。"""
        if self.use_edge and self.edge_ok and tts_edge:
            vid = self.edge_voice_en
            return tts_edge.VOICE_DESC.get(vid, "")
        return "Windows 自带音色，断网时也能用"

    def status_text(self):
        """一句话描述当前音源状态，显示在状态栏 / 音色旁边。"""
        if not self.edge_ok:
            return "本机音色"
        if self.use_edge:
            return "在线神经音色"
        return "本机音色（已切离线）"

    def cleanup(self):
        """删除临时目录里的 wav。"""
        try:
            self._cache.clear()
            for name in os.listdir(self._tmpdir):
                if name.endswith((".wav", ".mp3")):
                    try:
                        os.remove(os.path.join(self._tmpdir, name))
                    except OSError:
                        pass
            os.rmdir(self._tmpdir)
        except OSError:
            pass


if __name__ == "__main__":
    t = TTSEngine()
    print("powershell:", POWERSHELL)
    p = t.synthesize("Hello, this is a test of the dictation engine.")
    print("wav:", p, "size:", os.path.getsize(p) if p else 0)
    print("err:", t.last_error())
