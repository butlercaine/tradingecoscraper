"""
Playwright Utilities

Helper functions for advanced Playwright browser automation.
"""

from typing import List, Optional
from playwright.sync_api import Page, Browser, BrowserContext
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


@contextmanager
def get_browser_context(
    headless: bool = True,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    user_agent: Optional[str] = None,
):
    """
    Context manager for Playwright browser and context.
    
    Args:
        headless: Run in headless mode (default True for CI/CD)
        viewport_width: Browser viewport width
        viewport_height: Browser viewport height
        user_agent: Custom User-Agent string
        
    Yields:
        Tuple of (page, browser)
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "Playwright is not installed. "
            "Install with: pip install playwright && playwright install"
        )
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
            ],
        )
        
        context = browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent=user_agent or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        
        page = context.new_page()
        
        try:
            yield page, browser, context
        finally:
            context.close()
            browser.close()


def scrape_page_sync(
    url: str,
    wait_for_selectors: Optional[List[str]] = None,
    wait_timeout_ms: int = 30000,
) -> str:
    """
    Synchronous Playwright page scraper.
    
    Args:
        url: URL to scrape
        wait_for_selectors: List of selectors to wait for
        wait_timeout_ms: Timeout in milliseconds
        
    Returns:
        Page HTML content
    """
    logger.info(f"Scraping with Playwright: {url}")
    
    with get_browser_context() as (page, browser, context):
        # Navigate
        page.goto(url, wait_until="networkidle", timeout=wait_timeout_ms)
        
        # Wait for selectors
        if wait_for_selectors:
            for selector in wait_for_selectors:
                try:
                    page.wait_for_selector(
                        selector,
                        timeout=wait_timeout_ms,
                        state="attached",
                    )
                except Exception as e:
                    logger.warning(f"Selector '{selector}' not found: {e}")
        
        return page.content()


def wait_for_ajax(page: Page, timeout_ms: int = 10000) -> None:
    """
    Wait for all AJAX requests to complete.
    
    Args:
        page: Playwright page object
        timeout_ms: Maximum wait time
    """
    page.wait_for_load_state("networkidle", timeout=timeout_ms)


def extract_dynamic_table(
    page: Page,
    table_selector: str,
    header_selector: str = "th",
    row_selector: str = "tr",
) -> List[dict]:
    """
    Extract data from a dynamically loaded table.
    
    Args:
        page: Playwright page object
        table_selector: CSS selector for the table
        header_selector: Selector for table headers
        row_selector: Selector for table rows
        
    Returns:
        List of dictionaries with row data
    """
    table = page.query_selector(table_selector)
    if not table:
        return []
    
    # Extract headers
    headers = []
    header_elements = table.query_selector_all(header_selector)
    for header in header_elements:
        headers.append(header.inner_text().strip())
    
    # Extract rows
    rows = []
    row_elements = table.query_selector_all(row_selector)
    for row in row_elements:
        row_data = {}
        cells = row.query_selector_all("td")
        for i, cell in enumerate(cells):
            if i < len(headers):
                row_data[headers[i]] = cell.inner_text().strip()
        if row_data:
            rows.append(row_data)
    
    return rows


def handle_cookie_banner(
    page: Page,
    accept_selector: str = "[class*='cookie'] button, [id*='cookie'] button",
) -> bool:
    """
    Try to accept/close cookie banners.
    
    Args:
        page: Playwright page object
        accept_selector: Selector for accept button
        
    Returns:
        True if banner was handled, False otherwise
    """
    try:
        button = page.query_selector(accept_selector)
        if button:
            button.click()
            logger.debug("Accepted cookie banner")
            return True
    except Exception as e:
        logger.debug(f"Cookie banner not found or couldn't be clicked: {e}")
    return False


def take_screenshot(
    page: Page,
    path: str,
    full_page: bool = False,
) -> None:
    """
    Take a screenshot of the page.
    
    Args:
        page: Playwright page object
        path: File path to save screenshot
        full_page: Capture full page or just viewport
    """
    page.screenshot(path=path, full_page=full_page)
    logger.info(f"Screenshot saved to {path}")


class PlaywrightPool:
    """
    Simple pool for reusing Playwright browser instances.
    
    Useful for batch scraping operations.
    """
    
    def __init__(self, size: int = 2, headless: bool = True):
        """
        Initialize pool.
        
        Args:
            size: Number of browser instances
            headless: Run in headless mode
        """
        from playwright.sync_api import sync_playwright
        
        self.size = size
        self.headless = headless
        self.playwright = sync_playwright().start()
        self.browsers: List[Browser] = []
        
        # Pre-launch browsers
        for _ in range(size):
            browser = self.playwright.chromium.launch(
                headless=headless,
                args=["--no-sandbox"],
            )
            self.browsers.append(browser)
    
    def get_browser(self) -> Browser:
        """Get a browser from the pool."""
        if self.browsers:
            return self.browsers.pop()
        
        # Create new if pool exhausted
        return self.playwright.chromium.launch(headless=self.headless)
    
    def return_browser(self, browser: Browser) -> None:
        """Return a browser to the pool."""
        if len(self.browsers) < self.size:
            self.browsers.append(browser)
        else:
            browser.close()
    
    def close(self) -> None:
        """Close all browsers and Playwright."""
        for browser in self.browsers:
            browser.close()
        self.playwright.stop()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
