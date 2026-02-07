# DECISIONS.md - Architectural Decisions

> Project: tradingecoscraper | Last updated: 2026-02-07

## Purpose
Record significant architectural and implementation decisions for the trading economics scraper project.

---

## Template

```markdown
### YYYY-MM-DD | [Decision Title]

**Status:** [Proposed | Accepted | Deprecated]

**Context:**
<!-- What prompted this decision? -->

**Options Considered:**
- Option 1: [description]
- Option 2: [description]
- ...

**Decision:** [Chosen approach]
<!-- Include brief rationale -->

**Consequences:**
<!-- What changes? What trade-offs? -->

**References:**
- [Link or notes]
```

---

## Decisions

### 2026-02-07 | HTTP Client Selection (httpx over requests)

**Status:** Accepted

**Context:**
Need an HTTP client for fetching HTML pages from Trading Economics. The choice affects async support, timeout handling, and retry logic.

**Options Considered:**
- **Option A:** `requests` — Popular synchronous library, simple API
- **Option B:** `httpx` — Modern async support, requests-compatible API
- **Option C:** `aiohttp` — Low-level async HTTP, steeper learning curve
- **Option D:** `urllib.request` — Standard library, no external dependency

**Decision:** `httpx` with async support.

**Rationale:**
- Async support enables parallel fetching of multiple pages
- Requests-compatible API reduces learning curve
- Built-in timeout handling (`timeout=30.0`)
- Automatic retry via custom middleware or httpx extensions
- Modern Python 3.10+ type hints support
- Clean async/await syntax for pipeline orchestration

**Consequences:**
- Must install `httpx` dependency
- Async functions require event loop management
- Synchronous wrappers needed for CLI entry points
- Retry logic implemented as custom middleware or wrapper function

**References:**
- PROJECT_BRIEF.md (Technical Stack section)
- TASK_002_RESPONSE.md (HTTP Scraper Core)
- config.py (HTTP_TIMEOUT, RETRY_CONFIG)

---

### 2026-02-07 | HTML Parsing Strategy (BeautifulSoup4 + lxml)

**Status:** Accepted

**Context:**
Trading Economics uses HTML tables and panels for data display. Need reliable parsing that handles imperfect HTML.

**Options Considered:**
- **Option A:** Built-in `html.parser` — No external dependency, slower
- **Option B:** `lxml` — Fast C-based parsing, less forgiving of bad HTML
- **Option C:** `html5lib` — Most forgiving, very slow, heavy dependency
- **Option D:** BeautifulSoup4 with `lxml` parser — Best balance of speed and forgiveness

**Decision:** BeautifulSoup4 with `lxml` parser.

**Rationale:**
- BeautifulSoup provides convenient CSS selector access (`.select()`)
- `lxml` parser is significantly faster than `html.parser`
- BS4 handles malformed HTML gracefully
- CSS selectors are more readable than navigating the tree manually
- Industry standard for Python web scraping
- Good ecosystem for testing with fixtures

**Implementation:**
```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html_content, 'lxml')
elements = soup.select('.commodity-row .instrument-name')
```

**Consequences:**
- Additional dependency: `beautifulsoup4` and `lxml`
- `lxml` requires system-level library installation
- Parsing speed is good but not as fast as raw lxml
- Must handle selector changes if site redesigns

**References:**
- PROJECT_BRIEF.md (HTML Parser requirement)
- parsers/markets.py, parsers/macro.py, parsers/headlines.py

---

### 2026-02-07 | Playwright Fallback Trigger Condition

**Status:** Accepted

**Context:**
Some Trading Economics panels may use JavaScript to render content. Need a fallback strategy that doesn't add overhead for static pages.

**Options Considered:**
- **Option A:** Always use Playwright — Simple but slow
- **Option B:** URL-based detection — Check if known JS page, use Playwright selectively
- **Option C:** Selector-based detection — Try static first, fallback if selectors empty
- **Option D:** Response header analysis — Check for JS indicators in headers

**Decision:** Selector-based detection with `scrape_with_fallback()` function.

**Rationale:**
- Avoids Playwright overhead for static pages (~10x slower)
- Automatic detection: no hardcoded URL lists to maintain
- Graceful degradation: works with or without JavaScript
- Clear failure mode: empty selectors trigger fallback
- Configurable selectors per category

**Implementation Logic:**
```
1. Fetch static HTML with httpx
2. Check if expected selectors exist
3. If selectors found → return static HTML
4. If selectors empty → invoke Playwright
5. Return rendered HTML from Playwright
```

**Trigger Condition:**
```python
async def scrape_with_fallback(
    url: str,
    selectors_to_check: list[str],
    wait_for_selectors: Optional[list] = None,
) -> str:
    # Try static first
    static_html = await scrape_page(url)
    soup = BeautifulSoup(static_html, 'lxml')
    
    # Check if critical selectors exist
    if all(soup.select(sel) for sel in selectors_to_check):
        return static_html
    
    # Fallback to Playwright
    return await scrape_with_playwright(url, wait_for_selectors)
```

**Consequences:**
- Dual code path: static and Playwright
- Playwright must be installed (`pip install playwright`)
- Chromium browser must be installed (`playwright install chromium`)
- Slightly more complex error handling

**References:**
- TASK_008_RESPONSE.md (Playwright Fallback)
- scraper.py (scrape_with_fallback, scrape_with_playwright)

---

### 2026-02-07 | Pydantic Model Design Decisions

**Status:** Accepted

**Context:**
Need structured data models for validation, serialization, and type safety across the scraper.

**Design Decisions:**

#### 1. Base Model Hierarchy

