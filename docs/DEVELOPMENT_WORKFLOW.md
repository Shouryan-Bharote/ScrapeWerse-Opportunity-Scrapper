# Development Workflow

## Workflow Conventions

1. **Virtual Environment & Package Management:**
   - Always use `uv` for python virtualenv and package operations.
   - Command to create venv: `uv venv`
   - Command to install dependencies: `uv pip install -e .`

2. **State & Progress Tracking:**
   - All session tasks are tracked in `.state/TASK_QUEUE.md`.
   - Architectural decisions are logged in `.state/DECISIONS.md`.
   - Development milestones and status updates are recorded in `.state/DEVELOPMENT_STATUS.md`.

3. **Layered Code Rules:**
   - All models go into `scrape_werse/shared/models/`.
   - Scraper clients and sync adapters go into `scrape_werse/scraper/`.
   - Business orchestration logic sits in `pipeline_orchestrator.py`.
   - No circular or upward imports.

4. **Testing:**
   - Test files are placed in `tests/`.
   - Run tests via `pytest`.
