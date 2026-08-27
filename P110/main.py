import asyncio
import os

from dotenv import load_dotenv

from power_monitor.pricing import calculate_cost
from power_monitor.tapo import TapoPowerReader


load_dotenv()


async def main() -> None:
    reader = TapoPowerReader(
        username=os.environ["TAPO_USERNAME"],
        password=os.environ["TAPO_PASSWORD"],
        ip=os.environ["TAPO_IP"],
    )

    snapshot = await reader.read()

    price = float(os.environ["ELECTRICITY_PRICE_EUR_KWH"])

    print(f"Potència actual: {snapshot.power_w:.2f} W")
    print(f"Consum avui:     {snapshot.today_kwh:.3f} kWh")
    print(f"Consum mes:      {snapshot.month_kwh:.3f} kWh")
    print(f"Cost avui:       {calculate_cost(snapshot.today_kwh, price):.3f} €")
    print(f"Cost mes:        {calculate_cost(snapshot.month_kwh, price):.3f} €")


if __name__ == "__main__":
    asyncio.run(main())