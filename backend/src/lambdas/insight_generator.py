"""
Insight Generator Lambda Function
Uses Amazon Bedrock to generate AI-powered narrative recaps from player statistics.
Creates engaging, personalized insights in the style of Spotify Wrapped.
"""

print("INSIGHT GENERATOR STARTING...")

import json
import os
from typing import Any, Dict
import logging

# Import shared modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.models import ProcessedStats, GeneratedInsight, BedrockPrompt
from shared.aws_clients import (
    get_s3_client, get_dynamodb_client, get_bedrock_client,
    get_bucket_name, get_table_name, AWSClientError
)
from shared.utils import (
    format_lambda_response, setup_logging, generate_s3_key, get_current_timestamp,
    analyze_personality_profile, suggest_champion_matches,
    predict_next_season, generate_rival_analysis
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
    print(f"INSIGHT GENERATOR HANDLER STARTED: {event}")
    logger.info(f"Insight generator invoked with event: {json.dumps(event)}")
    
    try:
        # Parse session ID from direct invocation, path parameters, or body
        session_id = None
        
        print("INSIGHT GENERATOR: Parsing session ID...")
        
        # Direct Lambda invocation (from data processor)
        if 'session_id' in event:
            session_id = event['session_id']
            print(f"INSIGHT GENERATOR: Session ID from direct invocation: {session_id}")
            logger.info(f"Session ID from direct invocation: {session_id}")
        
        # API Gateway invocation
        elif 'pathParameters' in event and event['pathParameters']:
            session_id = event['pathParameters'].get('sessionId')
            print(f"INSIGHT GENERATOR: Session ID from path parameters: {session_id}")
            logger.info(f"Session ID from path parameters: {session_id}")
        
        # Body parameter
        elif 'body' in event:
            body = event.get("body", "{}")
            if isinstance(body, str):
                payload = json.loads(body)
            else:
                payload = body
            session_id = payload.get('session_id')
            print(f"INSIGHT GENERATOR: Session ID from body: {session_id}")
            logger.info(f"Session ID from body: {session_id}")
        
        if not session_id:
            print(f"INSIGHT GENERATOR: ERROR - No session ID found in event: {event}")
            logger.error(f"No session ID found in event: {event}")
            return format_lambda_response(400, {
                "error": "MISSING_SESSION_ID",
                "message": "Session ID is required"
            })
        
        print("INSIGHT GENERATOR: Initializing AWS clients...")
        
        # Initialize AWS clients
        try:
            dynamodb_client = get_dynamodb_client()
            print("INSIGHT GENERATOR: DynamoDB client initialized")
        except Exception as e:
            print(f"INSIGHT GENERATOR: ERROR - Failed to initialize DynamoDB client: {e}")
            raise
        
        try:
            bedrock_client = get_bedrock_client()
            print("INSIGHT GENERATOR: Bedrock client initialized")
        except Exception as e:
            print(f"INSIGHT GENERATOR: ERROR - Failed to initialize Bedrock client: {e}")
            raise
        
        try:
            s3_client = get_s3_client()
            print("INSIGHT GENERATOR: S3 client initialized")
        except Exception as e:
            print(f"INSIGHT GENERATOR: ERROR - Failed to initialize S3 client: {e}")
            raise
        
        # Get table and bucket names
        try:
            player_stats_table = get_table_name("PLAYER_STATS")
            processed_insights_bucket = get_bucket_name("PROCESSED_INSIGHTS")
            print(f"INSIGHT GENERATOR: Table: {player_stats_table}, Bucket: {processed_insights_bucket}")
        except Exception as e:
            print(f"INSIGHT GENERATOR: ERROR - Failed to get table/bucket names: {e}")
            raise
        
        print(f"INSIGHT GENERATOR: Generating insights for session {session_id}")
        logger.info(f"Generating insights for session {session_id}")
        
        # Check if insights already exist in S3 (caching)
        insights_key = f"insights/{session_id}/narrative.json"
        print(f"INSIGHT GENERATOR: Checking for cached insights at key: {insights_key}")
        
        try:
            existing_insights = s3_client.get_object(processed_insights_bucket, insights_key)
            if existing_insights:
                print(f"INSIGHT GENERATOR: Found cached insights for session {session_id}")
                logger.info(f"Found cached insights for session {session_id}")
                return format_lambda_response(200, json.loads(existing_insights))
        except Exception as e:
            print(f"INSIGHT GENERATOR: No cached insights found (expected): {e}")
        
        # Load player statistics from DynamoDB by scanning for session_id
        print(f"INSIGHT GENERATOR: Scanning DynamoDB table {player_stats_table} for session_id: {session_id}")
        
        try:
            scan_result = dynamodb_client.scan_table(
                player_stats_table,
                filter_expression="session_id = :session_id",
                expression_values={":session_id": session_id}
            )
            print(f"INSIGHT GENERATOR: Scan result: {scan_result}")
        except Exception as e:
            print(f"INSIGHT GENERATOR: ERROR - DynamoDB scan failed: {e}")
            raise
        
        if not scan_result:
            print(f"INSIGHT GENERATOR: No statistics found for session {session_id}")
            return format_lambda_response(404, {
                "error": "NO_INSIGHTS",
                "message": f"No insights found for session {session_id}. Generate insights first."
            })
        
        # Use the first (and should be only) result
        stats_data = scan_result[0]
        
        # Get actual summoner name from DynamoDB data
        actual_summoner_name = stats_data.get('summoner_name', 'Unknown')
        if actual_summoner_name.startswith('Player_'):
            # Clean up the encoded summoner name
            actual_summoner_name = actual_summoner_name.replace('Player_', '').replace('%20', ' ')
        
        # Create ProcessedStats object from DynamoDB data with real values
        total_games = int(stats_data.get('total_games', 0))
        win_rate = float(stats_data.get('win_rate', 0))
        avg_kda = float(stats_data.get('avg_kda', 0))
        
        # Calculate derived stats
        total_wins = int(total_games * win_rate / 100)
        total_losses = total_games - total_wins
        
        # Estimate kills/deaths/assists from KDA and games
        estimated_deaths_per_game = max(1, 8 - (avg_kda * 2))  
        total_deaths = int(total_games * estimated_deaths_per_game)
        total_kills_assists = int(total_deaths * avg_kda)
        total_kills = int(total_kills_assists * 0.4)  
        total_assists = total_kills_assists - total_kills
        
        # Parse champion stats from DynamoDB
        champion_stats_data = stats_data.get('champion_stats', [])
        champion_stats_objects = []
        
        # Convert champion stats if available
        if champion_stats_data:
            from shared.models import ChampionStat
            for champ_data in champion_stats_data[:5]:  
                champ_stat = ChampionStat(
                    champion_id=champ_data.get('champion_id', 0),
                    champion_name=champ_data.get('champion_name', 'Unknown'),
                    games_played=int(champ_data.get('games_played', 0)),
                    wins=int(champ_data.get('wins', 0)),
                    losses=int(champ_data.get('losses', 0)),
                    win_rate=float(champ_data.get('win_rate', 0)),
                    total_kills=int(champ_data.get('total_kills', 0)),
                    total_deaths=int(champ_data.get('total_deaths', 0)),
                    total_assists=int(champ_data.get('total_assists', 0)),
                    avg_kda=float(champ_data.get('avg_kda', 0)),
                    total_damage=int(champ_data.get('total_damage', 0)),
                    total_gold=int(champ_data.get('total_gold', 0)),
                    total_cs=int(champ_data.get('total_cs', 0))
                )
                champion_stats_objects.append(champ_stat)
        
        # Get most played and best performing champions
        most_played_champion = champion_stats_objects[0] if champion_stats_objects else None
        best_kda_champion = max(champion_stats_objects, key=lambda x: x.avg_kda) if champion_stats_objects else None
        highest_winrate_champion = max(champion_stats_objects, key=lambda x: x.win_rate) if champion_stats_objects else None
        
        # Calculate improvement trend from monthly data if available
        monthly_trends_data = stats_data.get('monthly_trends', [])
        improvement_trend = 0.0
        consistency_score = 75.0
        
        if len(monthly_trends_data) >= 2:
            # Calculate trend from first to last month
            first_month_kda = float(monthly_trends_data[0].get('avg_kda', avg_kda))
            last_month_kda = float(monthly_trends_data[-1].get('avg_kda', avg_kda))
            improvement_trend = (last_month_kda - first_month_kda) / max(1, len(monthly_trends_data))
            
            # Calculate consistency as inverse of KDA variance
            kda_values = [float(month.get('avg_kda', avg_kda)) for month in monthly_trends_data]
            if len(kda_values) > 1:
                mean_kda = sum(kda_values) / len(kda_values)
                variance = sum((kda - mean_kda) ** 2 for kda in kda_values) / len(kda_values)
                consistency_score = max(0, min(100, 100 - (variance * 20)))
        
        real_stats = ProcessedStats(
            summoner_id=stats_data.get('PK', '').replace('PLAYER#', ''),
            summoner_name=actual_summoner_name,
            region=stats_data.get('region', 'unknown'),
            total_games=total_games,
            total_wins=total_wins,
            total_losses=total_losses,
            win_rate=win_rate,
            total_kills=total_kills,
            total_deaths=total_deaths,
            total_assists=total_assists,
            avg_kda=avg_kda,
            champion_stats=champion_stats_objects,
            monthly_trends=[], 
            most_played_champion=most_played_champion,
            highest_winrate_champion=highest_winrate_champion,
            best_kda_champion=best_kda_champion,
            improvement_trend=improvement_trend,
            consistency_score=consistency_score
        )
        
        try:
            # Generate narrative using Bedrock
            print("INSIGHT GENERATOR: Generating narrative with Bedrock...")
            logger.info("Generating narrative with Bedrock")
            
            try:
                narrative_prompt = create_narrative_prompt(real_stats)
                print(f"INSIGHT GENERATOR: Created narrative prompt (length: {len(narrative_prompt)})")
                
                narrative = bedrock_client.invoke_claude(narrative_prompt, max_tokens=500)
                print(f"INSIGHT GENERATOR: Generated narrative (length: {len(narrative)})")
            except Exception as e:
                print(f"INSIGHT GENERATOR: ERROR - Bedrock narrative generation failed: {e}")
                raise
            
            # Generate highlights
            print("INSIGHT GENERATOR: Generating highlights...")
            logger.info("Generating highlights")
            
            try:
                highlights_prompt = create_highlights_prompt(real_stats)
                highlights_response = bedrock_client.invoke_claude(highlights_prompt, max_tokens=300)
                print(f"INSIGHT GENERATOR: Generated highlights response (length: {len(highlights_response)})")
            except Exception as e:
                print(f"INSIGHT GENERATOR: ERROR - Bedrock highlights generation failed: {e}")
                raise
            
            # Parse highlights (expecting JSON array)
            try:
                highlights = json.loads(highlights_response)
                if not isinstance(highlights, list):
                    highlights = [highlights_response]  
            except json.JSONDecodeError:
                highlights = [highlights_response]  
            
            # Generate achievements
            achievements = create_achievements_prompt(real_stats)
            
            # Create fun facts with real data
            fun_facts = [
                f"You played {real_stats.total_games} games this year - that's like watching {real_stats.total_games * 30 // 60} hours of League!",
                f"Your {real_stats.avg_kda} KDA means you're definitely not feeding... most of the time 😉",
                f"With a {real_stats.win_rate}% win rate, you're climbing faster than a Katarina combo!"
            ]
            
            # Add champion-specific fun facts
            if real_stats.most_played_champion:
                fun_facts.append(f"You're practically married to {real_stats.most_played_champion.champion_name} with {real_stats.most_played_champion.games_played} games!")
            
            if real_stats.best_kda_champion and real_stats.best_kda_champion != real_stats.most_played_champion:
                fun_facts.append(f"Your secret weapon: {real_stats.best_kda_champion.champion_name} with a {real_stats.best_kda_champion.avg_kda} KDA!")
            
            # Create recommendations based on real performance
            recommendations = []
            if real_stats.avg_kda < 2.0:
                recommendations.append("Focus on positioning and map awareness to improve your KDA")
            if real_stats.win_rate < 55:
                recommendations.append("Consider reviewing your champion pool and focusing on your best performers")
            if real_stats.improvement_trend < 0:
                recommendations.append("Take breaks between games to avoid tilt and maintain performance")
            if real_stats.consistency_score < 70:
                recommendations.append("Work on maintaining consistent performance across all games")
            
            if not recommendations:
                recommendations = [
                    "Keep up the great work and maintain your winning streak!",
                    "Consider trying new champions to expand your versatility"
                ]
            
            # Placeholder for advanced analytics (would be calculated in data processing)
            champion_improvements = []
            behavioral_insights = []
            
            # Create generated insight object
            generated_insight = GeneratedInsight(
                narrative=narrative,
                highlights=highlights[:5], 
                achievements=achievements,
                fun_facts=fun_facts,
                recommendations=recommendations
            )
            
            # Generate new AI features using real data
            from shared.utils import (
                analyze_personality_profile, suggest_champion_matches,
                predict_next_season, generate_rival_analysis
            )
            
            personality_profile = analyze_personality_profile(real_stats)
            champion_suggestions = suggest_champion_matches(real_stats)
            next_season_prediction = predict_next_season(real_stats)
            rival_analysis = generate_rival_analysis(real_stats)
            
            # Prepare response data with new analytics
            insight_data = {
                "session_id": session_id,
                "narrative": generated_insight.narrative,
                "highlights": generated_insight.highlights,
                "achievements": generated_insight.achievements,
                "fun_facts": generated_insight.fun_facts,
                "recommendations": generated_insight.recommendations,
                "highlight_matches": real_stats.highlight_matches,
                "champion_improvements": champion_improvements,
                "behavioral_patterns": behavioral_insights,
                "personality_profile": personality_profile,
                "champion_suggestions": champion_suggestions,
                "next_season_prediction": next_season_prediction,
                "rival_analysis": rival_analysis,
                "generated_at": get_current_timestamp(),
                "statistics_summary": {
                    "summoner_name": real_stats.summoner_name,
                    "region": real_stats.region,
                    "total_games": real_stats.total_games,
                    "win_rate": real_stats.win_rate,
                    "avg_kda": real_stats.avg_kda,
                    "improvement_trend": real_stats.improvement_trend,
                    "consistency_score": real_stats.consistency_score
                }
            }
            
            # Cache insights in S3
            print(f"INSIGHT GENERATOR: Caching insights to S3 key: {insights_key}")
            try:
                s3_client.put_object(
                    processed_insights_bucket,
                    insights_key,
                    json.dumps(insight_data, indent=2)
                )
                print("INSIGHT GENERATOR: Successfully cached insights to S3")
            except Exception as e:
                print(f"INSIGHT GENERATOR: ERROR - Failed to cache insights to S3: {e}")
                # Continue anyway, don't fail the whole function
            
            print(f"INSIGHT GENERATOR: Successfully generated insights for session {session_id}")
            logger.info(f"Successfully generated and cached insights for session {session_id}")
            
            return format_lambda_response(200, insight_data)
            
        except AWSClientError as e:
            print(f"INSIGHT GENERATOR: AWS service error: {e}")
            logger.error(f"AWS service error: {e}")
            return format_lambda_response(503, {
                "error": "SERVICE_ERROR",
                "message": "Failed to generate insights using AI services",
                "details": str(e)
            })
            
    except Exception as e:
        print(f"INSIGHT GENERATOR: Unexpected error: {e}")
        logger.error(f"Unexpected error in insight generator: {e}", exc_info=True)
        
        return format_lambda_response(500, {
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred during insight generation",
            "details": str(e)
        })
