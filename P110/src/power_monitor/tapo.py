import asyncio

from tapo import ApiClient

from .models import PowerSnapshot


class TapoPowerReader:

    def __init__(self, username: str, password: str, ip: str) -> None:
        self._username = username
        self._password = password
        self._ip = ip
        self._device = None
        self._lock = asyncio.Lock()

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
