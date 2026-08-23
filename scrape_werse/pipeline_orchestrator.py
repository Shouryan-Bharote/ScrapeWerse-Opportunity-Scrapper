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
    db_client: FirestoreRESTClient,
) -> None:
    """
    Execute one full ingestion pipeline run.

    Args:
        urls: Target URLs to scrape.
        collector_id: Bright Data Scraper Studio template/collector ID.
        bd_client: Initialized BrightDataClient.
        db_client: Initialized FirestoreRESTClient.
    """
    logger.info(
        f"━━━ Pipeline Run Started ━━━ "
        f"Collector: '{collector_id}' | URLs: {len(urls)}"
    )

    # ── Step 1: Trigger Scraper ───────────────────────────────────────────────
    trigger_resp = await bd_client.trigger_scraper(collector_id, urls)
    response_id = trigger_resp.get("id")
    if not response_id:
        logger.error("Trigger response missing 'id'. Cannot proceed.")
        return

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
    if broken_flag:
        logger.warning(
            "⚠️  Schema drift detected. Initiating autonomous self-healing loop..."
        )

        # Build a descriptive prompt for the Cloud AI based on observed failures
        unique_errors = list(set(validation_errors))
        heal_prompt = (
            "Selector 'title' or 'organizer' broke on the latest website "
            "redesign and is returning null/empty values. "
            f"Observed errors: {'; '.join(unique_errors[:3])}. "
            "Locate the correct header and organizer elements on this page "
            "and remap the selectors to extract them accurately."
        )

        await bd_client.initiate_self_heal(collector_id, heal_prompt)

        heal_success = await bd_client.auto_approve_heal(collector_id)

        if heal_success:
            logger.info(
                "🔧 Selectors auto-healed! Re-running scraper to capture "
                "clean data with updated extraction template..."
            )

            # Re-trigger and re-validate with the healed selectors
            re_trigger = await bd_client.trigger_scraper(collector_id, urls)
            healed_dataset = await bd_client.get_dataset(re_trigger.get("id"))

            valid_records.clear()
            for row in healed_dataset:
                try:
                    validated = Opportunity(**row)
                    valid_records.append(validated.model_dump(mode="json"))
                except Exception as exc:
                    logger.warning(
                        f"Post-heal validation still failing: {exc}. "
                        "Manual investigation required."
                    )

            logger.info(
                f"Post-heal extraction: {len(valid_records)} valid record(s)."
            )
        else:
            logger.error(
                "❌ Autonomous healing was unable to recover selectors. "
                "Alerting developers — manual intervention required."
            )
            # TODO: Hook in alerting (email/Slack/PagerDuty) here
            return

    # ── Step 5: Stream to Firestore ───────────────────────────────────────────
    if not valid_records:
        logger.warning("No valid records to sync. Pipeline run complete (no-op).")
        return

    logger.info(
        f"📤 Syncing {len(valid_records)} verified record(s) to Firestore "
        f"collection 'opportunities'..."
    )

    doc_ids = await db_client.batch_upsert(valid_records)

    logger.info(
        f"✅ Pipeline run complete. "
        f"{len(doc_ids)}/{len(valid_records)} records synced to Firestore."
    )


# ── Entrypoint ────────────────────────────────────────────────────────────────


async def main() -> None:
    """
    Main entrypoint: reads config from environment and runs one pipeline
    per configured source (Devpost, Unstop, Hack2Skill).

    Required env vars (set in .env):
      - BRIGHTDATA_API_KEY
      - BRIGHTDATA_DEVPOST_COLLECTOR_ID
      - BRIGHTDATA_UNSTOP_HACKATHON_COLLECTOR_ID
      - BRIGHTDATA_UNSTOP_COMPETITION_COLLECTOR_ID
      - BRIGHTDATA_HACK2SKILL_COLLECTOR_ID
      - FIREBASE_PROJECT_ID

    Optional env vars:
      - FIREBASE_API_KEY
      - SELF_HEAL_MAX_ATTEMPTS (default: 15)
      - SELF_HEAL_POLL_INTERVAL (default: 3)
      - LOG_LEVEL (default: INFO)
    """
    # ── Environment Validation ────────────────────────────────────────────────
    bd_key = os.getenv("BRIGHTDATA_API_KEY")
    fb_project = os.getenv("FIREBASE_PROJECT_ID")

    # Per-source collector IDs
    collector_ids: dict[str, str | None] = {
        "devpost": os.getenv("BRIGHTDATA_DEVPOST_COLLECTOR_ID"),
        "unstop_hackathon": os.getenv("BRIGHTDATA_UNSTOP_HACKATHON_COLLECTOR_ID"),
        "unstop_competition": os.getenv("BRIGHTDATA_UNSTOP_COMPETITION_COLLECTOR_ID"),
        "hack2skill": os.getenv("BRIGHTDATA_HACK2SKILL_COLLECTOR_ID"),
    }

    missing: list[str] = []
    if not bd_key:
        missing.append("BRIGHTDATA_API_KEY")
    if not fb_project:
        missing.append("FIREBASE_PROJECT_ID")
    for source, cid in collector_ids.items():
        if not cid:
            missing.append(f"BRIGHTDATA_{source.upper()}_COLLECTOR_ID")

    if missing:
        logger.error(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in your credentials."
        )
        sys.exit(1)

    # ── Initialize Clients ────────────────────────────────────────────────────
    bd_client = BrightDataClient(api_key=bd_key)  # type: ignore[arg-type]
    db_client = FirestoreRESTClient(
        project_id=fb_project,  # type: ignore[arg-type]
        api_key=os.getenv("FIREBASE_API_KEY"),
    )

    # ── Run one pipeline per source sequentially ──────────────────────────────
    for source, collector_id in collector_ids.items():
        url = DEFAULT_TARGET_URLS[source]
        logger.info(f"\n{'='*60}\n  Source: {source.upper()}\n{'='*60}")
        await run_pipeline(
            urls=[url],
            collector_id=collector_id,  # type: ignore[arg-type]
            bd_client=bd_client,
            db_client=db_client,
        )


if __name__ == "__main__":
    asyncio.run(main())
