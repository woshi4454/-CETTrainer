# -*- coding: utf-8 -*-
"""题库导入解析器

把用户从别处复制来的纯文本，解析成程序内部使用的数据结构。
解析尽可能宽容：中英文标点、空行、多余空格、全角符号都能容忍。

支持五类：
  reading     阅读理解   —— 「## 文章」「## 题目」两段
  cloze       选词填空   —— 「## 词库」「## 文章」「## 答案」三段
  translate   翻译       —— 一行一题：中文 | 译文
  vocab       词汇       —— 一行一词：单词 | 音标 | 词性 | 释义 [| 例句 | 例句翻译]
  sentences   听写句子   —— 一行一句：句子 | 译文 | 难度
"""

import re

KIND_LABELS = {
    "reading": "阅读理解",
    "cloze": "选词填空",
    "translate": "翻译",
    "vocab": "词汇",
    "sentences": "听写句子",
}

# ---------------------------------------------------------------- 通用工具

_OPT_PREFIX = re.compile(r"^\s*[\(\[]?([A-Za-z])[\)\].、:：\s]\s*")
_ANS_LINE = re.compile(r"^\s*(?:答案|正确答案|answer)\s*[:：]\s*(.+?)\s*$", re.I)
_EXP_LINE = re.compile(r"^\s*(?:解析|分析|explain)\s*[:：]\s*(.+?)\s*$", re.I)
_NUM_LINE = re.compile(r"^\s*(\d{1,3})\s*[\.、\):：]\s*(.*)$")
_SEC_HEAD = re.compile(r"^\s*#{1,6}\s*(.+?)\s*$")


def _norm(s):
    """全角转半角、去掉零宽字符和首尾空白。"""
    if s is None:
        return ""
    s = str(s)
    trans = {"\u3000": " ", "\u00a0": " ", "\ufeff": "", "\u200b": ""}
    for k, v in trans.items():
        s = s.replace(k, v)
    return s.strip()


