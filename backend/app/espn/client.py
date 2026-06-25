import time

import httpx

from app.config import settings
from app.logging import get_logger

logger = get_logger("espn-client")

_client: httpx.Client | None = None


def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(
            base_url=settings.ESPN_BASE_URL,
            headers={"Accept": "application/json"},
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
    return _client


def _request_with_retry(path: str, params: dict | None = None, max_retries: int = 3) -> dict:
    client = _get_client()
    delays = [0.5, 1.0, 2.0]

    for attempt in range(max_retries):
        try:
            response = client.get(path, params=params)

            if response.status_code == 200:
                return response.json()

            if 400 <= response.status_code < 500:
                logger.warning(
                    "espn_client_4xx",
                    status_code=response.status_code,
                    path=path,
                )
                return {"events": []}

            # 5xx — retry
            logger.warning(
                "espn_client_5xx",
                status_code=response.status_code,
                path=path,
                attempt=attempt + 1,
            )

        except httpx.TransportError as exc:
            logger.warning(
                "espn_client_transport_error",
                error=str(exc),
                path=path,
                attempt=attempt + 1,
            )

        if attempt < max_retries - 1:
            time.sleep(delays[attempt])

    logger.error("espn_client_retries_exhausted", path=path, max_retries=max_retries)
    return {"events": []}


def fetch_scoreboard(date_str: str | None = None) -> list[dict]:
    """Fetch scoreboard from ESPN. Returns the list of event dicts."""
    params = {"dates": date_str} if date_str else None
    response = _request_with_retry("/scoreboard", params=params)
    return response.get("events", [])


def fetch_live_scores() -> list[dict]:
    """Fetch today's scoreboard and return only in-progress events."""
    events = fetch_scoreboard()
    return [
        event
        for event in events
        if event.get("competitions", [{}])[0].get("status", {}).get("type", {}).get("state") == "in"
    ]


def fetch_schedule(start_date: str, end_date: str) -> list[dict]:
    """Fetch all events in a date range."""
    return fetch_scoreboard(f"{start_date}-{end_date}")
