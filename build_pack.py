# -*- coding: utf-8 -*-
"""把 data_*.py 素材汇成 cet_pack.json（程序启动时由 cetpack 导入本地库）。

运行：  python build_pack.py
产物：  ./cet_pack.json

说明：原始素材以元组形式写在各 data_*.py 里；本脚本把它们读出来，
拼成 cetpack.import_pack 约定的数据包格式（JSON）。json 不支持元组，
这里统一转成列表。
"""

import json
import os

import data_vocab
import data_phrases
import data_sentences
import data_extra
import data_gaokao


def to_list(x):
    if isinstance(x, tuple):
        return [to_list(i) for i in x]
    if isinstance(x, list):
        return [to_list(i) for i in x]
    if isinstance(x, dict):
        return {k: to_list(v) for k, v in x.items()}
    return x


def build():
    payload = {
        "version": "2024-11-v1",
        "vocab": {
            "CET4": to_list(data_vocab.CET4_WORDS),
            "CET6": to_list(data_vocab.CET6_WORDS),
            "GZ": to_list(data_gaokao.GAOKAO_WORDS),
        },
        "phrases": to_list(data_phrases.PHRASE_BANK),
        "reading": to_list(data_sentences.READING_PASSAGES)
                   + to_list(data_extra.EXTRA_READING),
        "cloze": to_list(data_sentences.CLOZE_PASSAGES)
                 + to_list(data_extra.EXTRA_CLOZE),
        "translate": to_list(data_sentences.TRANSLATIONS)
                     + to_list(data_extra.EXTRA_TRANSLATIONS),
        "sentences": to_list(data_sentences.SENTENCES)
                     + to_list(data_extra.EXTRA_SENTENCES),
    }
    return payload


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    payload = build()
    out = os.path.join(here, "cet_pack.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 统计
    vocab_n = sum(len(v) for v in payload["vocab"].values())
    print("已生成 cet_pack.json：")
    print(f"  词汇   : {vocab_n} 条（CET4 {len(payload['vocab']['CET4'])} / "
          f"CET6 {len(payload['vocab']['CET6'])} / GZ {len(payload['vocab']['GZ'])}）")
    print(f"  短语   : {len(payload['phrases'])} 条")
    print(f"  阅读   : {len(payload['reading'])} 篇")
    print(f"  选词   : {len(payload['cloze'])} 篇")
    print(f"  翻译   : {len(payload['translate'])} 条")
    print(f"  听写句 : {len(payload['sentences'])} 条")
    print(f"  文件大小: {os.path.getsize(out) // 1024} KB -> {out}")


if __name__ == "__main__":
    main()
