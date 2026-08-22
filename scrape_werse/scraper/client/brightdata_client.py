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
        payload = {
            "collector": collector_id,
            "inputs": [{"url": url} for url in urls],
        }

        logger.info(
            f"Triggering collector '{collector_id}' for {len(urls)} URL(s)..."
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint, headers=self.headers, json=payload
            )
            if response.status_code != 200:
                raise ValueError(
                    f"Failed to trigger scraper [{response.status_code}]: "
                    f"{response.text}"
                )
            data = response.json()
            logger.info(f"Scraper triggered. Response ID: {data.get('id')}")
            return data

    async def get_dataset(self, response_id: str) -> List[Dict[str, Any]]:
        """
        Fetch the extracted JSON results for a completed run.

        Args:
            response_id: The `id` returned by `trigger_scraper`.

        Returns:
            List of raw row dicts extracted by the scraper.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        endpoint = f"{self.BASE_URL}/dca/dataset?id={response_id}"
        logger.info(f"Fetching dataset for response ID: {response_id}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(endpoint, headers=self.headers)
            response.raise_for_status()
            rows: List[Dict[str, Any]] = response.json()
            logger.info(f"Fetched {len(rows)} raw row(s) from dataset.")
            return rows

    # ── Self-Healing Operations ───────────────────────────────────────────────

    async def initiate_self_heal(self, collector_id: str, prompt: str) -> None:
        """
        Trigger the Cloud AI self-heal loop to repair broken selectors.

        This calls Bright Data's `refactor_template` endpoint, which uses an AI
        model to inspect the target page and propose updated CSS/XPath selectors
        that match the current page structure.

        Args:
            collector_id: The collector whose selectors are broken.
            prompt: Natural language description of the breakage for the AI.

        Raises:
            httpx.HTTPStatusError: If the self-heal job fails to start.
        """
        endpoint = f"{self.BASE_URL}/refactor_template"
        payload = {"collector": collector_id, "prompt": prompt}

        logger.warning(
            f"Initiating self-heal for collector '{collector_id}'. "
            f"Prompt: {prompt[:80]}..."
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(f"Self-heal job started for collector '{collector_id}'.")

    async def auto_approve_heal(
        self,
        collector_id: str,
        max_attempts: int | None = None,
        poll_interval: float | None = None,
    ) -> bool:
        """
        Poll the healing job and programmatically accept the AI-proposed diff.

        Polling states:
          - `pending_answer`: AI has proposed a fix → auto-approve it.
          - `done`: AI finalized the fix automatically.
          - `failed`: Self-healing could not repair the selectors.

        Args:
            collector_id: The collector being healed.
            max_attempts: Override for SELF_HEAL_MAX_ATTEMPTS env var (default 15).
            poll_interval: Override for SELF_HEAL_POLL_INTERVAL env var (default 3s).

        Returns:
            True if the healing was successful, False if it failed.
        """
        _max_attempts = max_attempts or int(
            os.getenv("SELF_HEAL_MAX_ATTEMPTS", "15")
        )
        _poll_interval = poll_interval or float(
            os.getenv("SELF_HEAL_POLL_INTERVAL", "3")
        )

        progress_endpoint = (
            f"{self.BASE_URL}/refactor_template/progress"
            f"?collector={collector_id}"
        )
        approve_endpoint = f"{self.BASE_URL}/resume_automation_job"

        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(1, _max_attempts + 1):
                prog_resp = await client.get(
                    progress_endpoint, headers=self.headers
                )
                prog_resp.raise_for_status()
                status_data = prog_resp.json()
                status = status_data.get("status")

                logger.info(
                    f"[Heal poll {attempt}/{_max_attempts}] "
                    f"Collector '{collector_id}' status: {status}"
                )

                if status == "pending_answer":
                    # Programmatically approve the AI-generated selector update.
                    payload = {
                        "message": True,
                        "auto_save": True,
                        "collector": collector_id,
                    }
                    app_resp = await client.post(
                        approve_endpoint, headers=self.headers, json=payload
                    )
                    app_resp.raise_for_status()
                    logger.info(
                        "✅ Healing diff approved. Selectors updated in Scraper Studio."
                    )
                    return True

                elif status == "done":
                    logger.info("✅ Heal job finalized automatically by Cloud AI.")
                    return True

                elif status == "failed":
                    logger.error(
                        f"❌ Cloud AI self-healing failed for '{collector_id}'."
                    )
                    return False

                await asyncio.sleep(_poll_interval)

        logger.error(
            f"Self-healing timed out after {_max_attempts} attempts "
            f"for collector '{collector_id}'."
        )
        return False


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
