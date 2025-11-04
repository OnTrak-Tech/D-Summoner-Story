"""
Shared data models and validation schemas for the League of Legends Year in Review application.
These models define the structure for API requests, responses, and internal data processing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, validator


# API Request/Response Models
class AuthRequest(BaseModel):
    summoner_name: str = Field(..., min_length=1, max_length=50)
    region: str = Field(..., pattern=r'^(na1|euw1|eun1|kr|br1|la1|la2|oc1|ru|tr1|jp1|sg2|tw2|vn2)$')


    @validator('summoner_name')
    def validate_summoner_name(cls, v):
        return v.strip()


class AuthResponse(BaseModel):
    session_id: str
    status: Literal["valid", "invalid"]


class FetchRequest(BaseModel):
    session_id: str
    summoner_name: str
    region: str


class ProcessRequest(BaseModel):
    session_id: str
    job_id: str


class RecapRequest(BaseModel):
    session_id: str


# Riot API Models
@dataclass
class RiotSummoner:
    id: str
    account_id: str
    puuid: str
    name: str
    profile_icon_id: int
    revision_date: int
    summoner_level: int


@dataclass
class RiotParticipant:
    summoner_id: str
    champion_id: int
    champion_name: str
    kills: int
    deaths: int
    assists: int
    win: bool
    game_duration: int
    item0: int = 0
    item1: int = 0
    item2: int = 0
    item3: int = 0
    item4: int = 0
    item5: int = 0
    item6: int = 0
    total_damage_dealt: int = 0
    gold_earned: int = 0
    cs_total: int = 0


@dataclass
class RiotMatch:
    match_id: str
    game_creation: int
    game_duration: int
    game_mode: str
    game_type: str
    queue_id: int
    participants: List[RiotParticipant]


# Statistics Models
@dataclass
class ChampionStat:
    champion_id: int
    champion_name: str
    games_played: int
    wins: int
    losses: int
    win_rate: float
    total_kills: int
    total_deaths: int
    total_assists: int
    avg_kda: float
    total_damage: int
    total_gold: int
    total_cs: int


@dataclass
class MonthlyData:
    month: str
    year: int
    games: int
    wins: int
    losses: int
    win_rate: float
    total_kills: int
    total_deaths: int
    total_assists: int
    avg_kda: float


@dataclass
class ProcessedStats:
    summoner_id: str
    summoner_name: str
    region: str
    total_games: int
    total_wins: int
    total_losses: int
    win_rate: float
    total_kills: int
    total_deaths: int
    total_assists: int
    avg_kda: float
    champion_stats: List[ChampionStat]
    monthly_trends: List[MonthlyData]
    most_played_champion: Optional[ChampionStat]
    highest_winrate_champion: Optional[ChampionStat]
    best_kda_champion: Optional[ChampionStat]
    improvement_trend: float  
    consistency_score: float  
    # AI Analytics fields
    highlight_matches: List[Dict[str, Any]] = field(default_factory=list)
    champion_improvements: List[str] = field(default_factory=list)
    behavioral_patterns: List[str] = field(default_factory=list)
    personality_profile: Optional[Dict[str, Any]] = None
    champion_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    next_season_prediction: Optional[Dict[str, Any]] = None
    rival_analysis: Optional[Dict[str, Any]] = None


# DynamoDB Models
class PlayerStatsItem(BaseModel):
    PK: str  
    SK: str  
    session_id: str
    summoner_name: str
    region: str
    total_games: int
    win_rate: float
    avg_kda: float
    champion_stats: List[Dict[str, Any]]
    monthly_trends: List[Dict[str, Any]]
    created_at: str
    ttl: int


class ProcessingJobItem(BaseModel):
    PK: str 
    session_id: str
    summoner_name: str
    region: str
    status: Literal["pending", "fetching", "processing", "generating", "completed", "failed"]
    progress: int = Field(ge=0, le=100)
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    ttl: int


# AI Generation Models
@dataclass
class BedrockPrompt:
    player_stats: ProcessedStats
    template_type: Literal["narrative", "highlights", "achievements"]
    tone: Literal["casual", "competitive", "humorous"] = "casual"


@dataclass
class GeneratedInsight:
    narrative: str
    highlights: List[str]
    achievements: List[str]
    fun_facts: List[str]
    recommendations: List[str]


# Frontend Response Models
class ChartConfig(BaseModel):
    chart_type: Literal["line", "bar", "pie", "doughnut", "radar"]
    data: Dict[str, Any]
    options: Dict[str, Any]


class RecapResponse(BaseModel):
    session_id: str
    summoner_name: str
    region: str
    narrative: str
    statistics: Dict[str, Any]
    visualizations: List[Dict[str, Any]]
    share_url: Optional[str] = None


# Error Models
class APIError(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Constants
RIOT_REGIONS = {
    "na1": "North America",
    "euw1": "Europe West", 
    "eun1": "Europe Nordic & East",
    "kr": "Korea",
    "br1": "Brazil",
    "la1": "Latin America North",
    "la2": "Latin America South", 
    "oc1": "Oceania",
    "ru": "Russia",
    "tr1": "Turkey",
    "jp1": "Japan"
}

QUEUE_TYPES = {
    420: "Ranked Solo/Duo",
    440: "Ranked Flex",
    400: "Normal Draft",
    430: "Normal Blind",
    450: "ARAM"
}

# Champion ID to name mapping (subset - full mapping would be loaded from Riot API)
CHAMPION_NAMES = {
    1: "Annie", 2: "Olaf", 3: "Galio", 4: "Twisted Fate", 5: "Xin Zhao",
    6: "Urgot", 7: "LeBlanc", 8: "Vladimir", 9: "Fiddlesticks", 10: "Kayle",
    # Add more as needed or load from Riot Data Dragon API
}