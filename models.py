"""
Pydantic Data Models for Trading Economics Scraper

Models for validated data structures:
    - MarketInstrument: Individual market data (forex, indices, commodities, etc.)
    - MacroIndicator: Macroeconomic data points
    - NewsArticle: News headlines and articles
    - TradingEconomicsOutput: Complete output container
"""

from datetime import datetime
from typing import List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class MarketCategory(str, Enum):
    """Categories for market instruments."""
    FOREX = "forex"
    INDICES = "indices"
    COMMODITIES = "commodities"
    BONDS = "bonds"
    CRYPTO = "crypto"
    STOCKS = "stocks"
    ETFs = "etfs"
    DERIVATIVES = "derivatives"


class CountryCode(str, Enum):
    """ISO 3166-1 alpha-2 country codes for macro indicators."""
    US = "US"
    UK = "UK"
    EU = "EU"
    JP = "JP"
    CN = "CN"
    DE = "DE"
    FR = "FR"
    IT = "IT"
    ES = "ES"
    CA = "CA"
    AU = "AU"
    BR = "BR"
    IN = "IN"


class MarketInstrument(BaseModel):
    """
    Model for a single market instrument/asset.
    
    Examples: EUR/USD, S&P 500, Gold, US 10Y Bond
    """
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Trading symbol (e.g., EURUSD, SPX, GOLD)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Full display name of the instrument"
    )
    value: float = Field(
        ...,
        description="Current market value"
    )
    change: Optional[float] = Field(
        default=None,
        description="Price change from previous close"
    )
    pct_change: Optional[float] = Field(
        default=None,
        ge=-100,
        le=100,
        description="Percentage change from previous close"
    )
    category: MarketCategory = Field(
        ...,
        description="Market category for grouping"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Data timestamp"
    )
    bid: Optional[float] = Field(
        default=None,
        description="Current bid price"
    )
    ask: Optional[float] = Field(
        default=None,
        description="Current ask price"
    )
    high: Optional[float] = Field(
        default=None,
        description="Day's high price"
    )
    low: Optional[float] = Field(
        default=None,
        description="Day's low price"
    )
    open: Optional[float] = Field(
        default=None,
        description="Opening price"
    )
    previous_close: Optional[float] = Field(
        default=None,
        description="Previous day's closing price"
    )
    
    @field_validator('symbol')
    @classmethod
    def symbol_must_be_valid(cls, v: str) -> str:
        """Validate symbol format."""
        if not re.match(r'^[A-Za-z0-9\-\.\/]+$', v):
            raise ValueError(f"Invalid symbol format: {v}")
        return v.upper()
    
    @model_validator(mode='after')
    def validate_change_consistency(self):
        """Ensure change and pct_change are consistent when both present."""
        if self.change is not None and self.pct_change is not None and self.previous_close:
            expected_pct = (self.change / self.previous_close) * 100
            if abs(self.pct_change - expected_pct) > 0.01:
                raise ValueError(
                    f"Inconsistent change values: change={self.change}, "
                    f"pct_change={self.pct_change}%, previous_close={self.previous_close}"
                )
        return self


class MacroIndicator(BaseModel):
    """
    Model for macroeconomic indicators.
    
    Examples: US GDP, EU Inflation, China PMI
    """
    country: CountryCode = Field(
        ...,
        description="ISO country code"
    )
    indicator_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the macroeconomic indicator"
    )
    value: Optional[float] = Field(
        default=None,
        description="Current indicator value"
    )
    previous: Optional[float] = Field(
        default=None,
        description="Previous period's value"
    )
    unit: str = Field(
        default="%",
        max_length=20,
        description="Unit of measurement (%, points, billions, etc.)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Data timestamp"
    )
    frequency: str = Field(
        default="monthly",
        max_length=20,
        description="Update frequency (daily, weekly, monthly, quarterly, yearly)"
    )
    source: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Data source organization"
    )
    actual: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Actual vs Expected indicator (better, worse, inline)"
    )
    forecast: Optional[float] = Field(
        default=None,
        description="Forecast/consensus value"
    )
    period: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Reporting period (e.g., Q4 2023, Jan 2024)"
    )
    
    @field_validator('indicator_name')
    @classmethod
    def indicator_name_must_be_valid(cls, v: str) -> str:
        """Clean and validate indicator name."""
        return v.strip()
    
    @field_validator('frequency')
    @classmethod
    def frequency_must_be_valid(cls, v: str) -> str:
        """Validate frequency value."""
        valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
        if v.lower() not in valid_frequencies:
            raise ValueError(f"Invalid frequency: {v}. Must be one of {valid_frequencies}")
        return v.lower()


