"""
HTTP Scraper Core with Robots.txt Compliance

Exports:
    scrape_page(url: str) -> str: Scrape a page and return HTML content
    orchestrate(): Complete scraping pipeline
"""

import asyncio
import time
import httpx
import logging
from urllib.parse import urlparse, urljoin
from typing import Optional, Set, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from config import (
    HEADERS,
    USER_AGENTS,
    RETRY_CONFIG,
    RATE_LIMIT_DELAY,
    HTTP_TIMEOUT,
    SELECTORS,
)


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class RobotsTxtError(ScraperError):
    """Raised when robots.txt violation detected."""
    pass


class RequestError(ScraperError):
    """Raised when request fails after retries."""
    pass


@dataclass
class RobotsTxt:
    """Simple robots.txt parser and checker."""
    allowed: Set[str] = field(default_factory=set)
    disallowed: Set[str] = field(default_factory=set)
    crawl_delay: Optional[float] = None
    last_checked: datetime = field(default_factory=datetime.now)
    cache_ttl: timedelta = field(default_factory=lambda: timedelta(hours=1))

    def is_allowed(self, path: str, user_agent: str) -> bool:
        """Check if a path is allowed for a user agent."""
        # Check if there's a more specific match (we simplify to checking both)
        for disallowed_path in self.disallowed:
            if path.startswith(disallowed_path):
                return False
        return True

    def crawl_delay_seconds(self) -> Optional[float]:
        """Get crawl delay in seconds."""
        return self.crawl_delay


class RobotsCache:
    """Cache for robots.txt files per host."""
    _cache: Dict[str, RobotsTxt] = {}
    
    @classmethod
    def get(cls, host: str) -> Optional[RobotsTxt]:
        """Get cached robots.txt or None if expired."""
        robots = cls._cache.get(host)
        if robots and (datetime.now() - robots.last_checked) < robots.cache_ttl:
            return robots
        return None
    
    @classmethod
    def set(cls, host: str, robots: RobotsTxt) -> None:
        """Cache robots.txt for a host."""
        cls._cache[host] = robots


async def parse_robots_txt(client: httpx.Client, url: str) -> RobotsTxt:
    """Fetch and parse robots.txt for a URL's host."""
    parsed = urlparse(url)
    host = parsed.netloc
    
    # Check cache first
    cached = RobotsCache.get(host)
    if cached:
        return cached
    
    robots_url = f"{parsed.scheme}://{host}/robots.txt"
    
    try:
        response = await client.get(robots_url, timeout=HTTP_TIMEOUT)
        if response.status_code == 404:
            # No robots.txt = allowed for all
            robots = RobotsTxt()
        elif response.status_code != 200:
            # If we can't fetch robots.txt, be permissive but log warning
            robots = RobotsTxt()
        else:
            robots = _parse_robots_content(response.text)
    except httpx.RequestError:
        # Network error - proceed with empty robots (permissive)
        robots = RobotsTxt()
    
    RobotsCache.set(host, robots)
    return robots


def _parse_robots_content(content: str) -> RobotsTxt:
    """Parse robots.txt content and extract rules."""
    allowed = set()
    disallowed = set()
    crawl_delay = None
    in_user_agent_block = False
    
    for line in content.splitlines():
        line = line.strip().lower()
        if not line or line.startswith('#'):
            continue
        
        if line.startswith('user-agent:'):
            in_user_agent_block = True
            # Reset for new UA block - we track all rules
        elif line.startswith('disallow:'):
            path = line.split(':', 1)[1].strip()
            if path:
                disallowed.add(path)
        elif line.startswith('allow:'):
            path = line.split(':', 1)[1].strip()
            if path:
                allowed.add(path)
        elif line.startswith('crawl-delay:'):
            try:
                crawl_delay = float(line.split(':', 1)[1].strip())
            except ValueError:
                pass
    
    return RobotsTxt(
        allowed=allowed,
        disallowed=disallowed,
        crawl_delay=crawl_delay,
    )


def get_random_user_agent() -> str:
    """Get a random User-Agent from the configured list."""
    import random
    return random.choice(USER_AGENTS)


def build_request_headers() -> Dict[str, str]:
    """Build request headers with random User-Agent."""
    headers = HEADERS.copy()
    headers["User-Agent"] = get_random_user_agent()
    return headers


class RateLimiter:
    """Simple rate limiter with per-host tracking."""
    _last_request: Dict[str, float] = {}
    
    @classmethod
    async def wait(cls, url: str) -> None:
        """Wait if necessary to respect rate limits."""
        parsed = urlparse(url)
        host = parsed.netloc
        
        now = time.time()
        last_time = cls._last_request.get(host, 0)
        elapsed = now - last_time
        
        if elapsed < RATE_LIMIT_DELAY:
            await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)
        
        cls._last_request[host] = time.time()


