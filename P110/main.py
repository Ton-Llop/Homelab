import asyncio

from power_monitor.config import load_settings
from power_monitor.pricing import calculate_cost
from power_monitor.tapo import TapoPowerReader


async def main() -> None:
    settings = load_settings()

    reader = TapoPowerReader(
        username=settings.tapo_username,
        password=settings.tapo_password,
        ip=settings.tapo_ip,
    )

    snapshot = await reader.read()
    price = settings.price_eur_kwh

    print(f"Potència actual: {snapshot.power_w:.2f} W")
    print(f"Consum avui:     {snapshot.today_kwh:.3f} kWh")
    print(f"Consum mes:      {snapshot.month_kwh:.3f} kWh")
    print(f"Cost avui:       {calculate_cost(snapshot.today_kwh, price):.3f} €")
    print(f"Cost mes:        {calculate_cost(snapshot.month_kwh, price):.3f} €")
    print(f"Cost any:        {calculate_cost(snapshot.month_kwh * 12, price):.3f} €")


if __name__ == "__main__":
    asyncio.run(main())
