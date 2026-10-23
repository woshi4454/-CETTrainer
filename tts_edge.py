# -*- coding: utf-8 -*-
"""微软 Edge 神经网络语音（在线）——纯标准库实现，不依赖任何第三方包。

背景
----
Windows 自带的 SAPI5 音色（Zira / Huihui）是 2010 年前后的拼接式合成，机械感重、
英文连读生硬；听力/跟读练习用它很容易听错。微软 Edge「大声朗读」背后是一整套
神经网络 TTS（Neural），音质接近真人录音、断句自然，正是四六级听力需要的。

本模块用标准库 socket + ssl 直接跑 WebSocket 协议调用该服务，不引入 aiohttp 等
依赖，打包进 --onefile 也不额外增大体积。

对外只暴露三样东西：
    VOICES                  —— 精选音色清单
    synthesize(...)         —— 合成 mp3，返回字节
    available()             —— 快速探活（用于启动时决定是否启用）
"""

import base64
import os
import socket
import ssl
import struct
import time
import uuid
from xml.sax.saxutils import escape

# ---------------------------------------------------------------------------
# 精选音色：只挑中英文里最清晰、最适合「学外语」的几个，不把 300 多个全塞给用户
# 元组 = (显示名, 内部 id, 语言, 一句话说明)
# ---------------------------------------------------------------------------
VOICES = [
    ("Ava（美音·女）", "en-US-AvaNeural", "en", "清晰明亮，标准美式发音，最推荐听力"),
    ("Andrew（美音·男）", "en-US-AndrewNeural", "en", "低沉沉稳，适合精听与跟读"),
    ("Emma（美音·女）", "en-US-EmmaNeural", "en", "语速温和，咬字干净，适合听写"),
    ("Brian（美音·男）", "en-US-BrianNeural", "en", "亲切自然，像真人播客"),
    ("Sonia（英音·女）", "en-GB-SoniaNeural", "en", "标准英式口音，四六级英音题用它"),
    ("Ryan（英音·男）", "en-GB-RyanNeural", "en", "英式男声，适合适应不同口音"),
    ("晓晓（中文·女）", "zh-CN-XiaoxiaoNeural", "zh", "温柔自然，中文朗读首选"),
    ("云希（中文·男）", "zh-CN-YunxiNeural", "zh", "清朗年轻，语速清晰"),
    ("晓伊（中文·女）", "zh-CN-XiaoyiNeural", "zh", "活泼偏快，适合练反应"),
    ("云扬（中文·男）", "zh-CN-YunyangNeural", "zh", "播音腔，正式、字正腔圆"),
]

# 内部 id -> 说明，方便界面显示
VOICE_DESC = {v[1]: v[3] for v in VOICES}
VOICE_LANG = {v[1]: v[2] for v in VOICES}
VOICE_LABEL = {v[1]: v[0] for v in VOICES}

DEFAULT_EN = "en-US-AvaNeural"
DEFAULT_ZH = "zh-CN-XiaoxiaoNeural"

# ---------------------------------------------------------------------------
# 服务端签名（Sec-MS-GEC）
# 该 token 由「Windows FILETIME 对齐到 5 分钟」+ 固定 client token 做一次
# 自定义 SHA-256 与 CS64 混合摘要得到，算法由 edge-tts 项目逆向得出，这里原样移植。
# ---------------------------------------------------------------------------
_TRUSTED_TOKEN = "6A5AA1D4EAFF4E9FB37E23D68491D6F4"
_SEC_MS_GEC_VERSION = "2-143.0.3650.75"
_WIN_EPOCH = 11644473600
_S_TO_NS = 1e9

