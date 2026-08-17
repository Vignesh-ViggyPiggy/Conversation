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
            session_id TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    return conn


def add_fact(character: str, session_id: str, text: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO facts (character, session_id, text, created_at) VALUES (?, ?, ?, ?)",
            (character, session_id, text, datetime.now(timezone.utc).isoformat()),
        )


def get_facts(character: str) -> list[str]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT text FROM facts WHERE character = ? ORDER BY id", (character,)
        ).fetchall()
    return [row[0] for row in rows]


def search_facts(character: str, query: str, k: int = 5) -> list[str]:
    """Up to k facts relevant to query, scored by word overlap. Facts with no
    overlapping words are excluded rather than injected as noise — same
    behavior as lore/retriever.py's tag matching."""
    facts = get_facts(character)
    if not facts:
        return []

    query_words = set(query.lower().split())
    scored = [(len(query_words & set(fact.lower().split())), fact) for fact in facts]
    scored = [pair for pair in scored if pair[0] > 0]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [fact for _, fact in scored[:k]]


def format_facts(facts: list[str]) -> str:
    if not facts:
        return ""
    lines = "\n".join(f"- {fact}" for fact in facts)
    return f"What you remember about this user from past conversations:\n{lines}"


def list_sessions(character: str) -> list[dict]:
    """Distinct sessions for a character, with fact count and time range."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT session_id, COUNT(*), MIN(created_at), MAX(created_at)
            FROM facts
            WHERE character = ?
            GROUP BY session_id
            ORDER BY MIN(created_at)
            """,
            (character,),
        ).fetchall()
    return [
        {"session_id": r[0], "fact_count": r[1], "started_at": r[2], "ended_at": r[3]}
        for r in rows
    ]


def get_session_facts(character: str, session_id: str) -> list[str]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT text FROM facts WHERE character = ? AND session_id = ? ORDER BY id",
            (character, session_id),
        ).fetchall()
    return [row[0] for row in rows]


def delete_session(character: str, session_id: str) -> int:
    """Deletes all facts belonging to one session. Returns rows deleted."""
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM facts WHERE character = ? AND session_id = ?",
            (character, session_id),
        )
        return cursor.rowcount
