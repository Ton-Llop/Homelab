from database import match_exists, save_match
from riot_api import extract_player_stats, get_match, get_match_ids

"""
Qui sincronitza games de la api a la bd
"""
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