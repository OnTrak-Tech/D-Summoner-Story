"""
Shared utility functions for data processing, statistics calculation, and common operations.
"""

import json
import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import asdict
from decimal import Decimal
import logging

from .models import (
    RiotMatch, RiotParticipant, ProcessedStats, ChampionStat, 
    MonthlyData, PlayerStatsItem, ProcessingJobItem
)

logger = logging.getLogger(__name__)


def calculate_kda(kills: int, deaths: int, assists: int) -> float:
    """Calculate KDA ratio with proper handling of zero deaths"""
    if deaths == 0:
        return float(kills + assists) if (kills + assists) > 0 else 0.0
    return round((kills + assists) / deaths, 2)


def calculate_win_rate(wins: int, total_games: int) -> float:
    """Calculate win rate percentage"""
    if total_games == 0:
        return 0.0
    return round((wins / total_games) * 100, 2)


def get_month_year_from_timestamp(timestamp: int) -> Tuple[str, int]:
    """Convert timestamp to month name and year"""
    dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    return month_names[dt.month - 1], dt.year


def convert_floats_to_decimal(obj):
    """Recursively convert float values to Decimal for DynamoDB compatibility"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    else:
        return obj


def process_match_statistics(matches: List[RiotMatch], summoner_puuid: str) -> ProcessedStats:
    """
    Process raw match data into comprehensive statistics.
    This is the core analytics function that transforms Riot API data into insights.
    """
    print(f"UTILS: process_match_statistics called with {len(matches)} matches for PUUID {summoner_puuid}")
    
    if not matches:
        print("UTILS: No matches provided, raising ValueError")
        raise ValueError("No matches provided for processing")
    
    print(f"UTILS: Starting statistics processing for {len(matches)} matches")
    
    # Initialize counters
    total_games = len(matches)
    total_wins = 0
    total_kills = 0
    total_deaths = 0
    total_assists = 0
    summoner_name = ""
    region = ""
    
    # Champion statistics tracking
    champion_stats: Dict[int, Dict[str, Any]] = {}
    
    # Monthly statistics tracking
    monthly_stats: Dict[str, Dict[str, Any]] = {}
    
    # Process each match
    print(f"UTILS: Processing {len(matches)} matches...")
    for i, match in enumerate(matches):
        print(f"UTILS: Processing match {i+1}/{len(matches)}: {match.match_id}")
        
        # Find the correct summoner's participant data by PUUID
        summoner_participant = None
        print(f"UTILS: Looking for participant with PUUID {summoner_puuid} in {len(match.participants)} participants")
        
        for participant in match.participants:
            # Match by summoner_id as proxy for PUUID (in real implementation, use PUUID)
            if participant.summoner_id == summoner_puuid:
                summoner_participant = participant
                print(f"UTILS: Found matching participant for PUUID {summoner_puuid}")
                break
        
        if not summoner_participant:
            # If we can't find the summoner in this match, skip it
            print(f"UTILS: WARNING - Summoner {summoner_puuid} not found in match {match.match_id}")
            logger.warning(f"Summoner {summoner_puuid} not found in match {match.match_id}")
            continue
        
        print(f"UTILS: Processing stats for match {match.match_id}")
        
        # Update overall statistics
        if summoner_participant.win:
            total_wins += 1
        
        total_kills += summoner_participant.kills
        total_deaths += summoner_participant.deaths
        total_assists += summoner_participant.assists
        
        # Update champion statistics
        champ_id = summoner_participant.champion_id
        if champ_id not in champion_stats:
            champion_stats[champ_id] = {
                'champion_name': summoner_participant.champion_name,
                'games': 0,
                'wins': 0,
                'kills': 0,
                'deaths': 0,
                'assists': 0,
                'damage': 0,
                'gold': 0,
                'cs': 0
            }
        
        champ_data = champion_stats[champ_id]
        champ_data['games'] += 1
        if summoner_participant.win:
            champ_data['wins'] += 1
        champ_data['kills'] += summoner_participant.kills
        champ_data['deaths'] += summoner_participant.deaths
        champ_data['assists'] += summoner_participant.assists
        champ_data['damage'] += summoner_participant.total_damage_dealt
        champ_data['gold'] += summoner_participant.gold_earned
        champ_data['cs'] += summoner_participant.cs_total
        
        # Update monthly statistics
        month, year = get_month_year_from_timestamp(match.game_creation)
        month_key = f"{year}-{month}"
        
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                'month': month,
                'year': year,
                'games': 0,
                'wins': 0,
                'kills': 0,
                'deaths': 0,
                'assists': 0
            }
        
        month_data = monthly_stats[month_key]
        month_data['games'] += 1
        if summoner_participant.win:
            month_data['wins'] += 1
        month_data['kills'] += summoner_participant.kills
        month_data['deaths'] += summoner_participant.deaths
        month_data['assists'] += summoner_participant.assists
    
    # Recalculate total_games based on matches where summoner was found
    actual_games = sum(1 for match in matches if any(p.summoner_id == summoner_puuid for p in match.participants))
    total_games = actual_games
    
    if total_games == 0:
        raise ValueError(f"No matches found for summoner {summoner_puuid}")
    
    # Calculate overall statistics
    win_rate = calculate_win_rate(total_wins, total_games)
    avg_kda = calculate_kda(total_kills, total_deaths, total_assists)
    
    # Process champion statistics
    champion_stat_objects = []
    for champ_id, data in champion_stats.items():
        champ_stat = ChampionStat(
            champion_id=champ_id,
            champion_name=data['champion_name'],
            games_played=data['games'],
            wins=data['wins'],
            losses=data['games'] - data['wins'],
            win_rate=calculate_win_rate(data['wins'], data['games']),
            total_kills=data['kills'],
            total_deaths=data['deaths'],
            total_assists=data['assists'],
            avg_kda=calculate_kda(data['kills'], data['deaths'], data['assists']),
            total_damage=data['damage'],
            total_gold=data['gold'],
            total_cs=data['cs']
        )
        champion_stat_objects.append(champ_stat)
    
    # Sort champions by games played
    champion_stat_objects.sort(key=lambda x: x.games_played, reverse=True)
    
    # Process monthly statistics
    monthly_data_objects = []
    for month_key, data in monthly_stats.items():
        monthly_data = MonthlyData(
            month=data['month'],
            year=data['year'],
            games=data['games'],
            wins=data['wins'],
            losses=data['games'] - data['wins'],
            win_rate=calculate_win_rate(data['wins'], data['games']),
            total_kills=data['kills'],
            total_deaths=data['deaths'],
            total_assists=data['assists'],
            avg_kda=calculate_kda(data['kills'], data['deaths'], data['assists'])
        )
        monthly_data_objects.append(monthly_data)
    
    # Sort monthly data chronologically
    monthly_data_objects.sort(key=lambda x: (x.year, x.month))
    
    # Calculate improvement trend (simple linear regression on monthly KDA)
    improvement_trend = calculate_improvement_trend(monthly_data_objects)
    
    # Calculate consistency score (based on KDA variance)
    consistency_score = calculate_consistency_score(monthly_data_objects)
    
    # Identify highlight matches
    highlight_matches = identify_highlight_matches(matches, summoner_puuid)
    
    # Calculate champion improvements
    champion_improvements = calculate_champion_improvements(champion_stats)
    
    # Identify behavioral patterns
    behavioral_patterns = identify_behavioral_patterns(monthly_data_objects)
    
    # Find top performers
    most_played = champion_stat_objects[0] if champion_stat_objects else None
    highest_winrate = max(champion_stat_objects, key=lambda x: x.win_rate) if champion_stat_objects else None
    best_kda = max(champion_stat_objects, key=lambda x: x.avg_kda) if champion_stat_objects else None
    
    processed_stats = ProcessedStats(
        summoner_id=summoner_puuid,
        summoner_name=summoner_name if summoner_name else "Unknown Player",
        region=region,
        total_games=total_games,
        total_wins=total_wins,
        total_losses=total_games - total_wins,
        win_rate=win_rate,
        total_kills=total_kills,
        total_deaths=total_deaths,
        total_assists=total_assists,
        avg_kda=avg_kda,
        champion_stats=champion_stat_objects,
        monthly_trends=monthly_data_objects,
        most_played_champion=most_played,
        highest_winrate_champion=highest_winrate,
        best_kda_champion=best_kda,
        improvement_trend=improvement_trend,
        consistency_score=consistency_score
    )
    
    # Add new analytics data
    processed_stats.highlight_matches = highlight_matches
    processed_stats.champion_improvements = champion_improvements
    processed_stats.behavioral_patterns = behavioral_patterns
    
    return processed_stats


def calculate_improvement_trend(monthly_data: List[MonthlyData]) -> float:
    """Calculate improvement trend using simple linear regression on KDA"""
    if len(monthly_data) < 2:
        return 0.0
    
    # Use month index as x, KDA as y
    x_values = list(range(len(monthly_data)))
    y_values = [data.avg_kda for data in monthly_data]
    
    n = len(x_values)
    sum_x = sum(x_values)
    sum_y = sum(y_values)
    sum_xy = sum(x * y for x, y in zip(x_values, y_values))
    sum_x2 = sum(x * x for x in x_values)
    
    # Calculate slope (trend)
    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        return 0.0
    
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    return round(slope, 3)


def calculate_consistency_score(monthly_data: List[MonthlyData]) -> float:
    """Calculate consistency score based on KDA variance (0-100 scale)"""
    if len(monthly_data) < 2:
        return 100.0
    
    kda_values = [data.avg_kda for data in monthly_data]
    mean_kda = sum(kda_values) / len(kda_values)
    
    # Calculate variance
    variance = sum((kda - mean_kda) ** 2 for kda in kda_values) / len(kda_values)
    
    # Convert to consistency score (lower variance = higher consistency)
    # Scale to 0-100 where 100 is perfect consistency
    if variance == 0:
        return 100.0
    
    # Normalize variance to a 0-100 scale (this is a heuristic)
    consistency = max(0, 100 - (variance * 20))
    return round(consistency, 1)


def create_processing_job(session_id: str, summoner_name: str, region: str) -> ProcessingJobItem:
    """Create a new processing job item for DynamoDB"""
    job_id = generate_job_id(session_id, summoner_name, region)
    current_time = datetime.now(timezone.utc).isoformat()
    ttl = int(time.time()) + (7 * 24 * 60 * 60)  # 7 days TTL
    
    return ProcessingJobItem(
        PK=f"JOB#{job_id}",
        session_id=session_id,
        summoner_name=summoner_name,
        region=region,
        status="pending",
        progress=0,
        created_at=current_time,
        updated_at=current_time,
        ttl=ttl
    )


def create_player_stats_item(session_id: str, stats: ProcessedStats) -> PlayerStatsItem:
    """Create a player stats item for DynamoDB"""
    current_time = datetime.now(timezone.utc).isoformat()
    current_year = datetime.now().year
    ttl = int(time.time()) + (365 * 24 * 60 * 60)  # 1 year TTL
    
    # Convert dataclasses to dictionaries for DynamoDB storage
    champion_stats_dict = [asdict(champ) for champ in stats.champion_stats]
    monthly_trends_dict = [asdict(month) for month in stats.monthly_trends]
    
    return PlayerStatsItem(
        PK=f"PLAYER#{stats.summoner_id}",
        SK=f"STATS#{current_year}",
        session_id=session_id,
        summoner_name=stats.summoner_name,
        region=stats.region,
        total_games=stats.total_games,
        win_rate=Decimal(str(stats.win_rate)),
        avg_kda=Decimal(str(stats.avg_kda)),
        champion_stats=convert_floats_to_decimal(champion_stats_dict),
        monthly_trends=convert_floats_to_decimal(monthly_trends_dict),
        created_at=current_time,
        ttl=ttl
    )


def generate_job_id(session_id: str, summoner_name: str, region: str) -> str:
    """Generate a unique job ID"""
    data = f"{session_id}:{summoner_name}:{region}:{time.time()}"
    return hashlib.md5(data.encode()).hexdigest()


def generate_s3_key(summoner_id: str, data_type: str, timestamp: Optional[int] = None) -> str:
    """Generate S3 object key for data storage"""
    if timestamp is None:
        timestamp = int(time.time())
    
    year = datetime.fromtimestamp(timestamp).year
    month = datetime.fromtimestamp(timestamp).month
    
    return f"{data_type}/{summoner_id}/{year}/{month:02d}/{timestamp}.json"


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def format_lambda_response(status_code: int, body: Any, 
                          headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Format Lambda response with proper CORS headers"""
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body, cls=DecimalEncoder) if not isinstance(body, str) else body
    }


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration for Lambda functions"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def validate_region(region: str) -> bool:
    """Validate if region is supported"""
    valid_regions = {
        'na1', 'euw1', 'eun1', 'kr', 'br1', 
        'la1', 'la2', 'oc1', 'ru', 'tr1', 'jp1',
        'sg2', 'tw2', 'vn2'
    }
    return region in valid_regions


