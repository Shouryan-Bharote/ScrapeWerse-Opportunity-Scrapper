# Task Queue

Tasks are listed in priority order. Update status as work progresses.

- `[ ]` Not started
- `[/]` In progress
- `[x]` Complete

---

## PHASE_00 — Project Setup

- [x] Create pyproject.toml with uv-compatible config
- [x] Initialize .venv with `uv venv`
- [x] Install dependencies with `uv pip install -e .`
- [x] Create scrape_werse/ package structure
- [x] Create models.py (Pydantic v2 domain layer)
- [x] Create brightdata_client.py (service layer)
- [x] Create firebase_sync.py (service layer)
- [x] Create pipeline_orchestrator.py (orchestration layer)
- [x] Create .agents/ workflow files
- [x] Create .state/ state files
- [x] Create docs/ structure
- [x] Create .env.example
- [x] Create .gitignore
- [x] Create README.md

---

## PHASE_01 — Domain Models & Data Contracts

- [ ] Copy .env.example → .env and fill in credentials
- [ ] Test import: `from scrape_werse.shared.models.models import Opportunity`
- [ ] Validate model with a sample Bright Data row (dry run)
- [ ] Adjust field types/validators based on real scraper output shapes
- [ ] Add `model_dump_for_firestore()` helper to Opportunity if needed
- [ ] Update docs/phases/PHASE_01.md with findings

---

## PHASE_02 — BrightData Client Integration

- [ ] Obtain Bright Data API key and Collector ID
- [ ] Test `trigger_scraper()` with a real collector
- [ ] Test `get_dataset()` with a real response_id
- [ ] Verify JSON output matches expected Opportunity fields
- [ ] Test self-heal trigger (`initiate_self_heal`)
- [ ] Test `auto_approve_heal` polling logic

---

## PHASE_03 — Firestore Sync Integration

- [ ] Create Firestore database in Firebase console
- [ ] Configure Firestore security rules (server-to-server write)
- [ ] Test `upsert_opportunity()` with a sample record
- [ ] Verify document shows up in Firebase console
- [ ] Test idempotency: upsert same URL twice, confirm single doc

---

## PHASE_04 — Orchestrator & Self-Healing Loop

- [ ] Run full pipeline end-to-end with real credentials
- [ ] Simulate schema drift (break a field) and confirm self-heal fires
- [ ] Confirm healed scraper re-runs and records sync to Firestore
- [ ] Add retry logic for transient network failures

---

## PHASE_05 — Testing & Validation

- [ ] Write pytest tests for Opportunity model validators
- [ ] Write pytest tests for Firestore type conversion
- [ ] Mock httpx for BrightDataClient unit tests
- [ ] Run graphify on final codebase
- [ ] Final end-to-end smoke test
