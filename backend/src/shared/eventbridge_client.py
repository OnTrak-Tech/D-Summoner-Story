"""
EventBridge client for publishing events in the D-Summoner-Story application.
Provides methods for publishing domain-specific events with proper error handling.
"""

import json
import os
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EventBridgeClientError(Exception):
    """Custom exception for EventBridge client errors"""
    pass


class EventBridgeClient:
    """EventBridge client wrapper for publishing events"""
    
    def __init__(self):
        self.client = boto3.client('events')
        self.event_bus_name = os.environ.get('EVENT_BUS_NAME')
        if not self.event_bus_name:
            logger.warning("EVENT_BUS_NAME not set, will use default event bus")
    
    def put_event(self, source: str, detail_type: str, detail: Dict[str, Any], 
                 event_bus_name: Optional[str] = None) -> bool:
        """Put event to EventBridge"""
        try:
            event_entry = {
                'Source': source,
                'DetailType': detail_type,
                'Detail': json.dumps(detail, default=str)
            }
            
            # Use provided event bus name or instance default
            bus_name = event_bus_name or self.event_bus_name
            if bus_name:
                event_entry['EventBusName'] = bus_name
            
            response = self.client.put_events(
                Entries=[event_entry]
            )
            
            # Check if event was successfully published
            if response['FailedEntryCount'] > 0:
                failed_entry = response['Entries'][0]
                error_msg = failed_entry.get('ErrorMessage', 'Unknown error')
                logger.error(f"Failed to publish event: {error_msg}")
                return False
            
            logger.info(f"Successfully published event: {detail_type} to {bus_name or 'default'}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to put event to EventBridge: {e}")
            raise EventBridgeClientError(f"EventBridge put_event failed: {e}")
    
    def put_match_data_fetched_event(self, session_id: str, summoner_name: str, 
                                   region: str, match_count: int, 
                                   event_bus_name: Optional[str] = None) -> bool:
        """Put match data fetched event"""
        detail = {
            'session_id': session_id,
            'summoner_name': summoner_name,
            'region': region,
            'match_count': match_count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        return self.put_event(
            source='d-summoner-story',
            detail_type='Match Data Fetched',
            detail=detail,
            event_bus_name=event_bus_name
        )
    
    def put_statistics_processed_event(self, session_id: str, summoner_name: str,
                                     region: str, statistics_summary: Dict[str, Any],
                                     event_bus_name: Optional[str] = None) -> bool:
        """Put statistics processed event"""
        detail = {
            'session_id': session_id,
            'summoner_name': summoner_name,
            'region': region,
            'statistics_summary': statistics_summary,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        return self.put_event(
            source='d-summoner-story',
            detail_type='Statistics Processed',
            detail=detail,
            event_bus_name=event_bus_name
        )
    
    def put_insights_generated_event(self, session_id: str, summoner_name: str,
                                   region: str, insights_summary: Dict[str, Any],
                                   event_bus_name: Optional[str] = None) -> bool:
        """Put insights generated event"""
        detail = {
            'session_id': session_id,
            'summoner_name': summoner_name,
            'region': region,
            'insights_summary': insights_summary,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        return self.put_event(
            source='d-summoner-story',
            detail_type='Insights Generated',
            detail=detail,
            event_bus_name=event_bus_name
        )


# Singleton instance for Lambda reuse
_eventbridge_client = None


def get_eventbridge_client() -> EventBridgeClient:
    """Get singleton EventBridge client"""
    global _eventbridge_client
    if _eventbridge_client is None:
        _eventbridge_client = EventBridgeClient()
    return _eventbridge_client