class ScrapingClient:
    """Async HTTP client with retry, rate limiting, and robots.txt compliance."""
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._transport = httpx.AsyncHTTPTransport()
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            transport=self._transport,
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
        )
        return self
    
    async def __aexit__(self, *args):
        await self._client.aclose()
        self._client = None
    
    async def _check_robots_txt(self, url: str) -> None:
        """Verify the URL is allowed by robots.txt."""
        robots = await parse_robots_txt(self._client, url)
        parsed = urlparse(url)
        path = parsed.path or "/"
        
        if not robots.is_allowed(path, "default"):
            raise RobotsTxtError(f"Blocked by robots.txt: {url}")
    
    async def _request_with_retry(
        self,
        url: str,
        headers: Dict[str, str],
        attempt: int = 0,
    ) -> httpx.Response:
        """Make a request with retry logic."""
        try:
            response = await self._client.get(url, headers=headers)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            
            # Retry on 5xx errors
            if 500 <= status_code < 600:
                if attempt < RETRY_CONFIG["max_retries"]:
                    backoff = RETRY_CONFIG["backoff_factor"] * (2 ** attempt)
                    await asyncio.sleep(backoff)
                    return await self._request_with_retry(url, headers, attempt + 1)
                else:
                    raise RequestError(f"Failed after {RETRY_CONFIG['max_retries']} retries: {url}")
            else:
                raise RequestError(f"HTTP {status_code}: {url}")
        except httpx.RequestError as e:
            if attempt < RETRY_CONFIG["max_retries"]:
                backoff = RETRY_CONFIG["backoff_factor"] * (2 ** attempt)
                await asyncio.sleep(backoff)
                return await self._request_with_retry(url, headers, attempt + 1)
            else:
                raise RequestError(f"Request failed after {RETRY_CONFIG['max_retries']} retries: {e}")
    
    async def scrape(self, url: str) -> str:
        """Scrape a URL and return HTML content."""
        if not self._client:
            raise ScraperError("Client not initialized. Use async context manager.")
        
        # Check robots.txt compliance
        await self._check_robots_txt(url)
        
        # Apply rate limiting
        await RateLimiter.wait(url)
        
        # Build headers with rotating UA
        headers = build_request_headers()
        
        # Make request with retry
        response = await self._request_with_retry(url, headers)
        
        return response.text


async def scrape_page(url: str) -> str:
    """
    Scrape a web page and return its HTML content.
    
    Args:
        url: The URL to scrape
        
    Returns:
        HTML content as string
        
    Raises:
        ScraperError: If scraping fails after retries
        RobotsTxtError: If URL is blocked by robots.txt
    """
    async with ScrapingClient() as client:
        return await client.scrape(url)


# Synchronous wrapper for convenience
def scrape_page_sync(url: str) -> str:
    """Synchronous wrapper for scrape_page."""
    return asyncio.run(scrape_page(url))


# ============================================================================
# ORCHESTRATION FUNCTIONS (see __main__.py for full pipeline)
# ============================================================================

