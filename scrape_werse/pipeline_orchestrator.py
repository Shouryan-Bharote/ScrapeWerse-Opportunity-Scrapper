"""
Pipeline Orchestrator — CLI / Orchestration Layer (Top-Level)
=============================================================
Controls the full end-to-end ingestion workflow:
  1. Trigger Bright Data Scraper Studio extraction
  2. Fetch raw dataset
  3. Validate against Pydantic v2 Opportunity schema
  4. If schema drift detected → initiate autonomous self-healing loop
  5. Re-scrape with healed selectors (if healing succeeded)
  6. Stream valid records to Google Cloud Firestore

Architectural Rule: This module sits at the TOP of the dependency stack.
It imports from the service layer (brightdata_client, firebase_sync) and
the domain layer (models), but NO module below imports from here.

Usage:
    python -m scrape_werse.pipeline_orchestrator

    Or with environment overrides:
    BRIGHTDATA_COLLECTOR_ID=abc123 python -m scrape_werse.pipeline_orchestrator
"""

import asyncio
import logging
import os
import sys

from typing import Optional

from dotenv import load_dotenv

from scrape_werse.scraper.client.brightdata_client import BrightDataClient
from scrape_werse.scraper.sync.firebase_sync import FirestoreRESTClient
from scrape_werse.shared.models.models import Opportunity

load_dotenv()

# ── Logging Setup ─────────────────────────────────────────────────────────────

_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("Pipeline")

# ── Default Target URLs ───────────────────────────────────────────────────────
# These are the seed pages from which the scraper extracts AI opportunities.
# Add or remove URLs as the project grows.

DEFAULT_TARGET_URLS: dict[str, str] = {
    "devpost": "https://devpost.com/hackathons?challenge_type=online&order_by=deadline",
    "unstop_hackathon": "https://unstop.com/hackathons?oppstatus=open",
    "unstop_competition": "https://unstop.com/competitions?oppstatus=open",
    "hack2skill": "https://hack2skill.com/hackathon",
    "dummywebsite": "https://scrape-event-website.onrender.com/",
}

# Target collection in Firestore per source
SOURCE_COLLECTIONS: dict[str, str] = {
    "devpost": "opportunities",
    "unstop_hackathon": "opportunities",
    "unstop_competition": "opportunities",
    "hack2skill": "opportunities",
    "dummywebsite": "demo_opportunities",  # Isolated for hackathon self-healing demo
}


# ── Row Normalization ─────────────────────────────────────────────────────────


def normalize_row(raw: dict) -> dict | None:
    """
    Normalize a raw scraper output row into a flat dict that matches the
    Opportunity Pydantic schema.

    Handles multiple scraper response shapes:
      1. Flat: {"title": ..., "source": ..., ...}
      2. Nested cards: {"hackathon_cards": [...]}, {"competitions": [...]}, {"events": [...]}
      3. Product page / link-only rows (ignored)

    Also maps scraper-specific field aliases to model field names:
      - eventtype  → opportunity_type
      - status     → is_active
      - total_prize_value → prizes_total
    """
    # Check for known nested array keys
    for array_key in ("hackathon_cards", "competitions", "event_cards", "cards", "events"):
        if array_key in raw and raw[array_key] and isinstance(raw[array_key], list):
            record = raw[array_key][0].copy()
            break
    else:
        if "title" in raw and raw.get("title"):
            record = raw.copy()
        else:
            return None

    # Map scraper field aliases → Opportunity field names
    alias_map = {
        "eventtype": "opportunity_type",
        "event_type": "opportunity_type",
        "status": "is_active",
        "total_prize_value": "prizes_total",
    }
    for scraper_key, model_key in alias_map.items():
        if scraper_key in record and model_key not in record:
            record[model_key] = record.pop(scraper_key)

    return record


# ── Core Pipeline ─────────────────────────────────────────────────────────────


