"""
Analytics Tracker with Consent Checks
Tracks user behavior and system metrics with proper consent verification
"""

import os
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from shared.consent_checker import check_analytics_consent, require_analytics_consent
from shared.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class AnalyticsTracker:
    """
    Analytics tracking service that respects user consent preferences.
    Only tracks analytics data for users who have granted consent.
    """
    
    def __init__(self):
        """Initialize the analytics tracker."""
        self.dynamodb = boto3.resource('dynamodb')
        self.analytics_table_name = os.environ.get(
            'ANALYTICS_TABLE',
            'aquachain-analytics-dev'
        )
        self.analytics_table = self.dynamodb.Table(self.analytics_table_name)
    
    def track_event(
        self,
        user_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track an analytics event if user has granted consent.
        
        Args:
            user_id: Unique identifier for the user
            event_type: Type of event (page_view, button_click, feature_usage, etc.)
            event_data: Event-specific data
            metadata: Optional metadata (ip_address, user_agent, etc.)
            
        Returns:
            True if event was tracked, False if consent not granted
        """
        # Check analytics consent
        if not check_analytics_consent(user_id):
            logger.log('info', 'Analytics tracking skipped - no consent',
                      user_id=user_id,
                      event_type=event_type)
            return False
        
        try:
            # Create analytics event record
            event_id = f"{user_id}:{event_type}:{datetime.utcnow().timestamp()}"
            
            event_record = {
                'event_id': event_id,
                'user_id': user_id,
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            # Store in DynamoDB
            self.analytics_table.put_item(Item=event_record)
            
            logger.log('info', 'Analytics event tracked',
                      user_id=user_id,
                      event_type=event_type)
            
            return True
            
        except Exception as e:
            logger.log('error', 'Failed to track analytics event',
                      user_id=user_id,
                      event_type=event_type,
                      error=str(e))
            return False
    
    @require_analytics_consent
    def track_page_view(
        self,
        user_id: str,
        page_path: str,
        referrer: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> None:
        """
        Track a page view event (requires analytics consent).
        
        Args:
            user_id: Unique identifier for the user
            page_path: Path of the page viewed
            referrer: Optional referrer URL
            duration_ms: Optional time spent on page in milliseconds
        """
        event_data = {
            'page_path': page_path,
            'referrer': referrer,
            'duration_ms': duration_ms
        }
        
        self.track_event(user_id, 'page_view', event_data)
    
    @require_analytics_consent
    def track_feature_usage(
        self,
        user_id: str,
        feature_name: str,
        action: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track feature usage event (requires analytics consent).
        
        Args:
            user_id: Unique identifier for the user
            feature_name: Name of the feature used
            action: Action performed (view, click, submit, etc.)
            additional_data: Optional additional data
        """
        event_data = {
            'feature_name': feature_name,
            'action': action,
            **(additional_data or {})
        }
        
        self.track_event(user_id, 'feature_usage', event_data)
    
    def track_system_metric(
        self,
        metric_name: str,
        metric_value: float,
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Track system-level metrics (does not require user consent).
        
        Args:
            metric_name: Name of the metric
            metric_value: Value of the metric
            dimensions: Optional dimensions for the metric
        """
        try:
            event_record = {
                'event_id': f"system:{metric_name}:{datetime.utcnow().timestamp()}",
                'event_type': 'system_metric',
                'metric_name': metric_name,
                'metric_value': metric_value,
                'dimensions': dimensions or {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.analytics_table.put_item(Item=event_record)
            
            logger.log('info', 'System metric tracked',
                      metric_name=metric_name,
                      metric_value=metric_value)
            
        except Exception as e:
            logger.log('error', 'Failed to track system metric',
                      metric_name=metric_name,
                      error=str(e))


# Global instance
analytics_tracker = AnalyticsTracker()


def track_user_event(
    user_id: str,
    event_type: str,
    event_data: Dict[str, Any]
) -> bool:
    """
    Convenience function to track user events with consent check.
    
    Args:
        user_id: Unique identifier for the user
        event_type: Type of event
        event_data: Event data
        
    Returns:
        True if event was tracked, False otherwise
    """
    return analytics_tracker.track_event(user_id, event_type, event_data)
