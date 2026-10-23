# -*- coding: utf-8 -*-
"""本地进度存储（SQLite）

存储位置优先放在 exe/脚本同目录的 data 子目录；不可写时退回用户 AppData。
"""

import json
import os
import sqlite3
import sys
import time


def _app_dir():
    """程序所在目录（兼容 PyInstaller 单文件模式）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _data_dir():
    base = _app_dir()
    d = os.path.join(base, "cet_data")
    try:
        os.makedirs(d, exist_ok=True)
        probe = os.path.join(d, ".write_test")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return d
    except OSError:
        alt = os.path.join(os.environ.get("LOCALAPPDATA", base), "CETTrainer")
        os.makedirs(alt, exist_ok=True)
        return alt


DB_PATH = os.path.join(_data_dir(), "progress.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS vocab_progress (
    word        TEXT PRIMARY KEY,
    level       TEXT NOT NULL,
    seen        INTEGER NOT NULL DEFAULT 0,
    correct     INTEGER NOT NULL DEFAULT 0,
    wrong       INTEGER NOT NULL DEFAULT 0,
    last_seen   INTEGER NOT NULL DEFAULT 0,
    mastered    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dict_progress (
    sentence    TEXT PRIMARY KEY,
    seen        INTEGER NOT NULL DEFAULT 0,
    perfect     INTEGER NOT NULL DEFAULT 0,
    accuracy    REAL NOT NULL DEFAULT 0,
    last_seen   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS exam_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,
    title       TEXT NOT NULL,
    score       REAL NOT NULL,
    total       REAL NOT NULL,
    detail      TEXT,
    created_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT
);

CREATE TABLE IF NOT EXISTS user_content (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,
    title       TEXT NOT NULL,
    level       TEXT,
    source      TEXT,
    data        TEXT NOT NULL,
    created_at  INTEGER NOT NULL,
    UNIQUE(kind, title)
);

CREATE TABLE IF NOT EXISTS wordbook (
    word        TEXT PRIMARY KEY,
    level       TEXT,
    note        TEXT,
    data        TEXT,
    added_at    INTEGER NOT NULL,
    reviews     INTEGER NOT NULL DEFAULT 0,
    correct     INTEGER NOT NULL DEFAULT 0,
    wrong       INTEGER NOT NULL DEFAULT 0,
    last_review INTEGER NOT NULL DEFAULT 0
);

-- 数据包带来的词条（扩充词库），与内置词表合并使用
CREATE TABLE IF NOT EXISTS pack_vocab (
    level       TEXT NOT NULL,
    word        TEXT NOT NULL,
    phon        TEXT NOT NULL DEFAULT '',
    pos         TEXT NOT NULL DEFAULT '',
    mean        TEXT NOT NULL DEFAULT '',
    example     TEXT NOT NULL DEFAULT '',
    example_cn  TEXT NOT NULL DEFAULT '',
    PRIMARY KEY(level, word)
);

-- 答题记录：每道题的完成情况（界面上的序号与完成标记靠它）
CREATE TABLE IF NOT EXISTS question_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,
    item_key    TEXT NOT NULL,
    q_index     INTEGER NOT NULL,
    answer      TEXT,
    correct     INTEGER NOT NULL DEFAULT 0,
    attempts    INTEGER NOT NULL DEFAULT 1,
    created_at  INTEGER NOT NULL,
    standard    TEXT,
    explain     TEXT,
    UNIQUE(kind, item_key, q_index)
);
"""