**Decision:** Separate models for each domain (MarketInstrument, MacroIndicator, NewsArticle) with a container model (TradingEconomicsOutput).

**Rationale:**
- Separation of concerns: markets vs macro vs news
- Each model has appropriate fields and validators
- Container model aggregates all data
- Easier testing: can validate individual models

#### 2. Field Validation Strategy

**Decision:** Use Pydantic's `Field` with constraints and `@field_validator` for complex validation.

**Examples:**
```python
class MarketInstrument(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    value: float = ...
    
    @field_validator('symbol')
    @classmethod
    def symbol_must_be_valid(cls, v: str) -> str:
        if not re.match(r'^[A-Za-z0-9\-\.\/]+$', v):
            raise ValueError(f"Invalid symbol format: {v}")
        return v.upper()
```

**Rationale:**
- Type safety at model creation
- Self-documenting constraints via Field metadata
- Custom validators for domain-specific rules

#### 3. Optional vs Required Fields

**Decision:** Market-critical fields required, auxiliary fields optional.

**Rationale:**
- `symbol`, `name`, `value` required — can't have valid instrument without these
- `change`, `pct_change`, `bid`, `ask` optional — not always available
- `timestamp` defaults to `utcnow()` if not provided

**Field Classification:**
| Required | Optional |
|----------|----------|
| symbol | change |
| name | pct_change |
| value | bid |
| category | ask |
| | high |
| | low |
| | open |
| | previous_close |

#### 4. Enum Usage

**Decision:** Use Enums for categorical data with finite values.

**Examples:**
```python
class MarketCategory(str, Enum):
    FOREX = "forex"
    INDICES = "indices"
    COMMODITIES = "commodities"
    # ...

class CountryCode(str, Enum):
    US = "US"
    UK = "UK"
    # ...
```

**Rationale:**
- Prevents typos (IDE autocomplete)
- Self-documenting categories
- Type-safe comparisons

#### 5. Cross-Field Validation

**Decision:** Use `@model_validator` for consistency checks.

**Example:**
```python
@model_validator(mode='after')
def validate_change_consistency(self):
    if self.change is not None and self.pct_change is not None and self.previous_close:
        expected_pct = (self.change / self.previous_close) * 100
        if abs(self.pct_change - expected_pct) > 0.01:
            raise ValueError("Inconsistent change values")
    return self
```

**Rationale:**
- Catches data inconsistencies early
- Ensures data quality before output

**References:**
- models.py (full implementation)
- TASK_003_RESPONSE.md (Pydantic Data Models)

---

### 2026-02-07 | Selector Management Approach

**Status:** Accepted

**Context:**
Trading Economics HTML structure requires CSS selectors to extract data. Selectors must be manageable and recoverable if the site changes.

**Options Considered:**
- **Option A:** Hardcoded selectors in parser functions
- **Option B:** Selectors in a separate config file (JSON/YAML)
- **Option C:** Selectors in config.py as constants
- **Option D:** Database-backed selector storage

**Decision:** Centralized in `config.py` with SELECTORS dictionary.

**Implementation:**
```python
# config.py
SELECTORS = {
    "forex_table": ".forex-panel table.data-list",
    "forex_symbol": ".currency-pair .symbol",
    "forex_value": ".currency-pair .value",
    "commodities_table": ".commodities-panel .commodities-list",
    # ...
}
```

**Rationale:**
- Single source of truth for all selectors
- Easy to update without touching parser code
- Centralized in version-controlled config
- Parser functions reference SELECTORS keys
- Can add versioning for selector changes

**Selector Organization:**
```
SELECTORS
├── Market Selectors
│   ├── forex_*
│   ├── indices_*
│   ├── commodities_*
│   ├── bonds_*
│   ├── crypto_*
│   └── stocks_*
├── Macro Selectors
│   ├── macro_table
│   ├── macro_country_row
│   └── macro_indicator_*
└── News Selectors
    ├── headlines_list
    ├── headline_item
    └── headline_title
```

**Consequences:**
- Selectors co-located with other config
- Parser functions remain focused on logic
- Easy to add new selectors
- Risk: if site changes, all selectors may need updates

**Selector Fallback Strategy:**
1. Primary selectors from config.py
2. If parsing fails, log which selector failed
3. Document selector changes in changelog
4. Consider selector version in metadata

**References:**
- config.py (SELECTORS dictionary)
- parsers/markets.py
- parsers/macro.py
- parsers/headlines.py

---

## Change Log

| Date | Decision | Status |
|------|----------|--------|
| 2026-02-07 | HTTP Client Selection (httpx) | Accepted |
| 2026-02-07 | HTML Parsing Strategy (BS4 + lxml) | Accepted |
| 2026-02-07 | Playwright Fallback Trigger | Accepted |
| 2026-02-07 | Pydantic Model Design | Accepted |
| 2026-02-07 | Selector Management Approach | Accepted |

---

## Appendix A: Configuration Reference

```python
# config.py - Key Settings
HTTP_TIMEOUT = 30.0  # seconds per request
RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 0.5,
    "status_forcelist": [429, 500, 502, 503, 504],
}
RATE_LIMIT_DELAY = 5.0  # seconds between requests
USER_AGENTS = [...]  # 5 rotating user agents
SELECTORS = {...}  # Centralized CSS selectors
```

## Appendix B: Dependencies

```txt
# requirements.txt
httpx>=0.25.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
pydantic>=2.5.0
playwright>=1.40.0  # Optional, fallback only
```

---

*Documented by: scribe*
*Project: PROJ-2026-0207-tradingecoscraper*
*Last update: 2026-02-07*
