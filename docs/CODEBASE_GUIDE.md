# Codebase Guide

## Directory Structure

```
scrape_werse/
├── __init__.py
├── pipeline_orchestrator.py           # Top-level orchestrator & CLI entrypoint
├── shared/
│   ├── __init__.py
│   └── models/
│       ├── __init__.py
│       └── models.py                  # Pydantic v2 schemas: Opportunity, Enums
└── scraper/
    ├── __init__.py
    ├── client/
    │   ├── __init__.py
    │   └── brightdata_client.py       # BrightData Scraper Studio async client
    └── sync/
        ├── __init__.py
        └── firebase_sync.py           # Firestore REST API async client
```

---

## File Responsibilities

### 1. `scrape_werse/shared/models/models.py`
- **Responsibility:** Defines domain contracts using Pydantic v2.
- **Key Models:** `Opportunity`, `OpportunityType`, `DifficultyLevel`, `LocationType`.
- **Validation Rules:** String length constraints, HttpUrl validation, soft-validation on deadlines, whitespace stripping, and ignoring extra scraper fields.

### 2. `scrape_werse/scraper/client/brightdata_client.py`
- **Responsibility:** Interacting with Bright Data Scraper Studio.
- **Key Methods:**
  - `trigger_scraper(collector_id, urls)`: POST `/dca/trigger`
  - `get_dataset(response_id)`: GET `/dca/dataset`
  - `initiate_self_heal(collector_id, prompt)`: POST `/refactor_template`
  - `auto_approve_heal(collector_id)`: Polls progress and calls `/resume_automation_job`

### 3. `scrape_werse/scraper/sync/firebase_sync.py`
- **Responsibility:** Synchronizing opportunity models to Google Cloud Firestore via REST API.
- **Key Methods:**
  - `_generate_doc_id(url)`: Deterministic SHA-256 hash of opportunity URL.
  - `_convert_to_firestore_fields(data)`: Maps Python types to Firestore REST JSON descriptors (`stringValue`, `doubleValue`, `booleanValue`, `arrayValue`, `nullValue`).
  - `upsert_opportunity(opportunity_data)`: PATCH endpoint to create/replace document.
  - `batch_upsert(records)`: Ingests multiple records sequentially.

### 4. `scrape_werse/pipeline_orchestrator.py`
- **Responsibility:** Coordinates the entire workflow: trigger scraper -> fetch -> validate -> self-heal on drift -> re-scrape -> push to Firestore.