def sanitize_summoner_name(summoner_name: str) -> str:
    """Sanitize summoner name for API calls"""
    return summoner_name.strip().replace(" ", "")


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero"""
    return numerator / denominator if denominator != 0 else default


def get_current_timestamp() -> int:
    """Get current timestamp in seconds"""
    return int(time.time())


def get_current_iso_time() -> str:
    """Get current time in ISO format"""
    return datetime.now(timezone.utc).isoformat()

def identify_highlight_matches(matches: List[RiotMatch], summoner_puuid: str):
    scores = []
    for m in matches:
        p = next((x for x in m.participants if x.summoner_id == summoner_puuid), None)
        if p:
            kda = calculate_kda(p.kills, p.deaths, p.assists)
            scores.append({'kda': kda, 'kills': p.kills, 'deaths': p.deaths, 'assists': p.assists, 'champion': p.champion_name, 'win': p.win})
    scores.sort(key=lambda x: x['kda'], reverse=True)
    return scores[:3]

def calculate_champion_improvements(champion_stats):
    imps = []
    for cid, d in champion_stats.items():
        if d['games'] >= 10:
            wr = calculate_win_rate(d['wins'], d['games'])
            if wr > 55:
                imps.append({'champion': d['champion_name'], 'improvement': round(wr - 45, 1), 'win_rate': wr})
    imps.sort(key=lambda x: x['improvement'], reverse=True)
    return imps[:3]

def identify_behavioral_patterns(monthly_data):
    patterns = []
    if len(monthly_data) >= 3:
        avg = sum(m.avg_kda for m in monthly_data[-3:]) / 3
        if avg > 2.5:
            patterns.append("Consistently strong KDA performance")
        if monthly_data[-1].avg_kda > monthly_data[0].avg_kda * 1.2:
            patterns.append("Significant improvement from early to late season")
    return patterns[:5]