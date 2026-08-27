import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from power_monitor.config import load_settings
from power_monitor.pricing import calculate_cost
from power_monitor.tapo import TapoPowerReader
from power_monitor.web import STATIC_DIR, router as web_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()

    app.state.settings = settings
    app.state.reader = TapoPowerReader(
        username=settings.tapo_username,
        password=settings.tapo_password,
        ip=settings.tapo_ip,
    )

    yield


app = FastAPI(title="My Homelab Power Monitor", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(web_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/power")
async def get_power():
    try:
        snapshot = await app.state.reader.read()
    except Exception as exc:
        logger.warning("No se ha podido leer el Tapo P110: %s", exc)
        raise HTTPException(status_code=503, detail="tapo_unreachable") from exc

    # El total anual es un extra: si falla esa consulta, la lectura en vivo
    # sigue siendo valida y el widget muestra un guion en esa fila.
    try:
        year_kwh = await app.state.reader.read_year_kwh()
    except Exception as exc:
        logger.warning("No se ha podido leer el consumo anual: %s", exc)
        year_kwh = None

    price = app.state.settings.price_eur_kwh

    return {
        "power_w": snapshot.power_w,
        "today_kwh": snapshot.today_kwh,
        "month_kwh": snapshot.month_kwh,
        "year_kwh": year_kwh,
        "today_runtime_min": snapshot.today_runtime_min,
        "month_runtime_min": snapshot.month_runtime_min,
        "today_cost_eur": calculate_cost(snapshot.today_kwh, price),
        "month_cost_eur": calculate_cost(snapshot.month_kwh, price),
        "year_cost_eur": None if year_kwh is None else calculate_cost(year_kwh, price),
    }
