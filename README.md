# ScrapeWerse — Global AI Opportunity Tracker

> **Hackathon Project** | Python Backend Ingestion Pipeline powered by [Bright Data Scraper Studio](https://brightdata.com)

A fully autonomous, self-healing backend pipeline that discovers AI opportunities (hackathons, competitions, conferences, fellowships, grants) from across the web and streams them to Google Cloud Firestore in real time.

---

## Architecture

```
CLI / Orchestration (pipeline_orchestrator.py)
       │
       ▼
Service Layer (brightdata_client.py · firebase_sync.py)
       │
       ▼
Domain Layer (shared/models/models.py — Pydantic v2)
```

The pipeline is strictly layered: dependencies flow **downward only**. All I/O is **fully async** (`httpx` + `asyncio`).

---

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) installed globally

### 1. Clone & set up the environment

```powershell
# Create virtual environment
uv venv

# Activate it
.venv\Scripts\Activate.ps1   # PowerShell
# or
.venv\Scripts\activate.bat   # CMD

# Install dependencies
uv pip install -e .
```

### 2. Configure credentials

```powershell
Copy-Item .env.example .env
# Edit .env with your BRIGHTDATA_API_KEY, BRIGHTDATA_COLLECTOR_ID, FIREBASE_PROJECT_ID
```

### 3. Run the pipeline

```powershell
python -m scrape_werse.pipeline_orchestrator
```

---

## Project Structure

```
scrape_werse/
├── shared/
│   └── models/
│       └── models.py              # Pydantic v2 domain contracts
├── scraper/
│   ├── client/
│   │   └── brightdata_client.py   # Bright Data async client + self-healing
│   └── sync/
│       └── firebase_sync.py       # Firestore REST upsert client
└── pipeline_orchestrator.py       # Orchestration entrypoint

docs/                              # Architecture docs + phase plans
.agents/                           # Agent workflow rules
.state/                            # Live development state
```

---

## Self-Healing Pipeline

When Pydantic validation fails (site layout changed → selectors broken):

1. **Detect** — schema drift caught by `Opportunity(**row)` validation failure
2. **Heal** — `BrightDataClient.initiate_self_heal()` sends AI prompt to Scraper Studio
3. **Approve** — `auto_approve_heal()` polls status and programmatically accepts the AI-generated diff
4. **Re-scrape** — clean data extracted with the updated selectors
5. **Sync** — all valid records pushed to Firestore

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Package Manager | uv |
| Data Validation | Pydantic v2 |
| HTTP Client | httpx (async) |
| Scraping Engine | Bright Data Scraper Studio |
| Database | Google Cloud Firestore (REST) |
| Knowledge Graph | graphify |
