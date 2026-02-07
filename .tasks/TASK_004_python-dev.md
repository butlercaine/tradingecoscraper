# TASK_004 — Market Panels Parser

**Project:** PROJ-2026-0207-tradingecoscraper
**Assignee:** python-cli-dev
**Created:** 2026-02-07

## Description

Build `parsers/markets.py` to parse 6 market panels (Commodities, Stock Indexes, Major Stocks, Forex, Government Bonds, Crypto) from HTML. Each panel returns list of `MarketInstrument` objects.

## Files to Create/Modify

- `~/Projects/tradingecoscraper/parsers/__init__.py`
- `~/Projects/tradingecoscraper/parsers/markets.py` — parse_commodities, parse_indexes, parse_stocks, parse_forex, parse_bonds, parse_crypto

## Dependencies

TASK_002, TASK_003

## Acceptance Criteria

- [ ] 6 parser functions, each extracts: symbol, name, value, change, pct_change
- [ ] Uses BeautifulSoup4 with lxml parser
- [ ] Selectors from `config.SELECTORS`
- [ ] Returns `List[MarketInstrument]` for each category
- [ ] Graceful handling of missing rows/columns

## Output

Write RESPONSE file to: `~/Projects/tradingecoscraper/.tasks/TASK_004_RESPONSE.md`
