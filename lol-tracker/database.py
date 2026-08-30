import sqlite3
import os
from pathlib import Path

# aixo pel cont de docker que pugui crear la lol.db dins de data --> LOL_DB_PATH=/data/lol.db
DB_PATH = Path(
    os.getenv(
        "LOL_DB_PATH",
        Path(__file__).resolve().parent / "lol.db",
    )
)


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)

def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY,
                played_at INTEGER NOT NULL,
                champion TEXT NOT NULL,
                win INTEGER NOT NULL,
                kills INTEGER NOT NULL,
                deaths INTEGER NOT NULL,
                assists INTEGER NOT NULL,
                cs INTEGER NOT NULL,
                duration REAL NOT NULL,
                queue_id INTEGER,
                game_version TEXT
            )
            """
        )


def save_match(stats: dict) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO matches (
                match_id,
                played_at,
                champion,
                win,
                kills,
                deaths,
                assists,
                cs,
                duration,
                queue_id,
                game_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stats["match_id"],
                stats["played_at"],
                stats["champion"],
                stats["win"],
                stats["kills"],
                stats["deaths"],
                stats["assists"],
                stats["cs"],
                stats["duration"],
                stats["queue_id"],
                stats["game_version"],
            ),
        )

        return cursor.rowcount > 0

def match_exists(match_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM matches WHERE match_id = ?",
            (match_id,),
        ).fetchone()

    return row is not None