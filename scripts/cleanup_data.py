#!/usr/bin/env python3
"""
Data cleanup script - removes old data based on retention settings.

Usage:
    python scripts/cleanup_data.py

This script runs the cleanup_old_data_task synchronously and can be executed:
- Manually from command line
- As a cron job
- Via CI/CD pipeline
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.cron.jobs import cleanup_old_data_task
import structlog

logger = structlog.get_logger()


async def main():
    """Run cleanup task."""
    logger.info("cleanup_script_started")
    try:
        await cleanup_old_data_task()
        logger.info("cleanup_script_completed", status="success")
        return 0
    except Exception as e:
        logger.error("cleanup_script_failed", error=str(e))
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