async def run_pipeline(
    urls: list[str],
    collector_id: str,
    bd_client: BrightDataClient,
    db_client: Optional[FirestoreRESTClient] = None,
    collection_name: str = "opportunities",
) -> list[dict]:
    """
    Execute one full ingestion pipeline run.

    Args:
        urls: Target URLs to scrape.
        collector_id: Bright Data Scraper Studio template/collector ID.
        bd_client: Initialized BrightDataClient.
        db_client: Optional Initialized FirestoreRESTClient. If None, runs in dry-run mode.
        collection_name: Firestore target collection.
    """
    logger.info(
        f"━━━ Pipeline Run Started ━━━ "
        f"Collector: '{collector_id}' | URLs: {len(urls)} | Target Collection: '{collection_name}'"
    )

    # ── Step 1: Trigger Scraper ───────────────────────────────────────────────
    trigger_resp = await bd_client.trigger_scraper(collector_id, urls)
    response_id = trigger_resp.get("id")
    if not response_id:
        logger.error("Trigger response missing 'id'. Cannot proceed.")
        return []

    # ── Step 2: Fetch Dataset ─────────────────────────────────────────────────
    raw_dataset = await bd_client.get_dataset(response_id)
    logger.info(f"Retrieved {len(raw_dataset)} raw row(s) from Scraper Studio.")

    # ── Step 3: Validate via Pydantic ─────────────────────────────────────────
    valid_records: list[dict] = []
    broken_flag = False
    validation_errors: list[str] = []

    for row in raw_dataset:
        try:
            # Normalize the raw row (unwrap nested structure, remap aliases)
            normalized = normalize_row(row)
            if normalized is None:
                logger.debug("Skipping empty/link-only row.")
                continue

            # Essential field guard — catches nulls BEFORE Pydantic sees them
            if not normalized.get("title") or not normalized.get("organizer"):
                raise ValueError(
                    f"Essential fields 'title' or 'organizer' returned "
                    f"empty or null. Row keys: {list(normalized.keys())}"
                )

            validated = Opportunity(**normalized)
            valid_records.append(validated.model_dump(mode="json"))

        except Exception as exc:
            error_msg = str(exc)
            logger.warning(f"Validation failure — schema drift detected: {error_msg}")
            validation_errors.append(error_msg)
            broken_flag = True

    logger.info(
        f"Validation complete: {len(valid_records)} valid, "
        f"{len(validation_errors)} failed."
    )

    # ── Step 4: Autonomous Self-Healing (if needed) ───────────────────────────
    # Only trigger a full heal when the ENTIRE dataset failed validation,
    # meaning the page layout almost certainly changed. Partial failures
    # (optional-field gaps) are handled gracefully by proceeding with
    # the valid records we already have.
    if broken_flag and len(valid_records) == 0 and len(raw_dataset) > 0:
        logger.warning(
            f"⚠️  Total schema drift on collector '{collector_id}' "
            f"({len(validation_errors)} rows failed, 0 passed). "
            "Initiating autonomous self-healing loop..."
        )

        unique_errors = list(set(validation_errors))
        heal_prompt = (
            "The scraper selectors are broken after a website layout change. "
            "Required fields 'title' and/or 'organizer' are returning null or empty. "
            f"Observed validation errors: {'; '.join(unique_errors[:5])}. "
            "Please re-inspect the target page DOM, find the correct elements for "
            "title, url, organizer, description, deadline, required_skills, source, "
            "eventtype, and status, then update the extraction selectors accordingly."
        )

        heal_success = await bd_client.self_heal_and_approve(collector_id, heal_prompt)

        if heal_success:
            logger.info(
                "🔧 Selectors healed and approved! Re-running scraper with "
                "updated extraction template..."
            )

            re_trigger = await bd_client.trigger_scraper(collector_id, urls)
            re_id = re_trigger.get("id")
            if re_id:
                healed_dataset = await bd_client.get_dataset(re_id)
                valid_records.clear()
                for row in healed_dataset:
                    try:
                        norm = normalize_row(row)
                        if norm:
                            validated = Opportunity(**norm)
                            valid_records.append(validated.model_dump(mode="json"))
                    except Exception as exc:
                        logger.warning(f"Post-heal validation error: {exc}")
                logger.info(
                    f"Post-heal extraction: {len(valid_records)} valid record(s)."
                )
        else:
            logger.error(
                f"❌ Autonomous healing failed for collector '{collector_id}'. "
                "Skipping this source for this run."
            )
            return valid_records

    elif broken_flag:
        logger.warning(
            f"Partial schema drift on collector '{collector_id}': "
            f"{len(validation_errors)} row(s) failed, "
            f"{len(valid_records)} row(s) passed. "
            "Proceeding with valid records (no heal needed)."
        )

    # ── Step 5: Stream to Firestore (if db_client is configured) ─────────────
    if not valid_records:
        logger.warning("No valid records to sync. Pipeline run complete.")
        return []

    if db_client is not None:
        logger.info(
            f"📤 Syncing {len(valid_records)} record(s) to Firestore "
            f"collection '{collection_name}'..."
        )
        doc_ids = await db_client.batch_upsert(valid_records, collection_name=collection_name)
        logger.info(
            f"✅ {len(doc_ids)}/{len(valid_records)} records synced to Firestore collection '{collection_name}'."
        )
    else:
        logger.info(f"ℹ️ [Dry-Run] {len(valid_records)} records ready. (Firestore not connected yet).")

    return valid_records


