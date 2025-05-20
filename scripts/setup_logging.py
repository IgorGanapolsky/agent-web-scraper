#!/usr/bin/env python3
"""
Script to test and demonstrate the logging configuration.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.logging import setup_logging, get_logger
from app.core.utils import log_performance, log_audit_event

# Configure logging
setup_logging(log_level="DEBUG")

# Get a logger for this module
logger = get_logger(__name__)

async def demo_logging():
    """Demonstrate different logging levels and features."""
    # Basic logging
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    
    # Log with extra data
    logger.info("User logged in", extra={
        "data": {
            "user_id": 12345,
            "username": "johndoe",
            "ip_address": "192.168.1.1"
        }
    })
    
    # Demonstrate performance logging
    with log_performance("demo_operation", {"param1": "value1", "param2": 42}):
        # Simulate work
        await asyncio.sleep(0.5)
        logger.info("Working inside performance context")
    
    # Demo audit logging
    log_audit_event(
        event_type="user_login",
        user="johndoe",
        resource="/api/login",
        action="login",
        status="success",
        details={"method": "password"}
    )
    
    # Log an error with exception
    try:
        result = 1 / 0
    except Exception as e:
        logger.error("An error occurred", exc_info=True, extra={
            "data": {
                "context": "division",
                "numerator": 1,
                "denominator": 0
            }
        })
    
    logger.info("Logging demonstration complete")

if __name__ == "__main__":
    asyncio.run(demo_logging())