class NewsArticle(BaseModel):
    """
    Model for news articles and headlines.
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Article headline"
    )
    summary: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Brief article summary"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Article publish time"
    )
    url: str = Field(
        ...,
        max_length=1000,
        description="Article URL"
    )
    source: Optional[str] = Field(
        default=None,
        max_length=100,
        description="News source name"
    )
    category: Optional[str] = Field(
        default=None,
        max_length=50,
        description="News category (economy, markets, policy, etc.)"
    )
    sentiment: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Sentiment classification (positive, negative, neutral)"
    )
    
    @field_validator('url')
    @classmethod
    def url_must_be_valid(cls, v: str) -> str:
        """Validate URL format."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:\S+(?::\S*)?@)?'  # optional user:pass@
            r'(?:'  # IP address exclusion
            r'(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}'
            r'(?:\.(?:[0-9]\d?|1\d\d|2[0-4]\d|25[0-5]))'  # IP address
            r'|'  # OR
            r'(?:(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})'  # domain name
            r')'
            r'(?::\d{2,5})?'  # optional port
            r'(?:[/?#][^\s]*)?$',  # optional path, query, fragment
            re.IGNORECASE
        )
        if not url_pattern.match(v):
            raise ValueError(f"Invalid URL format: {v}")
        return v
    
    @field_validator('sentiment')
    @classmethod
    def sentiment_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        """Validate sentiment value."""
        if v is None:
            return v
        valid_sentiments = ['positive', 'negative', 'neutral', 'bullish', 'bearish']
        if v.lower() not in valid_sentiments:
            raise ValueError(f"Invalid sentiment: {v}. Must be one of {valid_sentiments}")
        return v.lower()


