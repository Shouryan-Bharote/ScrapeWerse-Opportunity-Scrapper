# Project Overview

## ScrapeWerse — Global AI Opportunity Tracker

### Background & Mission
AI moves fast, but opportunity discovery doesn't. Students, researchers, and engineers looking to participate in AI hackathons, competitions, conferences, fellowships, and grants frequently hunt across fragmented platforms.

ScrapeWerse provides an automated, self-healing ingestion pipeline that extracts AI opportunities continuously, guarantees clean structured data via strict Pydantic v2 schemas, and publishes updates to Google Cloud Firestore in real time.

### Key Highlights
- **Serverless Extraction Engine:** Leverages Bright Data Scraper Studio.
- **Autonomous AI Self-Healing:** Recovers automatically when websites redesign layouts.
- **Lightweight Architecture:** Zero heavy Firebase SDKs; direct async REST endpoints with deterministic SHA-256 deduplication.
- **Knowledge Graph Ready:** Fully integrated with `graphify` for continuous codebase exploration and dependency tracking.
