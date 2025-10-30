import os
import time
import requests
import logging
from typing import List, Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class RiotSummoner:
    def __init__(self, puuid: str, name: str):
        self.puuid = puuid
        self.name = name


class RiotMatch:
    def __init__(self, match_id: str):
        self.match_id = match_id


class RiotAPIClient:
    BASE_URLS = {
        "americas": "https://americas.api.riotgames.com",
        "europe": "https://europe.api.riotgames.com",
        "asia": "https://asia.api.riotgames.com",
        "sea": "https://sea.api.riotgames.com",
    }

    REGION_TO_ROUTING = {
        "na1": "americas",
        "br1": "americas",
        "la1": "americas",
        "la2": "americas",
        "euw1": "europe",
        "eun1": "europe",
        "tr1": "europe",
        "ru": "europe",
        "kr": "asia",
        "jp1": "asia",
        "oc1": "sea",
        "ph2": "sea",
        "sg2": "sea",
        "th2": "sea",
        "tw2": "sea",
        "vn2": "sea",
    }

    def __init__(self):
        self.api_key = os.environ.get("RIOT_API_KEY")
        if not self.api_key:
            raise ValueError("Missing RIOT_API_KEY environment variable")

    def get_routing_region(self, platform_region: str) -> str:
        """Map platform region (na1, euw1) to routing region (americas, europe)."""
        return self.REGION_TO_ROUTING.get(platform_region.lower(), "americas")

    def get_summoner_by_name(self, summoner_name: str, region: str) -> RiotSummoner:
        """Fetch summoner info (including PUUID) from Riot API."""
        url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}"
        headers = {"X-Riot-Token": self.api_key}
        logger.info(f"Fetching summoner info for {summoner_name} from {url}")

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return RiotSummoner(puuid=data["puuid"], name=data["name"])

    def get_match_history(
        self, puuid: str, region: str, count: int = 20, start_time: int = None, end_time: int = None
    ) -> List[str]:
        """Fetch list of match IDs for a summoner within a given time range."""
        routing_region = self.get_routing_region(region)
        base_url = self.BASE_URLS[routing_region]
        params = {"count": count}

        if start_time and end_time:
            params["startTime"] = int(start_time)
            params["endTime"] = int(end_time)

        url = f"{base_url}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        headers = {"X-Riot-Token": self.api_key}

        logger.info(f"Fetching matches from {url} with params: {params}")
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 400:
            logger.warning("400 Bad Request — possibly invalid timestamps or puuid.")
            raise ValueError("Bad Request: Check PUUID or timestamps.")
        elif response.status_code == 404:
            logger.warning("No matches found for given range.")
            return []
        elif response.status_code != 200:
            logger.error(f"Unexpected error: {response.text}")
            response.raise_for_status()

        return response.json()

    def get_full_match_history(self, summoner: RiotSummoner, region: str, months_back: int = 12) -> List[RiotMatch]:
        """Fetch full match history for a summoner in the last `months_back` months, with fallback logic."""
        current_time = int(time.time())
        start_time = current_time - (months_back * 30 * 24 * 60 * 60)

        all_matches = []
        batch_size = 100

        try:
            match_ids = self.get_match_history(
                summoner.puuid,
                region,
                count=batch_size,
                start_time=start_time,
                end_time=current_time,
            )
        except ValueError:
            # Fallback: retry without timestamps if API rejects them
            logger.warning("Retrying without timestamps due to Bad Request error...")
            match_ids = self.get_match_history(
                summoner.puuid,
                region,
                count=batch_size,
            )

        logger.info(f"Fetched {len(match_ids)} matches for {summoner.name}")
        return [RiotMatch(match_id=m) for m in match_ids]


# ✅ Example usage:
if __name__ == "__main__":
    client = RiotAPIClient()
    region = "na1"
    summoner_name = "Faker"

    try:
        summoner = client.get_summoner_by_name(summoner_name, region)
        matches = client.get_full_match_history(summoner, region, months_back=12)
        print(f"Recent matches for {summoner.name}: {[m.match_id for m in matches]}")
    except Exception as e:
        logger.error(f"Error fetching match history: {e}")
