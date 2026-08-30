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

# Columnes afegides despres de la primera versio de la taula. Les bases de
# dades que ja existeixen les reben per ALTER TABLE a init_db().
COLUMNES_NOVES = {
    "vision_score": "INTEGER",
    "kill_participation": "REAL",
}


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def migrate(conn: sqlite3.Connection) -> None:
    existents = {
        row[1]
        for row in conn.execute("PRAGMA table_info(matches)")
    }

    for nom, tipus in COLUMNES_NOVES.items():
        if nom not in existents:
            conn.execute(
                f"ALTER TABLE matches ADD COLUMN {nom} {tipus}"
            )


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
                game_version TEXT,
                vision_score INTEGER,
                kill_participation REAL
            )
            """
        )

        migrate(conn)


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
                game_version,
                vision_score,
                kill_participation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                stats.get("vision_score"),
                stats.get("kill_participation"),
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


def recent_matches(limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT match_id,
                   played_at,
                   champion,
                   win,
                   kills,
                   deaths,
                   assists,
                   cs,
                   duration,
                   queue_id,
                   game_version,
                   vision_score,
                   kill_participation
            FROM matches
            ORDER BY played_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def count_matches() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) FROM matches").fetchone()

    return row[0]


def delete_all_matches() -> int:
    """
    Per re-sincronitzar des de zero quan la taula canvia i les partides
    velles es queden sense les columnes noves.
    """
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM matches")

    return cursor.rowcount
