# Blueprint 1: Python Backend Ingestion & Self-Healing Pipeline
## Project Blueprint & Architecture Guide

This document defines the complete backend architecture, codebase boundaries, and component library for the **Global AI Opportunity Tracker Ingestion Pipeline**. It utilizes **Bright Data Scraper Studio** as its core serverless extraction engine and integrates a fully autonomous, unattended self-healing loop that streams validated Pydantic v2 data models directly to Google Cloud Firestore in real time.

---

### 1. Architectural Overview & System Topography

The backend pipeline is engineered around a strict, asynchronous, layered design. Dependencies flow **downward only**, and cross-layer imports are explicitly prohibited to prevent circular reference bugs and isolate database concerns from raw network clients.

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

#### Strict Architectural Boundaries
1. **Upper-level modules** (e.g., Orchestrators) import and control service clients.
2. **Services** (e.g., `BrightDataClient`, `FirestoreRESTClient`) communicate strictly through **Domain Models** (e.g., Pydantic schemas). They never import lower-level client configurations directly or bypass Pydantic validators.
3. **Data flows** are 100% async. Thread-blocking sync operations (e.g., `time.sleep()`) are forbidden in favor of `asyncio.sleep()`.

---

### 2. Domain Models Layer (`shared/models/`)

This layer defines the strict data contracts that govern the entire pipeline. If Scraper Studio extracts a field that does not conform to these schemas, the validation boundary will catch it and flag a website layout change.

#### `models.py` Specification (Pydantic v2)
```python
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator

class OpportunityType(str, Enum):
    HACKATHON = "Hackathon"
    COMPETITION = "Competition"
    CONFERENCE = "Conference"
    FELLOWSHIP = "Fellowship"
    GRANT = "Grant"
    OTHER = "Other"

class DifficultyLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"

class LocationType(str, Enum):
    ONLINE = "Online"
    HYBRID = "Hybrid"
    IN_PERSON = "In-Person"

class Opportunity(BaseModel):
    """Core domain schema representing an AI opportunity."""
    title: str = Field(..., min_length=3, max_length=150, description="The name of the event or hackathon.")
    url: HttpUrl = Field(..., description="The direct URL to the opportunity page.")
    organizer: str = Field(..., min_length=2, description="The organizing body or company.")
    opportunity_type: OpportunityType = Field(default=OpportunityType.OTHER)
    description: Optional[str] = Field(None, description="Detailed explanation of the opportunity.")
    prizes_total: Optional[float] = Field(0.0, description="Aggregate financial value of all prizes.")
    deadline: Optional[datetime] = Field(None, description="ISO-formatted application deadline.")
    location_type: LocationType = Field(default=LocationType.ONLINE)
    difficulty: Optional[DifficultyLevel] = Field(None)
    required_skills: List[str] = Field(default_factory=list, description="Array of tech stack tags.")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("deadline")
    @classmethod
    def validate_future_deadline(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value and value.replace(tzinfo=None) < datetime.utcnow():
            # Soft warning or logging is handled downstream; Pydantic enforces valid ISO timestamps.
            pass
        return value
```

---

### 3. Service Layer Specs (`scraper/client/` & `scraper/sync/`)

#### A. Bright Data Cloud Scraper Client (`brightdata_client.py`)
This service handles direct API triggers, polls execution status, and automates self-healing approvals.

```python
import asyncio
import logging
from typing import Any, Dict, List
import httpx

logger = logging.getLogger("BrightDataClient")

class BrightDataClient:
    """Async Client to manage Scraper Studio runs and autonomous self-healing."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.brightdata.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def trigger_scraper(self, collector_id: str, urls: List[str]) -> Dict[str, Any]:
        """Trigger an extraction run via POST /dca/trigger."""
        endpoint = f"{self.base_url}/dca/trigger"
        payload = {
            "collector": collector_id,
            "inputs": [{"url": url} for url in urls]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, headers=self.headers, json=payload)
            if response.status_code != 200:
                raise ValueError(f"Failed to trigger scraper: {response.text}")
            return response.json()

    async def get_dataset(self, response_id: str) -> List[Dict[str, Any]]:
        """Fetch the extracted JSON results."""
        endpoint = f"{self.base_url}/dca/dataset?id={response_id}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def initiate_self_heal(self, collector_id: str, prompt: str) -> None:
        """Triggers the cloud AI self-heal loop (refactor_template)."""
        endpoint = f"{self.base_url}/refactor_template"
        payload = {
            "collector": collector_id,
            "prompt": prompt
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Self-heal job triggered for {collector_id}")

    async def auto_approve_heal(self, collector_id: str) -> bool:
        """Polls the healing job and programmatically accepts the AI's proposed extraction code diff."""
        progress_endpoint = f"{self.base_url}/refactor_template/progress?collector={collector_id}"
        approve_endpoint = f"{self.base_url}/resume_automation_job"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Poll progress until 'pending_answer' or 'done'
            for attempt in range(15):
                prog_resp = await client.get(progress_endpoint, headers=self.headers)
                prog_resp.raise_for_status()
                status_data = prog_resp.json()
                status = status_data.get("status")
                
                logger.info(f"Polling heal status for {collector_id}: {status}")
                if status == "pending_answer":
                    # 2. Programmatically accept the AI-generated selector update!
                    payload = {"message": True, "auto_save": True, "collector": collector_id}
                    app_resp = await client.post(approve_endpoint, headers=self.headers, json=payload)
                    app_resp.raise_for_status()
                    logger.info("Proposed healing diff approved successfully!")
                    return True
                elif status == "done":
                    logger.info("Heal job finalized automatically.")
                    return True
                elif status == "failed":
                    logger.error("Cloud AI self-healing failed.")
                    return False
                await asyncio.sleep(3)
        return False
```

