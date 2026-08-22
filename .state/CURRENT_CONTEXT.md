# Current Context

**Last Updated:** 2026-08-22
**Active Session:** Project Setup

---

## What We're Working On

Initial project scaffolding for the **ScrapeWerse — Global AI Opportunity Tracker** backend pipeline.

## What Was Just Done

- Initialized `uv` project with `pyproject.toml`
- Created Python virtual environment at `.venv/`
- Created all source modules:
  - `scrape_werse/shared/models/models.py` — Pydantic v2 domain contracts
  - `scrape_werse/scraper/client/brightdata_client.py` — Bright Data async client
  - `scrape_werse/scraper/sync/firebase_sync.py` — Firestore REST client
  - `scrape_werse/pipeline_orchestrator.py` — top-level orchestrator
- Created `.agents/`, `.state/`, `docs/` structure
- Created config files (`.env.example`, `.gitignore`, `README.md`)

## Immediate Next Steps

1. Fill in `.env` with real API credentials (copy from `.env.example`)
2. Run pipeline verification: `python -m scrape_werse.pipeline_orchestrator`
3. Begin Phase 01: iterate on domain models based on real Bright Data output shapes
4. Run graphify on the codebase: `/graphify .`

## Active Blockers

- None — environment setup complete

## Open Questions

- What are the exact field names returned by the Bright Data collector for each target site?
- Do Firestore security rules require an API key or service account?
