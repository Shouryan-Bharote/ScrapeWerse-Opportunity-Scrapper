# PHASE_00 — Project Setup

**Status:** ✅ Complete
**Date:** 2026-08-22

---

## Goal

Set up the complete project skeleton using `uv` for package management and create the full layered architecture from the blueprint.

## Completed Work

### Environment
- Initialized `uv` virtual environment at `.venv/`
- Created `pyproject.toml` with `pydantic>=2.0`, `httpx>=0.27.0`, `python-dotenv>=1.0.0`
- Installed dependencies via `uv pip install -e .`

### Source Code (Layered Architecture)
```
scrape_werse/
├── shared/models/models.py         # Pydantic v2 — Opportunity, enums
├── scraper/client/brightdata_client.py  # Async BrightData client + self-healing
├── scraper/sync/firebase_sync.py   # Firestore REST upsert client
└── pipeline_orchestrator.py        # Top-level CLI orchestrator
```

### Project Infrastructure
- `.agents/` — agent rules and workflow files
- `.state/` — live development state tracking
- `docs/` — architecture docs and phase plans
- `.env.example` — credential template
- `.gitignore` — excludes .venv, .env, graphify-out
- `README.md` — project overview and quickstart

## Key Decisions Made

See `.state/DECISIONS.md` for full rationale:
- `DEC-001`: Use uv
- `DEC-002`: Firestore via REST (no SDK)
- `DEC-003`: SHA-256 document IDs
- `DEC-004`: `extra="ignore"` in Opportunity model
- `DEC-005`: bool-before-int in Firestore conversion
- `DEC-006`: Downward-only import architecture

## Next Phase

→ **PHASE_01**: Domain Models & Data Contracts
