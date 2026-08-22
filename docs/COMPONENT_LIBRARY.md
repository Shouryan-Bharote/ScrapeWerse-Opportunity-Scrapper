# Component Library

## Domain Models

### `Opportunity` (Pydantic v2)
| Field | Type | Description | Required | Default |
|-------|------|-------------|----------|---------|
| `title` | `str` | Name of the event / opportunity | Yes | - |
| `url` | `HttpUrl` | Direct URL to opportunity | Yes | - |
| `organizer` | `str` | Organizing body or platform | Yes | - |
| `opportunity_type` | `OpportunityType` | Classification enum | No | `OTHER` |
| `description` | `Optional[str]` | Detailed explanation | No | `None` |
| `prizes_total` | `Optional[float]` | Total prize money (USD) | No | `0.0` |
| `deadline` | `Optional[datetime]` | Application / submission deadline | No | `None` |
| `location_type` | `LocationType` | Online / Hybrid / In-Person | No | `ONLINE` |
| `difficulty` | `Optional[DifficultyLevel]` | Beginner / Intermediate / Advanced | No | `None` |
| `required_skills` | `List[str]` | Tech tags (Python, ML, NLP, etc.) | No | `[]` |
| `is_active` | `bool` | Open status | No | `True` |
| `created_at` | `datetime` | Ingestion timestamp | No | `utcnow()` |

---

## Service Components

### `BrightDataClient`
- **Class:** `BrightDataClient(api_key: str)`
- **Key Methods:**
  - `trigger_scraper(collector_id: str, urls: List[str]) -> Dict[str, Any]`
  - `get_dataset(response_id: str) -> List[Dict[str, Any]]`
  - `initiate_self_heal(collector_id: str, prompt: str) -> None`
  - `auto_approve_heal(collector_id: str, max_attempts: int, poll_interval: float) -> bool`

### `FirestoreRESTClient`
- **Class:** `FirestoreRESTClient(project_id: str, api_key: Optional[str])`
- **Key Methods:**
  - `_generate_doc_id(url: str) -> str`
  - `_convert_to_firestore_fields(data: Dict[str, Any]) -> Dict[str, Any]`
  - `upsert_opportunity(opportunity_data: Dict[str, Any]) -> str`
  - `batch_upsert(records: List[Dict[str, Any]]) -> List[str]`
