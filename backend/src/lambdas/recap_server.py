"""
Recap Server Lambda Function
Aggregates processed statistics and AI-generated insights for frontend consumption.
Serves complete year-in-review data with chart configurations and sharing capabilities.
"""

import json
import os
from typing import Any, Dict, List
import logging

# Import shared modules
import sys
sys.path.append('/opt/python') 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.models import RecapResponse, ChartConfig
from shared.aws_clients import get_s3_client, get_dynamodb_client, get_bucket_name, get_table_name
from shared.utils import format_lambda_response, setup_logging, get_current_timestamp

# Setup logging
setup_logging(os.environ.get('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Champion role and playstyle mapping for constellation visualization
CHAMPION_METADATA = {
    'Jinx': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Caitlyn': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Vayne': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Ezreal': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Yasuo': {'role': 'Mid', 'playstyle': 'Assassin'},
    'Zed': {'role': 'Mid', 'playstyle': 'Assassin'},
    'Ahri': {'role': 'Mid', 'playstyle': 'Mage'},
    'Lux': {'role': 'Mid', 'playstyle': 'Mage'},
    'Syndra': {'role': 'Mid', 'playstyle': 'Mage'},
    'Graves': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Lee Sin': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Thresh': {'role': 'Support', 'playstyle': 'Support'},
    'Leona': {'role': 'Support', 'playstyle': 'Tank'},
    'Garen': {'role': 'Top', 'playstyle': 'Tank'},
    'Darius': {'role': 'Top', 'playstyle': 'Fighter'},
    'Aatrox': {'role': 'Top', 'playstyle': 'Fighter'},
    'Akali': {'role': 'Mid', 'playstyle': 'Assassin'},
    'Alistar': {'role': 'Support', 'playstyle': 'Tank'},
    'Amumu': {'role': 'Jungle', 'playstyle': 'Tank'},
    'Anivia': {'role': 'Mid', 'playstyle': 'Mage'},
    'Annie': {'role': 'Mid', 'playstyle': 'Mage'},
    'Ashe': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Azir': {'role': 'Mid', 'playstyle': 'Mage'},
    'Bard': {'role': 'Support', 'playstyle': 'Support'},
    'Blitzcrank': {'role': 'Support', 'playstyle': 'Support'},
    'Brand': {'role': 'Support', 'playstyle': 'Mage'},
    'Braum': {'role': 'Support', 'playstyle': 'Tank'},
    'Camille': {'role': 'Top', 'playstyle': 'Fighter'},
    'Cassiopeia': {'role': 'Mid', 'playstyle': 'Mage'},
    'Cho\'Gath': {'role': 'Top', 'playstyle': 'Tank'},
    'Corki': {'role': 'Mid', 'playstyle': 'Marksman'},
    'Diana': {'role': 'Jungle', 'playstyle': 'Assassin'},
    'Draven': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Ekko': {'role': 'Jungle', 'playstyle': 'Assassin'},
    'Elise': {'role': 'Jungle', 'playstyle': 'Mage'},
    'Evelynn': {'role': 'Jungle', 'playstyle': 'Assassin'},
    'Fiddlesticks': {'role': 'Jungle', 'playstyle': 'Mage'},
    'Fiora': {'role': 'Top', 'playstyle': 'Fighter'},
    'Fizz': {'role': 'Mid', 'playstyle': 'Assassin'},
    'Galio': {'role': 'Mid', 'playstyle': 'Tank'},
    'Gangplank': {'role': 'Top', 'playstyle': 'Fighter'},
    'Gnar': {'role': 'Top', 'playstyle': 'Fighter'},
    'Gragas': {'role': 'Jungle', 'playstyle': 'Tank'},
    'Hecarim': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Heimerdinger': {'role': 'Mid', 'playstyle': 'Mage'},
    'Illaoi': {'role': 'Top', 'playstyle': 'Fighter'},
    'Irelia': {'role': 'Top', 'playstyle': 'Fighter'},
    'Ivern': {'role': 'Jungle', 'playstyle': 'Support'},
    'Janna': {'role': 'Support', 'playstyle': 'Support'},
    'Jarvan IV': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Jax': {'role': 'Top', 'playstyle': 'Fighter'},
    'Jayce': {'role': 'Top', 'playstyle': 'Fighter'},
    'Jhin': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Kai\'Sa': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Kalista': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Karma': {'role': 'Support', 'playstyle': 'Support'},
    'Karthus': {'role': 'Jungle', 'playstyle': 'Mage'},
    'Kassadin': {'role': 'Mid', 'playstyle': 'Assassin'},
    'Katarina': {'role': 'Mid', 'playstyle': 'Assassin'},
    'Kayle': {'role': 'Top', 'playstyle': 'Fighter'},
    'Kayn': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Kennen': {'role': 'Top', 'playstyle': 'Mage'},
    'Kha\'Zix': {'role': 'Jungle', 'playstyle': 'Assassin'},
    'Kindred': {'role': 'Jungle', 'playstyle': 'Marksman'},
    'Kled': {'role': 'Top', 'playstyle': 'Fighter'},
    'Kog\'Maw': {'role': 'ADC', 'playstyle': 'Marksman'},
    'LeBlanc': {'role': 'Mid', 'playstyle': 'Assassin'},
    'Lissandra': {'role': 'Mid', 'playstyle': 'Mage'},
    'Lucian': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Lulu': {'role': 'Support', 'playstyle': 'Support'},
    'Malphite': {'role': 'Top', 'playstyle': 'Tank'},
    'Malzahar': {'role': 'Mid', 'playstyle': 'Mage'},
    'Maokai': {'role': 'Support', 'playstyle': 'Tank'},
    'Master Yi': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Miss Fortune': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Mordekaiser': {'role': 'Top', 'playstyle': 'Fighter'},
    'Morgana': {'role': 'Support', 'playstyle': 'Support'},
    'Nami': {'role': 'Support', 'playstyle': 'Support'},
    'Nasus': {'role': 'Top', 'playstyle': 'Fighter'},
    'Nautilus': {'role': 'Support', 'playstyle': 'Tank'},
    'Nidalee': {'role': 'Jungle', 'playstyle': 'Assassin'},
    'Nocturne': {'role': 'Jungle', 'playstyle': 'Assassin'},
    'Nunu': {'role': 'Jungle', 'playstyle': 'Tank'},
    'Olaf': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Orianna': {'role': 'Mid', 'playstyle': 'Mage'},
    'Ornn': {'role': 'Top', 'playstyle': 'Tank'},
    'Pantheon': {'role': 'Support', 'playstyle': 'Fighter'},
    'Poppy': {'role': 'Top', 'playstyle': 'Tank'},
    'Pyke': {'role': 'Support', 'playstyle': 'Assassin'},
    'Qiyana': {'role': 'Mid', 'playstyle': 'Assassin'},
    'Quinn': {'role': 'Top', 'playstyle': 'Marksman'},
    'Rakan': {'role': 'Support', 'playstyle': 'Support'},
    'Rammus': {'role': 'Jungle', 'playstyle': 'Tank'},
    'Rek\'Sai': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Renekton': {'role': 'Top', 'playstyle': 'Fighter'},
    'Rengar': {'role': 'Jungle', 'playstyle': 'Assassin'},
    'Riven': {'role': 'Top', 'playstyle': 'Fighter'},
    'Rumble': {'role': 'Top', 'playstyle': 'Mage'},
    'Ryze': {'role': 'Mid', 'playstyle': 'Mage'},
    'Sejuani': {'role': 'Jungle', 'playstyle': 'Tank'},
    'Senna': {'role': 'Support', 'playstyle': 'Marksman'},
    'Seraphine': {'role': 'Support', 'playstyle': 'Support'},
    'Sett': {'role': 'Top', 'playstyle': 'Fighter'},
    'Shaco': {'role': 'Jungle', 'playstyle': 'Assassin'},
    'Shen': {'role': 'Top', 'playstyle': 'Tank'},
    'Shyvana': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Singed': {'role': 'Top', 'playstyle': 'Tank'},
    'Sion': {'role': 'Top', 'playstyle': 'Tank'},
    'Sivir': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Skarner': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Sona': {'role': 'Support', 'playstyle': 'Support'},
    'Soraka': {'role': 'Support', 'playstyle': 'Support'},
    'Swain': {'role': 'Support', 'playstyle': 'Mage'},
    'Sylas': {'role': 'Mid', 'playstyle': 'Assassin'},
    'Tahm Kench': {'role': 'Support', 'playstyle': 'Tank'},
    'Taliyah': {'role': 'Jungle', 'playstyle': 'Mage'},
    'Talon': {'role': 'Mid', 'playstyle': 'Assassin'},
    'Taric': {'role': 'Support', 'playstyle': 'Support'},
    'Teemo': {'role': 'Top', 'playstyle': 'Marksman'},
    'Tristana': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Trundle': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Tryndamere': {'role': 'Top', 'playstyle': 'Fighter'},
    'Twisted Fate': {'role': 'Mid', 'playstyle': 'Mage'},
    'Twitch': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Udyr': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Urgot': {'role': 'Top', 'playstyle': 'Fighter'},
    'Varus': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Veigar': {'role': 'Mid', 'playstyle': 'Mage'},
    'Vel\'Koz': {'role': 'Support', 'playstyle': 'Mage'},
    'Vi': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Viktor': {'role': 'Mid', 'playstyle': 'Mage'},
    'Vladimir': {'role': 'Mid', 'playstyle': 'Mage'},
    'Volibear': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Warwick': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Wukong': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Xayah': {'role': 'ADC', 'playstyle': 'Marksman'},
    'Xerath': {'role': 'Mid', 'playstyle': 'Mage'},
    'Xin Zhao': {'role': 'Jungle', 'playstyle': 'Fighter'},
    'Yorick': {'role': 'Top', 'playstyle': 'Fighter'},
    'Yuumi': {'role': 'Support', 'playstyle': 'Support'},
    'Zac': {'role': 'Jungle', 'playstyle': 'Tank'},
    'Ziggs': {'role': 'Mid', 'playstyle': 'Mage'},
    'Zilean': {'role': 'Support', 'playstyle': 'Support'},
    'Zoe': {'role': 'Mid', 'playstyle': 'Mage'},
    'Zyra': {'role': 'Support', 'playstyle': 'Mage'},
}


def create_chart_configurations(statistics: Dict[str, Any]) -> List[ChartConfig]:
    """Create chart configurations for data visualization"""
    
    charts = []
    
    # 1. Win Rate Pie Chart
    win_rate_chart = ChartConfig(
        chart_type="doughnut",
        data={
            "labels": ["Wins", "Losses"],
            "datasets": [{
                "data": [
                    statistics.get("total_wins", 0),
                    statistics.get("total_losses", 0)
                ],
                "backgroundColor": ["#10b981", "#f43f5e"],
                "borderWidth": 2,
                "borderColor": "#ffffff"
            }]
        },
        options={
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "position": "bottom",
                    "labels": {"color": "#475569", "font": {"size": 12}}
                },
                "title": {
                    "display": True,
                    "text": f"Win Rate: {statistics.get('win_rate', 0)}%",
                    "font": {"size": 16, "weight": "bold"},
                    "color": "#0f172a"
                }
            }
        }
    )
    charts.append(win_rate_chart)
    
    # 2. Monthly Performance Line Chart
    monthly_trends = statistics.get("monthly_trends", [])
    if monthly_trends:
        months = [f"{trend['month'][:3]} {trend['year']}" for trend in monthly_trends]
        win_rates = [trend.get('win_rate', 0) for trend in monthly_trends]
        kdas = [trend.get('avg_kda', 0) for trend in monthly_trends]
        
        monthly_chart = ChartConfig(
            chart_type="line",
            data={
                "labels": months,
                "datasets": [
                    {
                        "label": "Win Rate (%)",
                        "data": win_rates,
                        "borderColor": "#0f172a",
                        "backgroundColor": "rgba(15, 23, 42, 0.1)",
                        "tension": 0.4,
                        "borderWidth": 3,
                        "pointRadius": 4,
                        "fill": True,
                        "yAxisID": "y"
                    },
                    {
                        "label": "Average KDA",
                        "data": kdas,
                        "borderColor": "#f59e0b",
                        "backgroundColor": "rgba(245, 158, 11, 0.1)",
                        "tension": 0.4,
                        "borderWidth": 3,
                        "pointRadius": 4,
                        "yAxisID": "y1"
                    }
                ]
            },
            options={
                "responsive": True,
                "maintainAspectRatio": False,
                "interaction": {
                    "mode": "index",
                    "intersect": False
                },
                "scales": {
                    "y": {
                        "type": "linear",
                        "display": True,
                        "position": "left",
                        "title": {
                            "display": True,
                            "text": "Win Rate (%)",
                            "color": "#475569"
                        },
                        "ticks": {"color": "#64748b"},
                        "grid": {"color": "#e2e8f0"}
                    },
                    "y1": {
                        "type": "linear",
                        "display": True,
                        "position": "right",
                        "title": {
                            "display": True,
                            "text": "Average KDA",
                            "color": "#475569"
                        },
                        "ticks": {"color": "#64748b"},
                        "grid": {
                            "drawOnChartArea": False
                        }
                    },
                    "x": {
                        "ticks": {"color": "#64748b"},
                        "grid": {"color": "#e2e8f0"}
                    }
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Performance Trends Over Time",
                        "font": {"size": 16, "weight": "bold"},
                        "color": "#0f172a"
                    },
                    "legend": {
                        "labels": {"color": "#475569"}
                    }
                }
            }
        )
        charts.append(monthly_chart)
    
    # 3. Champion Performance Bar Chart
    champion_stats = statistics.get("champion_stats", [])[:5]  
    if champion_stats:
        champion_names = [champ['champion_name'] for champ in champion_stats]
        games_played = [champ['games_played'] for champ in champion_stats]
        win_rates = [champ['win_rate'] for champ in champion_stats]
        
        champion_chart = ChartConfig(
            chart_type="bar",
            data={
                "labels": champion_names,
                "datasets": [
                    {
                        "label": "Games Played",
                        "data": games_played,
                        "backgroundColor": "#64748b",
                        "borderRadius": 6,
                        "yAxisID": "y"
                    },
                    {
                        "label": "Win Rate (%)",
                        "data": win_rates,
                        "backgroundColor": "#10b981",
                        "borderRadius": 6,
                        "yAxisID": "y1"
                    }
                ]
            },
            options={
                "responsive": True,
                "maintainAspectRatio": False,
                "scales": {
                    "y": {
                        "type": "linear",
                        "display": True,
                        "position": "left",
                        "title": {
                            "display": True,
                            "text": "Games Played",
                            "color": "#475569"
                        },
                        "ticks": {"color": "#64748b"},
                        "grid": {"color": "#e2e8f0"}
                    },
                    "y1": {
                        "type": "linear",
                        "display": True,
                        "position": "right",
                        "title": {
                            "display": True,
                            "text": "Win Rate (%)",
                            "color": "#475569"
                        },
                        "ticks": {"color": "#64748b"},
                        "grid": {
                            "drawOnChartArea": False
                        }
                    },
                    "x": {
                        "ticks": {"color": "#64748b"},
                        "grid": {"display": False}
                    }
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Top Champions Performance",
                        "font": {"size": 16, "weight": "bold"},
                        "color": "#0f172a"
                    },
                    "legend": {
                        "labels": {"color": "#475569"}
                    }
                }
            }
        )
        charts.append(champion_chart)
    
    # 4. KDA Radar Chart
    kda_chart = ChartConfig(
        chart_type="radar",
        data={
            "labels": ["Kills", "Deaths (Inverted)", "Assists", "Win Rate", "Consistency"],
            "datasets": [{
                "label": "Performance Metrics",
                "data": [
                    min(statistics.get("avg_kills", 0) * 10, 100),
                    max(0, 100 - (statistics.get("avg_deaths", 0) * 15)),
                    min(statistics.get("avg_assists", 0) * 8, 100),
                    statistics.get("win_rate", 0),
                    statistics.get("consistency_score", 0)
                ],
                "backgroundColor": "rgba(15, 23, 42, 0.15)",
                "borderColor": "#0f172a",
                "borderWidth": 3,
                "pointBackgroundColor": "#0f172a",
                "pointBorderColor": "#ffffff",
                "pointBorderWidth": 2,
                "pointRadius": 5
            }]
        },
        options={
            "responsive": True,
            "maintainAspectRatio": False,
            "scales": {
                "r": {
                    "beginAtZero": True,
                    "max": 100,
                    "ticks": {
                        "color": "#64748b",
                        "backdropColor": "transparent"
                    },
                    "grid": {"color": "#e2e8f0"},
                    "pointLabels": {"color": "#475569", "font": {"size": 12}}
                }
            },
            "plugins": {
                "title": {
                    "display": True,
                    "text": "Overall Performance Profile",
                    "font": {"size": 16, "weight": "bold"},
                    "color": "#0f172a"
                },
                "legend": {
                    "labels": {"color": "#475569"}
                }
            }
        }
    )
    charts.append(kda_chart)
    
    return charts


