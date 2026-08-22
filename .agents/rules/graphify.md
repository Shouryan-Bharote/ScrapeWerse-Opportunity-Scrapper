# Graphify Integration Rules

## Purpose
Defines how graphify is used in the ScrapeWerse project to maintain a living knowledge graph of the codebase architecture and data flows.

---

## When to Run Graphify

Run `/graphify .` (or update the existing graph) at these milestones:
- After completing a new phase
- After adding a new module or significantly refactoring existing code
- Before a major architectural decision — the graph helps identify dependencies

---

## Graphify Output Location

All graphify outputs are written to `graphify-out/` at the project root.
This directory is in `.gitignore` — do NOT commit it.

---

## Knowledge Graph Scope

The graphify graph covers:
- All Python source files under `scrape_werse/`
- All markdown docs under `docs/` and `.state/`
- `pyproject.toml` and config files

---

## Query Conventions

When asking questions about the codebase using graphify:
- Use `/graphify query "..."` for broad questions about architecture
- Use `/graphify path "ModuleA" "ModuleB"` to trace dependency paths
- Use `/graphify explain "ClassName"` for deep-dives on a specific component

---

## Graphify and Architecture Validation

After any significant refactor, run:
```
/graphify query "What are the import dependencies between the service layer and domain layer?"
```
To verify the layered architecture rule (domain ← services ← orchestrator) is preserved.