# ── Entrypoint ────────────────────────────────────────────────────────────────


async def main() -> None:
    """
    Main entrypoint: reads config from environment and runs the pipeline.
    Pass '--demo' to run only the dummy website scraper in the isolated demo collection.
    """
    bd_key = os.getenv("BRIGHTDATA_API_KEY")
    fb_project = os.getenv("FIREBASE_PROJECT_ID")

    collector_ids: dict[str, str | None] = {
        "devpost": os.getenv("BRIGHTDATA_DEVPOST_COLLECTOR_ID"),
        "unstop_hackathon": os.getenv("BRIGHTDATA_UNSTOP_HACKATHON_COLLECTOR_ID"),
        "unstop_competition": os.getenv("BRIGHTDATA_UNSTOP_COMPETITION_COLLECTOR_ID"),
        "hack2skill": os.getenv("BRIGHTDATA_HACK2SKILL_COLLECTOR_ID"),
        "dummywebsite": os.getenv("BRIGHTDATA_DUMMYWEBSITE_COLLECTOR_ID"),
    }

    if not bd_key:
        logger.error("Missing BRIGHTDATA_API_KEY in .env")
        sys.exit(1)

    bd_client = BrightDataClient(api_key=bd_key)
    db_client = (
        FirestoreRESTClient(
            project_id=fb_project,
            api_key=os.getenv("FIREBASE_API_KEY"),
        )
        if fb_project
        else None
    )

    # Check for --demo flag
    is_demo = "--demo" in sys.argv
    sources_to_run = ["dummywebsite"] if is_demo else [s for s, cid in collector_ids.items() if cid]

    for source in sources_to_run:
        cid = collector_ids.get(source)
        if not cid:
            logger.warning(f"Skipping {source}: no collector ID set in .env")
            continue

        url = DEFAULT_TARGET_URLS[source]
        target_collection = SOURCE_COLLECTIONS.get(source, "opportunities")

        logger.info(f"\n{'='*60}\n  Source: {source.upper()} -> Collection: '{target_collection}'\n{'='*60}")
        await run_pipeline(
            urls=[url],
            collector_id=cid,
            bd_client=bd_client,
            db_client=db_client,
            collection_name=target_collection,
        )


if __name__ == "__main__":
    asyncio.run(main())

