# Trading Economics Scraper

A production-ready Python scraper for extracting market data, macroeconomic indicators, and news from TradingEconomics.com.

## Features

- **Market Data**: Forex, indices, commodities, bonds, crypto, stocks
- **Macroeconomics**: GDP, inflation, unemployment, interest rates for 13 countries
- **News**: Market headlines, earnings announcements, dividend news
- **Robust**: Retry logic, rate limiting, robots.txt compliance
- **JavaScript Support**: Playwright fallback for dynamic content
- **Type Safety**: Pydantic models for validation
- **Testing**: Comprehensive test suite with fixtures

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/tradingecoscraper.git
cd tradingecoscraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for JS-rendered pages)
playwright install chromium

# Or install all browsers
playwright install
```

### Dependencies

Core dependencies (see `requirements.txt`):

```
httpx>=0.25.0          # Async HTTP client with HTTP/2
beautifulsoup4>=4.12.0 # HTML parsing
lxml>=4.9.0            # Fast XML/HTML parser
playwright>=1.40.0     # Browser automation
pydantic>=2.5.0        # Data validation
pytest>=7.4.0          # Testing framework
```

Optional:
```
pytest-cov>=4.1.0      # Coverage reporting
```

## Usage

### Command Line

```bash
# Run with default settings (prints summary to stdout)
python -m tradingecoscraper

# Save output to JSON file
python -m tradingecoscraper --output tradingeconomics.json

# Verbose mode with file output
python -m tradingecoscraper --verbose --output data.json

# Show help
python -m tradingecoscraper --help
```

### Programmatic Usage

```python
import asyncio
from scraper import run_pipeline

async def main():
    # Run full pipeline
    output = await run_pipeline(
        output_path="tradingeconomics.json",
        verbose=True
    )
    
    # Access parsed data
    print(f"Total items: {output.total_items()}")
    print(output.summary())
    
    # Access specific markets
    for forex in output.forex:
        print(f"{forex.symbol}: {forex.value}")
    
    # Access macro indicators
    for indicator in output.macro_us:
        print(f"{indicator.indicator_name}: {indicator.value}{indicator.unit}")
    
    # Access news
    for article in output.market_headlines:
        print(f"{article.title} ({article.url})")

asyncio.run(main())
```

### Simple Scraper

```python
from scraper import scrape_page
from parsers.markets import parse_forex
from parsers.macro import parse_macro_indicators
from parsers.headlines import parse_headlines

async def main():
    # Fetch a page
    html = await scrape_page("https://tradingeconomics.com/forex")
    
    # Parse data
    forex = parse_forex(html)
    print(f"Found {len(forex)} forex instruments")
    
    for item in forex[:5]:
        print(f"  {item.symbol}: {item.value} ({item.pct_change}%)")

asyncio.run(main())
```

### Playwright Fallback

For JavaScript-rendered pages:

```python
from scraper import scrape_with_fallback

async def main():
    html = await scrape_with_fallback(
        url="https://tradingeconomics.com/stocks",
        selectors_to_check=[".stock-list", ".price-ticker"],
        wait_for_selectors=[".vue-component", "[data-ssr]"],
    )
    print(f"Fetched {len(html)} bytes")

asyncio.run(main())
```

## Configuration

Configuration is managed in `config.py`:

```python
# HTTP Settings
HTTP_TIMEOUT = 30.0          # Request timeout in seconds
RATE_LIMIT_DELAY = 5.0       # Delay between requests

# Retry Configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 0.5,
    "status_forcelist": [429, 500, 502, 503, 504],
}

# User-Agent Rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ...",
    # ...
]

# Page Selectors (for BeautifulSoup)
SELECTORS = {
    "product_list": ".product-item, .product-card",
    "product_name": ".product-title, .name",
    "product_price": ".price, .amount",
    # ...
}
```

### Environment Variables

```bash
# Override settings via environment
export HTTP_TIMEOUT=60.0
export RATE_LIMIT_DELAY=10.0
```

## Architecture

```
tradingecoscraper/
├── __main__.py           # CLI entry point
├── config.py             # Configuration (HTTP, retry, selectors)
├── models.py             # Pydantic data models
├── scraper.py            # HTTP client + Playwright fallback
├── utils.py              # Playwright utilities
├── requirements.txt      # Python dependencies
├── tradingeconomics.json # Sample output
│
├── parsers/              # HTML parsing modules
│   ├── __init__.py
│   ├── markets.py        # 6 market parsers
│   ├── macro.py          # 13-country macro parser
│   └── headlines.py      # News parser
│
├── tests/                # Test suite
│   ├── __init__.py
│   ├── conftest.py       # Pytest fixtures
│   ├── test_parsers.py   # Parser tests
│   └── fixtures/
│       └── homepage.html # Test HTML fixture
│
└── .tasks/               # Task documentation
```

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    main() Entry Point                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. HTTP Request (httpx) with retry & rate limiting        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Robots.txt Compliance Check                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. BeautifulSoup Parsing                                  │
│     - Markets (6 categories)                               │
│     - Macro (13 countries)                                 │
│     - Headlines (3 categories)                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Pydantic Validation                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. JSON Output                                            │
└─────────────────────────────────────────────────────────────┘
```

### Fallback Flow

```
Static HTML Empty?
     │
     ├── Yes → Playwright Render
     │           │
     └── No → Use Static HTML
```

## API Reference

### Scraper Functions

