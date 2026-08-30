"""
Calcula els agregats que ensenya el widget a partir de les partides
que ja tenim guardades. Aqui no es toca ni la API ni la base de dades.
"""
from datetime import datetime, timezone


def to_iso(played_at_ms: int) -> str:
    # La API de Riot dona el timestamp en milisegons.
    return datetime.fromtimestamp(
        played_at_ms / 1000,
        tz=timezone.utc,
    ).isoformat()


def mitjana(valors: list) -> float | None:
    """
    Mitjana ignorant els NULL. Les partides guardades abans d'afegir una
    columna no tenen valor, i no volem que comptin com un zero.
    """
    nets = [valor for valor in valors if valor is not None]

    if not nets:
        return None

    return sum(nets) / len(nets)


def current_streak(matches: list[dict]) -> dict:
    """
    Ratxa actual comptant des de la partida mes recent.
    Les partides han d'arribar ordenades de mes nova a mes vella.
    """
    if not matches:
        return {"type": None, "length": 0}

    won = bool(matches[0]["win"])
    length = 0

    for match in matches:
        if bool(match["win"]) != won:
            break

        length += 1

    return {
        "type": "W" if won else "L",
        "length": length,
    }


def compute_stats(matches: list[dict]) -> dict:
    total = len(matches)

    if total == 0:
        return {
            "games": 0,
            "wins": 0,
            "losses": 0,
            "winrate": None,
            "kda": None,
            "kills_avg": None,
            "deaths_avg": None,
            "assists_avg": None,
            "cs_per_min": None,
            "vision_avg": None,
            "kill_participation_avg": None,
            "streak": {"type": None, "length": 0},
            "last_played": None,
        }

    wins = sum(1 for match in matches if match["win"])
    kills = sum(match["kills"] for match in matches)
    deaths = sum(match["deaths"] for match in matches)
    assists = sum(match["assists"] for match in matches)
    cs = sum(match["cs"] for match in matches)
    minutes = sum(match["duration"] for match in matches)

    vision = mitjana([match.get("vision_score") for match in matches])
    kill_participation = mitjana(
        [match.get("kill_participation") for match in matches]
    )

    return {
        "games": total,
        "wins": wins,
        "losses": total - wins,
        "winrate": round(wins / total * 100, 1),
        # Amb 0 morts el KDA es "perfect": dividim per 1 per no petar.
        "kda": round((kills + assists) / max(deaths, 1), 2),
        "kills_avg": round(kills / total, 1),
        "deaths_avg": round(deaths / total, 1),
        "assists_avg": round(assists / total, 1),
        "cs_per_min": round(cs / minutes, 1) if minutes else None,
        "vision_avg": None if vision is None else round(vision, 1),
        # Riot la dona de 0 a 1; la passem a percentatge.
        "kill_participation_avg": (
            None
            if kill_participation is None
            else round(kill_participation * 100, 1)
        ),
        "streak": current_streak(matches),
        "last_played": to_iso(matches[0]["played_at"]),
    }
