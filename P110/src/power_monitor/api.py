import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from power_monitor.config import load_settings
from power_monitor.pricing import calculate_cost
from power_monitor.sampler import PowerSampler
from power_monitor.storage import SampleStore
from power_monitor.tapo import TapoPowerReader
from power_monitor.web import STATIC_DIR, router as web_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()

    store = SampleStore(settings.db_path)
    await asyncio.to_thread(store.prepare)

    reader = TapoPowerReader(
        username=settings.tapo_username,
        password=settings.tapo_password,
        ip=settings.tapo_ip,
    )

    sampler = PowerSampler(
        reader=reader,
        store=store,
        poll_seconds=settings.poll_seconds,
        store_seconds=settings.store_seconds,
        on_threshold_w=settings.on_threshold_w,
    )
    await sampler.prune(settings.retention_days)

    app.state.settings = settings
    app.state.reader = reader
    app.state.store = store
    app.state.sampler = sampler

    task = asyncio.create_task(sampler.run(), name="power-sampler")

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="My Homelab Power Monitor", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(web_router)


@app.get("/health")
async def health():
    return {"status": "ok", "sampler_fresh": app.state.sampler.is_fresh}


@app.get("/history")
async def get_history(
    hours: int = Query(default=24, ge=1, le=168),
    points: int = Query(default=180, ge=20, le=1000),
):
    since = datetime.now() - timedelta(hours=hours)
    series = await asyncio.to_thread(app.state.store.series, since, points)

    return {"hours": hours, "points": series}


@app.get("/power")
async def get_power():
    sampler = app.state.sampler

    # El muestreador es quien habla con el enchufe; aqui solo servimos su
    # ultima lectura, y si se ha quedado rancia devolvemos 503.
    if not sampler.is_fresh:
        raise HTTPException(status_code=503, detail="tapo_unreachable")

    snapshot = sampler.snapshot

    # El total anual es un extra: si falla esa consulta, la lectura en vivo
    # sigue siendo valida y el widget muestra un guion en esa fila.
    try:
        year_kwh = await app.state.reader.read_year_kwh()
    except Exception as exc:
        logger.warning("No se ha podido leer el consumo anual: %s", exc)
        year_kwh = None

    price = app.state.settings.price_eur_kwh
    measuring_since = sampler.measuring_since

    return {
        "power_w": snapshot.power_w,
        "today_kwh": snapshot.today_kwh,
        "month_kwh": snapshot.month_kwh,
        "year_kwh": year_kwh,
        "today_runtime_min": snapshot.today_runtime_min,
        "month_runtime_min": snapshot.month_runtime_min,
        "year_runtime_min": sampler.year_runtime_min,
        "today_cost_eur": calculate_cost(snapshot.today_kwh, price),
        "month_cost_eur": calculate_cost(snapshot.month_kwh, price),
        "year_cost_eur": None if year_kwh is None else calculate_cost(year_kwh, price),
        "measuring_since": None if measuring_since is None else measuring_since.isoformat(),
    }
