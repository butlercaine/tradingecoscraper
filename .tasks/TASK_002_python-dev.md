# TASK_002 — HTTP Scraper Core + Robots.txt Compliance

**Project:** PROJ-2026-0207-tradingecoscraper
**Assignee:** python-cli-dev
**Created:** 2026-02-07

## Description

Build `scraper.py` with httpx client, async support, retry logic (3 attempts), rate limiting, robots.txt parsing/checking, and error handling. Exports `scrape_page(url: str) -> str`.

## Files to Create/Modify

- `~/Projects/tradingecoscraper/scraper.py` — httpx client class, retry decorator, robots.txt check, error handling

## Dependencies

TASK_001

## Acceptance Criteria

- [ ] `scrape_page()` returns HTML string, raises `ScraperError` on failure
- [ ] Respects robots.txt (check before scraping)
- [ ] 3 retries with exponential backoff on 5xx errors
- [ ] 5-second delay between requests (configurable)
- [ ] User-Agent header rotates or uses realistic UA

## Output

Write RESPONSE file to: `~/Projects/tradingecoscraper/.tasks/TASK_002_RESPONSE.md`
