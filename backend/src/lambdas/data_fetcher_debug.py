"""
Debug version of Data Fetcher Lambda Function with enhanced Riot API logging
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
from shared.riot_client_debug import get_riot_client  # Use debug version
from shared.aws_clients import get_s3_client, get_dynamodb_client, get_bucket_name, get_table_name
from shared.utils import (
    format_lambda_response, setup_logging, validate_region, 
    sanitize_summoner_name, generate_s3_key, create_processing_job,
    get_current_timestamp
)

# Setup logging
setup_logging(os.environ.get('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

print("DATA FETCHER DEBUG: Starting...")

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Debug version of data fetcher handler"""
    print(f"DATA FETCHER DEBUG: Handler started with event: {event}")
    
    try:
        # Parse request body
        body = event.get("body", "{}")
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body
        
        print(f"DATA FETCHER DEBUG: Parsed payload: {payload}")
        
        # Validate request
        try:
            request = FetchRequest(**payload)
            print(f"DATA FETCHER DEBUG: Valid request for {request.summoner_name} in {request.region}")
        except Exception as e:
            print(f"DATA FETCHER DEBUG: Invalid request format: {e}")
            return format_lambda_response(400, {
                "error": "INVALID_REQUEST",
                "message": "Invalid request format",
                "details": str(e)
            })
        
        # Initialize AWS clients
        print("DATA FETCHER DEBUG: Initializing clients...")
        riot_client = get_riot_client()
        s3_client = get_s3_client()
        dynamodb_client = get_dynamodb_client()
        
        # Get bucket and table names
        raw_data_bucket = get_bucket_name("RAW_DATA")
        processing_jobs_table = get_table_name("PROCESSING_JOBS")
        print(f"DATA FETCHER DEBUG: Using bucket: {raw_data_bucket}, table: {processing_jobs_table}")
        
        # Create processing job
        job = create_processing_job(request.session_id, request.summoner_name, request.region)
        job_id = job.PK.split('#')[1]
        print(f"DATA FETCHER DEBUG: Created job {job_id}")
        
        # Store initial job in DynamoDB
        dynamodb_client.put_item(processing_jobs_table, job.model_dump())
        
        try:
            # Step 1: Get summoner information
            print(f"DATA FETCHER DEBUG: Fetching summoner info for {request.summoner_name}")
            summoner = riot_client.get_summoner_by_name(request.summoner_name, request.region)
            print(f"DATA FETCHER DEBUG: Got summoner: {summoner.name} (ID: {summoner.id}, PUUID: {summoner.puuid})")
            
            # Step 2: Get match history
            print(f"DATA FETCHER DEBUG: Fetching match history...")
            matches = riot_client.get_full_match_history(summoner, request.region, months_back=12)
            print(f"DATA FETCHER DEBUG: Retrieved {len(matches)} matches")
            
            if not matches:
                print("DATA FETCHER DEBUG: No matches found - updating job status")
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
            
            # Step 3: Store raw data in S3
            print(f"DATA FETCHER DEBUG: Storing {len(matches)} matches in S3")
            
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
            
            s3_key = generate_s3_key(summoner.id, "raw-matches")
            s3_client.put_object(raw_data_bucket, s3_key, json.dumps(raw_data, indent=2))
            print(f"DATA FETCHER DEBUG: Stored data at S3 key: {s3_key}")
            
            # Update job as completed
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #status = :status, #progress = :progress",
                {":status": "completed", ":progress": 100},
                {"#status": "status", "#progress": "progress"}
            )
            
            print(f"DATA FETCHER DEBUG: Successfully completed job {job_id}")
            
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
            
        except Exception as e:
            print(f"DATA FETCHER DEBUG: Error during processing: {e}")
            # Update job with error
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #status = :status, #error_message = :error",
                {":status": "failed", ":error": str(e)},
                {"#status": "status", "#error_message": "error_message"}
            )
            raise
            
    except Exception as e:
        print(f"DATA FETCHER DEBUG: Unexpected error: {e}")
        return format_lambda_response(500, {
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": str(e)
        })