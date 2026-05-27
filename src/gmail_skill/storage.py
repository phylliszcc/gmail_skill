"""Local archive: SQLite + .eml + Markdown."""
import sqlite3
import base64
from pathlib import Path

DATA_DIR = Path.home() / "data" / "gmail"
MESSAGES_DIR = DATA_DIR / "messages"
MARKDOWNS_DIR = DATA_DIR / "markdowns"
DB_PATH = DATA_DIR / "gmail.db"


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MESSAGES_DIR.mkdir(exist_ok=True)
    MARKDOWNS_DIR.mkdir(exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id       TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                subject  TEXT,
                sender   TEXT,
                recipients TEXT,
                date     TEXT,
                snippet  TEXT,
                labels   TEXT,
                has_eml  INTEGER DEFAULT 0,
                has_md   INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_thread ON messages(thread_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_date   ON messages(date)")
        conn.commit()


def save_message_meta(msg: dict):
    headers = {
        h["name"].lower(): h["value"]
        for h in msg.get("payload", {}).get("headers", [])
    }
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO messages
                (id, thread_id, subject, sender, recipients, date, snippet, labels)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                msg["id"],
                msg["threadId"],
                headers.get("subject", ""),
                headers.get("from", ""),
                headers.get("to", ""),
                headers.get("date", ""),
                msg.get("snippet", ""),
                ",".join(msg.get("labelIds", [])),
            ),
        )
        conn.commit()


def save_eml(msg_id: str, raw_bytes: bytes):
    (MESSAGES_DIR / f"{msg_id}.eml").write_bytes(raw_bytes)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE messages SET has_eml = 1 WHERE id = ?", (msg_id,))
        conn.commit()


def save_markdown(msg_id: str, subject: str, sender: str, date: str, body: str) -> Path:
    md = (
        f"---\nid: {msg_id}\nsubject: {subject}\nfrom: {sender}\ndate: {date}\n---\n\n"
        f"# {subject}\n\n**From:** {sender}  \n**Date:** {date}\n\n---\n\n{body}"
    )
    path = MARKDOWNS_DIR / f"{msg_id}.md"
    path.write_text(md, encoding="utf-8")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE messages SET has_md = 1 WHERE id = ?", (msg_id,))
        conn.commit()
    return path


def search_local(query: str, limit: int = 20) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        like = f"%{query}%"
        rows = conn.execute(
            """
            SELECT id, thread_id, subject, sender, date, snippet
            FROM messages
            WHERE subject LIKE ? OR sender LIKE ? OR snippet LIKE ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (like, like, like, limit),
        ).fetchall()
    return [dict(r) for r in rows]
