from tapo import ApiClient

from .models import PowerSnapshot


class TapoPowerReader:
    def __init__(self, username: str, password: str, ip: str) -> None:
        self._username = username
        self._password = password
        self._ip = ip

    async def read(self) -> PowerSnapshot:
        client = ApiClient(self._username, self._password)
        device = await client.p110(self._ip)

        energy = await device.get_energy_usage()

        return PowerSnapshot(
            power_w=energy.current_power / 1000,
            today_kwh=energy.today_energy / 1000,
            month_kwh=energy.month_energy / 1000,
            today_runtime_min=energy.today_runtime,
            month_runtime_min=energy.month_runtime,
        )