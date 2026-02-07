# TASK_007 — Main Scraper Orchestrator

**Project:** PROJ-2026-0207-tradingecoscraper
**Assignee:** python-cli-dev
**Created:** 2026-02-07

## Description

Create `scraper.py` main function or `__main__.py` that orchestrates: fetch HTML → parse markets → parse macro → parse headlines → validate with Pydantic → output structured dict.

## Files to Create/Modify

- `~/Projects/tradingecoscraper/__main__.py` — main() entry point
- `~/Projects/tradingecoscraper/scraper.py` — orchestrate function (append to existing)

## Dependencies

TASK_002, TASK_004, TASK_005, TASK_006

## Acceptance Criteria

- [ ] `main()`: fetch → parse all → validate → print JSON
- [ ] Output to `tradingeconomics.json` with `--output` flag
- [ ] Exit code 0 on success, 1 on error
- [ ] Logging for progress and errors

## Output

Write RESPONSE file to: `~/Projects/tradingecoscraper/.tasks/TASK_007_RESPONSE.md`
