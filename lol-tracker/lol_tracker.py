from sincronitzador import sync_matches
from database import init_db


def main() -> None:
    init_db()

    new_matches = sync_matches()

    print(f"\nSync completado: {new_matches} partidas nuevas")


if __name__ == "__main__":
    main()