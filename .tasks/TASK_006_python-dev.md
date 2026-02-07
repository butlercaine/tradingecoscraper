# TASK_006 — Headlines Parser

**Project:** PROJ-2026-0207-tradingecoscraper
**Assignee:** python-cli-dev
**Created:** 2026-02-07

## Description

Build `parsers/headlines.py` to parse 3 headline news articles from HTML. Extract title, summary, timestamp, and URL into `NewsArticle` objects.

## Files to Create/Modify

- `~/Projects/tradingecoscraper/parsers/headlines.py` — parse_headlines

## Dependencies

TASK_002, TASK_003

## Acceptance Criteria

- [ ] Extracts exactly 3 articles (or fewer if unavailable)
- [ ] Fields: title (str), summary (str), timestamp (datetime), url (str)
- [ ] Returns `List[NewsArticle]`
- [ ] Handles missing summary or timestamp

## Output

Write RESPONSE file to: `~/Projects/tradingecoscraper/.tasks/TASK_006_RESPONSE.md`
