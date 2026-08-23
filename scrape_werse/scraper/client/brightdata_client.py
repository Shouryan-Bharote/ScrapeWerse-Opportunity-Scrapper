"""
Bright Data Scraper Studio Client — Service Layer
==================================================
Async client for triggering Scraper Studio runs, fetching extracted datasets,
and driving the fully autonomous self-healing loop.

Architectural Rule: This module imports ONLY from the domain layer (models.py)
and the standard library / third-party packages. It never imports other service
modules (firebase_sync, etc.) to preserve downward-only dependency flow.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("BrightDataClient")


class BrightDataClient:
    """
    Async client to manage Scraper Studio runs and autonomous self-healing.

    The self-healing loop works as follows:
      1. `trigger_scraper` fires an extraction run.
      2. `get_dataset` fetches the resulting JSON rows.
      3. If Pydantic validation fails (schema drift detected), the orchestrator
         calls `initiate_self_heal` to ask the Cloud AI to repair the selectors.
      4. `auto_approve_heal` polls the healing job and programmatically accepts
         the AI-generated selector diff when it enters `pending_answer` state.
      5. The orchestrator re-triggers the scraper with the healed selectors.
    """

    BASE_URL = "https://api.brightdata.com"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ── Core Scraping Operations ───────────────────────────────────────────────

    async def trigger_scraper(
        self, collector_id: str, urls: List[str]
    ) -> Dict[str, Any]:
        """
        Trigger an extraction run via POST /dca/trigger.

        Args:
            collector_id: The Scraper Studio template/collector ID.
            urls: List of target URLs to extract from.

        Returns:
            Trigger response dict containing the `id` (response_id) to poll.

        Raises:
            ValueError: If the API returns a non-200 status.
        """
        endpoint = f"{self.BASE_URL}/dca/trigger"
        # collector_id is passed as a query parameter; inputs go in the body.
        params = {"collector": collector_id}
        payload = [{"url": url} for url in urls]

        logger.info(
            f"Triggering collector '{collector_id}' for {len(urls)} URL(s)..."
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint, headers=self.headers, params=params, json=payload
            )
            if response.status_code != 200:
                raise ValueError(
                    f"Failed to trigger scraper [{response.status_code}]: "
                    f"{response.text}"
                )
            data = response.json()
            # The newer Scraper Studio API returns 'collection_id';
            # normalise to 'id' for backward compatibility.
            if "collection_id" in data and "id" not in data:
                data["id"] = data["collection_id"]
            logger.info(f"Scraper triggered. Response ID: {data.get('id')}")
            return data


    async def get_dataset(
        self, response_id: str, poll_timeout: int = 600, poll_interval: float = 5.0
    ) -> List[Dict[str, Any]]:
        """
        Fetch the extracted JSON results for a completed run, polling until ready.

        Args:
            response_id: The `id` / `collection_id` returned by `trigger_scraper`.
            poll_timeout: Max seconds to wait for results (default 300s).
            poll_interval: Seconds between status checks (default 5s).

        Returns:
            List of raw row dicts extracted by the scraper.

        Raises:
            TimeoutError: If results are not ready within poll_timeout seconds.
            httpx.HTTPStatusError: On non-2xx responses.
        """
        import time
        endpoint = f"{self.BASE_URL}/dca/dataset"
        params = {"id": response_id}
        logger.info(f"Fetching dataset for response ID: {response_id}")

        deadline = time.monotonic() + poll_timeout
        attempt = 0
        async with httpx.AsyncClient(timeout=60.0) as client:
            while time.monotonic() < deadline:
                attempt += 1
                response = await client.get(endpoint, headers=self.headers, params=params)
                # 200 with JSON array = ready; 202 = still processing
                if response.status_code == 200:
                    rows: List[Dict[str, Any]] = response.json()
                    logger.info(f"Fetched {len(rows)} raw row(s) from dataset.")
                    return rows
                elif response.status_code == 202:
                    logger.info(
                        f"Dataset not ready yet (attempt {attempt}), "
                        f"retrying in {poll_interval}s..."
                    )
                    await asyncio.sleep(poll_interval)
                else:
                    response.raise_for_status()

        raise TimeoutError(
            f"Dataset for response_id '{response_id}' not ready "
            f"after {poll_timeout}s."
        )

    # ── Self-Healing Operations ───────────────────────────────────────────────

    async def self_heal_and_approve(
        self,
        collector_id: str,
        prompt: str,
        poll_timeout: int = 600,
        poll_interval: float = 5.0,
    ) -> bool:
        """
        Full self-heal cycle using the same REST calls as `bdata scraper heal`
        followed by `bdata scraper approve`.

        Endpoint sequence:
          1. POST /dca/adjust — kick off AI-powered selector repair.
          2. Poll GET /dca/adjust/progress?collector=ID until status is
             `awaiting_approval` or `done`.
          3. POST /dca/adjust/approve — auto-approve the proposed diff.

        Args:
            collector_id: The Scraper Studio collector ID to heal.
            prompt: Natural language description of what is broken.
            poll_timeout: Max seconds to wait for the heal job (default 600s).
            poll_interval: Seconds between status checks (default 5s).

        Returns:
            True if healing succeeded and was approved, False otherwise.
        """
        import time

        heal_endpoint   = f"{self.BASE_URL}/dca/adjust"
        status_endpoint = f"{self.BASE_URL}/dca/adjust/progress"
        approve_endpoint = f"{self.BASE_URL}/dca/adjust/approve"

        logger.warning(
            f"⚠️  Initiating self-heal for collector '{collector_id}'. "
            f"Prompt: {prompt[:120]}..."
        )

        # Step 1: Kick off healing job
        async with httpx.AsyncClient(timeout=60.0) as client:
            heal_resp = await client.post(
                heal_endpoint,
                headers=self.headers,
                json={"collector_id": collector_id, "prompt": prompt},
            )
            if heal_resp.status_code not in (200, 201, 202):
                logger.error(
                    f"Heal trigger failed [{heal_resp.status_code}]: {heal_resp.text[:200]}"
                )
                return False
            logger.info(f"Heal job started for collector '{collector_id}'.")

        # Step 2: Poll until awaiting_approval or done
        deadline = time.monotonic() + poll_timeout
        attempt = 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            while time.monotonic() < deadline:
                attempt += 1
                prog_resp = await client.get(
                    status_endpoint,
                    headers=self.headers,
                    params={"collector": collector_id},
                )
                if prog_resp.status_code != 200:
                    await asyncio.sleep(poll_interval)
                    continue

                data = prog_resp.json()
                status = data.get("status", "")
                logger.info(
                    f"[Heal poll {attempt}] Collector '{collector_id}' → status: {status}"
                )

                if status in ("awaiting_approval", "pending_answer"):
                    # Step 3: Auto-approve the AI-proposed diff
                    app_resp = await client.post(
                        approve_endpoint,
                        headers=self.headers,
                        json={"collector_id": collector_id, "auto_save": True},
                    )
                    if app_resp.status_code in (200, 201, 202):
                        logger.info(
                            "✅ Heal approved and saved. Scraper template updated."
                        )
                        return True
                    else:
                        logger.error(
                            f"Heal approve failed [{app_resp.status_code}]: "
                            f"{app_resp.text[:200]}"
                        )
                        return False

                elif status == "done":
                    logger.info("✅ Heal completed and auto-saved by Bright Data AI.")
                    return True

                elif status in ("failed", "error"):
                    logger.error(
                        f"❌ Self-healing failed for collector '{collector_id}'. "
                        f"Details: {data.get('message', 'no details')}"
                    )
                    return False

                await asyncio.sleep(poll_interval)

        logger.error(
            f"Self-healing timed out after {poll_timeout}s for '{collector_id}'."
        )
        return False

    # Keep backward-compat aliases so existing orchestrator calls still work
    async def initiate_self_heal(self, collector_id: str, prompt: str) -> None:
        """Deprecated: use self_heal_and_approve() instead."""
        await self.self_heal_and_approve(collector_id, prompt)

    async def auto_approve_heal(self, collector_id: str, **kwargs) -> bool:
        """Deprecated: use self_heal_and_approve() instead."""
        return True  # approval is now bundled in self_heal_and_approve


def create_client_from_env() -> BrightDataClient:
    """
    Convenience factory that reads BRIGHTDATA_API_KEY from the environment.

    Raises:
        EnvironmentError: If BRIGHTDATA_API_KEY is not set.
    """
    api_key = os.getenv("BRIGHTDATA_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "BRIGHTDATA_API_KEY is not set. "
            "Copy .env.example to .env and fill in your credentials."
        )
    return BrightDataClient(api_key=api_key)
