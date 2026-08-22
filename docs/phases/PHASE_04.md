# PHASE_04 — Orchestrator & Self-Healing Loop

**Status:** ⬜ Planned

---

## Goal

Run the full end-to-end pipeline and verify the autonomous self-healing loop works when schema drift is detected.

## Tasks

- [ ] Run full pipeline: `python -m scrape_werse.pipeline_orchestrator`
- [ ] Confirm trigger → fetch → validate → sync all succeed
- [ ] Simulate schema drift (break a field name in the scraper, or pass malformed row)
- [ ] Confirm `broken_flag = True` is detected and self-heal fires
- [ ] Confirm `auto_approve_heal` polls and approves the fix
- [ ] Confirm re-scrape runs and produces clean records
- [ ] Confirm all records sync to Firestore after healing

## Self-Healing Flow

```
Trigger Scraper
     ↓
Fetch Dataset
     ↓
Pydantic Validation
     ↓ (fails)
initiate_self_heal() → Cloud AI generates new selectors
     ↓
auto_approve_heal() → Poll until pending_answer → auto-approve
     ↓
Re-trigger Scraper (with healed template)
     ↓
Sync to Firestore
```
