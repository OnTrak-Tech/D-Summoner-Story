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
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.models import RecapResponse, ChartConfig
from shared.aws_clients import get_s3_client, get_dynamodb_client, get_bucket_name, get_table_name
from shared.utils import format_lambda_response, setup_logging, get_current_timestamp

# Setup logging
setup_logging(os.environ.get('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)


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
                "backgroundColor": ["#10B981", "#EF4444"],
                "borderWidth": 0
            }]
        },
        options={
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "position": "bottom"
                },
                "title": {
                    "display": True,
                    "text": f"Win Rate: {statistics.get('win_rate', 0)}%"
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
                        "borderColor": "#3B82F6",
                        "backgroundColor": "rgba(59, 130, 246, 0.1)",
                        "tension": 0.4,
                        "yAxisID": "y"
                    },
                    {
                        "label": "Average KDA",
                        "data": kdas,
                        "borderColor": "#F59E0B",
                        "backgroundColor": "rgba(245, 158, 11, 0.1)",
                        "tension": 0.4,
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
                            "text": "Win Rate (%)"
                        }
                    },
                    "y1": {
                        "type": "linear",
                        "display": True,
                        "position": "right",
                        "title": {
                            "display": True,
                            "text": "Average KDA"
                        },
                        "grid": {
                            "drawOnChartArea": False
                        }
                    }
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Performance Trends Over Time"
                    }
                }
            }
        )
        charts.append(monthly_chart)
    
    # 3. Champion Performance Bar Chart
    champion_stats = statistics.get("champion_stats", [])[:5]  # Top 5 champions
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
                        "backgroundColor": "rgba(99, 102, 241, 0.8)",
                        "yAxisID": "y"
                    },
                    {
                        "label": "Win Rate (%)",
                        "data": win_rates,
                        "backgroundColor": "rgba(16, 185, 129, 0.8)",
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
                            "text": "Games Played"
                        }
                    },
                    "y1": {
                        "type": "linear",
                        "display": True,
                        "position": "right",
                        "title": {
                            "display": True,
                            "text": "Win Rate (%)"
                        },
                        "grid": {
                            "drawOnChartArea": False
                        }
                    }
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Top Champions Performance"
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
                    min(statistics.get("avg_kills", 0) * 10, 100),  # Normalize to 0-100
                    max(0, 100 - (statistics.get("avg_deaths", 0) * 15)),  # Invert deaths
                    min(statistics.get("avg_assists", 0) * 8, 100),
                    statistics.get("win_rate", 0),
                    statistics.get("consistency_score", 0)
                ],
                "backgroundColor": "rgba(139, 92, 246, 0.2)",
                "borderColor": "rgba(139, 92, 246, 1)",
                "pointBackgroundColor": "rgba(139, 92, 246, 1)"
            }]
        },
        options={
            "responsive": True,
            "maintainAspectRatio": False,
            "scales": {
                "r": {
                    "beginAtZero": True,
                    "max": 100
                }
            },
            "plugins": {
                "title": {
                    "display": True,
                    "text": "Overall Performance Profile"
                }
            }
        }
    )
    charts.append(kda_chart)
    
    return charts


def generate_share_url(session_id: str) -> str:
    """Generate shareable URL for the recap"""
    # In a real implementation, this would create a public sharing link
    base_url = os.environ.get('WEBSITE_URL', 'https://your-domain.com')
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
        
        # Check if this is a sharing request
        http_method = event.get('httpMethod', 'GET')
        is_share_request = http_method == 'POST' and 'share' in event.get('path', '')
        
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
        
        if is_share_request:
            # Handle sharing functionality
            share_url = generate_share_url(session_id)
            
            # Store sharing metadata (in a real implementation)
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
        
        # Create chart configurations
        chart_configs = create_chart_configurations(statistics)
        visualizations = [chart.__dict__ for chart in chart_configs]
        
        # Prepare complete recap response
        recap_data = RecapResponse(
            session_id=session_id,
            summoner_name=insights.get("statistics_summary", {}).get("summoner_name", "Unknown Summoner"),
            region="na1",  # This should come from the actual data
            narrative=insights.get("narrative", ""),
            statistics=statistics,
            visualizations=visualizations,
            share_url=generate_share_url(session_id)
        )
        
        # Add additional metadata
        response_data = recap_data.__dict__.copy()
        response_data.update({
            "highlights": insights.get("highlights", []),
            "achievements": insights.get("achievements", []),
            "fun_facts": insights.get("fun_facts", []),
            "recommendations": insights.get("recommendations", []),
            "generated_at": insights.get("generated_at"),
            "served_at": get_current_timestamp()
        })
        
        logger.info(f"Successfully served recap for session {session_id}")
        logger.info(f"Response data keys: {list(response_data.keys())}")
        
        return format_lambda_response(200, response_data)
        
    except Exception as e:
        logger.error(f"Unexpected error in recap server: {e}", exc_info=True)
        
        return format_lambda_response(500, {
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred while serving the recap",
            "details": str(e)
        })
