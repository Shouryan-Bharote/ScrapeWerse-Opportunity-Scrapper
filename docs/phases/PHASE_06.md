# PHASE_06 — API & REST Exposure

**Status:** ⬜ Planned

---

## Goal

Expose ingested opportunities through a high-performance REST API (FastAPI) enabling search, category filtering, skill tagging, and pagination for mobile and web clients.

## Tasks

- [ ] Initialize FastAPI application and router structure
- [ ] Implement `GET /api/v1/opportunities` with query filters:
  - `opportunity_type` (Hackathon, Competition, Conference, etc.)
  - `location_type` (Online, Hybrid, In-Person)
  - `skills` (filter by required skills)
  - `search` (full text search over title/description)
  - `is_active` status filter
- [ ] Implement `GET /api/v1/opportunities/{id}` for single opportunity lookup
- [ ] Integrate pagination (cursor/offset) and rate limiting
- [ ] Write integration tests for API endpoints