#### `scrape_page(url: str) -> str`
Fetch a URL and return HTML content.

```python
html = await scrape_page("https://tradingeconomics.com/forex")
```

#### `scrape_with_playwright(url: str) -> str`
Fetch a URL using Playwright for JS-rendered pages.

```python
html = await scrape_with_playwright("https://example.com/page")
```

#### `scrape_with_fallback(url: str, selectors_to_check: list) -> str`
Smart scraping: try static first, fallback to Playwright.

```python
html = await scrape_with_fallback(
    url="https://tradingeconomics.com/stocks",
    selectors_to_check=[".stock-list", ".price"],
)
```

#### `run_pipeline(output_path: str) -> TradingEconomicsOutput`
Run the complete scraping pipeline.

```python
output = await run_pipeline(output_path="data.json")
```

### Parsers

#### Market Parsers

```python
from parsers.markets import (
    parse_forex,
    parse_indexes,
    parse_commodities,
    parse_bonds,
    parse_crypto,
    parse_stocks,
)

forex = parse_forex(html)      # List[MarketInstrument]
indices = parse_indexes(html)   # List[MarketInstrument]
```

#### Macro Parser

```python
from parsers.macro import parse_macro_indicators

macro = parse_macro_indicators(html)
# Returns: Dict[str, List[MacroIndicator]]
# Keys: "US", "UK", "EU", "JP", "CN", "DE", "FR", "IT", "ES", "CA", "AU", "BR", "IN"
```

#### Headlines Parser

```python
from parsers.headlines import parse_headlines, parse_all_news_categories

headlines = parse_headlines(html)              # List[NewsArticle]
categories = parse_all_news_categories(html)   # Dict with market_headlines, earnings, dividends
```

### Models

#### `MarketInstrument`
```python
{
    "symbol": str,           # Trading symbol (e.g., "EURUSD")
    "name": str,             # Full name
    "value": float,          # Current price/yield
    "change": Optional[float],  # Daily change
    "pct_change": Optional[float],  # Percentage change
    "category": MarketCategory,  # FOREX, INDICES, COMMODITIES, BONDS, CRYPTO, STOCKS
    "timestamp": datetime,
    "bid": Optional[float],
    "ask": Optional[float],
    "high": Optional[float],
    "low": Optional[float],
}
```

#### `MacroIndicator`
```python
{
    "country": CountryCode,   # US, UK, EU, JP, CN, DE, FR, IT, ES, CA, AU, BR, IN
    "indicator_name": str,    # e.g., "GDP Growth", "Inflation Rate"
    "value": Optional[float],
    "previous": Optional[float],
    "unit": str,             # e.g., "%", "points"
    "frequency": str,        # daily, weekly, monthly, quarterly, yearly
    "source": Optional[str],
}
```

#### `NewsArticle`
```python
{
    "title": str,
    "summary": Optional[str],
    "timestamp": datetime,
    "url": str,
    "source": Optional[str],
    "category": Optional[str],
    "sentiment": Optional[str],  # positive, negative, neutral
}
```

#### `TradingEconomicsOutput`
Main container model with all parsed data.

```python
output = TradingEconomicsOutput(
    forex=[...],
    indices=[...],
    commodities=[...],
    bonds=[...],
    crypto=[...],
    stocks=[...],
    macro_us=[...],
    macro_uk=[...],
    # ... all 13 countries
    market_headlines=[...],
    earnings_announcements=[...],
    dividend_news=[...],
    metadata={...},
    errors=[...],
)

# Methods
output.total_items()      # Total count of all items
output.summary()          # Dict with counts by category
output.all_markets()      # List of all market instruments
output.all_macro_indicators()  # List of all macro indicators
output.all_news()         # List of all news articles
```

### Exceptions

```python
from scraper import ScraperError, RobotsTxtError, RequestError

try:
    html = await scrape_page(url)
except RobotsTxtError:
    print("URL blocked by robots.txt")
except RequestError:
    print("Request failed after retries")
except ScraperError as e:
    print(f"Scraping error: {e}")
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run specific test class
pytest tests/test_parsers.py::TestForexParser -v

# Run specific test
pytest tests/test_parsers.py::TestForexParser::test_parse_forex_returns_list -v
```

### Test Coverage

| Module | Coverage Target |
|--------|-----------------|
| parsers/markets.py | 90% |
| parsers/macro.py | 85% |
| parsers/headlines.py | 85% |
| models.py | 100% |
| **Overall** | **≥80%** |

## Error Handling

The scraper handles several error types:

| Error Type | Cause | Handling |
|------------|-------|----------|
| `RobotsTxtError` | Blocked by robots.txt | Logged, continues with next URL |
| `RequestError` | Network failure after retries | Logged, item skipped |
| `ScraperError` | General scraping error | Logged, may fallback to Playwright |
| `ValidationError` | Pydantic validation failed | Item skipped |

All errors are collected in `output.errors` for review.

## Rate Limiting & Ethics

- **5-second delay** between requests to each domain
- **User-Agent rotation** to distribute load
- **robots.txt compliance** - checks before scraping
- **Retry with backoff** on rate limit (429) responses

Please respect TradingEconomics.com's terms of service and `robots.txt`.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure tests pass and coverage maintained
5. Submit a pull request

## Changelog

### v1.0.0 (2026-02-07)
- Initial release
- 6 market parsers
- 13-country macro parser
- News headlines parser
- Playwright fallback for JS content
- Pydantic validation
- Comprehensive test suite
