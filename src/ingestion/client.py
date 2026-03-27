import logging
import time

import httpx

from src.ingestion.config import DEFAULT_DELAY, MAX_RETRIES, REQUEST_TIMEOUT, USER_AGENT

logger = logging.getLogger("ufc.scraper.client")


class UFCStatsClient:
    def __init__(self, delay: float = DEFAULT_DELAY):
        self._delay = delay
        self._client = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )

    def get(self, url: str) -> str:
        time.sleep(self._delay)
        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._client.get(url)
                response.raise_for_status()
                return response.text
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_error = exc
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500:
                    raise
                wait = 2 ** (attempt - 1)
                logger.warning("Retry %d/%d for %s: %s (waiting %ds)", attempt, MAX_RETRIES, url, exc, wait)
                time.sleep(wait)

        raise RuntimeError(f"Failed after {MAX_RETRIES} retries for {url}") from last_error

    def close(self) -> None:
        self._client.close()
