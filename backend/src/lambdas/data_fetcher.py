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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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

print("DATA FETCHER: Starting...")

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
    print(f"DATA FETCHER: Handler started with event: {event}")
    
    try:
        # Parse request body
        body = event.get("body", "{}")
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body
        
        print(f"DATA FETCHER: Parsed payload: {payload}")
        
        # Validate request
        try:
            request = FetchRequest(**payload)
            print(f"DATA FETCHER: Valid request for {request.summoner_name} in {request.region}")
        except Exception as e:
            print(f"DATA FETCHER: Invalid request format: {e}")
            logger.error(f"Invalid request format: {e}")
            return format_lambda_response(400, {
                "error": "INVALID_REQUEST",
                "message": "Invalid request format",
                "details": str(e)
            })
        
        # Validate region
        if not validate_region(request.region):
            print(f"DATA FETCHER: Invalid region: {request.region}")
            return format_lambda_response(400, {
                "error": "INVALID_REGION",
                "message": f"Region '{request.region}' is not supported"
            })
        
        # Sanitize summoner name
        summoner_name = sanitize_summoner_name(request.summoner_name)
        print(f"DATA FETCHER: Sanitized summoner name: {summoner_name}")
        
        # Initialize AWS clients
        print("DATA FETCHER: Initializing clients...")
        riot_client = get_riot_client()
        s3_client = get_s3_client()
        dynamodb_client = get_dynamodb_client()
        
        # Get bucket and table names
        raw_data_bucket = get_bucket_name("RAW_DATA")
        processing_jobs_table = get_table_name("PROCESSING_JOBS")
        print(f"DATA FETCHER: Using bucket: {raw_data_bucket}, table: {processing_jobs_table}")
        
        # Create processing job
        job = create_processing_job(request.session_id, summoner_name, request.region)
        job_id = job.PK.split('#')[1]
        print(f"DATA FETCHER: Created job {job_id}")
        
        # Store initial job in DynamoDB
        dynamodb_client.put_item(processing_jobs_table, job.model_dump())

        
        logger.info(f"Starting data fetch for Riot ID {request.summoner_name} in {request.region}")
        print(f"DATA FETCHER: Starting data fetch for Riot ID {request.summoner_name} in {request.region}")
        
        # Update job status to fetching
        dynamodb_client.update_item(
            processing_jobs_table,
            {"PK": job.PK},
            "SET #status = :status, #progress = :progress, #updated_at = :updated_at",
            {
                ":status": "fetching",
                ":progress": 10,
                ":updated_at": get_current_timestamp()
            },
            {
                "#status": "status",
                "#progress": "progress",
                "#updated_at": "updated_at"
            }
        )
        
        try:
            # Step 1: Get summoner information
            logger.info(f"Fetching summoner info for {summoner_name}")
            print(f"DATA FETCHER: Fetching summoner info for {summoner_name}")
            summoner = riot_client.get_summoner_by_name(summoner_name, request.region)
            print(f"DATA FETCHER: Got summoner: {summoner.name} (ID: {summoner.id}, PUUID: {summoner.puuid})")
            
            # Update progress
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #progress = :progress",
                {":progress": 30},
                {"#progress": "progress"}
            )
            
            # Step 2: Get match history (reduced for dev API key limits)
            logger.info(f"Fetching match history for {summoner.name}")
            print(f"DATA FETCHER: Fetching match history for {summoner.name}")
            
            # Add detailed logging for match history
            import time
            now = int(time.time())
            past_12_months = now - (12 * 30 * 24 * 60 * 60)  # 12 months back
            logger.info(f"Fetching matches for {summoner.name} from {past_12_months} to {now} in {request.region}")
            print(f"DATA FETCHER: Fetching matches for {summoner.name} from {past_12_months} to {now} in {request.region}")
            
            matches = riot_client.get_full_match_history(summoner, request.region, months_back=12)
            print(f"DATA FETCHER: Retrieved {len(matches)} matches")
            
            if not matches:
                print("DATA FETCHER: No matches found - updating job status")
                # Update job as completed with insufficient data
                dynamodb_client.update_item(
                    processing_jobs_table,
                    {"PK": job.PK},
                    "SET #status = :status, #progress = :progress, #error_message = :error",
                    {
                        ":status": "completed",
                        ":progress": 100,
                        ":error": "No match history found for the past 12 months"
                    },
                    {
                        "#status": "status",
                        "#progress": "progress",
                        "#error_message": "error_message"
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
                {":progress": 70},
                {"#progress": "progress"}
            )
            
            # Step 3: Store raw data in S3
            logger.info(f"Storing {len(matches)} matches in S3")
            print(f"DATA FETCHER: Storing {len(matches)} matches in S3")
            
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
            s3_key = generate_s3_key(summoner.puuid, "raw-matches")
            
            # Store in S3
            s3_client.put_object(
                raw_data_bucket,
                s3_key,
                json.dumps(raw_data, indent=2)
            )
            
            # Update job as processing (not completed yet)
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #status = :status, #progress = :progress, #updated_at = :updated_at",
                {
                    ":status": "processing",
                    ":progress": 50,
                    ":updated_at": get_current_timestamp()
                },
                {
                    "#status": "status",
                    "#progress": "progress",
                    "#updated_at": "updated_at"
                }
            )
            
            logger.info(f"Successfully fetched and stored data for {summoner.name}")
            print(f"DATA FETCHER: Successfully completed for {summoner.name}")
            
            # Create response to return immediately
            response = format_lambda_response(200, {
                "job_id": job_id,
                "status": "processing",
                "summoner_info": {
                    "id": summoner.id,
                    "name": summoner.name,
                    "level": summoner.summoner_level,
                    "region": request.region
                },
                "match_count": len(matches),
                "s3_key": s3_key,
                "message": f"Successfully fetched {len(matches)} matches, processing..."
            })
            
            # Invoke data processor Lambda AFTER creating response
            try:
                import boto3
                lambda_client = boto3.client('lambda')
                processor_function_name = os.environ.get('DATA_PROCESSOR_FUNCTION_NAME')
                
                if processor_function_name:
                    lambda_client.invoke(
                        FunctionName=processor_function_name,
                        InvocationType='Event',  # Async
                        Payload=json.dumps({
                            'session_id': request.session_id,
                            'job_id': job_id,
                            'summoner_puuid': summoner.puuid
                        })
                    )
                    logger.info(f"Invoked data processor for job {job_id}")
                    print(f"DATA FETCHER: Invoked data processor for job {job_id}")
                else:
                    logger.warning("DATA_PROCESSOR_FUNCTION_NAME not set, skipping processor invocation")
                    print("DATA FETCHER: DATA_PROCESSOR_FUNCTION_NAME not set")
            except Exception as e:
                logger.error(f"Failed to invoke data processor: {e}")
                print(f"DATA FETCHER: Failed to invoke data processor: {e}")
            
            return response
            
        except SummonerNotFound:
            print("DATA FETCHER: Summoner not found")
            # Update job with error
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #status = :status, #error_message = :error",
                {
                    ":status": "failed",
                    ":error": f"Summoner '{summoner_name}' not found in region '{request.region}'"
                },
                {
                    "#status": "status",
                    "#error_message": "error_message"
                }
            )
            
            return format_lambda_response(404, {
                "error": "SUMMONER_NOT_FOUND",
                "message": f"Summoner '{summoner_name}' not found in region '{request.region}'"
            })
            
        except RiotAPIError as e:
            print(f"DATA FETCHER: Riot API error: {e}")
            # Update job with error
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
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
            
            logger.error(f"Riot API error: {e}")
            return format_lambda_response(503, {
                "error": "RIOT_API_ERROR",
                "message": "Failed to fetch data from Riot Games API",
                "details": str(e)
            })
            
    except Exception as e:
        print(f"DATA FETCHER: Unexpected error: {e}")
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
                    },
                    {
                        "#status": "status",
                        "#error_message": "error_message"
                    }
                )
        except:
            pass  # Don't fail on cleanup
        
        return format_lambda_response(500, {
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": str(e)
        })