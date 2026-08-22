# PHASE_03 — Firestore Sync Integration

**Status:** ⬜ Planned

---

## Goal

Verify that validated Opportunity records can be written to and read from Google Cloud Firestore via the REST client.

## Tasks

- [ ] Create Firestore database in Firebase console
- [ ] Configure security rules to allow server-side writes
- [ ] Set `FIREBASE_PROJECT_ID` (and optionally `FIREBASE_API_KEY`) in `.env`
- [ ] Test `upsert_opportunity()` with a hardcoded sample record
- [ ] Confirm document appears in Firebase console under `opportunities/`
- [ ] Test idempotency: upsert same URL twice → single document (PATCH semantics)
- [ ] Test `batch_upsert()` with multiple records

## Verification

```python
import asyncio
from scrape_werse.scraper.sync.firebase_sync import create_client_from_env

sample = {
    "title": "Test Hackathon",
    "url": "https://devpost.com/hackathons",
    "organizer": "Devpost",
    "is_active": True,
    "required_skills": ["Python", "ML"],
}

async def test():
    client = create_client_from_env()
    doc_id = await client.upsert_opportunity(sample)
    print(f"Wrote doc: {doc_id}")

asyncio.run(test())
```
