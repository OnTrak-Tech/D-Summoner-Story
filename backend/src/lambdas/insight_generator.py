"""
Insight Generator Lambda Function
Uses Amazon Bedrock to generate AI-powered narrative recaps from player statistics.
Creates engaging, personalized insights in the style of Spotify Wrapped.
"""

import json
import os
from typing import Any, Dict
import logging

# Import shared modules
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.models import ProcessedStats, GeneratedInsight, BedrockPrompt
from shared.aws_clients import (
    get_s3_client, get_dynamodb_client, get_bedrock_client,
    get_bucket_name, get_table_name, AWSClientError
)
from shared.utils import (
    format_lambda_response, setup_logging, generate_s3_key, get_current_timestamp
)

# Setup logging
setup_logging(os.environ.get('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)


def create_narrative_prompt(stats: ProcessedStats) -> str:
    """Create an engaging prompt for narrative generation"""
    
    # Determine player archetype based on stats
    if stats.avg_kda >= 2.0 and stats.win_rate >= 60:
        archetype = "dominant force"
    elif stats.avg_kda >= 1.5 and stats.win_rate >= 55:
        archetype = "skilled strategist"
    elif stats.improvement_trend > 0.1:
        archetype = "rising star"
    elif stats.consistency_score >= 80:
        archetype = "reliable teammate"
    else:
        archetype = "determined competitor"
    
    # Get top champion info
    top_champ = stats.most_played_champion
    best_kda_champ = stats.best_kda_champion
    
    prompt = f"""
Create an engaging League of Legends year-in-review narrative for {stats.summoner_name}, a {archetype} from the {stats.region} region.

PLAYER STATISTICS:
- Total Games: {stats.total_games}
- Win Rate: {stats.win_rate}%
- Average KDA: {stats.avg_kda}
- Most Played Champion: {top_champ.champion_name if top_champ else 'Various'} ({top_champ.games_played if top_champ else 0} games)
- Best KDA Champion: {best_kda_champ.champion_name if best_kda_champ else 'N/A'} ({best_kda_champ.avg_kda if best_kda_champ else 0} KDA)
- Improvement Trend: {stats.improvement_trend} (positive = improving)
- Consistency Score: {stats.consistency_score}/100

WRITING STYLE:
- Write like Spotify Wrapped but for League of Legends
- Use gaming terminology and League-specific references
- Be engaging, positive, and celebratory
- Include specific numbers and achievements
- Make it personal and relatable
- Keep it concise but impactful (200-300 words)

STRUCTURE:
1. Opening hook about their year in League
2. Highlight their main champion and playstyle
3. Mention their best achievements or improvements
4. Include a fun fact or interesting statistic
5. End with encouragement for the next season

Generate a narrative that makes {stats.summoner_name} feel proud of their League journey this year!
"""
    
    return prompt


def create_highlights_prompt(stats: ProcessedStats) -> str:
    """Create prompt for generating key highlights"""
    
    prompt = f"""
Based on these League of Legends statistics for {stats.summoner_name}, generate 5 key highlights in a fun, engaging style:

STATS:
- {stats.total_games} total games with {stats.win_rate}% win rate
- {stats.avg_kda} average KDA
- Most played: {stats.most_played_champion.champion_name if stats.most_played_champion else 'Various'}
- Best KDA: {stats.best_kda_champion.champion_name if stats.best_kda_champion else 'N/A'} ({stats.best_kda_champion.avg_kda if stats.best_kda_champion else 0})
- Improvement trend: {stats.improvement_trend}
- Consistency: {stats.consistency_score}/100

Generate exactly 5 bullet points, each highlighting a different achievement or interesting fact. Make them celebratory and specific to their performance.

Format as a JSON array of strings.
"""
    
    return prompt


def create_achievements_prompt(stats: ProcessedStats) -> str:
    """Create prompt for generating achievement badges"""
    
    achievements = []
    
    # Determine achievements based on stats
    if stats.win_rate >= 70:
        achievements.append("🏆 Challenger Mindset - 70%+ Win Rate")
    elif stats.win_rate >= 60:
        achievements.append("💎 Diamond Performance - 60%+ Win Rate")
    elif stats.win_rate >= 55:
        achievements.append("🥇 Gold Standard - 55%+ Win Rate")
    
    if stats.avg_kda >= 3.0:
        achievements.append("⚔️ KDA Warrior - 3.0+ Average KDA")
    elif stats.avg_kda >= 2.0:
        achievements.append("🎯 Precision Player - 2.0+ Average KDA")
    
    if stats.total_games >= 500:
        achievements.append("🎮 Dedicated Summoner - 500+ Games")
    elif stats.total_games >= 200:
        achievements.append("⚡ Active Player - 200+ Games")
    
    if stats.improvement_trend > 0.2:
        achievements.append("📈 Rising Star - Significant Improvement")
    elif stats.improvement_trend > 0.1:
        achievements.append("🌟 Getting Better - Steady Improvement")
    
    if stats.consistency_score >= 85:
        achievements.append("🎯 Mr. Reliable - 85%+ Consistency")
    elif stats.consistency_score >= 75:
        achievements.append("⚖️ Steady Performer - 75%+ Consistency")
    
    if stats.most_played_champion and stats.most_played_champion.games_played >= 50:
        achievements.append(f"🎭 {stats.most_played_champion.champion_name} Main - 50+ Games")
    
    return achievements


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for insight generation.
    
    Responsibilities:
    1. Load processed statistics from DynamoDB
    2. Generate AI-powered narrative using Amazon Bedrock
    3. Create highlights and achievements
    4. Cache generated insights in S3
    5. Return formatted insights for frontend
    """
    try:
        # Parse session ID from path parameters or body
        session_id = None
        
        if 'pathParameters' in event and event['pathParameters']:
            session_id = event['pathParameters'].get('sessionId')
        
        if not session_id:
            body = event.get("body", "{}")
            if isinstance(body, str):
                payload = json.loads(body)
            else:
                payload = body
            session_id = payload.get('session_id')
        
        if not session_id:
            return format_lambda_response(400, {
                "error": "MISSING_SESSION_ID",
                "message": "Session ID is required"
            })
        
        # Initialize AWS clients
        dynamodb_client = get_dynamodb_client()
        bedrock_client = get_bedrock_client()
        s3_client = get_s3_client()
        
        # Get table and bucket names
        player_stats_table = get_table_name("PLAYER_STATS")
        processed_insights_bucket = get_bucket_name("PROCESSED_INSIGHTS")
        
        logger.info(f"Generating insights for session {session_id}")
        
        # Check if insights already exist in S3 (caching)
        insights_key = f"insights/{session_id}/narrative.json"
        existing_insights = s3_client.get_object(processed_insights_bucket, insights_key)
        
        if existing_insights:
            logger.info(f"Found cached insights for session {session_id}")
            return format_lambda_response(200, json.loads(existing_insights))
        
        # Load player statistics from DynamoDB
        # Note: We need to query by session_id, which requires a GSI or scan
        # For now, we'll use a placeholder approach
        
        # In a real implementation, you'd query by GSI on session_id
        # For this example, we'll create mock statistics
        mock_stats = ProcessedStats(
            summoner_id="mock_summoner",
            summoner_name="TestSummoner",
            region="na1",
            total_games=150,
            total_wins=95,
            total_losses=55,
            win_rate=63.3,
            total_kills=1250,
            total_deaths=890,
            total_assists=1680,
            avg_kda=3.3,
            champion_stats=[],
            monthly_trends=[],
            most_played_champion=None,
            highest_winrate_champion=None,
            best_kda_champion=None,
            improvement_trend=0.15,
            consistency_score=78.5
        )
        
        try:
            # Generate narrative using Bedrock
            logger.info("Generating narrative with Bedrock")
            narrative_prompt = create_narrative_prompt(mock_stats)
            narrative = bedrock_client.invoke_claude(narrative_prompt, max_tokens=500)
            
            # Generate highlights
            logger.info("Generating highlights")
            highlights_prompt = create_highlights_prompt(mock_stats)
            highlights_response = bedrock_client.invoke_claude(highlights_prompt, max_tokens=300)
            
            # Parse highlights (expecting JSON array)
            try:
                highlights = json.loads(highlights_response)
                if not isinstance(highlights, list):
                    highlights = [highlights_response]  # Fallback if not JSON
            except json.JSONDecodeError:
                highlights = [highlights_response]  # Use raw response as single highlight
            
            # Generate achievements
            achievements = create_achievements_prompt(mock_stats)
            
            # Create fun facts
            fun_facts = [
                f"You played {mock_stats.total_games} games this year - that's like watching {mock_stats.total_games * 30 // 60} hours of League!",
                f"Your {mock_stats.avg_kda} KDA means you're definitely not feeding... most of the time 😉",
                f"With a {mock_stats.win_rate}% win rate, you're climbing faster than a Katarina combo!"
            ]
            
            # Create recommendations
            recommendations = []
            if mock_stats.avg_kda < 2.0:
                recommendations.append("Focus on positioning and map awareness to improve your KDA")
            if mock_stats.win_rate < 55:
                recommendations.append("Consider reviewing your champion pool and focusing on your best performers")
            if mock_stats.improvement_trend < 0:
                recommendations.append("Take breaks between games to avoid tilt and maintain performance")
            
            if not recommendations:
                recommendations = [
                    "Keep up the great work and maintain your winning streak!",
                    "Consider trying new champions to expand your versatility"
                ]
            
            # Create generated insight object
            generated_insight = GeneratedInsight(
                narrative=narrative,
                highlights=highlights[:5],  # Limit to 5 highlights
                achievements=achievements,
                fun_facts=fun_facts,
                recommendations=recommendations
            )
            
            # Prepare response data
            insight_data = {
                "session_id": session_id,
                "narrative": generated_insight.narrative,
                "highlights": generated_insight.highlights,
                "achievements": generated_insight.achievements,
                "fun_facts": generated_insight.fun_facts,
                "recommendations": generated_insight.recommendations,
                "generated_at": get_current_timestamp(),
                "statistics_summary": {
                    "total_games": mock_stats.total_games,
                    "win_rate": mock_stats.win_rate,
                    "avg_kda": mock_stats.avg_kda,
                    "improvement_trend": mock_stats.improvement_trend,
                    "consistency_score": mock_stats.consistency_score
                }
            }
            
            # Cache insights in S3
            s3_client.put_object(
                processed_insights_bucket,
                insights_key,
                json.dumps(insight_data, indent=2)
            )
            
            logger.info(f"Successfully generated and cached insights for session {session_id}")
            
            return format_lambda_response(200, insight_data)
            
        except AWSClientError as e:
            logger.error(f"AWS service error: {e}")
            return format_lambda_response(503, {
                "error": "SERVICE_ERROR",
                "message": "Failed to generate insights using AI services",
                "details": str(e)
            })
            
    except Exception as e:
        logger.error(f"Unexpected error in insight generator: {e}", exc_info=True)
        
        return format_lambda_response(500, {
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred during insight generation",
            "details": str(e)
        })
