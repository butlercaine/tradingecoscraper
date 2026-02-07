# TASK_005 — Country Macro Indicators Parser

**Project:** PROJ-2026-0207-tradingecoscraper
**Assignee:** python-cli-dev
**Created:** 2026-02-07

## Description

Build `parsers/macro.py` to parse the 13-country macro indicators matrix from HTML. Extract 9 fields per country (GDP, Inflation, Unemployment, etc.) into `MacroIndicator` objects.

## Files to Create/Modify

- `~/Projects/tradingecoscraper/parsers/macro.py` — parse_macro_indicators

## Dependencies

TASK_002, TASK_003

## Acceptance Criteria

- [ ] Parses 13 countries: US, UK, Germany, France, China, Japan, India, Brazil, etc.
- [ ] Each country: 9 indicator fields
- [ ] Returns `Dict[str, List[MacroIndicator]]` (country → indicators)
- [ ] Handles missing/unavailable values gracefully

## Output

Write RESPONSE file to: `~/Projects/tradingecoscraper/.tasks/TASK_005_RESPONSE.md`
