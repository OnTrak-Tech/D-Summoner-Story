"""
Data Fetcher Lambda Function
Retrieves summoner information and match history from Riot Games API.
Implements rate limiting, error handling, and data persistence to S3.
"""

import json
import os
from typing import Any, Dict
from dataclasses import asdict
import logging

# Import shared modules
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.models import FetchRequest
from shared.riot_client import get_riot_client, RiotAPIError, SummonerNotFound
from shared.aws_clients import get_s3_client, get_dynamodb_client, get_bucket_name, get_table_name
from shared.utils import (
    format_lambda_response, setup_logging, validate_region, 
    sanitize_summoner_name, generate_s3_key, create_processing_job,
    get_current_timestamp
)

# Setup logging
setup_logging(os.environ.get('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for data fetching.
    
    Responsibilities:
    1. Validate summoner name and region
    2. Fetch summoner information from Riot API
    3. Retrieve match history with rate limiting
    4. Store raw match data in S3
    5. Update processing job status in DynamoDB
    """
    try:
        # Parse request body
        body = event.get("body", "{}")
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body
        
        # Validate request
        try:
            request = FetchRequest(**payload)
        except Exception as e:
            logger.error(f"Invalid request format: {e}")
            return format_lambda_response(400, {
                "error": "INVALID_REQUEST",
                "message": "Invalid request format",
                "details": str(e)
            })
        
        # Validate region
        if not validate_region(request.region):
            return format_lambda_response(400, {
                "error": "INVALID_REGION",
                "message": f"Region '{request.region}' is not supported"
            })
        
        # Sanitize summoner name
        summoner_name = sanitize_summoner_name(request.summoner_name)
        
        # Initialize AWS clients
        riot_client = get_riot_client()
        s3_client = get_s3_client()
        dynamodb_client = get_dynamodb_client()
        
        # Get bucket and table names
        raw_data_bucket = get_bucket_name("RAW_DATA")
        processing_jobs_table = get_table_name("PROCESSING_JOBS")
        
        # Create processing job
        job = create_processing_job(request.session_id, summoner_name, request.region)
        job_id = job.PK.split('#')[1]
        
        # Store initial job in DynamoDB
        dynamodb_client.put_item(processing_jobs_table, asdict(job))
        
        logger.info(f"Starting data fetch for {summoner_name} in {request.region}")
        
        # Update job status to fetching
        dynamodb_client.update_item(
            processing_jobs_table,
            {"PK": job.PK},
            "SET #status = :status, #progress = :progress, #updated_at = :updated_at",
            {
                ":status": "fetching",
                ":progress": 10,
                ":updated_at": get_current_timestamp()
            }
        )
        
        try:
            # Step 1: Get summoner information
            logger.info(f"Fetching summoner info for {summoner_name}")
            summoner = riot_client.get_summoner_by_name(summoner_name, request.region)
            
            # Update progress
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #progress = :progress",
                {":progress": 30}
            )
            
            # Step 2: Get match history
            logger.info(f"Fetching match history for {summoner.name}")
            matches = riot_client.get_full_match_history(summoner, request.region, months_back=12)
            
            if not matches:
                # Update job as completed with insufficient data
                dynamodb_client.update_item(
                    processing_jobs_table,
                    {"PK": job.PK},
                    "SET #status = :status, #progress = :progress, #error_message = :error",
                    {
                        ":status": "completed",
                        ":progress": 100,
                        ":error": "No match history found for the past 12 months"
                    }
                )
                
                return format_lambda_response(200, {
                    "job_id": job_id,
                    "status": "completed",
                    "message": "No match history found",
                    "summoner_info": {
                        "name": summoner.name,
                        "level": summoner.summoner_level,
                        "region": request.region
                    }
                })
            
            # Update progress
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #progress = :progress",
                {":progress": 70}
            )
            
            # Step 3: Store raw data in S3
            logger.info(f"Storing {len(matches)} matches in S3")
            
            # Prepare data for storage
            raw_data = {
                "summoner": asdict(summoner),
                "matches": [asdict(match) for match in matches],
                "metadata": {
                    "fetch_timestamp": get_current_timestamp(),
                    "region": request.region,
                    "total_matches": len(matches),
                    "session_id": request.session_id
                }
            }
            
            # Generate S3 key
            s3_key = generate_s3_key(summoner.id, "raw-matches")
            
            # Store in S3
            s3_client.put_object(
                raw_data_bucket,
                s3_key,
                json.dumps(raw_data, indent=2)
            )
            
            # Update job as completed
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #status = :status, #progress = :progress, #updated_at = :updated_at",
                {
                    ":status": "completed",
                    ":progress": 100,
                    ":updated_at": get_current_timestamp()
                }
            )
            
            logger.info(f"Successfully fetched and stored data for {summoner.name}")
            
            return format_lambda_response(200, {
                "job_id": job_id,
                "status": "completed",
                "summoner_info": {
                    "id": summoner.id,
                    "name": summoner.name,
                    "level": summoner.summoner_level,
                    "region": request.region
                },
                "match_count": len(matches),
                "s3_key": s3_key,
                "message": f"Successfully fetched {len(matches)} matches"
            })
            
        except SummonerNotFound:
            # Update job with error
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #status = :status, #error_message = :error",
                {
                    ":status": "failed",
                    ":error": f"Summoner '{summoner_name}' not found in region '{request.region}'"
                }
            )
            
            return format_lambda_response(404, {
                "error": "SUMMONER_NOT_FOUND",
                "message": f"Summoner '{summoner_name}' not found in region '{request.region}'"
            })
            
        except RiotAPIError as e:
            # Update job with error
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #status = :status, #error_message = :error",
                {
                    ":status": "failed",
                    ":error": str(e)
                }
            )
            
            logger.error(f"Riot API error: {e}")
            return format_lambda_response(503, {
                "error": "RIOT_API_ERROR",
                "message": "Failed to fetch data from Riot Games API",
                "details": str(e)
            })
            
    except Exception as e:
        logger.error(f"Unexpected error in data fetcher: {e}", exc_info=True)
        
        # Try to update job status if possible
        try:
            if 'job' in locals() and 'dynamodb_client' in locals() and 'processing_jobs_table' in locals():
                dynamodb_client.update_item(
                    processing_jobs_table,
                    {"PK": job.PK},
                    "SET #status = :status, #error_message = :error",
                    {
                        ":status": "failed",
                        ":error": f"Internal error: {str(e)}"
                    }
                )
        except:
            pass  # Don't fail on cleanup
        
        return format_lambda_response(500, {
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": str(e)
        })
