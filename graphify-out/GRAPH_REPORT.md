# Graph Report - .  (2026-08-22)

## Corpus Check
- Corpus is ~10,400 words - fits in a single context window. You may not need a graph.

## Summary
- 64 nodes · 79 edges · 13 communities (12 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]

## God Nodes (most connected - your core abstractions)
1. `BrightDataClient` - 11 edges
2. `FirestoreRESTClient` - 11 edges
3. `Opportunity` - 7 edges
4. `run_pipeline()` - 6 edges
5. `main()` - 5 edges
6. `OpportunityType` - 4 edges
7. `DifficultyLevel` - 4 edges
8. `LocationType` - 4 edges
9. `create_client_from_env()` - 3 edges
10. `create_client_from_env()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `run_pipeline()` --references--> `BrightDataClient`  [EXTRACTED]
  scrape_werse/pipeline_orchestrator.py → scrape_werse/scraper/client/brightdata_client.py
- `run_pipeline()` --references--> `FirestoreRESTClient`  [EXTRACTED]
  scrape_werse/pipeline_orchestrator.py → scrape_werse/scraper/sync/firebase_sync.py
- `run_pipeline()` --calls--> `Opportunity`  [EXTRACTED]
  scrape_werse/pipeline_orchestrator.py → scrape_werse/shared/models/models.py
- `main()` --calls--> `BrightDataClient`  [EXTRACTED]
  scrape_werse/pipeline_orchestrator.py → scrape_werse/scraper/client/brightdata_client.py
- `main()` --calls--> `FirestoreRESTClient`  [EXTRACTED]
  scrape_werse/pipeline_orchestrator.py → scrape_werse/scraper/sync/firebase_sync.py

## Import Cycles
- None detected.

## Communities (13 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.14
Nodes (10): BrightDataClient, create_client_from_env(), Any, Bright Data Scraper Studio Client — Service Layer ==============================, Trigger the Cloud AI self-heal loop to repair broken selectors.          This ca, Poll the healing job and programmatically accept the AI-proposed diff., Convenience factory that reads BRIGHTDATA_API_KEY from the environment.      Rai, Async client to manage Scraper Studio runs and autonomous self-healing.      The (+2 more)

### Community 1 - "Community 1"
Cohesion: 0.24
Nodes (7): FirestoreRESTClient, Any, Write or overwrite an opportunity in Firestore using a REST PATCH.          The, Upsert a list of opportunity records sequentially.          Note: Firestore REST, Async client to interact with Google Firestore REST API.      Upserts Opportunit, Generate a deterministic, URL-safe document ID from an opportunity URL., Convert a flat Python dict into the Firestore REST typed-value format.

### Community 2 - "Community 2"
Cohesion: 0.31
Nodes (9): Enum, DifficultyLevel, LocationType, OpportunityType, Domain Models — Layer 0 (Foundation) ===================================== Pydan, Classification of the AI opportunity., Skill level required for the opportunity., Modality of the opportunity. (+1 more)

### Community 3 - "Community 3"
Cohesion: 0.25
Nodes (6): BaseModel, datetime, Opportunity, Soft-validates that the deadline is in the future.         Expired deadlines are, Accept plain strings alongside HttpUrl objects., Core domain schema representing a single AI opportunity.      This model is the

### Community 4 - "Community 4"
Cohesion: 0.33
Nodes (6): main(), Pipeline Orchestrator — CLI / Orchestration Layer (Top-Level) ==================, # TODO: Hook in alerting (email/Slack/PagerDuty) here, Main entrypoint: reads config from environment and runs the pipeline.      Requi, Execute one full ingestion pipeline run.      Args:         urls: Target URLs to, run_pipeline()

### Community 5 - "Community 5"
Cohesion: 0.50
Nodes (3): create_client_from_env(), Firebase Firestore REST Client — Service Layer =================================, Convenience factory that reads Firebase config from the environment.      Raises

## Knowledge Gaps
- **1 isolated node(s):** `scrape-werse`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BrightDataClient` connect `Community 0` to `Community 4`?**
  _High betweenness centrality (0.306) - this node is a cross-community bridge._
- **Why does `FirestoreRESTClient` connect `Community 1` to `Community 4`, `Community 5`?**
  _High betweenness centrality (0.296) - this node is a cross-community bridge._
- **Why does `Opportunity` connect `Community 3` to `Community 2`, `Community 4`?**
  _High betweenness centrality (0.160) - this node is a cross-community bridge._
- **What connects `scrape-werse`, `Pipeline Orchestrator — CLI / Orchestration Layer (Top-Level) ==================`, `Execute one full ingestion pipeline run.      Args:         urls: Target URLs to` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.14166666666666666 - nodes in this community are weakly interconnected._