# CHANGELOG.md

# Changelog

## v1.1.0 (2026-02-07)

### Added
- ETFs parser (`parsers/etfs.py`) - 10+ ETFs (SPY, QQQ, IWM, VTI, VOO, etc.)
- Derivatives parser (`parsers/derivatives.py`) - VIX, S&P futures, and more

### Fixed
- URL regex in `models.py` - Updated for Python 3.14 compatibility
- Test fixtures - Regenerated to match actual DOM structure

### Changed
- `config.py` - Added ETFs and Derivatives selectors
- `models.py` - Added ETFS and DERIVATIVES to MarketCategory enum

---

## v1.0.0 (2026-02-07)

### Added
- Test suite with pytest (`tests/`)
- JSON export of scraped data (`tradingeconomics.json`)
- Complete README documentation
- `pyproject.toml` for modern Python packaging
- `DECISIONS.md` documenting architectural choices
- `uv.lock` for reproducible dependencies

### Changed
- Updated from requirements.txt to uv/pip + pyproject.toml

### Known Issues (Post-Release)
- URL regex in `models.py` requires Python 3.14 for full compatibility
- Test fixtures need regeneration to match actual DOM structure

### Full Changelog
- M1: Multi-source finance scraper with newspaper3k, yfinance, BeautifulSoup
- M2: Tests, JSON export, documentation, modern Python project structure

---

**Repository:** https://github.com/butlercaine/tradingecoscraper
