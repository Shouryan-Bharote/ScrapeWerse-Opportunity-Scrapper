# Architectural & Design Decisions

A log of all non-trivial decisions made during development, with rationale.

---

## DEC-001 — Use uv for Package Management

**Date:** 2026-08-22
**Decision:** Use `uv` (not pip, Poetry, or conda) for virtual environment and dependency management.
**Rationale:** User explicitly requested uv. It is significantly faster than pip, produces a lock file, and is compatible with `pyproject.toml` PEP 518 standard. No Poetry overhead needed for a hackathon project.

---

## DEC-002 — Firestore via REST (No SDK)

**Date:** 2026-08-22
**Decision:** Use raw `httpx` HTTP calls to the Firestore REST API instead of the official `firebase-admin` SDK.
**Rationale:** The blueprint explicitly specifies this. The SDK requires heavy gRPC + protobuf dependencies. For a write-only sync use case, REST PATCH calls are sufficient and keep the dependency footprint minimal.

---

## DEC-003 — SHA-256 Document IDs for Deduplication

**Date:** 2026-08-22
**Decision:** Use SHA-256(url)[:20] as the Firestore document ID for every opportunity.
**Rationale:** Deterministic IDs mean the same opportunity URL always maps to the same Firestore doc. A PATCH to an existing doc is a clean upsert — no separate deduplication logic needed. 20 hex chars = 80 bits of entropy, more than sufficient for this dataset size.

---

## DEC-004 — `extra="ignore"` in Opportunity Model

**Date:** 2026-08-22
**Decision:** Set `model_config = {"extra": "ignore"}` in the Opportunity Pydantic model.
**Rationale:** Bright Data scrapers may return additional metadata fields not in our schema. Raising on extra fields would break ingestion unnecessarily. We only care that required fields are present and valid.

---

## DEC-005 — bool-before-int in Firestore Type Conversion

**Date:** 2026-08-22
**Decision:** In `_convert_to_firestore_fields`, check `isinstance(v, bool)` BEFORE `isinstance(v, (int, float))`.
**Rationale:** In Python, `bool` is a subclass of `int`. Without this ordering, `True`/`False` would be serialized as `doubleValue: 1.0/0.0` instead of `booleanValue: true/false`, corrupting the `is_active` field in Firestore.

---

## DEC-006 — Layered Architecture with Downward-Only Imports

**Date:** 2026-08-22
**Decision:** Enforce strict 3-layer architecture: Domain → Services → Orchestrator. No reverse imports.
**Rationale:** Matches the blueprint specification. Prevents circular dependencies, isolates database concerns, and makes each layer independently testable.
