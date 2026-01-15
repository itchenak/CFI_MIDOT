#!/usr/bin/env python3
"""
Check for changes in NGO proper management certificate status.

This script compares the current scraped data with previously committed data
and sends email notifications via Gmail SMTP when changes are detected.

Usage:
    python check_proper_management.py

Required environment variables:
    - GMAIL_SMTP_USER: Gmail address (or account alias)
    - GMAIL_SMTP_PASSWORD: Gmail app password
    - EMAIL_FROM: Sender email address (must be Gmail)
    - EMAIL_TO: Recipient email address(es), comma-separated for multiple
    - REMOTE_PROPER_MANAGEMENT_URL: URL to previously published CSV
"""

import logging
import sys
from notifiers.proper_management_tracker import (
    ProperManagementChangeType,
    check_and_notify,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for proper management status checking."""
    logger.info("Starting proper management status check...")
    
    try:
        changes, email_sent = check_and_notify()
        
        if changes:
            gained = len([c for c in changes if c.change_type == ProperManagementChangeType.GAINED])
            lost = len([c for c in changes if c.change_type == ProperManagementChangeType.LOST])
            logger.info(
                f"Summary: {len(changes)} changes detected "
                f"({gained} gained, {lost} lost proper management)"
            )
            
            if email_sent:
                logger.info("Notification email sent successfully")
            else:
                logger.warning("Failed to send notification email")
                return 1
        else:
            logger.info("No changes detected in proper management status")
        
        logger.info("Proper management status check completed")
        return 0
        
    except Exception as e:
        logger.exception(f"Error during proper management check: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

