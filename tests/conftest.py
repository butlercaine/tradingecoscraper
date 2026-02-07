"""
Pytest configuration and fixtures.
"""

import pytest
import os
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def homepage_html(fixtures_dir):
    """Load homepage.html fixture."""
    html_path = fixtures_dir / "homepage.html"
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def empty_html():
    """Return empty HTML for testing."""
    return "<html><body></body></html>"


@pytest.fixture
def malformed_html():
    """Return malformed HTML for error testing."""
    return "<html><body><table><tr><td>invalid</td></tr></table></body></html>"


@pytest.fixture
def sample_market_instrument():
    """Sample market instrument data."""
    from models import MarketInstrument, MarketCategory
    from datetime import datetime
    
    return MarketInstrument(
        symbol="EURUSD",
        name="Euro/US Dollar",
        value=1.0850,
        change=0.0025,
        pct_change=0.23,
        category=MarketCategory.FOREX,
        timestamp=datetime(2024, 1, 25, 14, 30, 0),
    )


@pytest.fixture
def sample_macro_indicator():
    """Sample macro indicator data."""
    from models import MacroIndicator, CountryCode
    from datetime import datetime
    
    return MacroIndicator(
        country=CountryCode.US,
        indicator_name="GDP Growth",
        value=2.4,
        previous=2.1,
        unit="%",
        timestamp=datetime(2024, 1, 25, 14, 30, 0),
        frequency="quarterly",
        source="Bureau of Economic Analysis",
    )


@pytest.fixture
def sample_news_article():
    """Sample news article data."""
    from models import NewsArticle
    from datetime import datetime
    
    return NewsArticle(
        title="US GDP Growth Beats Estimates",
        summary="The US economy expanded 2.4% in Q4",
        timestamp=datetime(2024, 1, 25, 14, 30, 0),
        url="https://tradingeconomics.com/news/gdp",
        source="Trading Economics",
        category="Economy",
    )


@pytest.fixture
def sample_trading_economics_output():
    """Sample complete trading economics output."""
    from models import TradingEconomicsOutput
    from datetime import datetime
    
    return TradingEconomicsOutput(
        metadata={
            "scraped_at": datetime.utcnow().isoformat(),
            "pipeline_version": "1.0.0",
        },
        errors=[],
    )
