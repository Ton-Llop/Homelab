import os
import time
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(ENV_PATH)

# Res d'aixo es obligatori a l'importar: si falta configuracio volem que el
# servidor arrenqui igualment i que ho canti per /health i pel widget, en
# comptes de petar a l'arrencada i deixar-nos sense res que mirar.
API_KEY = (os.getenv("RIOT_API_KEY") or "").strip()

# El Riot ID (Nom#TAG) es estable per sempre. El PUUID no: va xifrat amb la
# key que el va generar, aixi que quan la key rota deixa de servir i Riot
# respon "Exception decrypting". Per aixo el resolem en calent.
GAME_NAME = (os.getenv("RIOT_GAME_NAME") or "").strip()
TAG_LINE = (os.getenv("RIOT_TAG_LINE") or "").strip()

# Compatibilitat cap enrere: si no hi ha Riot ID encara fem servir el PUUID
# de l'entorn, pero llavors tocara actualitzar-lo a ma cada cop.
ENV_PUUID = (os.getenv("RIOT_PUUID") or "").strip()

# Riot te dues rutes diferents i es facil equivocar-s'hi:
#   - regional  (europe) -> match-v5, account-v1
#   - plataforma (euw1)  -> league-v4, summoner-v4
BASE_URL = "https://europe.api.riotgames.com"

PLATFORM = (os.getenv("RIOT_PLATFORM") or "euw1").strip()
PLATFORM_URL = f"https://{PLATFORM}.api.riotgames.com"

# A partir de Master ja no hi ha divisions, pero Riot continua enviant
# rank: "I" a la resposta. Si el pintessim tal qual sortiria "MASTER I", que
# no es com ho ensenya el client del joc.
APEX_TIERS = {"MASTER", "GRANDMASTER", "CHALLENGER"}

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


class RiotApiError(RuntimeError):
    """Qualsevol altra resposta d'error de Riot, amb el motiu que dona."""


def _request(url: str, params: dict | None = None) -> dict | list:
    if not API_KEY:
        raise RiotAuthError("Falta RIOT_API_KEY a l'entorn")

    response = requests.get(
        url,
        headers={"X-Riot-Token": API_KEY},
        params=params,
        timeout=10,
    )

    if response.status_code in (401, 403):
        raise RiotAuthError(
            f"La API key de Riot no es valida o ha caducat "
            f"(HTTP {response.status_code})"
        )

    if not response.ok:
        # Riot explica el motiu al cos de la resposta. Amb un
        # raise_for_status() pelat nomes veiem "400 Bad Request" i no hi ha
        # manera de saber que li ha molestat.
        raise RiotApiError(
            f"HTTP {response.status_code} de Riot: {response.text[:300]}"
        )

    return response.json()


_puuid_cache: dict = {"value": None}


def get_puuid_by_riot_id(game_name: str, tag_line: str) -> str:
    url = (
        f"{BASE_URL}/riot/account/v1/accounts/by-riot-id/"
        f"{quote(game_name)}/{quote(tag_line)}"
    )

    return _request(url)["puuid"]


def get_puuid(refresh: bool = False) -> str:
    if not refresh and _puuid_cache["value"]:
        return _puuid_cache["value"]

    if GAME_NAME and TAG_LINE:
        puuid = get_puuid_by_riot_id(GAME_NAME, TAG_LINE)

    elif ENV_PUUID:
        puuid = ENV_PUUID

    else:
        raise RiotApiError(
            "Falta RIOT_GAME_NAME i RIOT_TAG_LINE a l'entorn "
            "(o be un RIOT_PUUID valid)"
        )

    _puuid_cache["value"] = puuid

    return puuid


def get_match_ids(count: int = 10):
    def demana(puuid: str):
        url = f"{BASE_URL}/lol/match/v5/matches/by-puuid/{puuid}/ids"

        return _request(url, params={"start": 0, "count": count})

    try:
        return demana(get_puuid())

    except RiotApiError as exc:
        # "Exception decrypting" vol dir que el PUUID el va generar una key
        # anterior. Si tenim el Riot ID el tornem a resoldre i reintentem un
        # sol cop; aixi una rotacio de key es cura sola.
        if "decrypting" not in str(exc) or not (GAME_NAME and TAG_LINE):
            raise

        return demana(get_puuid(refresh=True))


def get_match(match_id: str):
    url = f"{BASE_URL}/lol/match/v5/matches/{match_id}"

    return _request(url)


def get_ranked_entries() -> list:
    """
    Torna una entrada per cua on l'invocador estigui classificat: solo,
    flex, etc. Va per la ruta de plataforma, no per la regional.
    """
    url = f"{PLATFORM_URL}/lol/league/v4/entries/by-puuid/{get_puuid()}"

    return _request(url)


def get_solo_queue_rank() -> dict | None:
    for entry in get_ranked_entries():
        if entry.get("queueType") != "RANKED_SOLO_5x5":
            continue

        wins = entry.get("wins") or 0
        losses = entry.get("losses") or 0
        total = wins + losses

        tier = entry.get("tier")

        return {
            "tier": tier,
            "division": None if tier in APEX_TIERS else entry.get("rank"),
            "lp": entry.get("leaguePoints"),
            "wins": wins,
            "losses": losses,
            # Aquest winrate es el de tota la temporada, no el de les
            # ultimes 20 partides que ensenya la xifra gran.
            "winrate": round(wins / total * 100, 1) if total else None,
        }

    # Unranked: encara no ha fet les partides de classificacio.
    return None


def extract_player_stats(match: dict) -> dict:
    participants = match["info"]["participants"]
    puuid = get_puuid()

    player = next(
        (
            participant
            for participant in participants
            if participant["puuid"] == puuid
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