def _section(text):
    """把文本按 '## 标题' 切分成 {小标题: 内容}。

    若没有 '##' 标题，则返回 {"": 全文}。
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = {}
    cur = ""
    buf = []
    for ln in lines:
        m = _SEC_HEAD.match(ln)
        if m:
            if cur or any(x.strip() for x in buf):
                out.setdefault(cur, []).extend(buf)
            cur = m.group(1).strip()
            buf = []
        else:
            buf.append(ln)
    out.setdefault(cur, []).extend(buf)
    return {k: "\n".join(v).strip() for k, v in out.items() if k or any(x.strip() for x in v)}


def _pick_section(secs, *keywords):
    """按关键词找小节：'文章' 'passage' 都能匹配到 '## 文章' 或 '## Passage'。"""
    for key in secs:
        low = key.lower()
        for kw in keywords:
            if kw.lower() in low:
                return secs[key]
    return ""


def _title_of(text, default=""):
    """取第一个 '#' 或 '##' 里的内容当标题；也支持 '标题：xxx'。"""
    for ln in text.replace("\r\n", "\n").split("\n")[:8]:
        m = re.match(r"^\s*标题\s*[:：]\s*(.+)$", ln)
        if m:
            return _norm(m.group(1))
    m = re.search(r"^\s*#\s+(.+)$", text, re.M)
    if m:
        t = _norm(m.group(1))
        t = re.sub(r"^(?:阅读理解|选词填空|翻译|词汇|听写句子)\s*[:：]\s*", "", t)
        if t:
            return t
    return default


# ---------------------------------------------------------------- 阅读理解

def parse_reading(text):
    """解析阅读理解。返回 [{"title","passage","questions":[...]}]"""
    text = (text or "").replace("\r\n", "\n")
    if not text.strip():
        return []

    # 按「1. 题干」切题目块
    title = _title_of(text, "导入阅读")
    body = re.sub(r"^\s*#\s+.+$", "", text, count=1, flags=re.M)

    # 找出所有题号位置
    lines = body.split("\n")
    q_starts = []
    for i, ln in enumerate(lines):
        m = _NUM_LINE.match(ln)
        if m and m.group(2).strip():
            # 题干行后面通常紧跟 A. 选项；简单判断：该行不像选项行
            if not _OPT_PREFIX.match(m.group(2)):
                q_starts.append((i, int(m.group(1)), m.group(2).strip()))

    # 文章 = 题目开始之前的全部内容（去掉 "## 文章" 之类的标题行）
    if q_starts:
        first = q_starts[0][0]
        passage_lines = []
        for ln in lines[:first]:
            if _SEC_HEAD.match(ln):
                continue
            passage_lines.append(ln)
        passage = "\n".join(passage_lines).strip()
    else:
        passage = _pick_section(_section(body), "文章", "passage")
        if not passage:
            passage = body.strip()

    questions = []
    for k, (start, num, stem) in enumerate(q_starts):
        end = q_starts[k + 1][0] if k + 1 < len(q_starts) else len(lines)
        block = lines[start + 1:end]

        opts = []
        answer = ""
        explain_parts = []
        stem_extra = []
        for ln in block:
            s = ln.strip()
            if not s:
                continue
            m_ans = _ANS_LINE.match(s)
            if m_ans:
                answer = _norm(m_ans.group(1)).upper()[:1]
                continue
            m_exp = _EXP_LINE.match(s)
            if m_exp:
                explain_parts.append(_norm(m_exp.group(1)))
                continue
            m_opt = re.match(r"^\s*[\(\[]?([A-Da-d])[\)\].、:：\s]\s*(.*)$", s)
            if m_opt and len(m_opt.group(2).strip()) > 0:
                opts.append(f"{m_opt.group(1).upper()}. {_norm(m_opt.group(2))}")
                continue
            if _SEC_HEAD.match(s):
                continue
            if not opts and not answer:
                stem_extra.append(s)
            else:
                explain_parts.append(s)

        q_text = _norm(" ".join([stem] + stem_extra))
        if not q_text:
            continue
        # 没写答案时不收录（无法判分）
        if not answer:
            continue
        questions.append({
            "q": q_text,
            "options": opts if opts else ["A. ", "B. ", "C. ", "D. "],
            "answer": answer,
            "explain": " ".join(explain_parts) or "（导入题目未附解析）",
        })

    if not questions:
        return []
    return [{"title": title, "passage": passage, "questions": questions}]


# ---------------------------------------------------------------- 选词填空

def parse_cloze(text):
    """解析选词填空。返回 [{"title","text","blanks":[(答案,选项,解析)]}]"""
    text = (text or "").replace("\r\n", "\n")
    if not text.strip():
        return []

    title = _title_of(text, "导入选词填空")
    secs = _section(text)

    bank_raw = _pick_section(secs, "词库", "选项", "bank")
    passage = _pick_section(secs, "文章", "passage", "正文")
    ans_raw = _pick_section(secs, "答案", "answer", "解析")

    # 没有小标题时，尝试「全文当文章 + 词库在末尾」
    if not passage:
        body = re.sub(r"^\s*#\s+.+$", "", text, count=1, flags=re.M)
        passage = body.strip()

    # 词库：优先识别 "A. abandon" 这种带字母的写法，建立 字母→单词 映射
    letter_map = {}
    for ln in bank_raw.split("\n"):
        for m in re.finditer(r"(?:^|[\s,，、;；])\(?([A-Z])\)?\s*[\.、\):：]\s*([A-Za-z][A-Za-z'\-]{0,23})", ln):
            letter = m.group(1)
            word = m.group(2)
            if letter not in letter_map:
                letter_map[letter] = word

    pool = []
    for tok in re.split(r"[\s,，、;；]+", bank_raw):
        t = _norm(tok)
        t = _OPT_PREFIX.sub("", t).strip()
        t = t.strip(".")
        if not t:
            continue
        if re.fullmatch(r"[A-Za-z]", t):      # 单独的字母，不是单词
            continue
        if _ANS_LINE.match(t) or len(t) > 24:
            continue
        if t not in pool:
            pool.append(t)
    if not pool and letter_map:
        pool = list(dict.fromkeys(letter_map.values()))
    if not pool:
        # 从文章里找 ___N___ 数量，无法猜词库
        return []

    # 答案：每行「1. word  解析」
    answers = {}
    for ln in ans_raw.split("\n"):
        s = ln.strip()
        if not s:
            continue
        m = _NUM_LINE.match(s)
        if m:
            idx = int(m.group(1))
            rest = _norm(m.group(2))
            parts = re.split(r"\s{2,}|[；;]", rest, maxsplit=1)
            word = _norm(parts[0]).strip(" .。")
            exp = _norm(parts[1]) if len(parts) > 1 else ""
            answers[idx] = (word, exp)
        else:
            m2 = re.match(r"^\s*[\(\[〔]?(\d{1,2})[\)\]〕\.、:：]?\s*[:：=]?\s*(.+)$", s)
            if m2:
                idx = int(m2.group(1))
                answers[idx] = (_norm(m2.group(2)).strip(" .。"), "")

    # 正文里的空位 ___1___ / （1） / [1]
    slots = [int(x) for x in re.findall(r"___(\d+)___", passage)]
    if not slots:
        slots = [int(x) for x in re.findall(r"[\(\[（【〔](\d{1,2})[\)\]）】〕]", passage)]
        if slots:
            for n in sorted(set(slots)):
                passage = re.sub(r"[\(\[（【〔]%d[\)\]）】〕]" % n, f"___{n}___", passage)
    if not slots:
        return []
    slots = sorted(set(slots))

    blanks = []
    for n in slots:
        if n in answers:
            word, exp = answers[n]
            # 答案写成字母（如 "D"）时，映射回词库里的单词
            if re.fullmatch(r"[A-Za-z]", word or ""):
                word = letter_map.get(word.upper(), word)
        else:
            word, exp = "", "（导入题目未提供该空答案）"
        blanks.append((word, list(pool), exp))

    if not any(b[0] for b in blanks):
        return []
    return [{"title": title, "text": passage, "blanks": blanks}]


# ---------------------------------------------------------------- 翻译

def parse_translate(text):
    """一行一题：中文 | 参考译文 [| 难度]"""
    out = []
    for ln in (text or "").replace("\r\n", "\n").split("\n"):
        s = _norm(ln)
        if not s or s.startswith("#") or s.startswith("//"):
            continue
        parts = [p.strip() for p in re.split(r"\s*[|｜]\s*", s)]
        parts = [p for p in parts if p]
        if len(parts) < 2:
            continue
        diff = 2
        if len(parts) >= 3:
            m = re.search(r"[123]", parts[2])
            if m:
                diff = int(m.group(0))
        out.append((parts[0], parts[1], diff))
    return out


# ---------------------------------------------------------------- 词汇

def parse_vocab(text, level="CET4"):
    """一行一词：单词 | 音标 | 词性 | 释义 [| 例句 | 例句翻译]"""
    out = []
    for ln in (text or "").replace("\r\n", "\n").split("\n"):
        s = _norm(ln)
        if not s or s.startswith("#") or s.startswith("//"):
            continue
        parts = [p.strip() for p in re.split(r"\s*[|｜]\s*", s)]
        parts = [p for p in parts]
        if not parts or not re.match(r"^[A-Za-z][A-Za-z\-' ]*$", parts[0]):
            continue
        word = parts[0]
        phon = parts[1] if len(parts) > 1 else ""
        pos = parts[2] if len(parts) > 2 else ""
        mean = parts[3] if len(parts) > 3 else ""
        ex = parts[4] if len(parts) > 4 else ""
        ex_cn = parts[5] if len(parts) > 5 else ""
        if not mean:
            continue
        out.append((word, phon, pos, mean, ex, ex_cn))
    return out


# ---------------------------------------------------------------- 听写句子

def parse_sentences(text):
    """一行一句：句子 | 译文 [| 难度 1-3] [| 主题]"""
    out = []
    for ln in (text or "").replace("\r\n", "\n").split("\n"):
        s = _norm(ln)
        if not s or s.startswith("#") or s.startswith("//"):
            continue
        parts = [p.strip() for p in re.split(r"\s*[|｜]\s*", s)]
        parts = [p for p in parts if p]
        if len(parts) < 2:
            continue
        diff = 2
        theme = "导入"
        if len(parts) >= 3:
            m = re.search(r"[123]", parts[2])
            if m:
                diff = int(m.group(0))
        if len(parts) >= 4:
            theme = parts[3] or "导入"
        if not re.search(r"[A-Za-z]", parts[0]):
            continue
        out.append((parts[0], parts[1], diff, theme))
    return out


# ---------------------------------------------------------------- 总入口

def parse_all(kind, text, level="CET4"):
    """返回 (ok, items_or_error_message)"""
    if kind == "reading":
        items = parse_reading(text)
        if not items:
            return False, "没解析出题目。检查是否有「1. 题干 / A. 选项 / 答案：X」这样的结构。"
        return True, items

    if kind == "cloze":
        items = parse_cloze(text)
        if not items:
            return False, "没解析出填空。检查是否有「## 词库」「## 文章」（含 ___1___ 空位）「## 答案」。"
        return True, items

    if kind == "translate":
        items = parse_translate(text)
        if not items:
            return False, "没解析出翻译题。每行格式：中文原句 | 参考译文"
        return True, items

    if kind == "vocab":
        items = parse_vocab(text, level)
        if not items:
            return False, "没解析出单词。每行格式：单词 | 音标 | 词性 | 中文释义"
        return True, items

    if kind == "sentences":
        items = parse_sentences(text)
        if not items:
            return False, "没解析出句子。每行格式：英文句子 | 参考译文"
        return True, items

    return False, "不支持的类型"


TEMPLATES = {
    "reading": """# 2024年6月四级阅读（示例标题可改）
