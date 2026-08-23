import asyncio
import json
import os
from dotenv import load_dotenv
from scrape_werse.scraper.client.brightdata_client import BrightDataClient
from scrape_werse.shared.models.models import Opportunity
from scrape_werse.pipeline_orchestrator import normalize_row

load_dotenv()
bd_key = os.getenv("BRIGHTDATA_API_KEY")

jobs = {
    "devpost": "j_mt5bi2ab2plrzo3opb",
    "unstop_hackathon": "j_mt5bl41mah2mt2tk3",
    "unstop_competition": "j_mt5bnb02282wpa7hn6",
    "hack2skill": "j_mt5boh0l1aqoxc66wd",
}

async def inspect():
    client = BrightDataClient(api_key=bd_key)
    for name, jid in jobs.items():
        print(f"\n{'='*60}\nSource: {name} (Job: {jid})\n{'='*60}")
        try:
            rows = await client.get_dataset(jid)
            print(f"Total raw rows: {len(rows)}")
            if not rows:
                print("No rows returned.")
                continue

            print("Sample raw row 0:")
            print(json.dumps(rows[0], indent=2, ensure_ascii=False)[:400])

            valid = 0
            failed = 0
            for r in rows:
                norm = normalize_row(r)
                if norm is None:
                    continue
                try:
                    opp = Opportunity(**norm)
                    valid += 1
                except Exception as e:
                    failed += 1
                    if failed <= 3:
                        print(f"Validation error: {e}")
            print(f"--> Valid records parsed: {valid}, Failed: {failed}")
        except Exception as e:
            print(f"Error fetching job {jid}: {e}")

asyncio.run(inspect())
