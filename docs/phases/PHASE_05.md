# PHASE_05 — Testing & Validation

**Status:** ⬜ Planned

---

## Goal

Write a test suite that exercises the domain models, Firestore conversion, and pipeline logic with mocked external services.

## Tasks

- [ ] `tests/test_models.py` — Pydantic v2 Opportunity validators
- [ ] `tests/test_firebase_sync.py` — Firestore type conversion + doc ID generation
- [ ] `tests/test_brightdata_client.py` — mock httpx for trigger/fetch/heal
- [ ] `tests/test_pipeline_orchestrator.py` — end-to-end with mocked clients
- [ ] Run `pytest` and confirm all tests pass
- [ ] Run graphify on final codebase

## Test Commands

```powershell
# Activate venv
.venv\Scripts\Activate.ps1

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=scrape_werse --cov-report=term-missing
```

## Test File Locations

```
tests/
├── __init__.py
├── test_models.py
├── test_firebase_sync.py
├── test_brightdata_client.py
└── test_pipeline_orchestrator.py
```
