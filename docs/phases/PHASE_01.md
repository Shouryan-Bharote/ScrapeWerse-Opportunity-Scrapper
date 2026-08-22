# PHASE_01 — Domain Models & Data Contracts

**Status:** ⬜ Planned
**Target:** Verify and harden the Pydantic v2 `Opportunity` model against real Bright Data output.

---

## Goal

The domain model is the foundation of the entire pipeline. This phase validates that it correctly handles real-world scraper output — including edge cases, missing fields, and type coercions.

## Tasks

- [ ] Copy `.env.example` → `.env` and fill in credentials
- [ ] Run a test scrape on one target URL via `trigger_scraper`
- [ ] Inspect the raw JSON rows returned by `get_dataset`
- [ ] Map real field names from scraper output to Opportunity schema fields
- [ ] Adjust validators and field aliases as needed
- [ ] Test with malformed/missing fields to confirm graceful handling
- [ ] Document all field mappings

## Expected Outputs

- Confirmed field mapping table (scraper field → Opportunity field)
- Any additional validators added to `models.py`
- Updated `docs/COMPONENT_LIBRARY.md` with Opportunity schema table

## Notes

- Pay attention to date formats — Bright Data may return deadlines as strings rather than ISO datetimes. Add a `field_validator` for `deadline` if needed.
- The `required_skills` field expects a `List[str]` — verify the scraper returns a list and not a comma-separated string.