class Store:
    def __init__(self, db_path=None):
        self.path = db_path or DB_PATH
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self._migrate()
        self.conn.commit()

    # ---------- 设置 ----------
    def get_setting(self, key, default=None):
        cur = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )
        self.conn.commit()

    # ---------- 词汇 ----------
    def record_word(self, word, level, correct):
        now = int(time.time())
        self.conn.execute(
            "INSERT INTO vocab_progress(word, level, seen, correct, wrong, last_seen, mastered) "
            "VALUES(?, ?, 1, ?, ?, ?, 0) "
            "ON CONFLICT(word) DO UPDATE SET "
            "  seen = seen + 1, "
            "  correct = correct + ?, "
            "  wrong = wrong + ?, "
            "  last_seen = ?, "
            "  mastered = CASE WHEN (correct + ?) >= 3 THEN 1 ELSE mastered END",
            (word, level, 1 if correct else 0, 0 if correct else 1, now,
             1 if correct else 0, 0 if correct else 1, now, 1 if correct else 0),
        )
        self.conn.commit()

    def word_stats(self, level=None):
        if level:
            cur = self.conn.execute(
                "SELECT COUNT(*) c, SUM(mastered) m, SUM(seen) s FROM vocab_progress WHERE level=?",
                (level,),
            )
        else:
            cur = self.conn.execute(
                "SELECT COUNT(*) c, SUM(mastered) m, SUM(seen) s FROM vocab_progress"
            )
        row = cur.fetchone()
        return {
            "touched": row["c"] or 0,
            "mastered": row["m"] or 0,
            "reviews": row["s"] or 0,
        }

    def weak_words(self, level=None, limit=30):
        sql = ("SELECT word, level, correct, wrong FROM vocab_progress "
               "WHERE wrong > 0 AND mastered = 0 ")
        args = []
        if level:
            sql += "AND level = ? "
            args.append(level)
        sql += "ORDER BY (wrong * 1.0 / (seen + 1)) DESC, wrong DESC LIMIT ?"
        args.append(limit)
        rows = [dict(r) for r in self.conn.execute(sql, args).fetchall()]
        # 单词本复习记下的记录可能没有等级，用 wordbook 里的等级补上，方便显示
        for r in rows:
            if not r.get("level"):
                hit = self.conn.execute("SELECT level FROM wordbook WHERE word=?",
                                        (r["word"],)).fetchone()
                r["level"] = (hit["level"] if hit else "") or ""
        return rows

    # ---------- 听写 ----------
    def record_dictation(self, sentence, accuracy):
        now = int(time.time())
        perfect = 1 if accuracy >= 99.5 else 0
        self.conn.execute(
            "INSERT INTO dict_progress(sentence, seen, perfect, accuracy, last_seen) "
            "VALUES(?, 1, ?, ?, ?) "
            "ON CONFLICT(sentence) DO UPDATE SET "
            "  seen = seen + 1, perfect = perfect + ?, "
            "  accuracy = MAX(accuracy, ?), last_seen = ?",
            (sentence, perfect, accuracy, now, perfect, accuracy, now),
        )
        self.conn.commit()

    def dict_stats(self):
        row = self.conn.execute(
            "SELECT COUNT(*) c, SUM(perfect) p, AVG(accuracy) a FROM dict_progress"
        ).fetchone()
        return {
            "touched": row["c"] or 0,
            "perfect": row["p"] or 0,
            "avg_accuracy": round(row["a"] or 0, 1),
        }

    # ---------- 考试记录 ----------
    def add_exam(self, kind, title, score, total, detail=""):
        self.conn.execute(
            "INSERT INTO exam_history(kind, title, score, total, detail, created_at) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            (kind, title, score, total, detail, int(time.time())),
        )
        self.conn.commit()

    def last_exam(self, kind, title):
        row = self.conn.execute(
            "SELECT * FROM exam_history WHERE kind=? AND title=? "
            "ORDER BY created_at DESC LIMIT 1", (kind, title)).fetchone()
        return dict(row) if row else None

    def exam_best(self, kind):
        """该类型的最好成绩（按得分率），没有记录返回 None。"""
        row = self.conn.execute(
            "SELECT * FROM exam_history WHERE kind=? AND total>0 "
            "ORDER BY CAST(score AS REAL)/total DESC, created_at DESC LIMIT 1",
            (kind,)).fetchone()
        return dict(row) if row else None

    def exam_history(self, limit=50):
        rows = self.conn.execute(
            "SELECT * FROM exam_history ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ---------- 用户导入的题库 ----------
    def add_user_content(self, kind, title, data, level="", source=""):
        """保存一条导入内容；同 kind+title 覆盖（返回 True 表示新增，False 表示覆盖）。"""
        cur = self.conn.execute("SELECT id FROM user_content WHERE kind=? AND title=?",
                                (kind, title))
        old = cur.fetchone()
        self.conn.execute(
            "INSERT INTO user_content(kind, title, level, source, data, created_at) "
            "VALUES(?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(kind, title) DO UPDATE SET "
            "  level=excluded.level, source=excluded.source, "
            "  data=excluded.data, created_at=excluded.created_at",
            (kind, title, level or "", source or "",
             json.dumps(data, ensure_ascii=False), int(time.time())),
        )
        self.conn.commit()
        return old is None

    def user_content(self, kind, level=None):
        """取某类的全部导入内容，按导入时间倒序。"""
        sql = "SELECT * FROM user_content WHERE kind=?"
        args = [kind]
        if level:
            sql += " AND (level=? OR level='' OR level IS NULL)"
            args.append(level)
        sql += " ORDER BY created_at DESC, id DESC"
        rows = self.conn.execute(sql, args).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["data"] = json.loads(d["data"])
            except (ValueError, TypeError):
                continue
            out.append(d)
        return out

    def user_content_count(self):
        rows = self.conn.execute(
            "SELECT kind, COUNT(*) c FROM user_content GROUP BY kind").fetchall()
        return {r["kind"]: r["c"] for r in rows}

    def drop_pack_content(self):
        """清掉上一次数据包导入的题（重复导入新包前调用，避免残留过期题）。"""
        rows = self.conn.execute(
            "SELECT key FROM settings WHERE key LIKE 'pack_title:%'").fetchall()
        for r in rows:
            parts = r["key"].split(":", 2)
            if len(parts) < 3:
                continue
            kind, title = parts[1], parts[2]
            self.conn.execute("DELETE FROM user_content WHERE kind=? AND title=?",
                              (kind, title))
        self.conn.execute("DELETE FROM settings WHERE key LIKE 'pack_title:%'")
        self.conn.commit()

    def delete_user_content(self, cid):
        self.conn.execute("DELETE FROM user_content WHERE id=?", (cid,))
        self.conn.commit()

    # ---------- 单词本（收藏） ----------
    def add_wordbook(self, word, level="", data=None, note=""):
        """收藏一个单词。已存在则更新释义快照，返回 True 表示新收藏。"""
        word = (word or "").strip()
        if not word:
            return False
        old = self.conn.execute("SELECT word FROM wordbook WHERE word=?", (word,)).fetchone()
        payload = json.dumps(data, ensure_ascii=False) if data else None
        now = int(time.time())
        if old:
            self.conn.execute(
                "UPDATE wordbook SET level=?, note=?, data=CASE WHEN ? IS NULL THEN data ELSE ? END "
                "WHERE word=?",
                (level or "", note or "", payload, payload, word),
            )
            self.conn.commit()
            return False
        self.conn.execute(
            "INSERT INTO wordbook(word, level, note, data, added_at) VALUES(?, ?, ?, ?, ?)",
            (word, level or "", note or "", payload, now),
        )
        self.conn.commit()
        return True

    def remove_wordbook(self, word):
        self.conn.execute("DELETE FROM wordbook WHERE word=?", (word,))
        self.conn.commit()

    def in_wordbook(self, word):
        row = self.conn.execute("SELECT 1 FROM wordbook WHERE word=?", (word,)).fetchone()
        return row is not None

    def wordbook(self, level=None, order="added", limit=None):
        sql = "SELECT * FROM wordbook"
        args = []
        if level:
            sql += " WHERE level=?"
            args.append(level)
        if order == "wrong":
            sql += " ORDER BY (wrong * 1.0 / (reviews + 1)) DESC, wrong DESC, added_at DESC"
        elif order == "alpha":
            sql += " ORDER BY LOWER(word) ASC"
        else:
            sql += " ORDER BY added_at DESC, word ASC"
        if limit:
            sql += " LIMIT ?"
            args.append(int(limit))
        out = []
        for r in self.conn.execute(sql, args).fetchall():
            d = dict(r)
            try:
                d["data"] = json.loads(d["data"]) if d["data"] else None
            except (ValueError, TypeError):
                d["data"] = None
            out.append(d)
        return out

    def wordbook_count(self):
        rows = self.conn.execute(
            "SELECT level, COUNT(*) c FROM wordbook GROUP BY level").fetchall()
        return {r["level"] or "": r["c"] for r in rows}

    def record_wordbook_review(self, word, correct):
        self.conn.execute(
            "UPDATE wordbook SET reviews = reviews + 1, correct = correct + ?, "
            "wrong = wrong + ?, last_review = ? WHERE word=?",
            (1 if correct else 0, 0 if correct else 1, int(time.time()), word),
        )
        self.conn.commit()
        # 同步记入总体词汇进度，学习统计/错词本才能反映
        row = self.conn.execute("SELECT level FROM wordbook WHERE word=?", (word,)).fetchone()
        self.record_word(word, (row["level"] if row else "") or "", correct)

    # ---------- 数据包词条 ----------
    def bulk_vocab(self, level, rows):
        """整批写入某等级的词条（覆盖该等级旧数据）。rows: [[词,音标,词性,释义,例句,例句中文], ...]"""
        norm = []
        for r in rows:
            if not r:
                continue
            r = list(r) + [""] * 6
            word = (r[0] or "").strip()
            if not word:
                continue
            norm.append((level, word, r[1] or "", r[2] or "", r[3] or "",
                         r[4] or "", r[5] or ""))
        self.conn.execute("DELETE FROM pack_vocab WHERE level=?", (level,))
        self.conn.executemany(
            "INSERT OR REPLACE INTO pack_vocab"
            "(level, word, phon, pos, mean, example, example_cn) VALUES(?,?,?,?,?,?,?)",
            norm,
        )
        self.conn.commit()
        return len(norm)

    def pack_vocab(self, level):
        """取某等级的数据包词条，格式同内置词表元组。"""
        rows = self.conn.execute(
            "SELECT word, phon, pos, mean, example, example_cn FROM pack_vocab "
            "WHERE level=? ORDER BY word",
            (level,),
        ).fetchall()
        return [(r["word"], r["phon"], r["pos"], r["mean"], r["example"], r["example_cn"])
                for r in rows]

    def pack_vocab_count(self):
        rows = self.conn.execute(
            "SELECT level, COUNT(*) c FROM pack_vocab GROUP BY level").fetchall()
        return {r["level"]: r["c"] for r in rows}

    def mark_pack_title(self, kind, title, level=""):
        """记录某条内容是数据包带来的（便于统计与替换）。"""
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (f"pack_title:{kind}:{title}", level or ""),
        )
        self.conn.commit()

    # ---------- 逐题完成情况 ----------
    def record_question(self, kind, item_key, q_index, answer, correct):
        """记一道题的答题结果：同一题重复作答只累加次数，保存最新答案。"""
        now = int(time.time())
        self.conn.execute(
            "INSERT INTO question_log(kind, item_key, q_index, answer, correct, attempts, created_at) "
            "VALUES(?, ?, ?, ?, ?, 1, ?) "
            "ON CONFLICT(kind, item_key, q_index) DO UPDATE SET "
            "  answer=?2, correct=?3, attempts=attempts + 1",
            (kind, item_key, q_index, answer, 1 if correct else 0, now),
        )
        self.conn.commit()

    def log_question(self, kind, item_key, q_index, answer, correct,
                     standard="", explain=""):
        """逐题记录（带标准答案和解析），页面直接拿来渲染完成情况与批改。"""
        now = int(time.time())
        self.conn.execute(
            "INSERT INTO question_log(kind, item_key, q_index, answer, correct, attempts, "
            "standard, explain, created_at) VALUES(?, ?, ?, ?, ?, 1, ?, ?, ?) "
            "ON CONFLICT(kind, item_key, q_index) DO UPDATE SET "
            "  answer=?4, correct=?5, attempts=attempts + 1, "
            "  standard=?6, explain=?7, created_at=?8",
            (kind, item_key, q_index, answer, 1 if correct else 0,
             (standard or "")[:200],
             # 解析截得太短会丢知识点说明，这里放宽到 1500 字
             (explain or "")[:1500], now),
        )
        self.conn.commit()

    def question_log_full(self, kind, item_key):
        """{题号: {got, correct, answer(标准答案), explain}}"""
        rows = self.conn.execute(
            "SELECT q_index, answer, correct, standard, explain FROM question_log "
            "WHERE kind=? AND item_key=?", (kind, item_key)).fetchall()
        out = {}
        for r in rows:
            out[r["q_index"]] = {
                "got": r["answer"] or "",
                "correct": bool(r["correct"]),
                "answer": (r["standard"] or ""),
                "explain": (r["explain"] or ""),
            }
        return out

    def question_log(self, kind, item_key):
        """{题号: {answer, correct, attempts, at}}"""
        rows = self.conn.execute(
            "SELECT q_index, answer, correct, attempts, created_at FROM question_log "
            "WHERE kind=? AND item_key=?",
            (kind, item_key),
        ).fetchall()
        return {
            r["q_index"]: {
                "answer": r["answer"] or "",
                "correct": bool(r["correct"]),
                "attempts": r["attempts"],
                "at": r["created_at"],
            }
            for r in rows
        }

    def done_stats(self, kind):
        """某类题整体完成情况：{items: 已做过的套数, questions: 题数, correct: 答对题数}"""
        row = self.conn.execute(
            "SELECT COUNT(DISTINCT item_key) items, COUNT(*) q, SUM(correct) c "
            "FROM question_log WHERE kind=?",
            (kind,),
        ).fetchone()
        return {"items": row["items"] or 0, "questions": row["q"] or 0,
                "correct": row["c"] or 0}

    def wrong_questions(self, kind=None, limit=300):
        """错题本数据：所有答错的题，按最近答题时间倒序。"""
        sql = ("SELECT kind, item_key, q_index, answer, correct, standard, explain, "
               "attempts, created_at FROM question_log WHERE correct=0")
        args = []
        if kind:
            sql += " AND kind=?"
            args.append(kind)
        sql += " ORDER BY created_at DESC LIMIT ?"
        args.append(int(limit))
        rows = self.conn.execute(sql, args).fetchall()
        return [dict(r) for r in rows]

    def wrong_stats(self):
        """错题统计：{kind: 错题数}"""
        rows = self.conn.execute(
            "SELECT kind, COUNT(*) c FROM question_log WHERE correct=0 GROUP BY kind"
        ).fetchall()
        return {r["kind"]: r["c"] for r in rows}

    def mark_question_fixed(self, kind, item_key, q_index):
        """错题本里手动标记「已掌握」：把它从错题里摘掉（correct 置 1）。"""
        self.conn.execute(
            "UPDATE question_log SET correct=1 WHERE kind=? AND item_key=? AND q_index=?",
            (kind, item_key, q_index))
        self.conn.commit()

    def clear_question_log(self, kind, item_key=None):
        if item_key:
            self.conn.execute("DELETE FROM question_log WHERE kind=? AND item_key=?",
                              (kind, item_key))
        else:
            self.conn.execute("DELETE FROM question_log WHERE kind=?", (kind,))
        self.conn.commit()

    def _migrate(self):
        """老版本数据库缺列时自动补上，不动用户已有数据。"""
        cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(question_log)")}
        for name, decl in (("standard", "TEXT"), ("explain", "TEXT")):
            if name not in cols:
                self.conn.execute(f"ALTER TABLE question_log ADD COLUMN {name} {decl}")
        self.conn.commit()

    def close(self):
        try:
            self.conn.close()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    s = Store()
    print("db:", s.path)
    s.record_word("abandon", "CET4", True)
    s.record_word("abandon", "CET4", False)
    s.record_dictation("Hello world.", 88.5)
    s.add_exam("reading", "测试", 3, 5, "demo")
    print("word:", s.word_stats("CET4"))
    print("dict:", s.dict_stats())
    print("exam:", s.exam_history(3))
    print("weak:", s.weak_words("CET4", 3))
    s.close()
