"""
Qui sincronitza games de la api a la bd, i cada quant toca fer-ho.
"""
import os
from datetime import datetime

from database import match_exists, save_match
from riot_api import extract_player_stats, get_match, get_match_ids


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


def sync_matches(count: int = 20) -> int:
    new_matches = 0

    for match_id in get_match_ids(count=count):
        if match_exists(match_id):
            break

        match = get_match(match_id)
        stats = extract_player_stats(match)

        save_match(stats)
        new_matches += 1

        result = "WIN" if stats["win"] else "LOSS"

        print(
            f'NEW | '
            f'{stats["champion"]:12} | '
            f'{result:4} | '
            f'{stats["kills"]}/{stats["deaths"]}/{stats["assists"]} | '
            f'{stats["cs"]} CS | '
            f'{stats["duration"]} min'
        )

    return new_matches