def answer_player_question(question: str, insights: Dict, statistics: Dict) -> str:
    """Answer player questions using AI based on their data"""
    print(f"Answering question: {question}")
    try:
        from shared.aws_clients import get_bedrock_client
        
        prompt = f"""You are an AI coach for League of Legends. Answer this player's question based on their performance:

QUESTION: {question}

DATA:
- Games: {statistics.get('total_games', 0)}
- Win Rate: {statistics.get('win_rate', 0)}%
- KDA: {statistics.get('avg_kda', 0)}
- Highlights: {insights.get('highlights', [])[:2]}
- Recommendations: {insights.get('recommendations', [])[:2]}

Answer in 2-3 sentences. Be helpful and specific."""
        
        print("Getting Bedrock client...")
        bedrock_client = get_bedrock_client()
        print("Invoking Claude...")
        answer = bedrock_client.invoke_claude(prompt, max_tokens=150)
        print(f"Claude response: {answer}")
        return answer
    except Exception as e:
        print(f"Error in answer_player_question: {str(e)}")
        return "I'm having trouble right now. Try asking about your win rate, KDA, or improvement areas!"

def generate_share_url(session_id: str) -> str:
    """Generate shareable URL for the recap"""
    base_url = os.environ.get('WEBSITE_URL', 'https://d89hvhr82jyuz.cloudfront.net/')
    return f"{base_url}/share/{session_id}"


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for recap serving.
    
    Responsibilities:
    1. Load processed statistics from DynamoDB
    2. Load AI-generated insights from S3
    3. Create chart configurations for visualization
    4. Aggregate all data for frontend consumption
    5. Handle sharing functionality
    """
    print(f"Handler started with event: {json.dumps(event)}")
    logger.info(f"Handler started with event: {json.dumps(event)}")
    
    try:
        # Extract session ID from path parameters
        session_id = None
        
        if 'pathParameters' in event and event['pathParameters']:
            session_id = event['pathParameters'].get('sessionId')
        
        if not session_id:
            return format_lambda_response(400, {
                "error": "MISSING_SESSION_ID",
                "message": "Session ID is required in path parameters"
            })
        
        # Check request type (API Gateway v2 format)
        http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        path = event.get('rawPath', '')
        is_share_request = http_method == 'POST' and 'share' in path
        is_qa_request = http_method == 'POST' and 'ask' in path
        
        print(f"Request details: method={http_method}, path={path}, is_qa={is_qa_request}")
        logger.info(f"Request details: method={http_method}, path={path}, is_qa={is_qa_request}")
        
        # Initialize AWS clients
        dynamodb_client = get_dynamodb_client()
        s3_client = get_s3_client()
        
        # Get table and bucket names
        player_stats_table = get_table_name("PLAYER_STATS")
        processed_insights_bucket = get_bucket_name("PROCESSED_INSIGHTS")
        
        logger.info(f"Serving recap for session {session_id}")
        logger.info(f"Event: {json.dumps(event)}")
        
        # Load insights from S3
        insights_key = f"insights/{session_id}/narrative.json"
        insights_data = s3_client.get_object(processed_insights_bucket, insights_key)
        
        if not insights_data:
            return format_lambda_response(404, {
                "error": "INSIGHTS_NOT_FOUND",
                "message": f"No insights found for session {session_id}. Generate insights first."
            })
        
        insights = json.loads(insights_data)
        
        # Use real statistics from insights
        statistics = insights.get("statistics_summary", {})
        
        # Calculate total wins and losses from real data
        total_games = statistics.get("total_games", 0)
        win_rate = statistics.get("win_rate", 0)
        statistics["total_wins"] = int(total_games * win_rate / 100)
        statistics["total_losses"] = total_games - statistics["total_wins"]
        
        if is_qa_request:
            print(f"Processing Q&A request for session {session_id}")
            logger.info(f"Processing Q&A request for session {session_id}")
            # Handle AI Q&A request
            try:
                body = json.loads(event.get('body', '{}'))
                question = body.get('question', '')
                print(f"Question received: {question}")
                if not question:
                    return format_lambda_response(400, {"error": "Question required"})
                
                print("Calling answer_player_question...")
                answer = answer_player_question(question, insights, statistics)
                print(f"Answer generated: {answer}")
                return format_lambda_response(200, {
                    "question": question,
                    "answer": answer,
                    "suggested_questions": [
                        "How can I improve my win rate?",
                        "What are my biggest strengths?",
                        "Which champions should I focus on?",
                        "Am I getting better over time?",
                        "What should I work on next season?",
                        "What's my personality type?",
                        "What rank will I reach next season?",
                        "How do I compare to other players?"
                    ]
                })
            except Exception as e:
                print(f"Q&A error: {str(e)}")
                logger.error(f"Q&A error: {str(e)}", exc_info=True)
                return format_lambda_response(500, {"error": f"Failed to answer question: {str(e)}"})
        
        if is_share_request:
            # Handle sharing functionality
            share_url = generate_share_url(session_id)
            
            share_data = {
                "session_id": session_id,
                "share_url": share_url,
                "created_at": get_current_timestamp(),
                "preview_text": f"Check out my League of Legends Year in Review! {statistics.get('win_rate', 0)}% win rate with {statistics.get('avg_kda', 0)} KDA!"
            }
            
            return format_lambda_response(200, {
                "share_url": share_url,
                "preview_text": share_data["preview_text"],
                "message": "Share link generated successfully"
            })
        
        # Enhance champion stats with role/playstyle data for constellation
        champion_stats = statistics.get("champion_stats", [])
        for champ in champion_stats:
            champ_name = champ.get('champion_name', '')
            metadata = CHAMPION_METADATA.get(champ_name, {'role': 'Unknown', 'playstyle': 'Unknown'})
            champ['role'] = metadata['role']
            champ['playstyle'] = metadata['playstyle']
            # Ensure avg_kda exists
            if 'avg_kda' not in champ:
                champ['avg_kda'] = 1.0
        
        # Create chart configurations
        chart_configs = create_chart_configurations(statistics)
        visualizations = [chart.__dict__ for chart in chart_configs]
        
        # Get summoner name and region from insights
        summoner_name = insights.get("statistics_summary", {}).get("summoner_name", "Unknown Summoner")
        region = insights.get("statistics_summary", {}).get("region", "na1")
        
        # Clean up summoner name if needed
        if summoner_name.startswith('Player_'):
            summoner_name = summoner_name.replace('Player_', '').replace('%20', ' ')
        
        # Prepare complete recap response
        recap_data = RecapResponse(
            session_id=session_id,
            summoner_name=summoner_name,
            region=region,
            narrative=insights.get("narrative", ""),
            statistics=statistics,
            visualizations=visualizations,
            share_url=generate_share_url(session_id)
        )
        
        # Add additional metadata including new analytics
        response_data = recap_data.__dict__.copy()
        response_data.update({
            "highlights": insights.get("highlights", []),
            "achievements": insights.get("achievements", []),
            "fun_facts": insights.get("fun_facts", []),
            "recommendations": insights.get("recommendations", []),
            "highlight_matches": insights.get("highlight_matches", []),
            "champion_improvements": insights.get("champion_improvements", []),
            "behavioral_patterns": insights.get("behavioral_patterns", []),
            "personality_profile": insights.get("personality_profile", {}),
            "champion_suggestions": insights.get("champion_suggestions", []),
            "next_season_prediction": insights.get("next_season_prediction", {}),
            "rival_analysis": insights.get("rival_analysis", {}),
            "generated_at": insights.get("generated_at"),
            "served_at": get_current_timestamp()
        })
        
        logger.info(f"Successfully served recap for session {session_id}")
        logger.info(f"Response data keys: {list(response_data.keys())}")
        
        return format_lambda_response(200, response_data)
        
    except Exception as e:
        print(f"Unexpected error in recap server: {e}")
        logger.error(f"Unexpected error in recap server: {e}", exc_info=True)
        
        return format_lambda_response(500, {
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred while serving the recap",
            "details": str(e)
        })