_SHA256_INITIAL = (
    0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
    0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19,
)
_SHA256_STATE = (
    0xFD9FBEA2, 0x91243CE7, 0xBE499094, 0xCD2E1E0A,
    0x6C006F49, 0x04BD35AB, 0xFEB0A7E4, 0x03EFFBD2,
)
_SHA256_SCHEDULE = (
    0xEB24BF9E, 0x1558691F, 0xA0C09EE2, 0x0CFA32BA,
    0xA622EE8C, 0xD1DD9491, 0xC0DD25A0, 0xF9E70AB6,
    0xF0C31573, 0x7058CE4E, 0x7188E606, 0x00E5AB33,
    0xD258B060, 0x72766564,
)
_SHA256_ROUND_CONSTANTS = (
    0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5,
    0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
    0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3,
    0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
    0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC,
    0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
    0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7,
    0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
    0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13,
    0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
    0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3,
    0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
    0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5,
    0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
    0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208,
    0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2,
)
_SHA256_ADJUSTMENT = 0xC9DC06A7
_SHA256_BLOCK_CONSTANTS = (
    _SHA256_ROUND_CONSTANTS[:14] + (_SHA256_ADJUSTMENT,) + _SHA256_ROUND_CONSTANTS[15:]
)
_SHA256_SIGMA0_ADJUSTMENT = 0x059C0B80
_SHA256_SIGMA1_ADJUSTMENT = 0x000B92C0

_CS64_COEFFICIENTS = (
    (0xE82E91B1, 0xB32700D0), (0x44DE24C6, 0x88DFF51D),
    (0x3BEB65BC, 0x29514038), (0xC89C5933, 0xB328CBDF),
    (0x8D1EC211, 0xD405B4D5), (0x314EF5D5, 0x26E55F3C),
    (0xE92491B1, 0x607801C6), (0xF0A5B9D5, 0x82B2C1FB),
    (0x06064CF3, 0xFA51A3DA), (0xDA79FA60, 0x207CC464),
    (0xBED20560, 0x3C3C74F3), (0x89F9C9F8, 0xD2D14B61),
    (0x35FA38C6, 0xBB04A2C1), (0xCB49E3C6, 0xC5626167),
)
_CS64_FACTOR = 0x82893933
_CS64_ADJUSTMENT0 = 0xF2F90B1A
_CS64_ADJUSTMENT1 = 0x0B1A0000
_U32_MASK = 0xFFFFFFFF


def _rol16(value):
    value &= _U32_MASK
    return ((value << 16) | (value >> 16)) & _U32_MASK


