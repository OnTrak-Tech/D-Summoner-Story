"""
Data Processor Lambda Function
Processes raw match data into statistical insights and trends.
Calculates KDA, win rates, champion statistics, and monthly trends.
"""

import json
import os
from typing import Any, Dict, List
from dataclasses import asdict
import logging

# Import shared modules
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.models import ProcessRequest, RiotMatch, RiotParticipant
from shared.aws_clients import get_s3_client, get_dynamodb_client, get_bucket_name, get_table_name
from shared.utils import (
    format_lambda_response, setup_logging, process_match_statistics,
    create_player_stats_item, get_current_timestamp
)

# Setup logging
setup_logging(os.environ.get('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)


def load_matches_from_s3(s3_client, bucket: str, summoner_id: str) -> List[RiotMatch]:
    """Load and parse match data from S3"""
    try:
        # List objects for this summoner
        prefix = f"raw-matches/{summoner_id}/"
        object_keys = s3_client.list_objects(bucket, prefix)
        
        if not object_keys:
            logger.warning(f"No match data found for summoner {summoner_id}")
            return []
        
        # Get the most recent file (assuming timestamp in filename)
        latest_key = sorted(object_keys)[-1]
        
        # Load the data
        raw_data_str = s3_client.get_object(bucket, latest_key)
        if not raw_data_str:
            logger.error(f"Failed to load data from S3 key: {latest_key}")
            return []
        
        raw_data = json.loads(raw_data_str)
        
        # Parse matches
        matches = []
        for match_data in raw_data.get('matches', []):
            # Parse participants
            participants = []
            for p_data in match_data.get('participants', []):
                participant = RiotParticipant(
                    summoner_id=p_data['summoner_id'],
                    champion_id=p_data['champion_id'],
                    champion_name=p_data['champion_name'],
                    kills=p_data['kills'],
                    deaths=p_data['deaths'],
                    assists=p_data['assists'],
                    win=p_data['win'],
                    game_duration=p_data['game_duration'],
                    item0=p_data.get('item0', 0),
                    item1=p_data.get('item1', 0),
                    item2=p_data.get('item2', 0),
                    item3=p_data.get('item3', 0),
                    item4=p_data.get('item4', 0),
                    item5=p_data.get('item5', 0),
                    item6=p_data.get('item6', 0),
                    total_damage_dealt=p_data.get('total_damage_dealt', 0),
                    gold_earned=p_data.get('gold_earned', 0),
                    cs_total=p_data.get('cs_total', 0)
                )
                participants.append(participant)
            
            match = RiotMatch(
                match_id=match_data['match_id'],
                game_creation=match_data['game_creation'],
                game_duration=match_data['game_duration'],
                game_mode=match_data['game_mode'],
                game_type=match_data['game_type'],
                queue_id=match_data['queue_id'],
                participants=participants
            )
            matches.append(match)
        
        logger.info(f"Loaded {len(matches)} matches from S3")
        return matches
        
    except Exception as e:
        logger.error(f"Failed to load matches from S3: {e}")
        raise


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for data processing.
    
    Responsibilities:
    1. Load raw match data from S3
    2. Process matches into statistical insights
    3. Calculate KDA, win rates, champion stats, monthly trends
    4. Store processed statistics in DynamoDB
    5. Update processing job status
    """
    try:
        # Handle both direct invocation and API Gateway
        if 'pathParameters' in event:
            # API Gateway invocation - extract job ID from path
            job_id = event['pathParameters'].get('jobId')
            if not job_id:
                return format_lambda_response(400, {
                    "error": "MISSING_JOB_ID",
                    "message": "Job ID is required in path parameters"
                })
            
            # For status check, return job status
            dynamodb_client = get_dynamodb_client()
            processing_jobs_table = get_table_name("PROCESSING_JOBS")
            
            job_item = dynamodb_client.get_item(
                processing_jobs_table,
                {"PK": f"JOB#{job_id}"}
            )
            
            if not job_item:
                return format_lambda_response(404, {
                    "error": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found"
                })
            
            return format_lambda_response(200, {
                "job_id": job_id,
                "status": job_item.get('status'),
                "progress": job_item.get('progress', 0),
                "error_message": job_item.get('error_message'),
                "created_at": job_item.get('created_at'),
                "updated_at": job_item.get('updated_at')
            })
        
        # Direct invocation for processing
        body = event.get("body", "{}")
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body
        
        # Validate request
        try:
            request = ProcessRequest(**payload)
        except Exception as e:
            logger.error(f"Invalid request format: {e}")
            return format_lambda_response(400, {
                "error": "INVALID_REQUEST",
                "message": "Invalid request format",
                "details": str(e)
            })
        
        # Initialize AWS clients
        s3_client = get_s3_client()
        dynamodb_client = get_dynamodb_client()
        
        # Get bucket and table names
        raw_data_bucket = get_bucket_name("RAW_DATA")
        player_stats_table = get_table_name("PLAYER_STATS")
        processing_jobs_table = get_table_name("PROCESSING_JOBS")
        
        logger.info(f"Starting data processing for job {request.job_id}")
        
        # Get job information
        job_item = dynamodb_client.get_item(
            processing_jobs_table,
            {"PK": f"JOB#{request.job_id}"}
        )
        
        if not job_item:
            return format_lambda_response(404, {
                "error": "JOB_NOT_FOUND",
                "message": f"Job {request.job_id} not found"
            })
        
        # Update job status to processing
        dynamodb_client.update_item(
            processing_jobs_table,
            {"PK": f"JOB#{request.job_id}"},
            "SET #status = :status, #progress = :progress, #updated_at = :updated_at",
            {
                ":status": "processing",
                ":progress": 20,
                ":updated_at": get_current_timestamp()
            },
            {
                "#status": "status",
                "#progress": "progress",
                "#updated_at": "updated_at"
            }
        )
        
        try:
            # Extract summoner ID from S3 key in job data
            # Get the S3 key from the raw data to extract summoner ID
            raw_data_objects = s3_client.list_objects(raw_data_bucket, "raw-matches/")
            if not raw_data_objects:
                raise Exception("No raw match data found")
            
            # Find the most recent S3 key and extract summoner ID
            latest_key = sorted(raw_data_objects)[-1]
            summoner_id = latest_key.split('/')[1]  # Extract from raw-matches/{summoner_id}/...
            
            matches = load_matches_from_s3(s3_client, raw_data_bucket, summoner_id)
            
            if not matches:
                # Update job as failed
                dynamodb_client.update_item(
                    processing_jobs_table,
                    {"PK": f"JOB#{request.job_id}"},
                    "SET #status = :status, #error_message = :error",
                    {
                        ":status": "failed",
                        ":error": "No match data found to process"
                    },
                    {
                        "#status": "status",
                        "#error_message": "error_message"
                    }
                )
                
                return format_lambda_response(404, {
                    "error": "NO_DATA",
                    "message": "No match data found to process"
                })
            
            # Update progress
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": f"JOB#{request.job_id}"},
                "SET #progress = :progress",
                {":progress": 50},
                {"#progress": "progress"}
            )
            
            # Process matches into statistics
            logger.info(f"Processing {len(matches)} matches")
            processed_stats = process_match_statistics(matches, summoner_id)
            
            # Update progress
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": f"JOB#{request.job_id}"},
                "SET #progress = :progress",
                {":progress": 80},
                {"#progress": "progress"}
            )
            
            # Create player stats item for DynamoDB
            player_stats_item = create_player_stats_item(request.session_id, processed_stats)
            
            # Store processed statistics in DynamoDB
            dynamodb_client.put_item(player_stats_table, player_stats_item.model_dump())
            
            # Update job as completed
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": f"JOB#{request.job_id}"},
                "SET #status = :status, #progress = :progress, #updated_at = :updated_at",
                {
                    ":status": "completed",
                    ":progress": 100,
                    ":updated_at": get_current_timestamp()
                },
                {
                    "#status": "status",
                    "#progress": "progress",
                    "#updated_at": "updated_at"
                }
            )
            
            logger.info(f"Successfully processed statistics for {processed_stats.summoner_name}")
            
            return format_lambda_response(200, {
                "job_id": request.job_id,
                "status": "completed",
                "session_id": request.session_id,
                "statistics": {
                    "summoner_name": processed_stats.summoner_name,
                    "total_games": processed_stats.total_games,
                    "win_rate": processed_stats.win_rate,
                    "avg_kda": processed_stats.avg_kda,
                    "champion_count": len(processed_stats.champion_stats),
                    "improvement_trend": processed_stats.improvement_trend,
                    "consistency_score": processed_stats.consistency_score
                },
                "message": "Statistics processed successfully"
            })
            
        except Exception as e:
            # Update job with error
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": f"JOB#{request.job_id}"},
                "SET #status = :status, #error_message = :error",
                {
                    ":status": "failed",
                    ":error": str(e)
                },
                {
                    "#status": "status",
                    "#error_message": "error_message"
                }
            )
            
            logger.error(f"Processing error: {e}")
            raise
            
    except Exception as e:
        logger.error(f"Unexpected error in data processor: {e}", exc_info=True)
        
        return format_lambda_response(500, {
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred during processing",
            "details": str(e)
        })
