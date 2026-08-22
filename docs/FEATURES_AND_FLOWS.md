# Features and Flows

## Core Features

1. **Target Multi-Source Scraping:**
   - Automated ingestion across major opportunity platforms (Devpost, Unstop, Kaggle, Hack2Skill).
   - Async network operations preventing thread starvation.

2. **Pydantic v2 Data Contract Enforcement:**
   - Strict field type validations, boundary checks, and whitespace sanitization.
   - Automatic drift detection when target websites modify structure.

3. **Autonomous Self-Healing Loop:**
   - Detects selector failure -> fires refactoring job to Bright Data Scraper Studio -> polls for diff -> programmatically approves fix -> re-scrapes fresh dataset.

4. **Zero-SDK Firestore Synchronization:**
   - Async REST PATCH operations.
   - Idempotent deduplication using SHA-256 URL hashing.
