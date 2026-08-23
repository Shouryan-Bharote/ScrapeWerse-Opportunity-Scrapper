"""
Run Demo — Autonomous Self-Healing Scraper Demonstration
=========================================================
Standalone script to run ONLY the Dummy Website scraper for hackathon demo.

- Target Website: https://scrape-event-website.onrender.com/
- Target Firestore Collection: 'demo_opportunities'
- Autonomous Self-Healing: Enabled (auto-adjusts selectors if layout breaks)

Usage:
    python run_demo.py
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from scrape_werse.pipeline_orchestrator import run_pipeline, DEFAULT_TARGET_URLS, SOURCE_COLLECTIONS
from scrape_werse.scraper.client.brightdata_client import BrightDataClient
from scrape_werse.scraper.sync.firebase_sync import FirestoreRESTClient

# Ensure UTF-8 output encoding on Windows terminals to prevent charmap logging errors
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("DemoRunner")


async def main() -> None:
    bd_key = os.getenv("BRIGHTDATA_API_KEY")
    collector_id = os.getenv("BRIGHTDATA_DUMMYWEBSITE_COLLECTOR_ID")
    fb_project = os.getenv("FIREBASE_PROJECT_ID")
    fb_key = os.getenv("FIREBASE_API_KEY")

    if not bd_key:
        logger.error("Missing BRIGHTDATA_API_KEY in .env")
        sys.exit(1)

    if not collector_id:
        logger.error("Missing BRIGHTDATA_DUMMYWEBSITE_COLLECTOR_ID in .env")
        sys.exit(1)

    url = DEFAULT_TARGET_URLS["dummywebsite"]
    collection_name = SOURCE_COLLECTIONS["dummywebsite"]

    logger.info("=" * 60)
    logger.info("🎯 STARTING DUMMY WEBSITE SELF-HEALING DEMO")
    logger.info(f"Target URL:        {url}")
    logger.info(f"Collector ID:      {collector_id}")
    logger.info(f"Target Collection: {collection_name}")
    logger.info("=" * 60)

    bd_client = BrightDataClient(api_key=bd_key)
    db_client = FirestoreRESTClient(project_id=fb_project, api_key=fb_key) if fb_project else None

    await run_pipeline(
        urls=[url],
        collector_id=collector_id,
        bd_client=bd_client,
        db_client=db_client,
        collection_name=collection_name,
    )


if __name__ == "__main__":
    asyncio.run(main())
