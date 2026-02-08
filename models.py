"""
Pydantic Data Models for Trading Economics Scraper

Models for validated data structures.
"""

from datetime import datetime
from typing import List, Optional
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
    ETFS = "etfs"
    DERIVATIVES = "derivatives"


class CountryCode(str, Enum):
    """ISO 3166-1 alpha-2 country codes."""
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


# SIMPLIFIED URL PATTERN (Python 3.10-3.14 compatible)
URL_PATTERN = re.compile(
    r'^https?://[\w.-]+(?:\.[\w-]+)+(?:/\S*)?$',
    re.IGNORECASE
)


class MarketInstrument(BaseModel):
    """Model for a single market instrument/asset."""
    symbol: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    value: float = Field(...)
    change: Optional[float] = None
    pct_change: Optional[float] = Field(None, ge=-100, le=100)
    category: MarketCategory = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    bid: Optional[float] = None
    ask: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    previous_close: Optional[float] = None

    @field_validator('symbol')
    @classmethod
    def symbol_must_be_valid(cls, v: str) -> str:
        if not re.match(r'^[A-Za-z0-9\-\.\/]+$', v):
            raise ValueError(f"Invalid symbol format: {v}")
        return v.upper()


class MacroIndicator(BaseModel):
    """Model for macroeconomic indicators."""
    country: CountryCode = Field(...)
    indicator_name: str = Field(..., min_length=1, max_length=100)
    value: Optional[float] = None
    previous: Optional[float] = None
    unit: str = Field(default="%", max_length=20)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    frequency: str = Field(default="monthly", max_length=20)
    source: Optional[str] = Field(None, max_length=100)
    actual: Optional[str] = Field(None, max_length=20)
    forecast: Optional[float] = None
    period: Optional[str] = Field(None, max_length=50)

    @field_validator('frequency')
    @classmethod
    def frequency_must_be_valid(cls, v: str) -> str:
        valid = ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
        if v.lower() not in valid:
            raise ValueError(f"Invalid frequency: {v}")
        return v.lower()


class NewsArticle(BaseModel):
    """Model for news articles."""
    title: str = Field(..., min_length=1, max_length=500)
    summary: Optional[str] = Field(None, max_length=2000)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    url: str = Field(..., max_length=1000)
    source: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    sentiment: Optional[str] = Field(None, max_length=20)

    @field_validator('url')
    @classmethod
    def url_must_be_valid(cls, v: str) -> str:
        if not URL_PATTERN.match(v):
            raise ValueError(f"Invalid URL format: {v}")
        return v

    @field_validator('sentiment')
    @classmethod
    def sentiment_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = ['positive', 'negative', 'neutral', 'bullish', 'bearish']
        if v.lower() not in valid:
            raise ValueError(f"Invalid sentiment: {v}")
        return v.lower()


class TradingEconomicsOutput(BaseModel):
    """Complete output model."""
    forex: List[MarketInstrument] = Field(default_factory=list)
    indices: List[MarketInstrument] = Field(default_factory=list)
    commodities: List[MarketInstrument] = Field(default_factory=list)
    bonds: List[MarketInstrument] = Field(default_factory=list)
    crypto: List[MarketInstrument] = Field(default_factory=list)
    stocks: List[MarketInstrument] = Field(default_factory=list)
    etfs: List[MarketInstrument] = Field(default_factory=list)
    derivatives: List[MarketInstrument] = Field(default_factory=list)
    macro_us: List[MacroIndicator] = Field(default_factory=list)
    macro_uk: List[MacroIndicator] = Field(default_factory=list)
    macro_eu: List[MacroIndicator] = Field(default_factory=list)
    macro_jp: List[MacroIndicator] = Field(default_factory=list)
    macro_cn: List[MacroIndicator] = Field(default_factory=list)
    macro_de: List[MacroIndicator] = Field(default_factory=list)
    macro_fr: List[MacroIndicator] = Field(default_factory=list)
    macro_it: List[MacroIndicator] = Field(default_factory=list)
    macro_es: List[MacroIndicator] = Field(default_factory=list)
    macro_ca: List[MacroIndicator] = Field(default_factory=list)
    macro_au: List[MacroIndicator] = Field(default_factory=list)
    macro_br: List[MacroIndicator] = Field(default_factory=list)
    macro_in: List[MacroIndicator] = Field(default_factory=list)
    market_headlines: List[NewsArticle] = Field(default_factory=list)
    earnings_announcements: List[NewsArticle] = Field(default_factory=list)
    dividend_news: List[NewsArticle] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)

    def total_items(self) -> int:
        return len(self.forex) + len(self.indices) + len(self.commodities) + \
               len(self.bonds) + len(self.crypto) + len(self.stocks) + \
               len(self.etfs) + len(self.derivatives) + \
               len(self.all_macro_indicators()) + len(self.all_news())

    def all_macro_indicators(self) -> List[MacroIndicator]:
        return [ind for attr in dir(self) 
                if attr.startswith('macro_') 
                for ind in getattr(self, attr)]

    def all_news(self) -> List[NewsArticle]:
        return self.market_headlines + self.earnings_announcements + self.dividend_news

    def summary(self) -> dict:
        return {"total_items": self.total_items(), "errors": len(self.errors)}
