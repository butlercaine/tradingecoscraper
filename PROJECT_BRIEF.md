# PROJECT BRIEF — Trading Economics Homepage Scraper

**Project ID:** PROJ-2026-0207-tradingecoscraper
**Domain:** Engineering
**Complexity:** 3/5
**Created:** 2026-02-07
**Status:** Pending Gate 1 Approval

---

## 1. Overview

Build a Python web scraper to extract **100 data points** from the Trading Economics homepage (`https://www.tradingeconomics.com`). The scraper must collect data across 7 categories: Commodities, Stock Indexes, Major Stocks, Forex, Government Bonds, Crypto, and Country Macro Indicators — plus headline news.

**Key Requirements:**
- Extract exactly 100 data points as defined in the spec
- Parse HTML tables and panels using BeautifulSoup4
- Support fallback to headless browser (Playwright) for JS-rendered content
- Output structured JSON with validation
- Include error handling, retry logic, and robots.txt compliance

---

## 2. Scope

### In Scope
- 6 market panels (84 instruments: commodities, indexes, stocks, forex, bonds, crypto)
- 13-country macro indicators matrix
- 3 headline news articles
- HTML parsing with BeautifulSoup4 + lxml
- Playwright fallback for JS-rendered panels
- JSON output with Pydantic validation
- Unit tests with HTML fixtures

### Out of Scope
- Scheduled execution (APScheduler/cron) — scraper runs on-demand
- CSV/SQLite output (JSON only for v1)
- Data storage or database layer
- Commercial data redistribution

---

## 3. Technical Stack

| Component | Choice |
|-----------|--------|
| Language | Python 3.10+ |
| HTTP Client | httpx |
| HTML Parser | BeautifulSoup4 + lxml |
| JS Rendering | Playwright (fallback only) |
| Validation | Pydantic |
| Testing | pytest + fixtures |

---

## 4. Deliverables

```
trading_economics_scraper/
├── config.py
├── scraper.py
├── parsers/
│   ├── markets.py
│   ├── macro.py
│   └── headlines.py
├── models.py
├── utils.py
├── tests/
│   ├── test_parsers.py
│   └── fixtures/
│       └── homepage.html
├── requirements.txt
└── README.md
```

**Plus:**
- `tradingeconomics.json` — Sample output file
- Git repo committed to `butlercaine/tradingecoscraper`

---

## 5. Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| Market panels | 6 panels × 14 rows = 84 instruments |
| Macro indicators | 13 countries × 9 fields = 117 values |
| Headlines | 3 articles with title, summary, timestamp, URL |
| Total data points | 100 (per spec definition) |
| Validation | Pydantic model passes for all fields |
| Tests | ≥80% coverage, all parser tests pass |
| Committed | Clean git history, tagged release v1.0.0 |

---

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Site structure changes | High | DOM selector alerts; manual review flag |
| JS-rendered panels | Medium | Playwright fallback with selector detection |
| Rate limiting | Medium | 5s delay, User-Agent rotation, retry logic |
| ToS violation | Legal | Review robots.txt, limit frequency, no redistribution |

---

## 7. Team Composition (Requested)

- **Project Lead** — decomposition & architecture
- **Python Developer** — implementation
- **QA Engineer** — validation & tests
- **Git Commit Agent** — version control & release
- **Scribe** — decisions & documentation

---

## 8. Timeline Estimate

| Phase | Duration |
|-------|----------|
| Team Assembly | ~5 min |
| Decomposition | ~10 min |
| Implementation | ~45-60 min |
| QA & Validation | ~15 min |
| Commit & Release | ~5 min |
| **Total** | **~90 min** |

---

**Prepared by:** Caine (Orchestrator)
**For Approval:** Human Operator

---

*Gate 1: Approve PROJECT_BRIEF and proceed to Phase 3 (TEAM_ASSEMBLY)*
