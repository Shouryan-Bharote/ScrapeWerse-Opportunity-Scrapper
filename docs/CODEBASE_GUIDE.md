# Codebase Guide

A practical reference for navigating and working with the ScrapeWerse Python backend.

---

## Entry Points

| Script | Purpose | Command |
|---|---|---|
| `pipeline_orchestrator.py` | Full production pipeline | `python -m scrape_werse.pipeline_orchestrator` |
| `run_demo.py` | Self-healing demo (dummy website only) | `python run_demo.py` |
| `heal_all_scrapers.py` | Re-train all scrapers via Bright Data AI | `python heal_all_scrapers.py` |

---

## Module Reference

### `scrape_werse/pipeline_orchestrator.py` — Orchestration Layer

The top-level controller. Reads config from `.env`, wires up the service clients, and runs the full 5-step pipeline for each source.

**Key functions:**

| Function | Description |
|---|---|
| `run_pipeline(urls, collector_id, bd_client, db_client, collection_name)` | Executes one full scrape → validate → heal (if needed) → sync cycle |
| `extract_and_normalize_records(raw)` | Extracts all opportunity cards from a raw scraper row (handles nested arrays) |
| `normalize_single_card(card)` | Maps scraper field names to Opportunity model fields |
| `main()` | CLI entrypoint with `--demo`, `--source`, `--all` flags |

**Configuration constants:**

| Constant | Value |
|---|---|
| `DEFAULT_TARGET_URLS` | Dict of source name → seed URL |
| `SOURCE_COLLECTIONS` | Dict of source name → Firestore collection name |
| `PRODUCTION_SOURCES` | `["devpost", "unstop_hackathon", "unstop_competition"]` |

---

### `scrape_werse/scraper/client/brightdata_client.py` — Service Layer

Async HTTP client for Bright Data Scraper Studio. Handles triggering runs, polling for results, and the full autonomous self-healing loop.

**Key methods:**

| Method | REST Call | Description |
|---|---|---|
| `trigger_scraper(collector_id, urls)` | `POST /dca/trigger?collector={id}` | Starts an extraction run |
| `get_dataset(response_id)` | `GET /dca/dataset?id={id}` | Polls until dataset is ready (200 OK vs 202 Accepted) |
| `self_heal_and_approve(collector_id, prompt)` | Three calls (see below) | Full heal cycle: trigger → poll → approve |
| `_heal_via_cli(collector_id, prompt)` | `npx @brightdata/cli bdata scraper heal` | CLI fallback if REST fails |

**Self-healing REST sequence inside `self_heal_and_approve`:**

```
POST /dca/collectors/{id}/refactor_template          ← start AI repair
GET  /dca/collectors/{id}/refactor_template/progress ← poll (5s interval)
POST /dca/collectors/{id}/resume_automation_job      ← auto-approve
     payload: {"message": true, "auto_save": true}
```

---

### `scrape_werse/scraper/sync/firebase_sync.py` — Service Layer

Zero-SDK Firestore REST client. Writes records using HTTP PATCH (upsert semantics).

**Key methods:**

| Method | Description |
|---|---|
| `batch_upsert(records, collection_name)` | Writes all records to Firestore concurrently |
| `_build_document(record)` | Converts Python dict → Firestore REST document format |
| `_make_doc_id(url)` | SHA-256 hash of URL → 20-char hex document ID |

---

### `scrape_werse/shared/models/models.py` — Domain Layer

Pydantic v2 schema definitions. The single source of truth for what constitutes a valid opportunity record.

**Models:**

| Model | Description |
|---|---|
| `Opportunity` | Core record schema with validators and coercions |
| `OpportunityType` | Enum: `Hackathon`, `Competition`, `Conference`, `Fellowship`, `Grant`, `Other` |
| `DifficultyLevel` | Enum: `Beginner`, `Intermediate`, `Advanced` |
| `LocationType` | Enum: `Online`, `Hybrid`, `In-Person` |

**Smart validators on `Opportunity`:**

| Validator | Input → Output |
|---|---|
| `coerce_prizes_total` | `"$740,000"` / `{"value": 740000}` / `740000` → `float` |
| `parse_flexible_deadline` | `"27 days left"` / `"Oct 01, 2026"` / ISO string → `datetime` |
| `normalize_opportunity_type` | `"hackathon"` → `OpportunityType.HACKATHON` |
| `normalize_is_active` | `"active"` / `"upcoming"` → `True`; `"closed"` → `False` |

---

## CLI Flags Reference

### `pipeline_orchestrator.py`

```
python -m scrape_werse.pipeline_orchestrator [OPTIONS]

  (no args)        Run production scrapers (devpost, unstop_hackathon, unstop_competition)
                   → writes to 'opportunities' collection

  --demo           Run only dummywebsite scraper
                   → writes to 'demo_opportunities' collection

  --source NAME    Run a single named source
                   Choices: devpost | unstop_hackathon | unstop_competition | dummywebsite

  --all            Run all sources including dummywebsite
```

### `heal_all_scrapers.py`

```
python heal_all_scrapers.py [--target TARGET]

  (no args)               Heal all 3 production scrapers sequentially
  --target devpost        Heal only Devpost
  --target unstop_hackathon
  --target unstop_competition
```

---

## Adding a New Scraper Source

1. Create a new collector in Bright Data Scraper Studio.
2. Add its ID to `.env.example` and `.env`:
   ```env
   BRIGHTDATA_NEWSOURCE_COLLECTOR_ID=c_...
   ```
3. Add entries to `pipeline_orchestrator.py`:
   ```python
   DEFAULT_TARGET_URLS["newsource"] = "https://newsource.com/events"
   SOURCE_COLLECTIONS["newsource"] = "opportunities"
   PRODUCTION_SOURCES.append("newsource")  # if it's a production source
   ```
4. Add a healing prompt entry to `heal_all_scrapers.py` under `SCRAPERS`.
5. Run `python heal_all_scrapers.py --target newsource` to calibrate the template.

---

## Logging

Log level is controlled by the `LOG_LEVEL` environment variable (default `INFO`):

```env
LOG_LEVEL=DEBUG   # Maximum verbosity — shows every HTTP request
LOG_LEVEL=INFO    # Standard output — pipeline steps + summaries
LOG_LEVEL=WARNING # Minimal — only warnings and errors
```

On Windows, `sys.stdout` is reconfigured to UTF-8 at startup to prevent emoji/charmap encoding errors in the terminal.
