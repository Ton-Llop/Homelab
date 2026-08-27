import os

from dotenv import load_dotenv
from fastapi import FastAPI

from power_monitor.pricing import calculate_cost
from power_monitor.tapo import TapoPowerReader

load_dotenv()

app = FastAPI(title="My Homelab Power Monitor")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/power")
async def get_power():
    reader = TapoPowerReader(
        username=os.environ["TAPO_USERNAME"],
        password=os.environ["TAPO_PASSWORD"],
        ip=os.environ["TAPO_IP"],
    )

    snapshot = await reader.read()

    price = float(os.environ["ELECTRICITY_PRICE_EUR_KWH"])

    return {
        "power_w": snapshot.power_w,
        "today_kwh": snapshot.today_kwh,
        "month_kwh": snapshot.month_kwh,
        "today_runtime_min": snapshot.today_runtime_min,
        "month_runtime_min": snapshot.month_runtime_min,
        "cost_today_eur": calculate_cost(snapshot.today_kwh, price),
        "cost_month_eur": calculate_cost(snapshot.month_kwh, price),
    }