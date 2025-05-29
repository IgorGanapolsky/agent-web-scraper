#!/usr/bin/env python3
"""
Test script to verify Sentry integration.
"""

import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_sentry():
    """Test Sentry integration with different log levels."""
    try:
        # Import Sentry after environment is set up
        import sentry_sdk

        from app.observability import setup_sentry

        # Initialize Sentry
        sentry_dsn = os.getenv("SENTRY_DSN")
        if not sentry_dsn:
            logger.error("SENTRY_DSN not found in environment variables")
            return False

        environment = os.getenv("ENVIRONMENT", "development")
        setup_sentry(dsn=sentry_dsn, environment=environment)

        logger.info("Sentry initialized successfully")

        # Test different log levels
        logger.debug("This is a DEBUG message (should not appear in Sentry)")
        logger.info("This is an INFO message (should appear in breadcrumbs)")
        logger.warning("This is a WARNING message (should appear as event)")

        # Test an error
        try:
            1 / 0
        except Exception:
            logger.error("This is an ERROR with exception", exc_info=True)

        # Test a critical error
        logger.critical("This is a CRITICAL message")

        # Test a custom event
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("test", "custom_event")
            scope.set_extra("extra_info", {"key": "value"})
            sentry_sdk.capture_message("This is a custom event")

        return True

    except Exception as e_info:
        logger.error(f"Error testing Sentry: {e_info}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("Starting Sentry test...")
    if test_sentry():
        logger.info("Sentry test completed successfully")
        # Give Sentry some time to send events
        time.sleep(2)
    else:
        logger.error("Sentry test failed")
