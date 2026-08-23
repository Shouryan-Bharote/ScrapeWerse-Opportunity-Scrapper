# Graph Report - .  (2026-08-23)

## Corpus Check
- Corpus is ~10,266 words - fits in a single context window. You may not need a graph.

## Summary
- 77 nodes · 109 edges · 13 communities (12 shown, 1 thin omitted)
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
1. `BrightDataClient` - 15 edges
2. `Opportunity` - 14 edges
3. `FirestoreRESTClient` - 11 edges
4. `normalize_row()` - 7 edges
5. `run_pipeline()` - 7 edges
6. `main()` - 5 edges
7. `dry_run()` - 4 edges
8. `inspect()` - 4 edges
9. `OpportunityType` - 4 edges
10. `DifficultyLevel` - 4 edges

## Surprising Connections (you probably didn't know these)
- `dry_run()` --calls--> `Opportunity`  [EXTRACTED]
  dry_run.py → scrape_werse/shared/models/models.py
- `inspect()` --calls--> `Opportunity`  [EXTRACTED]
  inspect_datasets.py → scrape_werse/shared/models/models.py
- `dry_run()` --calls--> `normalize_row()`  [EXTRACTED]
  dry_run.py → scrape_werse/pipeline_orchestrator.py
- `dry_run()` --calls--> `BrightDataClient`  [EXTRACTED]
  dry_run.py → scrape_werse/scraper/client/brightdata_client.py
- `inspect()` --calls--> `normalize_row()`  [EXTRACTED]
  inspect_datasets.py → scrape_werse/pipeline_orchestrator.py

## Import Cycles
- None detected.

## Communities (13 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.16
Nodes (12): dry_run(), Dry-run validation script. Scrapes all 4 sources, validates data through the Pyd, inspect(), normalize_row(), Normalize a raw scraper output row into a flat dict that matches the     Opportu, BrightDataClient, create_client_from_env(), Bright Data Scraper Studio Client — Service Layer ============================== (+4 more)

### Community 1 - "Community 1"
Cohesion: 0.17
Nodes (10): create_client_from_env(), FirestoreRESTClient, Any, Firebase Firestore REST Client — Service Layer =================================, Write or overwrite an opportunity in Firestore using a REST PATCH.          The, Upsert a list of opportunity records sequentially.          Note: Firestore REST, Convenience factory that reads Firebase config from the environment.      Raises, Async client to interact with Google Firestore REST API.      Upserts Opportunit (+2 more)

### Community 2 - "Community 2"
Cohesion: 0.14
Nodes (9): BaseModel, datetime, Opportunity, Coerces prize value from various scraper formats:         - dict: {"value": 7400, Parses deadlines from various scraper formats:         - ISO datetime string: '2, Accept plain strings alongside HttpUrl objects., Maps raw scraper strings (e.g. 'hackathon', 'competition') to the         Opport, Converts scraper status strings ('active', 'upcoming', 'closed') to bool. (+1 more)

### Community 3 - "Community 3"
Cohesion: 0.31
Nodes (9): Enum, DifficultyLevel, LocationType, OpportunityType, Domain Models — Layer 0 (Foundation) ===================================== Pydan, Classification of the AI opportunity., Skill level required for the opportunity., Modality of the opportunity. (+1 more)

### Community 4 - "Community 4"
Cohesion: 0.33
Nodes (6): main(), Pipeline Orchestrator — CLI / Orchestration Layer (Top-Level) ==================, Execute one full ingestion pipeline run.      Args:         urls: Target URLs to, # TODO: Hook in alerting (email/Slack/PagerDuty) here, Main entrypoint: reads config from environment and runs one pipeline     per con, run_pipeline()

### Community 5 - "Community 5"
Cohesion: 0.40
Nodes (3): Any, Trigger an extraction run via POST /dca/trigger.          Args:             coll, Fetch the extracted JSON results for a completed run, polling until ready.

## Knowledge Gaps
- **1 isolated node(s):** `scrape-werse`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BrightDataClient` connect `Community 0` to `Community 4`, `Community 5`?**
  _High betweenness centrality (0.275) - this node is a cross-community bridge._
- **Why does `Opportunity` connect `Community 2` to `Community 0`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.270) - this node is a cross-community bridge._
- **Why does `FirestoreRESTClient` connect `Community 1` to `Community 4`?**
  _High betweenness centrality (0.258) - this node is a cross-community bridge._
- **What connects `Dry-run validation script. Scrapes all 4 sources, validates data through the Pyd`, `scrape-werse`, `Pipeline Orchestrator — CLI / Orchestration Layer (Top-Level) ==================` to the rest of the system?**
  _31 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._