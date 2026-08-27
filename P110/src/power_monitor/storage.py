import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS samples (
    ts       INTEGER PRIMARY KEY,
    power_w  REAL NOT NULL
);
"""


class SampleStore:
    """Historico de potencia en SQLite: una muestra por minuto."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path, timeout=5)

    def prepare(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        with closing(self._connect()) as conn:
            # WAL evita que una lectura larga bloquee la escritura del muestreador.
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)
            conn.commit()

    def record(self, when: datetime, power_w: float) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO samples (ts, power_w) VALUES (?, ?)",
                (int(when.timestamp()), power_w),
            )
            conn.commit()

    def minutes_above(self, since: datetime, threshold_w: float) -> int:
        """Minutos con el aparato encendido desde `since`.

        Cada fila representa el minuto que la contiene, que es la misma
        resolucion con la que el propio P110 cuenta su runtime diario.
        """
        with closing(self._connect()) as conn:
            (count,) = conn.execute(
                "SELECT COUNT(*) FROM samples WHERE ts >= ? AND power_w >= ?",
                (int(since.timestamp()), threshold_w),
            ).fetchone()

        return count

    def series(self, since: datetime, buckets: int) -> list[tuple[int, float]]:
        """Serie de potencia agregada en como mucho `buckets` puntos.

        Un dia entero son 1.440 muestras y la grafica del widget mide 300 px:
        agrupamos en el propio SQL para no mandar quince veces mas puntos que
        pixeles hay para dibujarlos.
        """
        start = int(since.timestamp())
        span = max(int(datetime.now().timestamp()) - start, 1)
        width = max(span // buckets, 60)

        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT (ts / ?) * ? AS bucket, AVG(power_w)
                FROM samples
                WHERE ts >= ?
                GROUP BY bucket
                ORDER BY bucket
                """,
                (width, width, start),
            ).fetchall()

        return [(int(bucket), round(power, 2)) for bucket, power in rows]

    def first_sample_at(self) -> datetime | None:
        with closing(self._connect()) as conn:
            (ts,) = conn.execute("SELECT MIN(ts) FROM samples").fetchone()

        return None if ts is None else datetime.fromtimestamp(ts)

    def delete_before(self, cutoff: datetime) -> int:
        with closing(self._connect()) as conn:
            deleted = conn.execute(
                "DELETE FROM samples WHERE ts < ?", (int(cutoff.timestamp()),)
            ).rowcount
            conn.commit()

        return deleted
