"""
Consent checker for notification service.
Self-contained version — no shared package imports.
Checks user consent flags stored in DynamoDB before sending marketing comms.
"""

import os
import boto3
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("REGION", "ap-south-1"))
USERS_TABLE = os.environ.get("USERS_TABLE", "aquachain-users")


def check_marketing_consent(user_id: str) -> bool:
    """
    Returns True if the user has consented to marketing communications.
    Defaults to False (opt-in model) if the flag is absent.
    """
    try:
        table = _dynamodb.Table(USERS_TABLE)
        response = table.get_item(
            Key={"userId": user_id},
            ProjectionExpression="preferences.notifications.marketingEmails"
        )
        item = response.get("Item", {})
        prefs = item.get("preferences", {}).get("notifications", {})
        return bool(prefs.get("marketingEmails", False))
    except Exception as e:
        logger.warning(f"consent_checker: could not read consent for {user_id}: {e}")
        return False  # deny on error — safe default


def check_analytics_consent(user_id: str) -> bool:
    """
    Returns True if the user has consented to analytics data collection.
    Defaults to False if the flag is absent.
    """
    try:
        table = _dynamodb.Table(USERS_TABLE)
        response = table.get_item(
            Key={"userId": user_id},
            ProjectionExpression="preferences.notifications.analyticsConsent"
        )
        item = response.get("Item", {})
        prefs = item.get("preferences", {}).get("notifications", {})
        return bool(prefs.get("analyticsConsent", False))
    except Exception as e:
        logger.warning(f"consent_checker: could not read analytics consent for {user_id}: {e}")
        return False
