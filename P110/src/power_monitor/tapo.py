import asyncio
import time
from datetime import date

from tapo import ApiClient
from tapo.requests import EnergyDataInterval

from .models import PowerSnapshot

# El total anual solo cambia de forma apreciable en horas: no tiene sentido
# pedirselo al enchufe en cada sondeo de 10 s.
YEAR_CACHE_SECONDS = 300


class TapoPowerReader:

    def __init__(self, username: str, password: str, ip: str) -> None:
        self._username = username
        self._password = password
        self._ip = ip
        self._device = None
        self._lock = asyncio.Lock()
        self._year_kwh: float | None = None
        self._year_read_at = 0.0

    async def _connect(self):
        if self._device is None:
            client = ApiClient(self._username, self._password)
            self._device = await client.p110(self._ip)
        return self._device

    async def read(self) -> PowerSnapshot:
        async with self._lock:
            try:
                device = await self._connect()
                energy = await device.get_energy_usage()
            except Exception:
                # si sessio caducada fem handshake
                self._device = None
                raise

        return PowerSnapshot(
            power_w=energy.current_power / 1000,
            today_kwh=energy.today_energy / 1000,
            month_kwh=energy.month_energy / 1000,
            today_runtime_min=energy.today_runtime,
            month_runtime_min=energy.month_runtime,
        )

    async def read_year_kwh(self) -> float:
        """Consumo real acumulado del año en curso, sumando los contadores mensuales."""
        if self._year_kwh is not None and time.monotonic() - self._year_read_at < YEAR_CACHE_SECONDS:
            return self._year_kwh

        async with self._lock:
            try:
                device = await self._connect()
                data = await device.get_energy_data(
                    EnergyDataInterval.Monthly,
                    date(date.today().year, 1, 1),
                )
            except Exception:
                self._device = None
                raise

        # Los meses aun no transcurridos vienen a None.
        self._year_kwh = sum(entry.energy or 0 for entry in data.entries) / 1000
        self._year_read_at = time.monotonic()
        return self._year_kwh
