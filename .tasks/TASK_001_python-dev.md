# TASK_001 — Project Setup + Configuration

**Project:** PROJ-2026-0207-tradingecoscraper
**Assignee:** python-cli-dev
**Created:** 2026-02-07

## Description

Create Python project structure with `config.py` containing HTTP settings, selectors, User-Agent rotation, rate limiting (5s delay), and retry configuration. Set up `requirements.txt` with all dependencies.

## Files to Create/Modify

- `~/Projects/tradingecoscraper/config.py` — HTTP timeout, retries, delay, selectors dict, UA list
- `~/Projects/tradingecoscraper/requirements.txt` — httpx, beautifulsoup4, lxml, playwright, pydantic, pytest
- `~/Projects/tradingecoscraper/.gitignore` — venv/, *.pyc, __pycache__/, .pytest_cache/

## Dependencies

None

## Acceptance Criteria

- [ ] `config.py` exports: `HEADERS`, `RETRY_CONFIG`, `SELECTORS`, `RATE_LIMIT_DELAY`
- [ ] `requirements.txt` contains all dependencies with version constraints
- [ ] Python 3.10+ compatible

## Output

Write RESPONSE file to: `~/Projects/tradingecoscraper/.tasks/TASK_001_RESPONSE.md`
