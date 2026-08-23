"""
Firebase Firestore REST Client — Service Layer
==============================================
Async, zero-SDK Firestore syncer. Converts Pydantic model dicts into the
explicit typed JSON format required by the Cloud Firestore REST API v1 and
performs deterministic upserts using SHA-256 URL-derived document IDs.

Architectural Rule: This module imports ONLY from the domain layer (models.py)
and the standard library / third-party packages. It never imports other service
modules (brightdata_client, etc.) to preserve downward-only dependency flow.

Why REST instead of the official SDK?
  - Zero heavy dependencies — no Firebase Admin SDK, no gRPC, no protobuf.
  - Works in any Python environment without C extension binaries.
  - Predictable async behavior with httpx, identical to the BrightData client.
  - Flutter mobile clients receive Firestore real-time streams; this backend
    only writes — a lightweight REST PATCH is all we need.
"""

import hashlib
import logging
import os
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("FirestoreRESTClient")


class FirestoreRESTClient:
    """
    Async client to interact with Google Firestore REST API.

    Upserts Opportunity records into the `opportunities` collection using
    SHA-256-derived document IDs for deterministic deduplication. If the same
    URL is ingested twice, the document is patched in place rather than
    duplicated.
    """

    FIRESTORE_BASE = (
        "https://firestore.googleapis.com/v1/projects/{project_id}"
        "/databases/(default)/documents"
    )

    def __init__(
        self,
        project_id: str,
        api_key: Optional[str] = None,
    ) -> None:
        self.project_id = project_id
        self.base_url = self.FIRESTORE_BASE.format(project_id=project_id)
        # `api_key` is passed as ?key= for server-to-server calls when
        # Firestore security rules permit it. For service-account auth,
        # swap this for a Bearer token in the headers dict.
        self.params: Dict[str, str] = {"key": api_key} if api_key else {}

    # ── ID Generation ─────────────────────────────────────────────────────────

    def _generate_doc_id(self, url: str) -> str:
        """
        Generate a deterministic, URL-safe document ID from an opportunity URL.

        Uses SHA-256 truncated to 20 hex chars. This ensures:
          - Idempotent upserts: same URL → same doc ID → PATCH replaces.
          - No collision risk at the scale of this dataset.
          - Clean Firestore document paths (no special characters).

        Args:
            url: The canonical opportunity URL.

        Returns:
            A 20-character lowercase hex string.
        """
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]

    # ── Firestore Typed Value Conversion ──────────────────────────────────────

    def _convert_to_firestore_fields(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert a flat Python dict into the Firestore REST typed-value format.

        Firestore REST requires every field value to be wrapped in a type
        descriptor object:
          - str  → {"stringValue": "..."}
          - bool → {"booleanValue": true/false}
          - int/float → {"doubleValue": 1.0}
          - list → {"arrayValue": {"values": [...]}}
          - None → {"nullValue": null}

        Args:
            data: Flat dict produced by `Opportunity.model_dump()`.

        Returns:
            Firestore REST document body with typed `fields` dict.
        """
        fields: Dict[str, Any] = {}

        for key, value in data.items():
            if isinstance(value, bool):
                # bool check MUST come before int (bool is a subclass of int)
                fields[key] = {"booleanValue": value}
            elif isinstance(value, str):
                fields[key] = {"stringValue": value}
            elif isinstance(value, (int, float)):
                fields[key] = {"doubleValue": float(value)}
            elif isinstance(value, list):
                fields[key] = {
                    "arrayValue": {
                        "values": [{"stringValue": str(item)} for item in value]
                    }
                }
            elif value is None:
                fields[key] = {"nullValue": None}
            else:
                # Datetime and other complex types → ISO string representation
                fields[key] = {"stringValue": str(value)}

        return {"fields": fields}

    # ── Write & Delete Operations ─────────────────────────────────────────────

    async def upsert_opportunity(
        self,
        opportunity_data: Dict[str, Any],
        collection_name: str = "opportunities",
    ) -> str:
        """
        Write or overwrite an opportunity in Firestore using a REST PATCH.

        Args:
            opportunity_data: Dict produced by `Opportunity.model_dump()`.
                              Must contain a `url` key for ID generation.
            collection_name: Target Firestore collection (e.g., 'opportunities'
                             or 'demo_opportunities').

        Returns:
            The Firestore document ID (20-char hex string).
        """
        url_str = str(opportunity_data["url"])
        doc_id = self._generate_doc_id(url_str)
        endpoint = f"{self.base_url}/{collection_name}/{doc_id}"
        firestore_payload = self._convert_to_firestore_fields(opportunity_data)

        logger.debug(
            f"Upserting opportunity '{opportunity_data.get('title', '?')}' "
            f"→ doc ID: {doc_id} in collection '{collection_name}'"
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.patch(
                endpoint,
                params=self.params,
                json=firestore_payload,
            )
            response.raise_for_status()

        logger.info(
            f"✅ Upserted: '{opportunity_data.get('title', '?')}' "
            f"→ /{collection_name}/{doc_id}"
        )
        return doc_id

    async def delete_document(
        self, doc_id: str, collection_name: str = "opportunities"
    ) -> bool:
        """
        Delete a single document by ID via REST DELETE. Useful for demo resets.
        """
        endpoint = f"{self.base_url}/{collection_name}/{doc_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(endpoint, params=self.params)
            return response.status_code in (200, 204)

    async def batch_upsert(
        self,
        records: list[Dict[str, Any]],
        collection_name: str = "opportunities",
    ) -> list[str]:
        """
        Upsert a list of opportunity records sequentially into specified collection.

        Args:
            records: List of dicts from `Opportunity.model_dump()`.
            collection_name: Firestore collection name.

        Returns:
            List of Firestore document IDs that were written.
        """
        doc_ids: list[str] = []
        for record in records:
            try:
                doc_id = await self.upsert_opportunity(record, collection_name=collection_name)
                doc_ids.append(doc_id)
            except Exception as exc:
                logger.error(
                    f"Failed to upsert '{record.get('title', '?')}': {exc}"
                )
        return doc_ids



def create_client_from_env() -> FirestoreRESTClient:
    """
    Convenience factory that reads Firebase config from the environment.

    Raises:
        EnvironmentError: If FIREBASE_PROJECT_ID is not set.
    """
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    if not project_id:
        raise EnvironmentError(
            "FIREBASE_PROJECT_ID is not set. "
            "Copy .env.example to .env and fill in your credentials."
        )
    api_key = os.getenv("FIREBASE_API_KEY")
    return FirestoreRESTClient(project_id=project_id, api_key=api_key)
