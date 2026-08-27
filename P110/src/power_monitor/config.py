import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    tapo_username: str
    tapo_password: str
    tapo_ip: str
    price_eur_kwh: float
    db_path: Path
    poll_seconds: int
    store_seconds: int
    on_threshold_w: float
    retention_days: int


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        tapo_username=os.environ["TAPO_USERNAME"],
        tapo_password=os.environ["TAPO_PASSWORD"],
        tapo_ip=os.environ["TAPO_IP"],
        price_eur_kwh=float(os.environ["ELECTRICITY_PRICE_EUR_KWH"]),
        db_path=Path(os.environ.get("POWER_DB_PATH", "data/power.db")),
        poll_seconds=int(os.environ.get("POLL_SECONDS", "10")),
        store_seconds=int(os.environ.get("STORE_SECONDS", "60")),
        on_threshold_w=float(os.environ.get("ON_THRESHOLD_W", "1")),
        retention_days=int(os.environ.get("RETENTION_DAYS", "400")),
    )
