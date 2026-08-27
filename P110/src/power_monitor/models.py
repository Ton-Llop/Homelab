from dataclasses import dataclass


@dataclass(slots=True)
class PowerSnapshot:
    power_w: float
    today_kwh: float
    month_kwh: float
    today_runtime_min: int
    month_runtime_min: int