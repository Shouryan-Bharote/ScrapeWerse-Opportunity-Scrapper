# PHASE_07 — Deduplication & Change Detection Pipeline

**Status:** ⬜ Planned

---

## Goal

Implement content-level deduplication and historical change detection so downstream clients and subscribers receive notifications on updated deadlines, new prizes, and fresh listings.

## Tasks

- [ ] Implement content hashing for title + organizer + description
- [ ] Track change history when opportunities are re-scraped
- [ ] Distinguish between new records, minor updates, and expired opportunities
- [ ] Add audit logging for data lifecycle events
