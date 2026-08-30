import os
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(ENV_PATH)

API_KEY = os.environ["RIOT_API_KEY"].strip()
RIOT_PUUID = os.environ["RIOT_PUUID"].strip()

HEADERS = {
    "X-Riot-Token": API_KEY,
}

BASE_URL = "https://europe.api.riotgames.com"


def get_match_ids(count: int = 10):
    url = f"{BASE_URL}/lol/match/v5/matches/by-puuid/{RIOT_PUUID}/ids"

    params = {
        "start": 0,
        "count": count,
    }

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=10,
    )
    response.raise_for_status()

    return response.json()


def get_match(match_id: str):
    url = f"{BASE_URL}/lol/match/v5/matches/{match_id}"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()

    return response.json()


def extract_player_stats(match: dict) -> dict:
    participants = match["info"]["participants"]

    player = next(
        (
            participant
            for participant in participants
            if participant["puuid"] == RIOT_PUUID
        ),
        None,
    )

    if player is None:
        raise RuntimeError(
            f"No encuentro al jugador en "
            f'{match["metadata"]["matchId"]}'
        )

    duration_minutes = match["info"]["gameDuration"] / 60

    cs = (
        player["totalMinionsKilled"]
        + player["neutralMinionsKilled"]
    )

    return {
        "match_id": match["metadata"]["matchId"],
        "played_at": match["info"]["gameCreation"],
        "champion": player["championName"],
        "win": player["win"],
        "kills": player["kills"],
        "deaths": player["deaths"],
        "assists": player["assists"],
        "cs": cs,
        "duration": round(duration_minutes, 1),
        "queue_id": match["info"]["queueId"],
        "game_version": match["info"]["gameVersion"],
    }