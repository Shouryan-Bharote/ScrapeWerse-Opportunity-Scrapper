# System Architecture

## Overview

ScrapeWerse is built around a **strict, three-layer asynchronous architecture**. Dependencies flow **downward only** — no module in a lower layer ever imports from a layer above it. All I/O is fully non-blocking (`httpx` + `asyncio`).

```
┌───────────────────────────────────────────────────────────────────┐
│                      CLI / Orchestration                           │
│         pipeline_orchestrator.py  ·  run_demo.py                  │
│         heal_all_scrapers.py                                       │
└──────────────────────────────┬────────────────────────────────────┘
                                │  Controls flow (top → down only)
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                         Service Layer                              │
│     brightdata_client.py  (Scraping + Autonomous Self-Healing)    │
│     firebase_sync.py      (Firestore REST Upsert + Dedup)         │
└──────────────────────────────┬────────────────────────────────────┘
                                │  Uses validated contracts
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                         Domain Layer                               │
│              shared/models/models.py  (Pydantic v2)               │
│              OpportunityType · DifficultyLevel · LocationType      │
└───────────────────────────────────────────────────────────────────┘
```

---

## Strict Layer Boundaries

| Layer | Module | Rule |
|---|---|---|
| **Orchestration** | `pipeline_orchestrator.py`, `run_demo.py` | Imports from Service + Domain layers. Nothing imports from here. |
| **Service** | `brightdata_client.py`, `firebase_sync.py` | Imports from Domain layer only. Never imports other service modules. |
| **Domain** | `models.py` | Imports **nothing** from this project. Pure Pydantic + stdlib. |

---

## Autonomous Self-Healing Flow

This is the core innovation of the project. The pipeline detects and repairs broken scrapers without any human intervention.

### Detection Triggers

Two conditions cause the pipeline to enter the healing loop:

1. **Empty extraction** — `len(raw_dataset) == 0`: The scraper found nothing because its CSS selectors no longer match the page's HTML structure.
2. **Total validation failure** — Every returned row fails Pydantic validation (0 valid records, N failures): The scraper is returning data but the field names / structure have completely changed.

Partial failures (some rows valid, some not) are handled gracefully — the pipeline proceeds with valid records and skips the heal.

### Healing Sequence

```
[1] POST /dca/trigger?collector={id}
      payload: [{"url": "https://target-site.com"}]
      response: {"id": "j_abc123"}          ← response_id
        │
        ▼
[2] GET /dca/dataset?id=j_abc123
      poll until 200 OK (was 202 Accepted)
      response: [...rows...]                ← raw_dataset
        │
        ▼
[3] Pydantic v2: Opportunity(**row) for each row
        │
        ├──> All valid ─────────────────────────────────────────┐
        │                                                         │
        └──> Drift detected (0 rows OR 0 valid)                  │
                    │                                             │
                    ▼                                             │
[4] POST /dca/collectors/{id}/refactor_template                  │
      payload: {"prompt": "...", "custom_input": []}             │
      Bright Data Cloud AI crawls the page DOM                   │
        │                                                         │
        ▼                                                         │
[5] GET /dca/collectors/{id}/refactor_template/progress          │
      poll every 5s until status = "pending_answer"              │
        │                                                         │
        ▼                                                         │
[6] POST /dca/collectors/{id}/resume_automation_job              │
      payload: {"message": true, "auto_save": true}              │
      Approves and permanently saves the AI-generated template   │
        │                                                         │
        ▼                                                         │
[7] POST /dca/trigger?collector={id}   (re-scrape)               │
        │                                                         │
        └──────────────────────────────────────────────────────── ┤
                                                                  ▼
                                              [8] PATCH Firestore /documents/{collection}/{id}
                                                  (SHA-256 dedup on event URL)
```

### CLI Fallback

If the REST `refactor_template` endpoint fails for any reason, `BrightDataClient._heal_via_cli()` automatically falls back to the Bright Data CLI:

```bash
npx -p @brightdata/cli bdata scraper heal {collector_id} {prompt} --auto-approve --auto-save
```

---

## Data Sources & Firestore Routing

| Source Key | Target URL | Bright Data Collector | Firestore Collection |
|---|---|---|---|
| `devpost` | `devpost.com/hackathons?page=N` | `BRIGHTDATA_DEVPOST_COLLECTOR_ID` | `opportunities` |
| `unstop_hackathon` | `unstop.com/hackathons?oppstatus=open` | `BRIGHTDATA_UNSTOP_HACKATHON_COLLECTOR_ID` | `opportunities` |
| `unstop_competition` | `unstop.com/competitions?oppstatus=open` | `BRIGHTDATA_UNSTOP_COMPETITION_COLLECTOR_ID` | `opportunities` |
| `dummywebsite` | `scrape-event-website.onrender.com` | `BRIGHTDATA_DUMMYWEBSITE_COLLECTOR_ID` | `demo_opportunities` |

---

## Normalization Logic

Raw scraper output is normalized in two steps inside `pipeline_orchestrator.py`:

### Step 1: `extract_and_normalize_records(raw: dict)`

Handles the structure difference between scraper output formats:

- **Nested arrays** (`event_cards`, `hackathon_cards`, `competitions`): loops through every card in the array and normalizes each individually.
- **Flat rows**: normalizes the row directly.

### Step 2: `normalize_single_card(card: dict)`

Maps scraper-specific field names to Opportunity model field names:

| Scraper Field | Opportunity Model Field |
|---|---|
| `eventtype` | `opportunity_type` |
| `event_type` | `opportunity_type` |
| `status` | `is_active` |
| `total_prize_value` | `prizes_total` |
| `prize` | `prizes_total` |
| `skills` / `tags` | `required_skills` |

Also infers `source` from the URL if the scraper doesn't include it, and defaults `organizer` to `"Community / Host"` if missing.

---

## Deduplication Strategy

Every document written to Firestore uses a **deterministic document ID** derived from the event URL:

```python
doc_id = hashlib.sha256(url.encode()).hexdigest()[:20]
# e.g. "c1a06677e5cb604558f3"
```

This means:
- Re-running the pipeline on the same events is **idempotent** (PATCH updates, no duplicates).
- Deleting and re-inserting the same event returns the same document ID.
- Document IDs are stable across runs and environments.

---

## Environment Configuration

All runtime configuration is managed via `.env`. Copy `.env.example` → `.env`:

```env
BRIGHTDATA_API_KEY=...
BRIGHTDATA_DEVPOST_COLLECTOR_ID=c_...
BRIGHTDATA_UNSTOP_HACKATHON_COLLECTOR_ID=c_...
BRIGHTDATA_UNSTOP_COMPETITION_COLLECTOR_ID=c_...
BRIGHTDATA_DUMMYWEBSITE_COLLECTOR_ID=c_...
FIREBASE_PROJECT_ID=...
FIREBASE_API_KEY=...
LOG_LEVEL=INFO
```
