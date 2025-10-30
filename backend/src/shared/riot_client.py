"""
Riot Games API client with rate limiting, error handling, and data transformation.
Handles all interactions with the League of Legends Developer API.
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


class RiotAPIError(Exception):
    """Custom exception for Riot API errors"""
    pass


class RateLimitExceeded(RiotAPIError):
    """Exception for rate limit exceeded"""
    pass


class SummonerNotFound(RiotAPIError):
    """Exception for summoner not found"""
    pass


class RiotAPIClient:
    """
    Riot Games API client with comprehensive error handling and rate limiting.
    Implements exponential backoff and circuit breaker patterns.
    """
    
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
        """Initialize Riot API client"""
        self._static_api_key = api_key
        self._cached_api_key = None
        self._api_key_cache_time = 0
        self._api_key_cache_ttl = 300  # 5 minutes
        
        if not api_key:
            # Initialize secrets client for dynamic key fetching
            try:
                self._secrets_client = get_secrets_client()
            except AWSClientError as e:
                logger.error(f"Failed to initialize secrets client: {e}")
                raise RiotAPIError(f"Failed to initialize Riot API client: {e}")
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Rate limiting state
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_reset = 0
        
        # Circuit breaker state
        self.failure_count = 0
        self.circuit_open_until = 0
        self.max_failures = 5
        self.circuit_timeout = 60  # seconds
    
    def _check_circuit_breaker(self):
        """Check if circuit breaker is open"""
        if self.circuit_open_until > time.time():
            raise RiotAPIError("Circuit breaker is open - too many failures")
        
        if self.circuit_open_until > 0:
            # Circuit breaker was open but timeout expired - reset
            self.failure_count = 0
            self.circuit_open_until = 0
            logger.info("Circuit breaker reset")
    
    def _make_request(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        """Make HTTP request with error handling and retries"""
        self._check_circuit_breaker()

        headers = {
            'X-Riot-Token': self.api_key,
            'Accept': 'application/json'
        }

        for attempt in range(max_retries):
            try:
                # Implement basic rate limiting
                current_time = time.time()
                if current_time - self.last_request_time < 1.2:  # 1.2 seconds between requests
                    time.sleep(1.2 - (current_time - self.last_request_time))

                logger.debug(f"Making request to {url}")
                response = self.session.get(url, headers=headers, timeout=10)
                self.last_request_time = time.time()

                # Handle rate limiting
                self._handle_rate_limit(response)

                if response.status_code == 200:
                    self.failure_count = 0  # Reset failure count on success
                    return response.json()
                elif response.status_code == 404:
                    raise SummonerNotFound("Summoner not found")
                elif response.status_code == 403:
                    if not self._static_api_key and attempt == 0:
                        logger.warning("403 error, attempting to refresh API key")
                        self._refresh_api_key()
                        headers['X-Riot-Token'] = self.api_key
                        continue
                    raise RiotAPIError("Forbidden - check API key")
                else:
                    response.raise_for_status()

            except RateLimitExceeded:
                if attempt == max_retries - 1:
                    raise
                continue
            except requests.exceptions.RequestException as e:
                self.failure_count += 1
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")

                if self.failure_count >= self.max_failures:
                    self.circuit_open_until = time.time() + self.circuit_timeout
                    logger.error("Circuit breaker opened due to too many failures")

                if attempt == max_retries - 1:
                    raise RiotAPIError(f"Request failed after {max_retries} attempts: {e}")

                # Exponential backoff
                wait_time = (2 ** attempt) + (time.time() % 1)
                time.sleep(wait_time)

        raise RiotAPIError("Max retries exceeded")
    
    def _handle_rate_limit(self, response: requests.Response):
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))  # Default to 60 seconds
            logger.warning(f"Rate limited, waiting {retry_after} seconds")
            time.sleep(retry_after)
            raise RateLimitExceeded(f"Rate limited, retry after {retry_after} seconds")
    
    @property
    def api_key(self) -> str:
        """Get API key with caching and refresh logic"""
        if self._static_api_key:
            return self._static_api_key
        
        current_time = time.time()
        if (self._cached_api_key and 
            current_time - self._api_key_cache_time < self._api_key_cache_ttl):
            return self._cached_api_key
        
        return self._refresh_api_key()
    
    def _refresh_api_key(self) -> str:
        """Refresh API key from AWS Secrets Manager"""
        try:
            self._cached_api_key = self._secrets_client.get_riot_api_key(force_refresh=True)
            self._api_key_cache_time = time.time()
            logger.info("API key refreshed from Secrets Manager")
            return self._cached_api_key
        except AWSClientError as e:
            logger.error(f"Failed to refresh API key: {e}")
            if self._cached_api_key:
                logger.warning("Using cached API key due to refresh failure")
                return self._cached_api_key
            raise RiotAPIError(f"Failed to get API key: {e}")
    
    def get_summoner_by_name(self, summoner_name: str, region: str) -> RiotSummoner:
        """Get summoner information by name (supports Riot ID format)"""
        # Enhanced input validation and logging for Riot ID
        logger.debug(f"get_summoner_by_name called with: {summoner_name}, region: {region}")
        if '#' in summoner_name:
            parts = summoner_name.split('#')
            if len(parts) == 2 and all(parts):
                logger.debug(f"Detected Riot ID format: {parts[0]}#{parts[1].upper()}")
                return self.get_summoner_by_riot_id(parts[0], parts[1].upper(), region)
            else:
                logger.error("Invalid Riot ID format. Expected 'GameName#TagLine'.")
                raise RiotAPIError("Invalid Riot ID format. Expected 'GameName#TagLine'.")
        
        # Default tag for regions without explicit tag
        default_tags = {
            'kr': 'KR1', 'na1': 'NA1', 'euw1': 'EUW', 'eun1': 'EUNE',
            'sg2': 'SG2', 'tw2': 'TW2', 'vn2': 'VN2'
        }
        tag = default_tags.get(region, 'NA1')
        return self.get_summoner_by_riot_id(summoner_name, tag, region)
    
    def get_summoner_by_riot_id(self, game_name: str, tag_line: str, region: str) -> RiotSummoner:
        """Get summoner information by Riot ID"""
        regional_platform = self.REGION_TO_REGIONAL.get(region)
        if not regional_platform:
            raise RiotAPIError(f"Invalid region: {region}")
        try:
            base_url = self.REGIONAL_URLS[regional_platform]
            account_url = f"{base_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
            account_data = self._make_request(account_url)
            puuid = account_data['puuid']
            
            region_url = self.BASE_URLS[region]
            summoner_url = f"{region_url}/lol/summoner/v4/summoners/by-puuid/{puuid}"
            summoner_data = self._make_request(summoner_url)
            
            # Handle flexible field mapping with fallbacks
            return RiotSummoner(
                id=summoner_data.get('id', summoner_data.get('summonerId', '')),
                account_id=summoner_data.get('accountId', summoner_data.get('account_id', '')),
                puuid=summoner_data.get('puuid', puuid),
                name=summoner_data.get('name', summoner_data.get('displayName', game_name)),
                profile_icon_id=summoner_data.get('profileIconId', summoner_data.get('profile_icon_id', 0)),
                revision_date=summoner_data.get('revisionDate', summoner_data.get('revision_date', int(time.time() * 1000))),
                summoner_level=summoner_data.get('summonerLevel', summoner_data.get('summoner_level', 1))
            )
        except SummonerNotFound:
            raise RiotAPIError(f"Summoner not found for Riot ID {game_name}#{tag_line} in {region}")
        except Exception as e:
            logger.error(f"Failed to get summoner {game_name}#{tag_line} in {region}: {e}")
            raise
    
    def get_match_history(self, puuid: str, region: str, count: int = 100, 
                         start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[str]:
        """Get match history for a player"""
        regional_platform = self.REGION_TO_REGIONAL.get(region)
        if not regional_platform:
            raise RiotAPIError(f"Invalid region for match history: {region}")
        
        base_url = self.REGIONAL_URLS[regional_platform]
        url = f"{base_url}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        
        params = {'count': min(count, 100)}  # API limit is 100
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        # Add query parameters to URL
        if params:
            url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        print(f"RIOT CLIENT: Calling match history API: {url}")
        logger.info(f"Match history API call: {url}")
        
        try:
            match_ids = self._make_request(url)
            print(f"RIOT CLIENT: API returned {len(match_ids)} match IDs")
            logger.info(f"Match history API returned {len(match_ids)} match IDs")
            return match_ids
        except Exception as e:
            print(f"RIOT CLIENT: Match history API failed: {e}")
            logger.error(f"Failed to get match history for {puuid}: {e}")
            raise
    
    def get_match_details(self, match_id: str, region: str) -> RiotMatch:
        """Get detailed match information"""
        regional_platform = self.REGION_TO_REGIONAL.get(region)
        if not regional_platform:
            raise RiotAPIError(f"Invalid region for match details: {region}")
        
        base_url = self.REGIONAL_URLS[regional_platform]
        url = f"{base_url}/lol/match/v5/matches/{match_id}"
        
        try:
            data = self._make_request(url)
            
            # Parse participants
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
            logger.error(f"Failed to get match details for {match_id}: {e}")
            raise
    
    def get_full_match_history_with_time(self, summoner: RiotSummoner, region: str, 
                                        start_time: int, end_time: int) -> List[RiotMatch]:
        """Get full match history for a summoner with explicit time range"""
        print(f"RIOT CLIENT: Using time range {start_time} to {end_time}")
        logger.info(f"Match history time range: {start_time} to {end_time}")
        
        all_matches = []
        start_index = 0
        batch_size = 100
        
        try:
            while True:
        
        all_matches = []
        start_index = 0
        batch_size = 100
        
        try:
            while True:
                # Get batch of match IDs
                match_ids = self.get_match_history(
                    summoner.puuid, 
                    region, 
                    count=batch_size,
                    start_time=start_time * 1000,  # Convert to milliseconds
                    end_time=end_time * 1000
                )
                
                if not match_ids:
                    print(f"RIOT CLIENT: No match IDs returned")
                    break
                
                print(f"RIOT CLIENT: Got {len(match_ids)} match IDs")
                
                # Get detailed match data
                for match_id in match_ids:
                    try:
                        match_details = self.get_match_details(match_id, region)
                        all_matches.append(match_details)
                        
                        # Add small delay to avoid rate limiting
                        time.sleep(0.1)
                        
                    except Exception as e:
                        logger.warning(f"Failed to get details for match {match_id}: {e}")
                        continue
                
                # If we got fewer matches than requested, we've reached the end
                if len(match_ids) < batch_size:
                    break
                
                start_index += batch_size
                
                # Safety limit to avoid infinite loops
                if len(all_matches) >= 1000:
                    logger.warning("Reached maximum match limit (1000)")
                    break
            
            logger.info(f"Retrieved {len(all_matches)} matches for {summoner.name}")
            return all_matches
            
        except Exception as e:
            logger.error(f"Failed to get full match history: {e}")
            raise
    
    def get_full_match_history(self, summoner: RiotSummoner, region: str, 
                              months_back: int = 12) -> List[RiotMatch]:
        """Get full match history for a summoner over specified months"""
        # Calculate time range (last N months)
        now = int(time.time())
        past_12_months = now - (months_back * 30 * 24 * 60 * 60)  # months_back months ago
        return self.get_full_match_history_with_time(summoner, region, past_12_months, now)


# Singleton instance for Lambda reuse
_riot_client = None


def get_riot_client() -> RiotAPIClient:
    """Get singleton Riot API client"""
    global _riot_client
    if _riot_client is None:
        _riot_client = RiotAPIClient()
    return _riot_client