async def orchestrate(
    output_path: Optional[str] = None,
    verbose: bool = False,
) -> dict:
    """
    Orchestrate the complete scraping pipeline.
    
    This is a convenience function that wraps the full pipeline.
    For full functionality, use __main__.py as the entry point.
    
    Args:
        output_path: Optional path to save JSON output
        verbose: Enable debug logging
        
    Returns:
        dict with scraped data structure
    """
    import json
    from datetime import datetime
    
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    start_time = datetime.utcnow()
    logger.info("Starting orchestration...")
    
    errors = []
    data = {
        "forex": [],
        "indices": [],
        "commodities": [],
        "bonds": [],
        "crypto": [],
        "stocks": [],
        "macro": {},
        "news": {},
        "metadata": {
            "scraped_at": start_time.isoformat(),
            "errors": errors,
        },
    }
    
    try:
        async with ScrapingClient() as client:
            # Import parsers here to avoid circular imports
            from parsers.markets import (
                parse_commodities,
                parse_indexes,
                parse_stocks,
                parse_forex,
                parse_bonds,
                parse_crypto,
            )
            from parsers.macro import parse_macro_indicators
            from parsers.headlines import parse_all_news_categories
            
            # Fetch and parse markets
            logger.info("Fetching market data...")
            
            try:
                html = await client.scrape("https://tradingeconomics.com/forex")
                data["forex"] = parse_forex(html)
            except Exception as e:
                logger.warning(f"Could not fetch forex: {e}")
                errors.append(f"forex: {str(e)}")
            
            try:
                html = await client.scrape("https://tradingeconomics.com/indices")
                data["indices"] = parse_indexes(html)
            except Exception as e:
                logger.warning(f"Could not fetch indices: {e}")
                errors.append(f"indices: {str(e)}")
            
            try:
                html = await client.scrape("https://tradingeconomics.com/commodities")
                data["commodities"] = parse_commodities(html)
            except Exception as e:
                logger.warning(f"Could not fetch commodities: {e}")
                errors.append(f"commodities: {str(e)}")
            
            try:
                html = await client.scrape("https://tradingeconomics.com/bonds")
                data["bonds"] = parse_bonds(html)
            except Exception as e:
                logger.warning(f"Could not fetch bonds: {e}")
                errors.append(f"bonds: {str(e)}")
            
            try:
                html = await client.scrape("https://tradingeconomics.com/crypto")
                data["crypto"] = parse_crypto(html)
            except Exception as e:
                logger.warning(f"Could not fetch crypto: {e}")
                errors.append(f"crypto: {str(e)}")
            
            try:
                html = await client.scrape("https://tradingeconomics.com/stocks")
                data["stocks"] = parse_stocks(html)
            except Exception as e:
                logger.warning(f"Could not fetch stocks: {e}")
                errors.append(f"stocks: {str(e)}")
            
            # Fetch macro
            logger.info("Fetching macro data...")
            try:
                html = await client.scrape("https://tradingeconomics.com/macro")
                data["macro"] = parse_macro_indicators(html)
            except Exception as e:
                logger.warning(f"Could not fetch macro: {e}")
                errors.append(f"macro: {str(e)}")
            
            # Fetch news
            logger.info("Fetching news...")
            try:
                html = await client.scrape("https://tradingeconomics.com/news")
                data["news"] = parse_all_news_categories(html)
            except Exception as e:
                logger.warning(f"Could not fetch news: {e}")
                errors.append(f"news: {str(e)}")
            
            # Update metadata
            duration = (datetime.utcnow() - start_time).total_seconds()
            data["metadata"]["duration_seconds"] = duration
            data["metadata"]["errors"] = errors
            
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        errors.append(str(e))
        data["metadata"]["errors"] = errors
    
    logger.info(f"Orchestration complete in {data['metadata'].get('duration_seconds', 0):.2f}s")
    
    # Save to file if path specified
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        logger.info(f"Output saved to {output_path}")
    
    return data


def orchestrate_sync(output_path: Optional[str] = None, verbose: bool = False) -> dict:
    """Synchronous wrapper for orchestrate."""
    return asyncio.run(orchestrate(output_path, verbose))


# ============================================================================
# PLAYWRIGHT FALLBACK FOR JS-RENDERED CONTENT
# ============================================================================

import asyncio
from contextlib import asynccontextmanager
from typing import Optional


