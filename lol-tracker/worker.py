"""
Es qui mirarà cada X temps si hi ha un nou game o no, estarà en un cont docker
"""
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from sincronitzador import sync_matches
from database import init_db


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


POLL_DAY_SECONDS = int(
    os.getenv("LOL_POLL_DAY_SECONDS", "1800")
)

POLL_EVENING_SECONDS = int(
    os.getenv("LOL_POLL_EVENING_SECONDS", "600")
)

POLL_NIGHT_SECONDS = int(
    os.getenv("LOL_POLL_NIGHT_SECONDS", "3600")
)


def get_poll_interval() -> int:
    hour = datetime.now().hour

    if 0 <= hour < 8:
        return POLL_NIGHT_SECONDS

    if 8 <= hour < 16:
        return POLL_DAY_SECONDS

    return POLL_EVENING_SECONDS


def main() -> None:
    init_db()

    try:
        while True:
            try:
                new_matches = sync_matches()

                print(
                    f"[worker] sync completado: "
                    f"{new_matches} partidas nuevas"
                )

            except Exception as exc:
                print(f"[worker] error durante sync: {exc}")

            interval = get_poll_interval()

            print(
                f"[worker] próximo sync en "
                f"{interval // 60} min"
            )

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n[worker] detenido")


if __name__ == "__main__":
    main()