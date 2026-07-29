import logging

from playwright.sync_api import sync_playwright

from src.pipeline.config import EVENTS_INDEX_URL, USER_AGENT

logger = logging.getLogger("ufc.scraper.session")

NAVIGATION_TIMEOUT_MS = 60_000
CONTENT_TIMEOUT_MS = 30_000
CONTENT_SELECTOR = "tr.b-statistics__table-row"


def solve_challenge() -> dict[str, str]:
    """Run the site's challenge JavaScript in a real browser and return its cookies."""
    logger.info("Establishing session via headless browser")
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        try:
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()
            page.goto(EVENTS_INDEX_URL, wait_until="networkidle", timeout=NAVIGATION_TIMEOUT_MS)
            page.wait_for_selector(CONTENT_SELECTOR, timeout=CONTENT_TIMEOUT_MS)
            cookies = {c["name"]: c["value"] for c in context.cookies()}
            logger.info("Session established, cookies: %s", sorted(cookies))
            return cookies
        finally:
            browser.close()
