# Agent Session Workflow

## Purpose
Defines the standard workflow for each development session on the ScrapeWerse project.

---

## Standard Session Flow

```
1. READ STATE         →  Read .state/ files to orient
2. PICK TASK          →  Choose next task from TASK_QUEUE.md
3. READ DOCS          →  Read relevant docs/phases/PHASE_NN.md
4. CODE               →  Implement the task
5. VERIFY             →  Run verification (imports, tests, manual checks)
6. UPDATE STATE       →  Update .state/ files
7. REPORT             →  Summarize what was done
```

---

## Architectural Rules (ALWAYS Enforce)

1. **Downward-only imports**: `pipeline_orchestrator` → `service layer` → `models`. NEVER reverse.
2. **No sync I/O**: All network calls use `async/await` with `httpx`. Never `requests` or `time.sleep()`.
3. **Pydantic at every boundary**: Raw dicts from the scraper MUST be validated through `Opportunity(**row)` before any further processing.
4. **Environment variables only**: Credentials NEVER hardcoded. Always `os.getenv()` + `python-dotenv`.
5. **Explicit error handling**: Every `httpx` call is wrapped in try/except or uses `.raise_for_status()`.

---

## Adding a New Feature

When adding a new module or feature:
1. Identify which layer it belongs to (domain / service / orchestration)
2. Create the module in the correct directory
3. Add `__init__.py` if creating a new package
4. Document the module's responsibility at the top of the file
5. Update `docs/CODEBASE_GUIDE.md` with the new module
6. Update `.state/DEVELOPMENT_STATUS.md`
