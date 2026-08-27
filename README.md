# ScrapeWerse — Autonomous AI Opportunity Tracker

> **Hackathon Submission** · Python Ingestion Backend · Powered by [Bright Data Scraper Studio](https://brightdata.com)

ScrapeWerse is a **fully autonomous, self-healing web scraping pipeline** that continuously discovers AI hackathons and competitions from across the web and syncs them into Google Cloud Firestore — **without any human intervention**, even when target websites change their layout.

---

## ✨ Key Features

| Feature | Details |
|---|---|
| **4 Live Data Sources** | Devpost, Unstop Hackathons, Unstop Competitions, Dummy Demo Site |
| **Autonomous Self-Healing** | Detects broken selectors, triggers Bright Data Cloud AI repair, auto-approves the fix — zero manual clicks |
| **Pydantic v2 Validation** | Strict schema enforcement with smart field coercion (prizes, deadlines, enums) |
| **Deduplication** | SHA-256 hash of event URL as document ID — safe to re-run anytime |
| **Fully Async** | 100% non-blocking I/O via `httpx` + `asyncio` |
| **Zero SDK dependencies** | Firestore via plain REST — no Firebase Admin SDK needed |

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                      CLI / Orchestration                           │
│         pipeline_orchestrator.py  ·  run_demo.py                  │
└──────────────────────────────┬────────────────────────────────────┘
                                │  Controls flow
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                         Service Layer                              │
│     brightdata_client.py  (Scraping + Self-Healing)               │
│     firebase_sync.py      (Firestore REST Upsert)                 │
└──────────────────────────────┬────────────────────────────────────┘
                                │  Uses contracts
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                         Domain Layer                               │
│              shared/models/models.py  (Pydantic v2)               │
└───────────────────────────────────────────────────────────────────┘
```

Dependencies flow **downward only**. All I/O is non-blocking async.

---

## 🔄 Self-Healing Pipeline (The Core Innovation)

When a scraped website changes its HTML layout, the pipeline detects and repairs itself autonomously:

```
[1] Trigger Bright Data Scraper
        │
        ▼
[2] Fetch Dataset
        │
        ▼
[3] Validate via Pydantic v2 ─── ✅ All valid ──────────────────┐
        │                                                         │
        └── ❌ Schema drift detected (0 rows OR validation fail)  │
                    │                                             │
                    ▼                                             │
[4] POST /dca/collectors/{id}/refactor_template                  │
        │  (AI analyzes page DOM, repairs selectors)              │
        ▼                                                         │
[5] Poll GET /refactor_template/progress                         │
        │  (Wait for status: pending_answer)                      │
        ▼                                                         │
[6] POST /dca/collectors/{id}/resume_automation_job              │
        │  { "message": true, "auto_save": true }                │
        │  (Auto-approve + permanently save healed template)      │
        ▼                                                         │
[7] Re-trigger Scraper with Healed Selectors                     │
        │                                                         │
        └──────────────────────────────────────────────────────── ┤
                                                                  ▼
                                                    [8] Upsert → Firestore
```

> **No browser. No manual clicks. No Scraper Studio UI.** The entire cycle runs via REST API calls in Python.

---

## 🗂️ Project Structure

```
python backend/
├── scrape_werse/
│   ├── __init__.py
│   ├── pipeline_orchestrator.py      # Top-level CLI entrypoint + pipeline logic
│   ├── scraper/
│   │   ├── client/
│   │   │   └── brightdata_client.py  # Bright Data async client + self-healing loop
│   │   └── sync/
│   │       └── firebase_sync.py      # Firestore REST upsert client (zero-SDK)
│   └── shared/
│       └── models/
│           └── models.py             # Pydantic v2 domain schema (Opportunity)
│
├── run_demo.py                       # Standalone self-healing demo entrypoint
├── heal_all_scrapers.py              # One-shot script to re-train all scrapers via AI
├── pyproject.toml                    # Package manifest (uv / hatch)
├── .env.example                      # Template for required credentials
└── docs/                             # Architecture & development documentation
    ├── ARCHITECTURE.md
    ├── CODEBASE_GUIDE.md
    └── ...
```
## Collector IDs

BRIGHTDATA_DEVPOST_COLLECTOR_ID="c_mt4jpiou19flhu6gce"
BRIGHTDATA_UNSTOP_HACKATHON_COLLECTOR_ID="c_mt4hrdrz2btpn3rhfl"
BRIGHTDATA_UNSTOP_COMPETITION_COLLECTOR_ID="c_mt4it8pc14m5t3pppg"
BRIGHTDATA_DUMMYWEBSITE_COLLECTOR_ID="c_mt5ncuzs26vmtydqmp"

---
# 📱 Looking for the Mobile Client?
The Flutter frontend source code for this project is hosted in a dedicated repository:
👉 [Click here to view the Flutter Mobile Client Repo](https://github.com/Shouryan-Bharote/global-ai-opportunity-tracker-app/tree/ScrapeWerse)

## ⚡ Quick Start

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) package manager
- A [Bright Data](https://brightdata.com) account with Scraper Studio collectors configured
- A [Firebase](https://firebase.google.com) project with Firestore enabled

### 1. Clone & Set Up the Environment

```powershell
# Create virtual environment
uv venv

# Activate it (PowerShell)
.venv\Scripts\Activate.ps1

# Install all dependencies
uv pip install -e .
```

### 2. Configure Credentials

```powershell
Copy-Item .env.example .env
# Then edit .env with your actual API keys
```

Required `.env` variables:

```env
# Bright Data
BRIGHTDATA_API_KEY=your_brightdata_api_key_here
BRIGHTDATA_DEVPOST_COLLECTOR_ID=c_...
BRIGHTDATA_UNSTOP_HACKATHON_COLLECTOR_ID=c_...
BRIGHTDATA_UNSTOP_COMPETITION_COLLECTOR_ID=c_...
BRIGHTDATA_DUMMYWEBSITE_COLLECTOR_ID=c_...

# Firebase
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_API_KEY=your_firebase_web_api_key
```

---

## 🚀 Running the Pipeline

### Production Run (Devpost + Unstop → `opportunities` collection)

```powershell
python -m scrape_werse.pipeline_orchestrator
```

### Single Source

```powershell
python -m scrape_werse.pipeline_orchestrator --source devpost
python -m scrape_werse.pipeline_orchestrator --source unstop_hackathon
python -m scrape_werse.pipeline_orchestrator --source unstop_competition
```

### Self-Healing Demo (Dummy Website → `demo_opportunities` collection)

```powershell
python run_demo.py
# or equivalently:
python -m scrape_werse.pipeline_orchestrator --demo
```

### Run All Sources (including demo)

```powershell
python -m scrape_werse.pipeline_orchestrator --all
```

### Re-Heal All Scrapers (re-train templates via AI)

```powershell
python heal_all_scrapers.py                              # all scrapers
python heal_all_scrapers.py --target devpost             # specific scraper
python heal_all_scrapers.py --target unstop_hackathon
python heal_all_scrapers.py --target unstop_competition
```

---

## 🎬 Demo Video — "The Money Shot"

To demonstrate the autonomous self-healing for judges:

**Step 1 — Break the dummy website layout:**
```
GET https://scrape-event-website.onrender.com/toggle
```
This swaps the HTML class names, breaking the existing selectors.

**Step 2 — Run the demo pipeline:**
```powershell
python run_demo.py
```

**Step 3 — Watch the terminal. You'll see:**
```
[WARNING] Pipeline — Schema drift detected: Scraper returned 0 rows — selectors broken.
                     Initiating autonomous self-healing loop...
[INFO]    BrightDataClient — Self-heal job triggered for collector 'c_mt5...'
[INFO]    BrightDataClient — [Heal poll 1..N] status: running
[INFO]    BrightDataClient — [Heal poll N]    status: pending_answer
[INFO]    httpx — POST .../resume_automation_job "HTTP/1.1 200 OK"
[INFO]    BrightDataClient — Autonomous heal approved and saved. Template updated.
[INFO]    Pipeline — 🔧 Re-running scraper with healed selectors...
[INFO]    Pipeline — ✅ 20/20 records synced to Firestore 'demo_opportunities'.
```

**Step 4 — Show the Firebase Console:** All 20 events appear in `demo_opportunities` — zero manual clicks.

---

## 📐 Domain Model

The `Opportunity` Pydantic v2 model is the single source of truth for all records:

```python
class Opportunity(BaseModel):
    title: str                          # Event name (3–150 chars)
    url: HttpUrl                        # Canonical link to the event page
    source: str                         # "devpost" | "unstop" | "dummywebsite"
    organizer: str                      # Host institution / company
    opportunity_type: OpportunityType   # Hackathon | Competition | Conference | Fellowship | Grant | Other
    description: Optional[str]          # Short event summary
    prizes_total: Optional[float]       # Aggregate prize pool (USD), default 0.0
    deadline: Optional[datetime]        # Parsed from strings like "27 days left" or "Oct 01, 2026"
    location_type: LocationType         # Online | Hybrid | In-Person
    difficulty: Optional[DifficultyLevel]
    required_skills: List[str]          # e.g. ["Python", "ML", "NLP"]
    is_active: bool                     # True for "active" / "upcoming"; False for "closed"
    created_at: datetime                # Ingestion timestamp (UTC)
```

Smart coercions handle messy scraper output:
- `prizes_total`: accepts `"$740,000"`, `740000`, `{"value": 740000, "currency": "USD"}`
- `deadline`: parses `"27 days left"`, `"Aug 04 - 31, 2026"`, ISO strings
- `opportunity_type`: maps `"hackathon"` → `OpportunityType.HACKATHON` etc.
- `is_active`: maps `"active"` / `"upcoming"` → `True`; `"closed"` → `False`

---

## 🛢️ Firestore Collections

| Collection | Contents | Populated By |
|---|---|---|
| `opportunities` | Live hackathons from Devpost + Unstop | Production pipeline |
| `demo_opportunities` | Events from dummy website | `run_demo.py` |

All documents use a **deterministic SHA-256 hash of the event URL** as their document ID — making every pipeline run fully idempotent (safe to re-run without duplicates).

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Package Manager | `uv` |
| Data Validation | Pydantic v2 |
| HTTP Client | `httpx` (fully async) |
| Scraping Engine | Bright Data Scraper Studio (REST API) |
| Self-Healing | Bright Data Cloud AI (`/refactor_template` + `/resume_automation_job`) |
| Database | Google Cloud Firestore (plain REST — no SDK) |
| Deduplication | SHA-256 hash of canonical URL |

---

## 📄 License

MIT