## 文章
The passage text goes here. Copy the whole article here, line breaks are fine.

## 题目
1. What is the main idea of the passage?
A. option one
B. option two
C. option three
D. option four
答案：A
解析：第一段明确说了……

2. According to the passage, why ...?
A. ...
B. ...
C. ...
D. ...
答案：C
解析：……
""",
    "cloze": """# 2024年6月四级选词填空
## 词库
A. abandon B. absorb C. balance D. capacity E. decline
F. effective G. factor H. generate I. impact J. maintain
K. obvious L. potential M. reduce N. species O. tradition

## 文章
The text with blanks goes here. Replace each gap with ___1___ ___2___ ...
There are usually 10 blanks: ___1___ ___2___ ___3___ ___4___ ___5___ ___6___ ___7___ ___8___ ___9___ ___10___

## 答案
1. D  形容词，修饰 capacity
2. F  固定搭配
3. J
4. C
5. A
6. K
7. I
8. M
9. G
10. O
""",
    "translate": """# 一行一题，格式：中文原句 | 参考译文 | 难度(1-3，可省)
中国的传统节日承载着丰富的文化内涵。 | Traditional Chinese festivals carry rich cultural connotations. | 2
越来越多的人开始重视环境保护。 | More and more people are beginning to attach importance to environmental protection. | 1
""",
    "vocab": """# 一行一词，格式：单词 | 音标 | 词性 | 中文释义 | 例句(可省) | 例句翻译(可省)
abandon | /əˈbændən/ | v. | 放弃；抛弃 | He abandoned the plan. | 他放弃了这个计划。
absorb | /əbˈsɔːb/ | v. | 吸收；理解 | Plants absorb water. | 植物吸收水分。
""",
    "sentences": """# 一行一句，格式：英文句子 | 参考译文 | 难度(1-3，可省) | 主题(可省)
The conference was postponed because of the heavy rain. | 会议因大雨推迟。 | 2 | 校园
I would like to apply for the position advertised on your website. | 我想申请你们网站上招聘的职位。 | 2 | 求职
""",
}
