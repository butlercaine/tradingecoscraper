# TASK_012 — HTML Fixtures + Unit Tests

**Project:** PROJ-2026-0207-tradingecoscraper
**Assignee:** python-cli-dev
**Created:** 2026-02-07

## Description

Create `tests/fixtures/homepage.html` with sample HTML for testing. Write `tests/test_parsers.py` with ≥80% coverage testing all parsers with fixtures.

## Files to Create/Modify

- `~/Projects/tradingecoscraper/tests/__init__.py`
- `~/Projects/tradingecoscraper/tests/fixtures/homepage.html`
- `~/Projects/tradingecoscraper/tests/test_parsers.py`
- `~/Projects/tradingecoscraper/tests/conftest.py` — pytest fixtures

## Dependencies

TASK_004, TASK_005, TASK_006

## Acceptance Criteria

- [ ] `homepage.html` contains representative HTML for all 6 panels + macro + headlines
- [ ] Tests cover: markets parser, macro parser, headlines parser, model validation
- [ ] Coverage ≥80% (run `pytest --cov`)
- [ ] All tests pass

## Output

Write RESPONSE file to: `~/Projects/tradingecoscraper/.tasks/TASK_012_RESPONSE.md`
