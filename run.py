#!/usr/bin/env python3
"""
Main entry point for the application.

This script runs the Streamlit web interface.
"""
import sys
import os
from pathlib import Path
import streamlit.web.bootstrap
from app.utils.port_utils import find_available_port
from app.observability import log_exceptions
from app.config.safe_logger import get_logger, setup_logging

def run_web():
    """Run the Streamlit web application."""
    # Set up logging
    setup_logging()
    logger = get_logger(__name__)
    
    @log_exceptions
    def run_streamlit():
        """Run the Streamlit application with proper configuration."""
        try:
            port = find_available_port()
            logger.info(f"Starting Streamlit on port {port}")
            
            streamlit.web.bootstrap.run(
                "app/web/app.py",
                "",
                [],
                flag_options={
                    "server.port": port,
                    "server.headless": False,
                    "server.enableCORS": True,
                    "server.enableXsrfProtection": True,
                },
            )
        except Exception as e:
            logger.error(f"Failed to start Streamlit: {str(e)}")
            sys.exit(1)
    
    run_streamlit()

if __name__ == "__main__":
    # Add the project root to the Python path
    project_root = str(Path(__file__).parent.absolute())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    run_web()