def _words_le4_even(data):
    padded = data + b"\x00" * ((-len(data)) % 4)
    if not padded:
        return []
    words = list(struct.unpack("<%dI" % (len(padded) // 4), padded))
    if len(words) % 2:
        words.append(0)
    return words


def _sigma0(value):
    return ((value >> 7) ^ (value << 25) ^ (value >> 18)
            ^ (value << 14) ^ (value >> 3)) & _U32_MASK


def _sigma1(value):
    return ((value >> 17) ^ (value << 15) ^ (value >> 19)
            ^ (value << 13) ^ (value >> 10)) & _U32_MASK


def _sha256_rounds(state, words, first_round=0):
    a, b, c, d, e, f, g, h = state
    mask = _U32_MASK
    constants = _SHA256_BLOCK_CONSTANTS if first_round == 14 else _SHA256_ROUND_CONSTANTS
    aligned = min(64, ((first_round + 7) // 8) * 8)
    for index in range(first_round, aligned):
        rot_e = e * 0x100000001
        rot_a = a * 0x100000001
        t1 = (h + ((rot_e >> 6) ^ (rot_e >> 11) ^ (rot_e >> 25))
              + (g ^ (e & (f ^ g))) + constants[index] + words[index])
        t2 = (((rot_a >> 2) ^ (rot_a >> 13) ^ (rot_a >> 22))
              + ((a & b) | (c & (a | b))))
        a, b, c, d, e, f, g, h = (t1 + t2) & mask, a, b, c, (d + t1) & mask, e, f, g
    for index in range(aligned, 64, 8):
        rot_e = e * 0x100000001
        rot_a = a * 0x100000001
        t1 = (h + ((rot_e >> 6) ^ (rot_e >> 11) ^ (rot_e >> 25))
              + (g ^ (e & (f ^ g))) + constants[index] + words[index])
        d = (d + t1) & mask
        h = (t1 + ((rot_a >> 2) ^ (rot_a >> 13) ^ (rot_a >> 22))
             + ((a & b) | (c & (a | b)))) & mask
        rot_e = d * 0x100000001
        rot_a = h * 0x100000001
        t1 = (g + ((rot_e >> 6) ^ (rot_e >> 11) ^ (rot_e >> 25))
              + (f ^ (d & (e ^ f))) + constants[index + 1] + words[index + 1])
        c = (c + t1) & mask
        g = (t1 + ((rot_a >> 2) ^ (rot_a >> 13) ^ (rot_a >> 22))
             + ((h & a) | (b & (h | a)))) & mask
        rot_e = c * 0x100000001
        rot_a = g * 0x100000001
        t1 = (f + ((rot_e >> 6) ^ (rot_e >> 11) ^ (rot_e >> 25))
              + (e ^ (c & (d ^ e))) + constants[index + 2] + words[index + 2])
        b = (b + t1) & mask
        f = (t1 + ((rot_a >> 2) ^ (rot_a >> 13) ^ (rot_a >> 22))
             + ((g & h) | (a & (g | h)))) & mask
        rot_e = b * 0x100000001
        rot_a = f * 0x100000001
        t1 = (e + ((rot_e >> 6) ^ (rot_e >> 11) ^ (rot_e >> 25))
              + (d ^ (b & (c ^ d))) + constants[index + 3] + words[index + 3])
        a = (a + t1) & mask
        e = (t1 + ((rot_a >> 2) ^ (rot_a >> 13) ^ (rot_a >> 22))
             + ((f & g) | (h & (f | g)))) & mask
        rot_e = a * 0x100000001
        rot_a = e * 0x100000001
        t1 = (d + ((rot_e >> 6) ^ (rot_e >> 11) ^ (rot_e >> 25))
              + (c ^ (a & (b ^ c))) + constants[index + 4] + words[index + 4])
        h = (h + t1) & mask
        d = (t1 + ((rot_a >> 2) ^ (rot_a >> 13) ^ (rot_a >> 22))
             + ((e & f) | (g & (e | f)))) & mask
        rot_e = h * 0x100000001
        rot_a = d * 0x100000001
        t1 = (c + ((rot_e >> 6) ^ (rot_e >> 11) ^ (rot_e >> 25))
              + (b ^ (h & (a ^ b))) + constants[index + 5] + words[index + 5])
        g = (g + t1) & mask
        c = (t1 + ((rot_a >> 2) ^ (rot_a >> 13) ^ (rot_a >> 22))
             + ((d & e) | (f & (d | e)))) & mask
        rot_e = g * 0x100000001
        rot_a = c * 0x100000001
        t1 = (b + ((rot_e >> 6) ^ (rot_e >> 11) ^ (rot_e >> 25))
              + (a ^ (g & (h ^ a))) + constants[index + 6] + words[index + 6])
        f = (f + t1) & mask
        b = (t1 + ((rot_a >> 2) ^ (rot_a >> 13) ^ (rot_a >> 22))
             + ((c & d) | (e & (c | d)))) & mask
        rot_e = f * 0x100000001
        rot_a = b * 0x100000001
        t1 = (a + ((rot_e >> 6) ^ (rot_e >> 11) ^ (rot_e >> 25))
              + (h ^ (f & (g ^ h))) + constants[index + 7] + words[index + 7])
        e = (e + t1) & mask
        a = (t1 + ((rot_a >> 2) ^ (rot_a >> 13) ^ (rot_a >> 22))
             + ((b & c) | (d & (b | c)))) & mask
    return a, b, c, d, e, f, g, h


def _expand_sha256_schedule(words, first_word=16):
    mask = _U32_MASK
    for index in range(first_word, 64):
        x, y = words[index - 2], words[index - 15]
        sigma1 = (x >> 17) ^ (x << 15) ^ (x >> 19) ^ (x << 13) ^ (x >> 10)
        sigma0 = (y >> 7) ^ (y << 25) ^ (y >> 18) ^ (y << 14) ^ (y >> 3)
        words.append((sigma1 + words[index - 7] + sigma0 + words[index - 16]) & mask)


def _sha256_init(data):
    mask = _U32_MASK
    words = [0] * 14 + [int.from_bytes(data[:3], "big")]
    words.append(int.from_bytes(data[3:7], "big"))
    for index in range(16, 30):
        value = _SHA256_SCHEDULE[index - 16]
        if index - 2 >= 14:
            value += ((_sigma1(words[index - 2]) ^ _SHA256_SIGMA1_ADJUSTMENT)
                      if index == 16 else _sigma1(words[index - 2]))
        if index - 7 >= 14:
            value += words[index - 7]
        if index - 15 >= 14:
            value += ((_sigma0(words[index - 15]) ^ _SHA256_SIGMA0_ADJUSTMENT)
                      if index == 29 else _sigma0(words[index - 15]))
        words.append(value & mask)
    words.append((_sigma1(words[28]) + words[23] + _sigma0(words[15]) + words[14]
                  + _SHA256_ADJUSTMENT - _SHA256_ROUND_CONSTANTS[14]) & mask)
    _expand_sha256_schedule(words, 31)
    working = _sha256_rounds(_SHA256_STATE, words, 14)
    return tuple((x + y) & mask for x, y in zip(_SHA256_INITIAL, working))


def _sha256_digest(data):
    if len(data) < 7:
        raise ValueError("token salt too short")
    mask = _U32_MASK
    length = 57 + len(data)
    padded = data[7:] + b"\x80" + b"\x00" * ((55 - length) % 64)
    padded += struct.pack(">Q", length * 8)
    state = _sha256_init(data[:7])
    for offset in range(0, len(padded), 64):
        words = list(struct.unpack(">16I", padded[offset:offset + 64]))
        _expand_sha256_schedule(words)
        working = _sha256_rounds(state, words)
        state = tuple((x + y) & mask for x, y in zip(state, working))
    return struct.pack(">8I", *state)


def _cs64_digest(data, digest):
    mask = _U32_MASK
    key_a, key_b = struct.unpack_from("<II", digest)
    key_a |= 1
    key_b |= 1
    factors = ((key_a * _CS64_FACTOR) & mask, (key_b * _CS64_FACTOR) & mask)
    terms = [(coefficient * factors[index % 2]) & mask
             for index, (coefficient, _) in enumerate(_CS64_COEFFICIENTS)]
    offsets = [offset for _, offset in _CS64_COEFFICIENTS]
    for index, word in enumerate(_words_le4_even(b"\x00" + data)):
        term = word * (key_a if index % 2 == 0 else key_b)
        offset = _rol16(word) * (0xEF0569FB if index % 2 == 0 else 0xC31713DB)
        if index == 0:
            term += _CS64_ADJUSTMENT0 * factors[0]
            offset += _CS64_ADJUSTMENT1
        terms.append(term & mask)
        offsets.append(offset & mask)
    swap_acc = swap_last = state = acc = 0
    for index in range(0, len(terms), 2):
        x, y = terms[index], terms[index + 1]
        t = _rol16((offsets[index] + x) & mask)
        q = (t * 0x76F50F34) & mask
        swap_acc += (_rol16(q) * 0xC3EFEA97 + q) & mask
        t = _rol16((offsets[index + 1] + y) & mask)
        q = (t * 0x1881CE3C) & mask
        swap_last = (_rol16(q) * 0x35BD1EC9 + q) & mask
        swap_acc = (swap_acc + swap_last) & mask

        state = (state * key_a + x) & mask
        state = (_rol16(state) * 0xCF98B111) & mask
        state = (_rol16(state) * 0x87085B9F) & mask
        state = (_rol16(state) * 0x12CEB96D) & mask
        state = (_rol16(state) * 0x257E1D83) & mask
        acc += state
        t = (state * key_b + y) & mask
        t = (_rol16(t) * 0xA27416F5) & mask
        t = (_rol16(t) * 0xD38396FF) & mask
        state = (_rol16((_rol16(t) * 0x7C932B89) & mask) * 0xBFA49F69) & mask
        acc = (acc + state) & mask
    return swap_last ^ state, swap_acc ^ acc


_GEC_CACHE = {"stamp": None, "value": None}


def gen_sec_ms_gec():
    """生成 Sec-MS-GEC 签名，同一 5 分钟窗口内复用，避免重复算 SHA。"""
    now = time.time()
    stamp = int((now + _WIN_EPOCH) // 300)
    if _GEC_CACHE["stamp"] == stamp and _GEC_CACHE["value"]:
        return _GEC_CACHE["value"]
    ticks = float(now + _WIN_EPOCH)
    ticks -= ticks % 300
    ticks *= _S_TO_NS / 100
    raw = ("%.0f%s" % (ticks, _TRUSTED_TOKEN)).encode("ascii")
    digest = _sha256_digest(raw)
    cs64 = struct.pack("<II", *_cs64_digest(raw, digest)).hex().upper()
    value = "%s-%s" % (cs64, digest.hex().upper())
    _GEC_CACHE["stamp"] = stamp
    _GEC_CACHE["value"] = value
    return value


# ---------------------------------------------------------------------------
# 极简 WebSocket 客户端（客户端掩码 + 分片重组，够用即可）
# ---------------------------------------------------------------------------
_HOST = "speech.platform.bing.com"
_PATH = "/consumer/speech/synthesize/readaloud/edge/v1"
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
       " (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0")


class _Sock(object):
    def __init__(self, timeout=30.0):
        url = "%s?TrustedClientToken=%s&Sec-MS-GEC=%s&Sec-MS-GEC-Version=%s&ConnectionId=%s" % (
            _PATH, _TRUSTED_TOKEN, gen_sec_ms_gec(), _SEC_MS_GEC_VERSION,
            uuid.uuid4().hex)
        raw = socket.create_connection((_HOST, 443), timeout=timeout)
        ctx = ssl.create_default_context()
        self.sock = ctx.wrap_socket(raw, server_hostname=_HOST)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        headers = [
            ("Host", _HOST), ("Connection", "Upgrade"), ("Upgrade", "websocket"),
            ("Sec-WebSocket-Key", key), ("Sec-WebSocket-Version", "13"),
            ("Pragma", "no-cache"), ("Cache-Control", "no-cache"),
            ("Origin", "chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold"),
            ("User-Agent", _UA), ("Accept-Encoding", "gzip, deflate, br"),
            ("Accept-Language", "en-US,en;q=0.9"),
        ]
        req = "GET %s HTTP/1.1\r\n" % url
        req += "".join("%s: %s\r\n" % h for h in headers) + "\r\n"
        self.sock.sendall(req.encode("ascii"))
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise IOError("connection closed during handshake")
            head += chunk
            if len(head) > 65536:
                raise IOError("handshake response too large")
        line = head.split(b"\r\n", 1)[0].decode("latin-1")
        if "101" not in line:
            raise IOError("handshake rejected: %s" % line)

    def send_text(self, payload):
        data = payload.encode("utf-8") if isinstance(payload, str) else payload
        size = len(data)
        frame = bytearray([0x81])
        if size < 126:
            frame.append(0x80 | size)
        elif size < 65536:
            frame.append(0x80 | 126)
            frame.extend(struct.pack(">H", size))
        else:
            frame.append(0x80 | 127)
            frame.extend(struct.pack(">Q", size))
        mask = os.urandom(4)
        frame.extend(mask)
        frame.extend(bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
        self.sock.sendall(bytes(frame))

    def _read(self, n):
        buf = b""
        while len(buf) < n:
            part = self.sock.recv(n - len(buf))
            if not part:
                raise IOError("connection closed")
            buf += part
        return buf

    def recv(self):
        """返回 (opcode, payload)。"""
        b1, b2 = self._read(2)
        opcode = b1 & 0x0F
        size = b2 & 0x7F
        if size == 126:
            size = struct.unpack(">H", self._read(2))[0]
        elif size == 127:
            size = struct.unpack(">Q", self._read(8))[0]
        mask = self._read(4) if (b2 & 0x80) else None
        data = self._read(size) if size else b""
        if mask:
            data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        return opcode, data

    def close(self):
        try:
            self.sock.close()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# 对外接口
# ---------------------------------------------------------------------------
def _now_string():
    return time.strftime("%a %b %d %Y %H:%M:%S GMT+0000 (Coordinated Universal Time)",
                         time.gmtime())


def _clean(text):
    """服务端不接受部分控制字符，去掉它们。"""
    out = []
    for ch in text:
        code = ord(ch)
        if (0 <= code <= 8) or (11 <= code <= 12) or (14 <= code <= 31):
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def synthesize(text, voice=DEFAULT_EN, rate="+0%", volume="+0%", pitch="+0Hz",
               timeout=30.0):
    """合成语音，返回 mp3 字节；失败返回 None。

    rate / pitch / volume 都是带符号的百分比字符串，例如 "+10%"、"-20%"。
    """
    text = _clean((text or "").strip())
    if not text:
        return None
    sock = None
    try:
        sock = _Sock(timeout=timeout)
        config = ('{"context":{"synthesis":{"audio":{"metadataoptions":{'
                  '"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"false"},'
                  '"outputFormat":"audio-24khz-48kbitrate-mono-mp3"}}}}')
        sock.send_text("X-Timestamp:%s\r\nContent-Type:application/json; charset=utf-8\r\n"
                       "Path:speech.config\r\n\r\n%s" % (_now_string(), config))
        ssml = ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' "
                "xml:lang='en-US'><voice name='%s'><prosody pitch='%s' rate='%s' "
                "volume='%s'>%s</prosody></voice></speak>"
                % (voice, pitch, rate, volume, escape(text)))
        sock.send_text("X-RequestId:%s\r\nContent-Type:application/ssml+xml\r\n"
                       "X-Timestamp:%sZ\r\nPath:ssml\r\n\r\n%s"
                       % (uuid.uuid4().hex, _now_string(), ssml))
        chunks = []
        deadline = time.time() + timeout
        while time.time() < deadline:
            opcode, data = sock.recv()
            if opcode == 0x8:
                break
            if opcode == 0x2 and len(data) > 2:
                head_len = struct.unpack(">H", data[:2])[0]
                header = data[2:2 + head_len].decode("utf-8", "ignore")
                if "Path:audio" in header:
                    chunks.append(data[2 + head_len:])
            elif opcode == 0x1 and b"Path:turn.end" in data:
                break
        audio = b"".join(chunks)
        return audio if len(audio) > 1000 else None
    except Exception:  # noqa: BLE001
        return None
    finally:
        if sock is not None:
            sock.close()


def available(timeout=8.0):
    """探活：能否连上服务（用于启动时决定是否启用在线音色）。"""
    data = synthesize("Hi", voice=DEFAULT_EN, timeout=timeout)
    return bool(data)


def list_voices():
    """返回精选音色清单 [(显示名, id, 语言, 说明)]。"""
    return list(VOICES)


if __name__ == "__main__":
    import sys
    print("voices:", len(VOICES))
    t0 = time.time()
    for name, vid, lang, _desc in VOICES[:2]:
        data = synthesize("The quick brown fox jumps over the lazy dog", voice=vid)
        print("%-22s %s" % (name, ("%d bytes" % len(data)) if data else "FAILED"))
    print("elapsed %.1fs" % (time.time() - t0))
    sys.exit(0)