@asynccontextmanager
async def get_playwright_browser():
    """
    Context manager for Playwright browser.
    
    Ensures proper cleanup even on errors.
    
    Usage:
        async with get_playwright_browser() as browser:
            page = await browser.new_page()
            ...
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError(
            "Playwright is not installed. "
            "Install with: pip install playwright && playwright install"
        )
    
    playwright = await async_playwright().start()
    
    try:
        browser = await playwright.chromium.launch(
            headless=True,  # Headless mode for CI/CD
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()
        
        try:
            yield page, browser, context
        finally:
            await context.close()
            await browser.close()
    finally:
        await playwright.stop()


async def scrape_with_playwright(
    url: str,
    wait_for_selectors: Optional[list] = None,
    wait_timeout_ms: int = 30000,
    html_content: Optional[str] = None,
) -> str:
    """
    Scrape a URL using Playwright for JavaScript-rendered pages.
    
    This function should be used as a fallback when static HTML
    doesn't contain the expected data (detected by empty selectors).
    
    Args:
        url: URL to scrape
        wait_for_selectors: Optional list wait for
 of CSS selectors to        wait_timeout_ms: Timeout for waiting on selectors (default 30s)
        html_content: Optional static HTML to check first
        
    Returns:
        Rendered HTML content as string
        
    Raises:
        ScraperError: If Playwright scraping fails
    """
    logger.info(f"Using Playwright to render: {url}")
    
    # Optional: Check if static HTML already has content
    if html_content:
        from bs4 import BeautifulSoup
        
        # If we have wait selectors, check if they exist in static HTML
        if wait_for_selectors:
            soup = BeautifulSoup(html_content, "lxml")
            has_content = any(soup.select(selector) for selector in wait_for_selectors)
            if has_content:
                logger.info(f"Static HTML already contains expected content, using that instead")
                return html_content
    
    try:
        async with get_playwright_browser() as (page, browser, context):
            # Navigate to page
            await page.goto(
                url,
                wait_until="networkidle",  # Wait for network to be idle
                timeout=wait_timeout_ms,
            )
            
            # Optional: Wait for specific selectors
            if wait_for_selectors:
                for selector in wait_for_selectors:
                    try:
                        await page.wait_for_selector(
                            selector,
                            timeout=wait_timeout_ms,
                            state="attached",
                        )
                    except Exception as e:
                        logger.warning(
                            f"Selector '{selector}' not found within {wait_timeout_ms}ms: {e}"
                        )
            
            # Wait a bit for any remaining JS to execute
            await page.wait_for_timeout(2000)
            
            # Get the rendered HTML
            html = await page.content()
            
            logger.info(f"Playwright rendered {len(html)} bytes from {url}")
            
            return html
            
    except ImportError as e:
        raise ScraperError(f"Playwright not available: {e}")
    except Exception as e:
        logger.error(f"Playwright scraping failed for {url}: {e}")
        raise ScraperError(f"Playwright error: {e}")


def scrape_with_playwright_sync(
    url: str,
    wait_for_selectors: Optional[list] = None,
    wait_timeout_ms: int = 30000,
    html_content: Optional[str] = None,
) -> str:
    """
    Synchronous wrapper for scrape_with_playwright.
    
    Usage for cases where async is not convenient.
    """
    return asyncio.run(
        scrape_with_playwright(
            url,
            wait_for_selectors,
            wait_timeout_ms,
            html_content,
        )
    )


async def scrape_with_fallback(
    url: str,
    selectors_to_check: Optional[list] = None,
    wait_for_selectors: Optional[list] = None,
) -> str:
    """
    Smart scraping function that tries static HTML first,
    then falls back to Playwright if needed.
    
    Args:
        url: URL to scrape
        selectors_to_check: Selectors that should exist in the content
        wait_for_selectors: Selectors to wait for with Playwright
        
    Returns:
        HTML content (static or rendered)
        
    Example:
        html = await scrape_with_fallback(
            url="https://example.com/page",
            selectors_to_check=[".product-grid", ".price"],
            wait_for_selectors=[".loading-spinner"],
        )
    """
    from bs4 import BeautifulSoup
    
    logger.info(f"Attempting to scrape: {url}")
    
    # First try: Static HTML with httpx
    try:
        static_html = await scrape_page(url)
        
        # Check if static HTML has the expected content
        if selectors_to_check and static_html:
            soup = BeautifulSoup(static_html, "lxml")
            has_content = any(soup.select(selector) for selector in selectors_to_check)
            
            if has_content:
                logger.info(f"Static HTML contains expected content")
                return static_html
            
            logger.info(f"Static HTML missing expected content, trying Playwright...")
        
        # Return static HTML if no selectors to check
        if not selectors_to_check:
            return static_html
            
    except Exception as e:
        logger.warning(f"Static scraping failed: {e}, trying Playwright...")
    
    # Second try: Playwright
    try:
        rendered_html = await scrape_with_playwright(
            url=url,
            wait_for_selectors=wait_for_selectors,
            html_content=static_html if 'static_html' in dir() else None,
        )
        return rendered_html
        
    except Exception as e:
        raise ScraperError(f"Both static and Playwright scraping failed: {e}")


# ============================================================================
# PLAYWRIGHT UTILITIES (for advanced use cases)
# ============================================================================

async def click_and_wait(
    page,
    selector: str,
    new_selector: str,
    timeout_ms: int = 30000,
) -> None:
    """
    Click a selector and wait for another selector to appear.
    
    Useful for pagination or loading more content.
    """
    await page.click(selector)
    await page.wait_for_selector(new_selector, timeout=timeout_ms)


async def scroll_to_load(
    page,
    selector: str,
    scroll_pause: float = 1.0,
    max_scrolls: int = 10,
) -> None:
    """
    Scroll down to load lazy-loaded content.
    
    Args:
        page: Playwright page object
        selector: Selector to check after each scroll
        scroll_pause: Seconds to pause between scrolls
        max_scrolls: Maximum number of scroll attempts
    """
    import time
    
    for i in range(max_scrolls):
        # Get current element count
        elements = await page.query_selector_all(selector)
        count = len(elements) if elements else 0
        
        # Scroll to bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        # Wait for new content
        await page.wait_for_timeout(int(scroll_pause * 1000))
        
        # Check if more elements loaded
        new_elements = await page.query_selector_all(selector)
        new_count = len(new_elements) if new_elements else 0
        
        if new_count == count:
            logger.debug(f"No new content after scroll {i + 1}/{max_scrolls}")
            break
    
    logger.debug(f"Scrolling complete, found {new_count if new_count else count} elements")
