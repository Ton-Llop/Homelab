import sqlite3
import os
import time
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


def _queue_id_from_env() -> int | None:
    """
    Cua que ensenya el widget. 420 es ranked solo/duo, la mateixa d'on surt
    l'elo: si aqui hi comptessim ARAMs, el winrate gran i el rang de sota
    parlarien de partides diferents. Amb LOL_QUEUE_ID=all es compten totes.
    """
    raw = (os.getenv("LOL_QUEUE_ID") or "420").strip().lower()

    if raw in ("", "all", "totes"):
        return None

    return int(raw)


DEFAULT_QUEUE_ID = _queue_id_from_env()


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def _queue_filter(queue_id: int | None) -> tuple[str, tuple]:
    if queue_id is None:
        return "", ()

    return "WHERE queue_id = ?", (queue_id,)


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

        # Riot no dona historic de LP: el que no anem guardant nosaltres es
        # perd per sempre. Una fila cada cop que el LP es mou.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rank_history (
                recorded_at INTEGER PRIMARY KEY,
                tier TEXT,
                division TEXT,
                lp INTEGER NOT NULL,
                wins INTEGER,
                losses INTEGER
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


def recent_matches(
    limit: int = 20,
    queue_id: int | None = DEFAULT_QUEUE_ID,
) -> list[dict]:
    where, params = _queue_filter(queue_id)

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            f"""
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
            {where}
            ORDER BY played_at DESC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()

    return [dict(row) for row in rows]


def top_champions(
    limit: int = 3,
    queue_id: int | None = DEFAULT_QUEUE_ID,
) -> list[dict]:
    """
    Els campions mes jugats de tot el que tenim guardat, no nomes de les
    ultimes partides: amb 20 partides un top no diria gran cosa.
    """
    where, params = _queue_filter(queue_id)

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT champion,
                   COUNT(*) AS games,
                   SUM(win) AS wins
            FROM matches
            {where}
            GROUP BY champion
            ORDER BY games DESC, wins DESC, champion ASC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()

    return [
        {
            "champion": champion,
            "games": games,
            "wins": wins,
            "losses": games - wins,
            "winrate": round(wins / games * 100, 1),
        }
        for champion, games, wins in rows
    ]


def count_matches(queue_id: int | None = None) -> int:
    where, params = _queue_filter(queue_id)

    with get_connection() as conn:
        row = conn.execute(
            f"SELECT COUNT(*) FROM matches {where}",
            params,
        ).fetchone()

    return row[0]


def last_rank() -> dict | None:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            """
            SELECT recorded_at, tier, division, lp, wins, losses
            FROM rank_history
            ORDER BY recorded_at DESC
            LIMIT 1
            """
        ).fetchone()

    return None if row is None else dict(row)


def save_rank(rank: dict | None) -> bool:
    """
    Guarda una mostra d'elo nomes si ha canviat respecte de l'ultima. El sync
    passa cada 10-60 min pero el LP nomes es mou quan jugues: sense aquesta
    comprovacio tindriem desenes de files identiques cada dia.
    """
    if not rank or rank.get("lp") is None:
        return False

    last = last_rank()

    if (
        last is not None
        and last["tier"] == rank.get("tier")
        and last["division"] == rank.get("division")
        and last["lp"] == rank["lp"]
    ):
        return False

    with get_connection() as conn:
        # OR REPLACE per si dues mostres cauen dins del mateix segon: val mes
        # perdre'n una que petar el bucle de sync.
        conn.execute(
            """
            INSERT OR REPLACE INTO rank_history (
                recorded_at, tier, division, lp, wins, losses
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                int(time.time()),
                rank.get("tier"),
                rank.get("division"),
                rank["lp"],
                rank.get("wins"),
                rank.get("losses"),
            ),
        )

    return True


def rank_history(limit: int = 60) -> list[dict]:
    """Ultimes mostres d'elo, de mes vella a mes nova per dibuixar-les."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT recorded_at, tier, division, lp
            FROM rank_history
            ORDER BY recorded_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in reversed(rows)]


def delete_all_matches() -> int:
    """
    Per re-sincronitzar des de zero quan la taula canvia i les partides
    velles es queden sense les columnes noves.
    """
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM matches")

    return cursor.rowcount