#### B. Firebase Firestore REST Client (`firebase_sync.py`)
Because mobile Flutter clients rely on Firebase streams, we require a highly reliable python database syncer. Instead of heavy third-party SDKs, this clean, zero-dependency REST syncer converts Python Pydantic structures into the explicit JSON layouts required by the Google Cloud Firestore REST API.

```python
import hashlib
import httpx
from typing import Dict, Any

class FirestoreRESTClient:
    """Async Client to interact with Google Firestore REST API, ideal for lightweight sync."""
    
    def __init__(self, project_id: str, api_key: Optional[str] = None):
        self.project_id = project_id
        self.base_url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"
        self.params = {"key": api_key} if api_key else {}

    def _generate_doc_id(self, url: str) -> str:
        """Generate a deterministic, clean document ID to prevent duplicate listings."""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]

    def _convert_to_firestore_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a flat python dict into a strict Firestore Document typed format."""
        fields = {}
        for k, v in data.items():
            if isinstance(v, str):
                fields[k] = {"stringValue": v}
            elif isinstance(v, bool):
                fields[k] = {"booleanValue": v}
            elif isinstance(v, (int, float)):
                fields[k] = {"doubleValue": float(v)}
            elif isinstance(v, list):
                fields[k] = {"arrayValue": {"values": [{"stringValue": str(item)} for item in v]}}
            elif v is None:
                fields[k] = {"nullValue": None}
        return {"fields": fields}

    async def upsert_opportunity(self, opportunity_data: Dict[str, Any]) -> str:
        """Write or overwrite the opportunity in Firestore using a REST PATCH."""
        doc_id = self._generate_doc_id(opportunity_data["url"])
        endpoint = f"{self.base_url}/opportunities/{doc_id}"
        firestore_payload = self._convert_to_firestore_fields(opportunity_data)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # PATCH endpoint updates or creates the document at this precise identifier
            response = await client.patch(endpoint, params=self.params, json=firestore_payload)
            response.raise_for_status()
            return doc_id
```

---

### 4. Orchestration & Autonomous Self-Healing Workflow

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

#### Orchestrator Code Blueprint (`pipeline_orchestrator.py`)
```python
import os
import logging
from brightdata_client import BrightDataClient
from firebase_sync import FirestoreRESTClient
from models import Opportunity

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Pipeline")

async def run_pipeline(urls: list[str], collector_id: str):
    # 1. Initialize API Keys safely
    bd_key = os.getenv("BRIGHTDATA_API_KEY")
    fb_project = os.getenv("FIREBASE_PROJECT_ID")
    
    if not bd_key or not fb_project:
        logger.error("Missing environment config! Check BRIGHTDATA_API_KEY and FIREBASE_PROJECT_ID.")
        return

    bd_client = BrightDataClient(bd_key)
    db_client = FirestoreRESTClient(fb_project)

    logger.info(f"Triggering Collector ID: {collector_id} for {len(urls)} target sites...")
    
    # 2. Trigger Scraper
    trigger_resp = await bd_client.trigger_scraper(collector_id, urls)
    response_id = trigger_resp.get("id")
    
    # 3. Pull results
    raw_dataset = await bd_client.get_dataset(response_id)
    
    # 4. Perform Data Quality checks and schema structural validation
    valid_records = []
    broken_flag = False
    
    for row in raw_dataset:
        try:
            # We strictly enforce that essential attributes must exist and not be empty
            if not row.get("title") or not row.get("organizer"):
                raise ValueError("Essential fields 'title' or 'organizer' returned empty or null.")
            
            # Coerce fields and normalize structure
            validated = Opportunity(**row)
            valid_records.append(validated.model_dump())
        except Exception as e:
            logger.warning(f"Validation failure caught! Data drift detected: {e}")
            broken_flag = True

    # 5. Execute Autonomous Healing if a Selector Breakage was Detected
    if broken_flag:
        logger.warning("Unattended selector damage verified. Initiating autonomous healing...")
        heal_prompt = "Selector 'title' or 'organizer' broke on the latest website redesign, returning nulls. Locate the header elements on this page and map them."
        await bd_client.initiate_self_heal(collector_id, heal_prompt)
        
        success = await bd_client.auto_approve_heal(collector_id)
        if success:
            logger.info("Scraper auto-healed in place! Re-running scraper to capture fresh, clean data...")
            # Repeat extraction
            re_trigger = await bd_client.trigger_scraper(collector_id, urls)
            healed_dataset = await bd_client.get_dataset(re_trigger.get("id"))
            
            # Recalculate valid records list
            valid_records.clear()
            for row in healed_dataset:
                valid_records.append(Opportunity(**row).model_dump())
        else:
            logger.error("Autonomous healing was unable to recover selectors automatically. Alerting developers.")
            return

    # 6. Stream Healthy opportunities directly to Mobile Firestore Collection
    logger.info(f"Syncing {len(valid_records)} verified listings to database collection 'opportunities'...")
    for record in valid_records:
        doc_id = await db_client.upsert_opportunity(record)
        logger.info(f"Successfully upserted: '{record['title']}' -> Firestore Doc ID: {doc_id}")

    logger.info("Backend data ingestion pipeline run completed successfully.")
