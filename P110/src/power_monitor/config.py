import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    tapo_username: str
    tapo_password: str
    tapo_ip: str
    price_eur_kwh: float


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        tapo_username=os.environ["TAPO_USERNAME"],
        tapo_password=os.environ["TAPO_PASSWORD"],
        tapo_ip=os.environ["TAPO_IP"],
        price_eur_kwh=float(os.environ["ELECTRICITY_PRICE_EUR_KWH"]),
    )
