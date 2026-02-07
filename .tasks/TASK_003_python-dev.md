# TASK_003 — Pydantic Data Models

**Project:** PROJ-2026-0207-tradingecoscraper
**Assignee:** python-cli-dev
**Created:** 2026-02-07

## Description

Create `models.py` with Pydantic models for all scraped data: MarketInstrument, MacroIndicator, NewsArticle, and TradingEconomicsOutput. Include validation for all fields.

## Files to Create/Modify

- `~/Projects/tradingecoscraper/models.py` — MarketInstrument, MacroIndicator, NewsArticle, TradingEconomicsOutput

## Dependencies

TASK_001

## Acceptance Criteria

- [ ] `MarketInstrument`: symbol, name, value, change, pct_change, category
- [ ] `MacroIndicator`: country, indicator_name, value, previous, unit, timestamp
- [ ] `NewsArticle`: title, summary, timestamp, url
- [ ] `TradingEconomicsOutput`: markets (6 lists), macro (13 countries), headlines (3), metadata
- [ ] All models pass Pydantic validation

## Output

Write RESPONSE file to: `~/Projects/tradingecoscraper/.tasks/TASK_003_RESPONSE.md`
