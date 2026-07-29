import logging
import time

import httpx

from src.pipeline.config import DEFAULT_DELAY, MAX_RETRIES, REQUEST_TIMEOUT, USER_AGENT
from src.pipeline.errors import ChallengeError

logger = logging.getLogger("ufc.scraper.client")

CHALLENGE_MARKERS = ("Checking your browser", "__cf_chl", "Just a moment")


def is_challenge(html: str) -> bool:
    return any(marker in html for marker in CHALLENGE_MARKERS)


class UFCStatsClient:
    def __init__(self, delay: float = DEFAULT_DELAY):
        self._delay = delay
        self._client = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
        self._session_ready = False

    def _request(self, url: str) -> httpx.Response:
        time.sleep(self._delay)
        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._client.get(url)
                response.raise_for_status()
                return response
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_error = exc
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500:
                    raise
                wait = 2 ** (attempt - 1)
                logger.warning("Retry %d/%d for %s: %s (waiting %ds)", attempt, MAX_RETRIES, url, exc, wait)
                time.sleep(wait)

        raise RuntimeError(f"Failed after {MAX_RETRIES} retries for {url}") from last_error

    def _establish_session(self) -> None:
        from src.pipeline.session import solve_challenge

        self._client.cookies.update(solve_challenge())
        self._session_ready = True

    def get(self, url: str) -> str:
        html = self._request(url).text
        if not is_challenge(html):
            return html

        logger.info("Challenge received for %s, establishing session", url)
        self._establish_session()

        html = self._request(url).text
        if is_challenge(html):
            raise ChallengeError(f"Challenge still present after establishing session: {url}")
        return html

    def get_bytes(self, url: str) -> bytes:
        return self._request(url).content

    def close(self) -> None:
        self._client.close()
