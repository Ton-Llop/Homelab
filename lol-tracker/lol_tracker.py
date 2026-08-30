"""
Sync a ma, sense aixecar el servidor web.
"""
import argparse
import sys

from database import delete_all_matches, init_db
from riot_api import RiotAuthError, get_match_ids
from sincronitzador import sync_matches


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sincronitza les partides de LoL a la base de dades",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="quantes partides demanar a Riot (per defecte 20)",
    )
    parser.add_argument(
        "--resync",
        action="store_true",
        help="esborra les partides guardades i les torna a baixar senceres",
    )

    args = parser.parse_args()

    init_db()

    if args.resync:
        # Comprovem que la key funciona ABANS d'esborrar res. Si no, ens
        # quedariem sense partides i sense poder tornar-les a baixar.
        try:
            get_match_ids(count=1)

        except RiotAuthError as exc:
            print(f"No borro nada: {exc}")
            sys.exit(1)

        borradas = delete_all_matches()
        print(f"Borradas {borradas} partidas, volviendo a bajarlas...")

    new_matches = sync_matches(count=args.count)

    print(f"\nSync completado: {new_matches} partidas nuevas")


if __name__ == "__main__":
    main()
