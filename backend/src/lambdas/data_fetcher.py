"""
Data Fetcher Lambda Function
Retrieves summoner information and match history from Riot Games API.
Implements rate limiting, error handling, and data persistence to S3.
"""

import json
import os
import logging
import sys
from typing import Any, Dict
from dataclasses import asdict
import time

# Import shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.models import FetchRequest
from shared.aws_clients import (
    get_s3_client,
    get_dynamodb_client,
    get_bucket_name,
    get_table_name,
)
from shared.utils import (
    format_lambda_response,
    setup_logging,
    validate_region,
    sanitize_summoner_name,
    generate_s3_key,
    create_processing_job,
    get_current_timestamp,
)
from riot_client import RiotAPIClient, RiotAPIError  # ✅ our fixed Riot client

# Setup logging
setup_logging(os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

print("DATA FETCHER: Lambda cold start complete.")


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for data fetching.
    Steps:
    1. Validate summoner name and region
    2. Fetch summoner info via Riot API
    3. Retrieve match history (retry on 400)
    4. Store raw data in S3
    5. Update DynamoDB job status
    """
    print(f"DATA FETCHER: Event received: {json.dumps(event)}")

    try:
        # Parse request body
        body = event.get("body", "{}")
        payload = json.loads(body) if isinstance(body, str) else body
        print(f"DATA FETCHER: Parsed payload: {payload}")

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

        # Initialize clients
        logger.info(f"Initializing Riot client for {summoner_name} ({request.region})")
        riot_client = RiotAPIClient()
        s3_client = get_s3_client()
        dynamodb_client = get_dynamodb_client()

        # Resolve AWS resources
        raw_data_bucket = get_bucket_name("RAW_DATA")
        processing_jobs_table = get_table_name("PROCESSING_JOBS")

        # Create new job entry
        job = create_processing_job(request.session_id, summoner_name, request.region)
        job_id = job.PK.split("#")[1]
        dynamodb_client.put_item(processing_jobs_table, job.model_dump())
        logger.info(f"Created processing job {job_id}")

        # Update status to fetching
        dynamodb_client.update_item(
            processing_jobs_table,
            {"PK": job.PK},
            "SET #status = :status, #progress = :progress",
            {":status": "fetching", ":progress": 10},
            {"#status": "status", "#progress": "progress"},
        )

        # Step 1: Fetch Summoner Info
        try:
            summoner = riot_client.get_summoner_by_name(summoner_name, request.region)
        except Exception as e:
            logger.error(f"Summoner not found: {e}")
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #status = :status, #error_message = :error",
                {":status": "failed", ":error": str(e)},
                {"#status": "status", "#error_message": "error_message"},
            )
            return format_lambda_response(404, {
                "error": "SUMMONER_NOT_FOUND",
                "message": f"Summoner '{summoner_name}' not found"
            })

        logger.info(f"Summoner found: {summoner.name} (PUUID: {summoner.puuid})")
        dynamodb_client.update_item(
            processing_jobs_table,
            {"PK": job.PK},
            "SET #progress = :progress",
            {":progress": 30},
            {"#progress": "progress"},
        )

        # Step 2: Fetch Match History (with retry on 400)
        logger.info(f"Fetching match history for {summoner.name}")
        try:
            matches = riot_client.get_full_match_history(summoner, request.region, months_back=12)
        except Exception as e:
            logger.error(f"Match history fetch failed: {e}")
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #status = :status, #error_message = :error",
                {":status": "failed", ":error": str(e)},
                {"#status": "status", "#error_message": "error_message"},
            )
            return format_lambda_response(503, {
                "error": "MATCH_HISTORY_ERROR",
                "message": "Failed to fetch match history",
                "details": str(e)
            })

        if not matches:
            logger.warning("No matches found for this summoner.")
            dynamodb_client.update_item(
                processing_jobs_table,
                {"PK": job.PK},
                "SET #status = :status, #progress = :progress, #error_message = :error",
                {
                    ":status": "completed",
                    ":progress": 100,
                    ":error": "No match history found"
                },
                {
                    "#status": "status",
                    "#progress": "progress",
                    "#error_message": "error_message"
                },
            )
            return format_lambda_response(200, {
                "job_id": job_id,
                "status": "completed",
                "message": "No match history found",
            })

        dynamodb_client.update_item(
            processing_jobs_table,
            {"PK": job.PK},
            "SET #progress = :progress",
            {":progress": 70},
            {"#progress": "progress"},
        )

        # Step 3: Store raw data in S3
        raw_data = {
            "summoner": asdict(summoner),
            "matches": [asdict(m) for m in matches],
            "metadata": {
                "fetch_timestamp": get_current_timestamp(),
                "region": request.region,
                "total_matches": len(matches),
                "session_id": request.session_id
            }
        }

        s3_key = generate_s3_key(summoner.id, "raw-matches")
        s3_client.put_object(raw_data_bucket, s3_key, json.dumps(raw_data, indent=2))
        logger.info(f"Stored {len(matches)} matches in S3: {s3_key}")

        # Step 4: Mark job as completed
        dynamodb_client.update_item(
            processing_jobs_table,
            {"PK": job.PK},
            "SET #status = :status, #progress = :progress, #updated_at = :updated",
            {
                ":status": "completed",
                ":progress": 100,
                ":updated": get_current_timestamp()
            },
            {
                "#status": "status",
                "#progress": "progress",
                "#updated_at": "updated_at"
            },
        )

        logger.info(f"Data fetch complete for {summoner.name}")
        return format_lambda_response(200, {
            "job_id": job_id,
            "status": "completed",
            "match_count": len(matches),
            "s3_key": s3_key,
            "summoner_info": {
                "name": summoner.name,
                "puuid": summoner.puuid,
                "region": request.region
            },
            "message": f"Fetched {len(matches)} matches successfully"
        })

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return format_lambda_response(500, {
            "error": "INTERNAL_ERROR",
            "message": str(e)
        })
