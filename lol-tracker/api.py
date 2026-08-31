import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles

from database import (
    DEFAULT_QUEUE_ID,
    count_matches,
    init_db,
    rank_history,
    recent_matches,
    save_rank,
    top_champions,
)
from estadistiques import compute_stats, to_iso
from riot_api import (
    RiotAuthError,
    champion_icon_url,
    get_ddragon_version,
    get_solo_queue_rank,
)
from sincronitzador import get_poll_interval, sync_matches
from web import STATIC_DIR, router as web_router

# Uvicorn nomes configura els seus propis loggers, aixi que un
# logging.getLogger() pelat es queda a nivell WARNING i els syncs correctes
# no es veurien enlloc. Li posem sortida propia perque `docker logs` ensenyi
# que el servei esta viu encara que no hi hagi partides noves.
logger = logging.getLogger("lol-tracker")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(_handler)
    logger.propagate = False

DEFAULT_COUNT = 20


@dataclass
class SyncState:
    """Estat de l'ultim sync, que es el que mira el widget."""

    last_sync_at: datetime | None = None
    last_error: str | None = None
    key_valid: bool = True
    new_matches: int = 0
    rank: dict | None = None

    @property
    def status(self) -> str:
        if not self.key_valid:
            return "auth_error"

        if self.last_error:
            return "degraded"

        if self.last_sync_at is None:
            return "starting"

        return "ok"


async def sync_loop(state: SyncState) -> None:
    """
    El mateix bucle del worker, pero com a tasca d'asyncio. Nomes hi ha un
    proces parlant amb Riot, independentment de quantes pestanyes de Homarr
    hi hagi obertes.
    """
    while True:
        try:
            # sync_matches fa servir requests, que bloqueja: fora del loop.
            new_matches = await asyncio.to_thread(sync_matches)

            state.last_sync_at = datetime.now(timezone.utc)
            state.new_matches = new_matches
            state.last_error = None
            state.key_valid = True

            logger.info(
                "sync fet: %s partides noves, proper en %s min",
                new_matches,
                get_poll_interval() // 60,
            )

        except RiotAuthError as exc:
            # La key de desenvolupament caduca cada 24 h. Ho marquem a part
            # perque el widget ho pugui cantar en comptes d'ensenyar dades
            # velles com si res.
            state.key_valid = False
            state.last_error = str(exc)

            logger.warning("API key de Riot no valida: %s", exc)

        except Exception as exc:
            state.last_error = str(exc)

            logger.warning("error durant el sync: %s", exc)

        # L'elo va a part: si league-v4 falla, les partides que acabem de
        # baixar continuen sent bones i el widget nomes es queda sense el
        # rang, en comptes de marcar tot el sync com a trencat.
        try:
            state.rank = await asyncio.to_thread(get_solo_queue_rank)

            # Riot no guarda historic de LP, aixi que el que no anotem aqui
            # es perd. save_rank nomes escriu si el LP s'ha mogut.
            if await asyncio.to_thread(save_rank, state.rank):
                logger.info("elo nou: %s LP", state.rank["lp"])

        except Exception as exc:
            logger.warning("no he pogut llegir l'elo: %s", exc)

        await asyncio.sleep(get_poll_interval())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(init_db)

    state = SyncState()
    app.state.sync = state

    task = asyncio.create_task(sync_loop(state), name="lol-sync")

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="My Homelab LoL Tracker", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(web_router)


@app.get("/health")
async def health():
    state = app.state.sync

    return {
        "status": state.status,
        "key_valid": state.key_valid,
        "last_sync": (
            None
            if state.last_sync_at is None
            else state.last_sync_at.isoformat()
        ),
        "last_error": state.last_error,
        "total_matches": await asyncio.to_thread(count_matches),
        # El widget nomes ensenya una cua: si el total i el de la cua no
        # s'assemblen, es que la majoria de partides son d'ARAM o de flex.
        "queue_id": DEFAULT_QUEUE_ID,
        "queue_matches": await asyncio.to_thread(
            count_matches, DEFAULT_QUEUE_ID
        ),
    }


@app.get("/stats")
async def stats(count: int = Query(default=DEFAULT_COUNT, ge=1, le=100)):
    matches = await asyncio.to_thread(recent_matches, count)

    payload = compute_stats(matches)
    payload["status"] = app.state.sync.status
    # El rang el porta el bucle de sync, aixi el widget nomes fa una crida.
    payload["rank"] = app.state.sync.rank

    return payload


@app.get("/matches")
async def matches(limit: int = Query(default=5, ge=1, le=50)):
    rows = await asyncio.to_thread(recent_matches, limit)
    version = await asyncio.to_thread(get_ddragon_version)

    return {
        "ddragon_version": version,
        "matches": [
            {
                "match_id": row["match_id"],
                "played_at": to_iso(row["played_at"]),
                "champion": row["champion"],
                "icon": champion_icon_url(row["champion"], version),
                "win": bool(row["win"]),
                "kills": row["kills"],
                "deaths": row["deaths"],
                "assists": row["assists"],
                "cs": row["cs"],
                "duration": row["duration"],
                "queue_id": row["queue_id"],
            }
            for row in rows
        ],
    }


@app.get("/rank-history")
async def historic_elo(limit: int = Query(default=60, ge=2, le=500)):
    """Mostres de LP per dibuixar la linia, de mes vella a mes nova."""
    points = await asyncio.to_thread(rank_history, limit)

    return {"points": points}


@app.get("/champions")
async def champions(limit: int = Query(default=3, ge=1, le=20)):
    rows = await asyncio.to_thread(top_champions, limit)
    version = await asyncio.to_thread(get_ddragon_version)

    return {
        "ddragon_version": version,
        "champions": [
            {
                **row,
                "icon": champion_icon_url(row["champion"], version),
            }
            for row in rows
        ],
    }
