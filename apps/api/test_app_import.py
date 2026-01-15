#!/usr/bin/env python3
"""Test if app.main can be imported without crashing."""
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("Starting import test...")

try:
    logger.info("Importing app.main...")
    from app import main
    logger.info("SUCCESS: app.main imported without errors")
    logger.info(f"FastAPI app created: {main.app}")
    logger.info(f"App title: {main.app.title}")
    logger.info(f"Routes: {len(main.app.routes)} routes")
except Exception as e:
    logger.error(f"FAILED to import app.main: {e}", exc_info=True)
    sys.exit(1)
