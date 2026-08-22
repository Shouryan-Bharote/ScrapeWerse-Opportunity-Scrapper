# Hackathon Project Proposal

## Global AI Opportunity Tracker

> **Note for evaluation:** This is one of my currently in-progress projects (actively under development). It is built entirely from scratch with custom infrastructure — it does **not** use Scrapper Studio or any similar no-code/low-code scraping platform.

---

## 1. The Problem

AI moves fast, but opportunity discovery doesn't. Students and professionals who want to participate in AI hackathons, competitions, conferences, fellowships, and research programs have to manually hunt across dozens of fragmented platforms — Unstop, Devpost, Kaggle, Hack2Skill, and more. Each site has a different layout, update cadence, and discovery experience.

The result:

- Great opportunities are **missed** simply because nobody knew they existed.
- Hours are wasted **manually checking** the same sites repeatedly.
- Existing aggregators are either too narrow, too generic, or don't focus on AI-specific growth opportunities.

## 2. The Solution

A **production-quality, modular backend pipeline** that automates the entire lifecycle of discovering AI-related professional opportunities:

```
Scrape → LLM-Generate Selectors → Extract → Normalize → Structure → Store → Serve via API
```

1. **Scrapes** targeted websites (Unstop, Hack2Skill, Devpost, Kaggle) using stealth browser automation.
2. **Uses LLMs to generate CSS/XPath selectors** for each page dynamically — no brittle hand-written selectors per site.
3. **Extracts and normalizes** raw HTML data into unified internal formats.
4. **Structures** everything into validated `Opportunity` models (title, deadlines, categories: hackathons, competitions, conferences, workshops, research programs, scholarships, etc.).
5. **Stores** processed opportunities and **exposes them through a high-performance FastAPI REST API** with search, filtering, and pagination.

The end goal: one clean API that answers *"what AI opportunities can I apply to right now?"*

## 3. What Makes It Interesting (The AI Angle)

This isn't "just a scraper" — the core innovation is an **LLM-driven parsing pipeline** that makes web extraction resilient and self-adapting:

- **LLM-Generated Selector Profiles**: Page HTML is sent to an LLM (via LiteLLM — supporting Gemini, Groq, OpenRouter), which returns a structured `SelectorProfile` containing CSS/XPath selectors per field, complete with priority, confidence scores, wait conditions, and timeout metadata.
- **Constrained Outputs**: An `OpportunityField` enum constrains the LLM to only emit valid fields — no hallucinated schema.
- **Priority-Based Extraction Engine**: A `SelectorEngine` executes selectors in priority order with automatic fallback across 6 extraction types (text, attribute, html, list, table, json).
- **Validation Before Execution**: A dedicated validator ensures selector profile integrity before any extraction runs.
- **Structured Output Parsing**: Raw extracted dictionaries are normalized and coerced into fully validated Pydantic v2 `Opportunity` models.

If a website changes its layout, the system can regenerate selectors via the LLM instead of requiring manual re-engineering — a genuine application of AI to solve a classic automation pain point.

## 4. Architecture Highlights

Strict **layered architecture** with downward-only dependencies and single-responsibility modules:

| Layer | Responsibility | Status |
|-------|---------------|--------|
| Foundation | Config, logging, constants, domain models | ✅ Complete |
| Browser Engine | Patchright stealth Chromium (`BrowserFactory` + `BrowserManager`) | ✅ Complete |
| Scraper Framework | Abstract `BaseScraper` lifecycle management | ✅ Complete |
| Website Scrapers | Concrete scrapers (Unstop, Hack2Skill, Devpost, Kaggle) + LLM parsing | 🔄 In Progress |
| LLM Pipeline (Advanced) | Caching, retries, multi-provider fallback | ⬜ Planned |
| Exporters | JSON / CSV export | ⬜ Planned |
| Database | Persistence & deduplication | ⬜ Planned |
| Scheduler | Automated periodic scraping | ⬜ Planned |
| FastAPI Backend | REST API exposure | ⬜ Planned |
| Deployment | Docker, CI/CD, monitoring | ⬜ Planned |

**Key design principles:** downward-only dependencies, no cross-layer imports, explicit Pydantic contracts at every boundary, composition over inheritance.

## 5. Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.13+ |
| Browser Automation | Patchright (stealth Chromium, async API) |
| LLM Orchestration | LiteLLM (Gemini, Groq, OpenRouter) |
| Data Validation | Pydantic v2+ |
| API Framework | FastAPI |
| Package Management | Poetry |
| Testing | pytest |

## 6. Current Progress (Honest Status)

This is a **work-in-progress project**, developed with production-grade discipline:

- ✅ Phases 0–3 complete: architecture research, foundation, browser engine core, and scraper framework.
- 🔄 Phase 4 in progress: full LLM infrastructure is implemented (LLM client, manager, selector profiles, validation, parser pipeline); concrete platform scrapers are being built now.
- ⬜ Remaining phases (API, DB, scheduling, deployment) are planned per the roadmap.

By hackathon time, the project demonstrates a **working end-to-end flow**: URL → stealth browser → LLM-generated selectors → extracted data → structured `Opportunity` model.

## 7. Why This Fits a Hackathon

- **Real problem**: Opportunity discovery for the AI community is genuinely fragmented and painful.
- **Novel use of LLMs**: Not chatbots or RAG — LLMs here act as dynamic code/schema generators powering resilient web automation.
- **Strong engineering**: Clean layered architecture, strict contracts, tested components — not a weekend glue script.
- **Extensible**: New platforms = new thin scraper classes; new categories = enum entries. The pipeline generalizes far beyond the four initial targets.
- **Built from scratch**: All infrastructure (browser engine, scraper framework, LLM pipeline, parsers) is custom-built — **no Scrapper Studio** or off-the-shelf scraping platforms involved.

## 8. Future Vision

- Multi-provider LLM fallback with response caching for cost efficiency.
- Deduplication and change detection so users only see fresh opportunities.
- Scheduled autonomous crawls keeping the dataset continuously up to date.
- A public REST API (and later a frontend) where anyone can discover AI hackathons, competitions, and programs in one place.
