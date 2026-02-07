# TASK_008 — Playwright Fallback for JS-Rendered Content

**Project:** PROJ-2026-0207-tradingecoscraper
**Assignee:** python-cli-dev
**Created:** 2026-02-07

## Description

Implement Playwright fallback in `scraper.py` for panels that require JS rendering. Detect JS-rendered panels via selector check; if static HTML fails, use Playwright to get rendered page.

## Files to Create/Modify

- `~/Projects/tradingecoscraper/scraper.py` — add `scrape_with_playwright()`
- `~/Projects/tradingecoscraper/utils.py` — playwright helper if needed

## Dependencies

TASK_002

## Acceptance Criteria

- [ ] `scrape_with_playwright(url: str) -> str` returns rendered HTML
- [ ] Playwright only invoked when BeautifulSoup finds empty selectors
- [ ] Browser properly closed after use (context manager)
- [ ] Headless mode configured for CI/CD

## Output

Write RESPONSE file to: `~/Projects/tradingecoscraper/.tasks/TASK_008_RESPONSE.md`
