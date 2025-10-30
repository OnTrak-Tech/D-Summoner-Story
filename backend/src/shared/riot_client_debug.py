"""
Enhanced Riot API client with comprehensive logging for debugging
"""

import logging
import time
from typing import Dict, Any, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import RiotSummoner, RiotMatch, RiotParticipant, CHAMPION_NAMES
from .aws_clients import get_secrets_client, AWSClientError

logger = logging.getLogger(__name__)

class RiotAPIClient:
    """Enhanced Riot API client with detailed logging"""
    
    BASE_URLS = {
        'na1': 'https://na1.api.riotgames.com',
        'euw1': 'https://euw1.api.riotgames.com',
        'eun1': 'https://eun1.api.riotgames.com',
        'kr': 'https://kr.api.riotgames.com',
        'br1': 'https://br1.api.riotgames.com',
        'la1': 'https://la1.api.riotgames.com',
        'la2': 'https://la2.api.riotgames.com',
        'oc1': 'https://oc1.api.riotgames.com',
        'ru': 'https://ru.api.riotgames.com',
        'tr1': 'https://tr1.api.riotgames.com',
        'jp1': 'https://jp1.api.riotgames.com',
        'sg2': 'https://sg2.api.riotgames.com',
        'tw2': 'https://tw2.api.riotgames.com',
        'vn2': 'https://vn2.api.riotgames.com'
    }
    
    REGIONAL_URLS = {
        'americas': 'https://americas.api.riotgames.com',
        'europe': 'https://europe.api.riotgames.com',
        'asia': 'https://asia.api.riotgames.com'
    }
    
    REGION_TO_REGIONAL = {
        'na1': 'americas', 'br1': 'americas', 'la1': 'americas', 'la2': 'americas',
        'euw1': 'europe', 'eun1': 'europe', 'tr1': 'europe', 'ru': 'europe',
        'kr': 'asia', 'jp1': 'asia', 'oc1': 'asia', 'sg2': 'asia', 'tw2': 'asia', 'vn2': 'asia'
    }
    
    def __init__(self, api_key: Optional[str] = None):
        print(f"RIOT CLIENT: Initializing with static API key: {bool(api_key)}")
        self._static_api_key = api_key
        self._cached_api_key = None
        self._api_key_cache_time = 0
        self._api_key_cache_ttl = 300
        
        if not api_key:
            try:
                self._secrets_client = get_secrets_client()
                print("RIOT CLIENT: Secrets client initialized")
            except AWSClientError as e:
                print(f"RIOT CLIENT: Failed to initialize secrets client: {e}")
                raise
        
        self.session = requests.Session()
        print("RIOT CLIENT: HTTP session created")
    
    def _make_request(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        """Enhanced request method with detailed logging"""
        print(f"RIOT CLIENT: Making request to {url}")
        
        headers = {
            'X-Riot-Token': self.api_key,
            'Accept': 'application/json'
        }
        print(f"RIOT CLIENT: Using API key ending in: ...{self.api_key[-4:] if self.api_key else 'None'}")

        for attempt in range(max_retries):
            try:
                print(f"RIOT CLIENT: Attempt {attempt + 1}/{max_retries}")
                response = self.session.get(url, headers=headers, timeout=10)
                
                print(f"RIOT CLIENT: Response status: {response.status_code}")
                print(f"RIOT CLIENT: Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"RIOT CLIENT: Success - received {len(str(data))} characters of data")
                    return data
                elif response.status_code == 404:
                    print("RIOT CLIENT: 404 - Resource not found")
                    raise Exception("Resource not found")
                elif response.status_code == 403:
                    print(f"RIOT CLIENT: 403 - Forbidden. Response: {response.text}")
                    raise Exception(f"Forbidden - API key issue: {response.text}")
                elif response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '60')
                    print(f"RIOT CLIENT: 429 - Rate limited. Retry after: {retry_after}s")
                    raise Exception(f"Rate limited - retry after {retry_after}s")
                else:
                    print(f"RIOT CLIENT: Error {response.status_code}: {response.text}")
                    raise Exception(f"HTTP {response.status_code}: {response.text}")

            except requests.exceptions.RequestException as e:
                print(f"RIOT CLIENT: Request exception on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Request failed after {max_retries} attempts: {e}")
                time.sleep(2 ** attempt)

        raise Exception("Max retries exceeded")
    
    @property
    def api_key(self) -> str:
        """Get API key with logging"""
        if self._static_api_key:
            print("RIOT CLIENT: Using static API key")
            return self._static_api_key
        
        print("RIOT CLIENT: Fetching API key from Secrets Manager")
        try:
            self._cached_api_key = self._secrets_client.get_riot_api_key(force_refresh=True)
            print(f"RIOT CLIENT: Retrieved API key ending in: ...{self._cached_api_key[-4:] if self._cached_api_key else 'None'}")
            return self._cached_api_key
        except Exception as e:
            print(f"RIOT CLIENT: Failed to get API key: {e}")
            raise
    
    def get_summoner_by_name(self, summoner_name: str, region: str) -> RiotSummoner:
        """Get summoner with detailed logging"""
        print(f"RIOT CLIENT: get_summoner_by_name({summoner_name}, {region})")
        
        if '#' in summoner_name:
            parts = summoner_name.split('#')
            print(f"RIOT CLIENT: Detected Riot ID format: {parts[0]}#{parts[1]}")
            return self.get_summoner_by_riot_id(parts[0], parts[1].upper(), region)
        
        default_tags = {'na1': 'NA1', 'euw1': 'EUW', 'eun1': 'EUNE', 'kr': 'KR1'}
        tag = default_tags.get(region, 'NA1')
        print(f"RIOT CLIENT: Using default tag {tag} for region {region}")
        return self.get_summoner_by_riot_id(summoner_name, tag, region)
    
    def get_summoner_by_riot_id(self, game_name: str, tag_line: str, region: str) -> RiotSummoner:
        """Get summoner by Riot ID with logging"""
        print(f"RIOT CLIENT: get_summoner_by_riot_id({game_name}, {tag_line}, {region})")
        
        regional_platform = self.REGION_TO_REGIONAL.get(region)
        print(f"RIOT CLIENT: Regional platform: {regional_platform}")
        
        try:
            # Step 1: Get PUUID from Riot ID
            base_url = self.REGIONAL_URLS[regional_platform]
            account_url = f"{base_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
            print(f"RIOT CLIENT: Fetching account data from: {account_url}")
            
            account_data = self._make_request(account_url)
            puuid = account_data['puuid']
            print(f"RIOT CLIENT: Got PUUID: {puuid}")
            
            # Step 2: Get summoner data from PUUID
            region_url = self.BASE_URLS[region]
            summoner_url = f"{region_url}/lol/summoner/v4/summoners/by-puuid/{puuid}"
            print(f"RIOT CLIENT: Fetching summoner data from: {summoner_url}")
            
            summoner_data = self._make_request(summoner_url)
            print(f"RIOT CLIENT: Got summoner data: {summoner_data}")
            
            return RiotSummoner(
                id=summoner_data.get('id', ''),
                account_id=summoner_data.get('accountId', ''),
                puuid=summoner_data.get('puuid', puuid),
                name=summoner_data.get('name', game_name),
                profile_icon_id=summoner_data.get('profileIconId', 0),
                revision_date=summoner_data.get('revisionDate', int(time.time() * 1000)),
                summoner_level=summoner_data.get('summonerLevel', 1)
            )
        except Exception as e:
            print(f"RIOT CLIENT: Error getting summoner: {e}")
            raise
    
    def get_match_history(self, puuid: str, region: str, count: int = 100, 
                         start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[str]:
        """Get match history with logging"""
        print(f"RIOT CLIENT: get_match_history(puuid={puuid[:8]}..., region={region}, count={count})")
        print(f"RIOT CLIENT: Time range: {start_time} to {end_time}")
        
        regional_platform = self.REGION_TO_REGIONAL.get(region)
        base_url = self.REGIONAL_URLS[regional_platform]
        url = f"{base_url}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        
        params = {'count': min(count, 100)}
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        if params:
            url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        print(f"RIOT CLIENT: Match history URL: {url}")
        
        try:
            match_ids = self._make_request(url)
            print(f"RIOT CLIENT: Retrieved {len(match_ids)} match IDs: {match_ids[:5]}...")
            return match_ids
        except Exception as e:
            print(f"RIOT CLIENT: Error getting match history: {e}")
            raise
    
    def get_full_match_history(self, summoner: RiotSummoner, region: str, 
                              months_back: int = 12) -> List[RiotMatch]:
        """Get full match history with comprehensive logging"""
        print(f"RIOT CLIENT: get_full_match_history for {summoner.name}, {months_back} months back")
        
        current_time = int(time.time())
        start_time = current_time - (months_back * 30 * 24 * 60 * 60)
        
        print(f"RIOT CLIENT: Time range: {start_time} to {current_time}")
        print(f"RIOT CLIENT: Using PUUID: {summoner.puuid}")
        
        try:
            match_ids = self.get_match_history(
                summoner.puuid, 
                region, 
                count=100,
                start_time=start_time * 1000,
                end_time=current_time * 1000
            )
            
            if not match_ids:
                print("RIOT CLIENT: No match IDs returned")
                return []
            
            print(f"RIOT CLIENT: Processing {len(match_ids)} matches")
            all_matches = []
            
            for i, match_id in enumerate(match_ids[:20]):  # Limit to 20 for dev API
                print(f"RIOT CLIENT: Processing match {i+1}/{min(len(match_ids), 20)}: {match_id}")
                try:
                    match_details = self.get_match_details(match_id, region)
                    all_matches.append(match_details)
                    time.sleep(0.1)  # Rate limiting
                except Exception as e:
                    print(f"RIOT CLIENT: Failed to get match {match_id}: {e}")
                    continue
            
            print(f"RIOT CLIENT: Successfully retrieved {len(all_matches)} matches")
            return all_matches
            
        except Exception as e:
            print(f"RIOT CLIENT: Error in get_full_match_history: {e}")
            raise
    
    def get_match_details(self, match_id: str, region: str) -> RiotMatch:
        """Get match details with logging"""
        regional_platform = self.REGION_TO_REGIONAL.get(region)
        base_url = self.REGIONAL_URLS[regional_platform]
        url = f"{base_url}/lol/match/v5/matches/{match_id}"
        
        try:
            data = self._make_request(url)
            
            participants = []
            for participant_data in data['info']['participants']:
                participant = RiotParticipant(
                    summoner_id=participant_data.get('summonerId', ''),
                    champion_id=participant_data['championId'],
                    champion_name=CHAMPION_NAMES.get(participant_data['championId'], f"Champion_{participant_data['championId']}"),
                    kills=participant_data['kills'],
                    deaths=participant_data['deaths'],
                    assists=participant_data['assists'],
                    win=participant_data['win'],
                    game_duration=data['info']['gameDuration'],
                    item0=participant_data.get('item0', 0),
                    item1=participant_data.get('item1', 0),
                    item2=participant_data.get('item2', 0),
                    item3=participant_data.get('item3', 0),
                    item4=participant_data.get('item4', 0),
                    item5=participant_data.get('item5', 0),
                    item6=participant_data.get('item6', 0),
                    total_damage_dealt=participant_data.get('totalDamageDealtToChampions', 0),
                    gold_earned=participant_data.get('goldEarned', 0),
                    cs_total=participant_data.get('totalMinionsKilled', 0) + participant_data.get('neutralMinionsKilled', 0)
                )
                participants.append(participant)
            
            return RiotMatch(
                match_id=data['metadata']['matchId'],
                game_creation=data['info']['gameCreation'],
                game_duration=data['info']['gameDuration'],
                game_mode=data['info']['gameMode'],
                game_type=data['info']['gameType'],
                queue_id=data['info']['queueId'],
                participants=participants
            )
        except Exception as e:
            print(f"RIOT CLIENT: Error getting match details: {e}")
            raise


def get_riot_client() -> RiotAPIClient:
    """Get debug Riot API client"""
    return RiotAPIClient()