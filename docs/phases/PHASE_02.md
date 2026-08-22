# PHASE_02 — BrightData Client Integration

**Status:** ⬜ Planned

---

## Goal

Establish a working connection to Bright Data Scraper Studio and validate the async client end-to-end.

## Tasks

- [ ] Obtain Bright Data API key (`BRIGHTDATA_API_KEY`)
- [ ] Create a Scraper Studio collector for at least one target site
- [ ] Record the `BRIGHTDATA_COLLECTOR_ID`
- [ ] Test `trigger_scraper()` — confirm 200 response and `id` field present
- [ ] Test `get_dataset()` with the response `id`
- [ ] Verify the self-heal endpoint is reachable (`initiate_self_heal`)
- [ ] Test `auto_approve_heal` polling with a dummy heal job

## Verification

```python
import asyncio
from scrape_werse.scraper.client.brightdata_client import create_client_from_env

async def test():
    client = create_client_from_env()
    resp = await client.trigger_scraper("YOUR_COLLECTOR_ID", ["https://devpost.com/hackathons"])
    print(resp)

asyncio.run(test())
```
