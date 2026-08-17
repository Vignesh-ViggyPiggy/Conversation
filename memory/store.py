import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("MEMORY_DB_PATH", Path(__file__).parent.parent / "memory.db"))


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    return conn


def add_fact(character: str, text: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO facts (character, text, created_at) VALUES (?, ?, ?)",
            (character, text, datetime.now(timezone.utc).isoformat()),
        )


def get_facts(character: str) -> list[str]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT text FROM facts WHERE character = ? ORDER BY id", (character,)
        ).fetchall()
    return [row[0] for row in rows]


def format_facts(facts: list[str]) -> str:
    if not facts:
        return ""
    lines = "\n".join(f"- {fact}" for fact in facts)
    return f"What you remember about this user from past conversations:\n{lines}"
