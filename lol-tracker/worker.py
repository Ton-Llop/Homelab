"""
Es qui mirarà cada X temps si hi ha un nou game o no.

Amb la API web activada aquest bucle viu dins d'api.py, igual que el
sampler del P110. Aquest fitxer queda per poder llançar el sync a mà
sense aixecar el servidor.
"""
import time

from database import init_db
from sincronitzador import get_poll_interval, sync_matches


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
