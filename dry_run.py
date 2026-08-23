"""
Dry-run validation script.
Scrapes all 4 sources, validates data through the Pydantic model,
and prints a summary WITHOUT writing anything to Firestore.
"""
import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from scrape_werse.scraper.client.brightdata_client import BrightDataClient
from scrape_werse.shared.models.models import Opportunity
from scrape_werse.pipeline_orchestrator import normalize_row, DEFAULT_TARGET_URLS

load_dotenv()

bd_key = os.getenv("BRIGHTDATA_API_KEY")
collector_ids = {
    "devpost":            os.getenv("BRIGHTDATA_DEVPOST_COLLECTOR_ID"),
    "unstop_hackathon":   os.getenv("BRIGHTDATA_UNSTOP_HACKATHON_COLLECTOR_ID"),
    "unstop_competition": os.getenv("BRIGHTDATA_UNSTOP_COMPETITION_COLLECTOR_ID"),
    "hack2skill":         os.getenv("BRIGHTDATA_HACK2SKILL_COLLECTOR_ID"),
}

missing = [k for k, v in {"BRIGHTDATA_API_KEY": bd_key, **{f"BRIGHTDATA_{k.upper()}_COLLECTOR_ID": v for k, v in collector_ids.items()}}.items() if not v]
if missing:
    print(f"ERROR: Missing env vars: {missing}")
    sys.exit(1)


async def dry_run():
    client = BrightDataClient(api_key=bd_key)
    total_valid = 0
    total_failed = 0
    sample_records = []

    for source, collector_id in collector_ids.items():
        url = DEFAULT_TARGET_URLS[source]
        print(f"\n{'='*60}\n  Scraping: {source.upper()}\n  URL: {url}\n{'='*60}")

        try:
            trigger = await client.trigger_scraper(collector_id, [url])
            response_id = trigger.get("id")
            if not response_id:
                print(f"  ERROR: No response_id from trigger. Response: {trigger}")
                continue

            raw_dataset = await client.get_dataset(response_id)
            print(f"  Raw rows returned: {len(raw_dataset)}")

            source_samples = []
            valid = 0
            failed = 0
            for row in raw_dataset:
                normalized = normalize_row(row)
                if normalized is None:
                    continue

                try:
                    opp = Opportunity(**normalized)
                    valid += 1
                    if len(source_samples) < 1:
                        source_samples.append(opp.model_dump(mode="json"))
                except Exception as e:
                    failed += 1
                    print(f"  VALIDATION FAIL: {e} | Row preview: {str(normalized)[:120]}")

            print(f"  --> Valid records: {valid} | Validation failed: {failed}")
            total_valid += valid
            total_failed += failed
            if source_samples:
                print(f"  --> Sample item from {source}:")
                print(f"      Title: {source_samples[0].get('title')}")
                print(f"      Organizer: {source_samples[0].get('organizer')}")
                print(f"      URL: {source_samples[0].get('url')}")
                print(f"      Type: {source_samples[0].get('opportunity_type')}")
                print(f"      Active: {source_samples[0].get('is_active')}")
                print(f"      Skills: {source_samples[0].get('required_skills')}")
            elif len(raw_dataset) > 0:
                print(f"  --> NOTE: {len(raw_dataset)} rows were returned but 0 had card data (possible link-only rows).")
                print(f"      First row keys: {list(raw_dataset[0].keys())}")

        except Exception as e:
            print(f"  SCRAPER ERROR for {source}: {e}")

    print(f"\n{'='*60}")
    print(f"  OVERALL DRY RUN SUMMARY")
    print(f"  Total valid parsed records: {total_valid}")
    print(f"  Total failed records:       {total_failed}")
    print(f"{'='*60}")



asyncio.run(dry_run())
