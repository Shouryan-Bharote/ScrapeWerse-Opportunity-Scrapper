# Graphify Workflow

## Purpose
Step-by-step instructions for running and querying the graphify knowledge graph in the ScrapeWerse project.

---

## Initial Build

Run this once after the project has meaningful code:

```powershell
# From the project root (with .venv activated)
/graphify "d:\Programming\ScrapeWerse hackathon"
```

This generates `graphify-out/graph.html`, `graphify-out/graph.json`, and `graphify-out/GRAPH_REPORT.md`.

---

## Incremental Update

After adding new files or making significant changes:

```powershell
/graphify "d:\Programming\ScrapeWerse hackathon" --update
```

---

## Key Queries for This Project

### Architecture verification
```
/graphify query "Trace the import dependency chain from pipeline_orchestrator to models"
```

### Self-healing flow
```
/graphify query "How does the self-healing loop work between BrightDataClient and the orchestrator?"
```

### Data flow
```
/graphify query "How does an Opportunity record flow from raw scraper data to Firestore?"
```

### Firestore conversion
```
/graphify explain "FirestoreRESTClient"
```

---

## After Each Phase

When a phase is complete, update the graph and run:
```
/graphify query "What components were added in the latest phase?"
```
Then paste the answer into the phase doc `docs/phases/PHASE_NN.md`.
