# System Architecture

## Architectural Overview & System Topography

The ScrapeWerse backend is engineered around a strict, asynchronous, layered design. Dependencies flow **downward only**, and cross-layer imports are explicitly prohibited to prevent circular reference bugs and isolate database concerns from raw network clients.

```
┌────────────────────────────────────────────────────────┐
│                   CLI / Orchestration                  │
│             (pipeline_orchestrator.py)                 │
└───────────────────────────┬────────────────────────────┘
                            │ (Controls flow)
                            ▼
┌────────────────────────────────────────────────────────┐
│                     Service Layer                      │
│     (brightdata_client.py, firebase_sync.py)           │
└───────────────────────────┬────────────────────────────┘
                            │ (Uses contracts)
                            ▼
┌────────────────────────────────────────────────────────┐
│                     Domain Layer                       │
│            (Pydantic v2 schemas: models.py)            │
└────────────────────────────────────────────────────────┘
```

---

## Strict Architectural Boundaries

1. **Upper-level modules** (e.g., `pipeline_orchestrator.py`) import and control service clients.
2. **Services** (`BrightDataClient`, `FirestoreRESTClient`) communicate strictly through **Domain Models** (`Opportunity`). They never import lower-level client configurations directly or bypass Pydantic validators.
3. **Data flows** are 100% async. Thread-blocking sync operations (e.g., `time.sleep()`) are forbidden in favor of `asyncio.sleep()`.

---

## Data Ingestion & Autonomous Self-Healing Flow

```
       ┌────────────────────────┐
       │ Trigger Scraper API    │
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │ Read Extracted Dataset │
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │ Parse via Pydantic     │
       └───────────┬────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
   [Validation OK]     [Schema Drift / Missing Fields]
         │                   │
         │                   ▼
         │             ┌────────────────────────┐
         │             │ Trigger Self-Heal API  │
         │             └───────────┬────────────┘
         │                         ▼
         │             ┌────────────────────────┐
         │             │ Auto-Approve Fix Diff  │
         │             └───────────┬────────────┘
         │                         ▼
         │             ┌────────────────────────┐
         │             │ Re-Scrape Clean Data   │
         │             └───────────┬────────────┘
         │                         │
         ▼◄────────────────────────┘
┌────────────────────────┐
│ Push Stream to Firebase│
└────────────────────────┘
```
