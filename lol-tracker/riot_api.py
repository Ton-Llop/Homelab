import os
import time
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

# Data Dragon es el CDN public de Riot per icones i dades estatiques.
# No necessita API key.
DDRAGON_BASE = "https://ddragon.leagueoflegends.com"
DDRAGON_TTL_SECONDS = 6 * 3600


class RiotAuthError(RuntimeError):
    """
    La API key no serveix. Les keys de desenvolupament de Riot caduquen
    cada 24 h, aixi que aixo passara sovint fins que en tinguem una de
    personal.
    """


def _request(url: str, params: dict | None = None) -> dict:
    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=10,
    )

    if response.status_code in (401, 403):
        raise RiotAuthError(
            f"La API key de Riot no es valida o ha caducat "
            f"(HTTP {response.status_code})"
        )

    response.raise_for_status()

    return response.json()


def get_match_ids(count: int = 10):
    url = f"{BASE_URL}/lol/match/v5/matches/by-puuid/{RIOT_PUUID}/ids"

    params = {
        "start": 0,
        "count": count,
    }

    return _request(url, params=params)


def get_match(match_id: str):
    url = f"{BASE_URL}/lol/match/v5/matches/{match_id}"

    return _request(url)


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

    # challenges no hi es a totes les cues ni a les partides mes velles,
    # aixi que si no hi es guardem NULL i el widget ensenya un guio.
    challenges = player.get("challenges") or {}

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
        "vision_score": player.get("visionScore"),
        "kill_participation": challenges.get("killParticipation"),
    }


_ddragon_cache: dict = {
    "version": None,
    "fetched_at": 0.0,
}


def get_ddragon_version() -> str | None:
    """
    La versio de Data Dragon nomes canvia cada parell de setmanes, aixi que
    la cachem. Si el CDN falla ens quedem amb l'ultima versio bona.
    """
    now = time.monotonic()
    cached = _ddragon_cache["version"]

    if cached and now - _ddragon_cache["fetched_at"] < DDRAGON_TTL_SECONDS:
        return cached

    try:
        response = requests.get(
            f"{DDRAGON_BASE}/api/versions.json",
            timeout=10,
        )
        response.raise_for_status()

        version = response.json()[0]

    except Exception:
        return cached

    _ddragon_cache["version"] = version
    _ddragon_cache["fetched_at"] = now

    return version


def champion_icon_url(champion: str, version: str | None) -> str | None:
    if not champion or not version:
        return None

    return f"{DDRAGON_BASE}/cdn/{version}/img/champion/{champion}.png"