class TradingEconomicsOutput(BaseModel):
    """
    Complete output model containing all scraped trading economics data.
    
    Structure mirrors TradingEconomics.com data sections:
    - Markets: Forex, Indices, Commodities, Bonds, Crypto, Stocks
    - Macroeconomics: 13 major economies
    - News: Market headlines, earnings, dividends
    """
    # Market Data - 6 categories
    forex: List[MarketInstrument] = Field(
        default_factory=list,
        description="Forex currency pairs"
    )
    indices: List[MarketInstrument] = Field(
        default_factory=list,
        description="Stock market indices"
    )
    commodities: List[MarketInstrument] = Field(
        default_factory=list,
        description="Commodity prices"
    )
    bonds: List[MarketInstrument] = Field(
        default_factory=list,
        description="Government bond yields"
    )
    crypto: List[MarketInstrument] = Field(
        default_factory=list,
        description="Cryptocurrency prices"
    )
    stocks: List[MarketInstrument] = Field(
        default_factory=list,
        description="Individual stock prices"
    )
    etfs: List[MarketInstrument] = Field(
        default_factory=list,
        description="ETF prices"
    )
    derivatives: List[MarketInstrument] = Field(
        default_factory=list,
        description="Futures and options data"
    )
    
    # Macroeconomic Data - 13 countries
    macro_us: List[MacroIndicator] = Field(
        default_factory=list,
        description="United States macroeconomic indicators"
    )
    macro_uk: List[MacroIndicator] = Field(
        default_factory=list,
        description="United Kingdom macroeconomic indicators"
    )
    macro_eu: List[MacroIndicator] = Field(
        default_factory=list,
        description="European Union macroeconomic indicators"
    )
    macro_jp: List[MacroIndicator] = Field(
        default_factory=list,
        description="Japan macroeconomic indicators"
    )
    macro_cn: List[MacroIndicator] = Field(
        default_factory=list,
        description="China macroeconomic indicators"
    )
    macro_de: List[MacroIndicator] = Field(
        default_factory=list,
        description="Germany macroeconomic indicators"
    )
    macro_fr: List[MacroIndicator] = Field(
        default_factory=list,
        description="France macroeconomic indicators"
    )
    macro_it: List[MacroIndicator] = Field(
        default_factory=list,
        description="Italy macroeconomic indicators"
    )
    macro_es: List[MacroIndicator] = Field(
        default_factory=list,
        description="Spain macroeconomic indicators"
    )
    macro_ca: List[MacroIndicator] = Field(
        default_factory=list,
        description="Canada macroeconomic indicators"
    )
    macro_au: List[MacroIndicator] = Field(
        default_factory=list,
        description="Australia macroeconomic indicators"
    )
    macro_br: List[MacroIndicator] = Field(
        default_factory=list,
        description="Brazil macroeconomic indicators"
    )
    macro_in: List[MacroIndicator] = Field(
        default_factory=list,
        description="India macroeconomic indicators"
    )
    
    # News Data - 3 categories
    market_headlines: List[NewsArticle] = Field(
        default_factory=list,
        description="Market news headlines"
    )
    earnings_announcements: List[NewsArticle] = Field(
        default_factory=list,
        description="Earnings announcements and results"
    )
    dividend_news: List[NewsArticle] = Field(
        default_factory=list,
        description="Dividend and payout news"
    )
    
    # Metadata
    metadata: dict = Field(
        default_factory=dict,
        description="Scraping metadata (timestamps, URLs, version)"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of errors encountered during scraping"
    )
    
    @model_validator(mode='after')
    def validate_total_macroeconomics(self):
        """Collect all macro indicators for convenience access."""
        # This is just for validation - actual aggregation happens at runtime
        return self
    
    def all_markets(self) -> List[MarketInstrument]:
        """Get all market instruments from all categories."""
        markets = []
        for attr in ['forex', 'indices', 'commodities', 'bonds', 'crypto', 'stocks', 'etfs', 'derivatives']:
            markets.extend(getattr(self, attr))
        return markets
    
    def all_macro_indicators(self) -> List[MacroIndicator]:
        """Get all macro indicators from all countries."""
        macros = []
        for attr in [a for a in dir(self) if a.startswith('macro_')]:
            macros.extend(getattr(self, attr))
        return macros
    
    def all_news(self) -> List[NewsArticle]:
        """Get all news articles from all categories."""
        news = []
        for attr in ['market_headlines', 'earnings_announcements', 'dividend_news']:
            news.extend(getattr(self, attr))
        return news
    
    def total_items(self) -> int:
        """Get total count of all items."""
        return (
            len(self.forex) + len(self.indices) + len(self.commodities) +
            len(self.bonds) + len(self.crypto) + len(self.stocks) +
            len(self.etfs) + len(self.derivatives) +
            len(self.all_macro_indicators()) +
            len(self.all_news())
        )
    
    def summary(self) -> dict:
        """Get a summary of the data."""
        return {
            "markets": {
                "forex": len(self.forex),
                "indices": len(self.indices),
                "commodities": len(self.commodities),
                "bonds": len(self.bonds),
                "crypto": len(self.crypto),
                "stocks": len(self.stocks),
                "etfs": len(self.etfs),
                "derivatives": len(self.derivatives),
            },
            "macroeconomics": {
                "US": len(self.macro_us),
                "UK": len(self.macro_uk),
                "EU": len(self.macro_eu),
                "Japan": len(self.macro_jp),
                "China": len(self.macro_cn),
                "Germany": len(self.macro_de),
                "France": len(self.macro_fr),
                "Italy": len(self.macro_it),
                "Spain": len(self.macro_es),
                "Canada": len(self.macro_ca),
                "Australia": len(self.macro_au),
                "Brazil": len(self.macro_br),
                "India": len(self.macro_in),
            },
            "news": {
                "market_headlines": len(self.market_headlines),
                "earnings": len(self.earnings_announcements),
                "dividends": len(self.dividend_news),
            },
            "total_items": self.total_items(),
            "errors": len(self.errors),
        }
