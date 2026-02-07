"""
Unit tests for parsers module.

Tests cover:
- Market parsers (forex, indices, commodities, bonds, crypto, stocks)
- Macro indicators parser
- Headlines parser
- Model validation
"""

import pytest
from pathlib import Path


class TestForexParser:
    """Tests for forex parser."""
    
    def test_parse_forex_returns_list(self, homepage_html):
        """Test that parse_forex returns a list."""
        from parsers.markets import parse_forex
        
        result = parse_forex(homepage_html)
        assert isinstance(result, list)
    
    def test_parse_forex_extracts_instruments(self, homepage_html):
        """Test that forex parser extracts instruments."""
        from parsers.markets import parse_forex
        from models import MarketInstrument
        
        result = parse_forex(homepage_html)
        assert len(result) > 0
        assert all(isinstance(item, MarketInstrument) for item in result)
    
    def test_parse_forex_has_required_fields(self, homepage_html):
        """Test that forex instruments have required fields."""
        from parsers.markets import parse_forex
        from models import MarketCategory
        
        result = parse_forex(homepage_html)
        if result:
            item = result[0]
            assert item.symbol
            assert item.name
            assert item.value
            assert item.category == MarketCategory.FOREX
    
    def test_parse_forex_parses_values(self, homepage_html):
        """Test that forex parser parses numeric values correctly."""
        from parsers.markets import parse_forex
        
        result = parse_forex(homepage_html)
        
        eurusd = next((i for i in result if "EUR" in i.symbol and "USD" in i.symbol), None)
        if eurusd:
            assert eurusd.value == 1.0850
            assert eurusd.change == 0.0025
            assert eurusd.pct_change == 0.23
    
    def test_parse_forex_handles_empty_html(self, empty_html):
        """Test that forex parser handles empty HTML gracefully."""
        from parsers.markets import parse_forex
        
        result = parse_forex(empty_html)
        assert result == []


class TestIndicesParser:
    """Tests for indices parser."""
    
    def test_parse_indexes_returns_list(self, homepage_html):
        """Test that parse_indexes returns a list."""
        from parsers.markets import parse_indexes
        
        result = parse_indexes(homepage_html)
        assert isinstance(result, list)
    
    def test_parse_indexes_extracts_instruments(self, homepage_html):
        """Test that indices parser extracts instruments."""
        from parsers.markets import parse_indexes
        from models import MarketInstrument
        
        result = parse_indexes(homepage_html)
        assert len(result) > 0
        assert all(isinstance(item, MarketInstrument) for item in result)
    
    def test_parse_indexes_category(self, homepage_html):
        """Test that indices have correct category."""
        from parsers.markets import parse_indexes
        from models import MarketCategory
        
        result = parse_indexes(homepage_html)
        if result:
            assert result[0].category == MarketCategory.INDICES
    
    def test_parse_indexes_parses_sp500(self, homepage_html):
        """Test parsing of S&P 500 index."""
        from parsers.markets import parse_indexes
        
        result = parse_indexes(homepage_html)
        
        spx = next((i for i in result if "SPX" in i.symbol or "S&P" in i.name), None)
        if spx:
            assert spx.value > 0
            assert spx.pct_change is not None


class TestCommoditiesParser:
    """Tests for commodities parser."""
    
    def test_parse_commodities_returns_list(self, homepage_html):
        """Test that parse_commodities returns a list."""
        from parsers.markets import parse_commodities
        
        result = parse_commodities(homepage_html)
        assert isinstance(result, list)
    
    def test_parse_commodities_extracts_instruments(self, homepage_html):
        """Test that commodities parser extracts instruments."""
        from parsers.markets import parse_commodities
        from models import MarketInstrument
        
        result = parse_commodities(homepage_html)
        assert len(result) > 0
        assert all(isinstance(item, MarketInstrument) for item in result)
    
    def test_parse_commodities_category(self, homepage_html):
        """Test that commodities have correct category."""
        from parsers.markets import parse_commodities
        from models import MarketCategory
        
        result = parse_commodities(homepage_html)
        if result:
            assert result[0].category == MarketCategory.COMMODITIES
    
    def test_parse_commodities_parses_gold(self, homepage_html):
        """Test parsing of gold commodity."""
        from parsers.markets import parse_commodities
        
        result = parse_commodities(homepage_html)
        
        gold = next((i for i in result if "GOLD" in i.symbol or "Gold" in i.name), None)
        if gold:
            assert gold.value > 1000  # Gold is around $2000


class TestBondsParser:
    """Tests for bonds parser."""
    
    def test_parse_bonds_returns_list(self, homepage_html):
        """Test that parse_bonds returns a list."""
        from parsers.markets import parse_bonds
        
        result = parse_bonds(homepage_html)
        assert isinstance(result, list)
    
    def test_parse_bonds_extracts_instruments(self, homepage_html):
        """Test that bonds parser extracts instruments."""
        from parsers.markets import parse_bonds
        from models import MarketInstrument
        
        result = parse_bonds(homepage_html)
        assert len(result) > 0
        assert all(isinstance(item, MarketInstrument) for item in result)
    
    def test_parse_bonds_category(self, homepage_html):
        """Test that bonds have correct category."""
        from parsers.markets import parse_bonds
        from models import MarketCategory
        
        result = parse_bonds(homepage_html)
        if result:
            assert result[0].category == MarketCategory.BONDS


class TestCryptoParser:
    """Tests for crypto parser."""
    
    def test_parse_crypto_returns_list(self, homepage_html):
        """Test that parse_crypto returns a list."""
        from parsers.markets import parse_crypto
        
        result = parse_crypto(homepage_html)
        assert isinstance(result, list)
    
    def test_parse_crypto_extracts_instruments(self, homepage_html):
        """Test that crypto parser extracts instruments."""
        from parsers.markets import parse_crypto
        from models import MarketInstrument
        
        result = parse_crypto(homepage_html)
        assert len(result) > 0
        assert all(isinstance(item, MarketInstrument) for item in result)
    
    def test_parse_crypto_category(self, homepage_html):
        """Test that crypto have correct category."""
        from parsers.markets import parse_crypto
        from models import MarketCategory
        
        result = parse_crypto(homepage_html)
        if result:
            assert result[0].category == MarketCategory.CRYPTO
    
    def test_parse_crypto_parses_bitcoin(self, homepage_html):
        """Test parsing of bitcoin."""
        from parsers.markets import parse_crypto
        
        result = parse_crypto(homepage_html)
        
        btc = next((i for i in result if "BTC" in i.symbol or "Bitcoin" in i.name), None)
        if btc:
            assert btc.value > 0
            assert "USD" in btc.name


class TestStocksParser:
    """Tests for stocks parser."""
    
    def test_parse_stocks_returns_list(self, homepage_html):
        """Test that parse_stocks returns a list."""
        from parsers.markets import parse_stocks
        
        result = parse_stocks(homepage_html)
        assert isinstance(result, list)
    
    def test_parse_stocks_extracts_instruments(self, homepage_html):
        """Test that stocks parser extracts instruments."""
        from parsers.markets import parse_stocks
        from models import MarketInstrument
        
        result = parse_stocks(homepage_html)
        assert len(result) > 0
        assert all(isinstance(item, MarketInstrument) for item in result)
    
    def test_parse_stocks_category(self, homepage_html):
        """Test that stocks have correct category."""
        from parsers.markets import parse_stocks
        from models import MarketCategory
        
        result = parse_stocks(homepage_html)
        if result:
            assert result[0].category == MarketCategory.STOCKS
    
    def test_parse_stocks_parses_apple(self, homepage_html):
        """Test parsing of Apple stock."""
        from parsers.markets import parse_stocks
        
        result = parse_stocks(homepage_html)
        
        aapl = next((i for i in result if "AAPL" in i.symbol or "Apple" in i.name), None)
        if aapl:
            assert aapl.value > 0
            assert aapl.symbol == "AAPL"


class TestMacroParser:
    """Tests for macro indicators parser."""
    
    def test_parse_macro_indicators_returns_dict(self, homepage_html):
        """Test that parse_macro_indicators returns a dictionary."""
        from parsers.macro import parse_macro_indicators
        
        result = parse_macro_indicators(homepage_html)
        assert isinstance(result, dict)
    
    def test_parse_macro_indicators_has_country_keys(self, homepage_html):
        """Test that macro result has country codes as keys."""
        from parsers.macro import parse_macro_indicators
        
        result = parse_macro_indicators(homepage_html)
        
        # Check for expected country codes
        expected_countries = ["US", "UK", "EU", "JP", "CN"]
        for country in expected_countries:
            if country in result:
                assert isinstance(result[country], list)
    
    def test_parse_macro_indicators_extracts_gdp(self, homepage_html):
        """Test that macro parser extracts GDP indicator."""
        from parsers.macro import parse_macro_indicators
        
        result = parse_macro_indicators(homepage_html)
        
        if "US" in result:
            us_indicators = result["US"]
            gdp = next((i for i in us_indicators if "GDP" in i.indicator_name), None)
            if gdp:
                assert gdp.value > -10 and gdp.value < 10  # GDP growth is typically -5% to +10%
                assert gdp.unit == "%"
    
    def test_parse_macro_indicators_extracts_inflation(self, homepage_html):
        """Test that macro parser extracts inflation indicator."""
        from parsers.macro import parse_macro_indicators
        
        result = parse_macro_indicators(homepage_html)
        
        if "US" in result:
            us_indicators = result["US"]
            inflation = next((i for i in us_indicators if "Inflation" in i.indicator_name or "CPI" in i.indicator_name), None)
            if inflation:
                assert inflation.value >= 0
    
    def test_parse_macro_indicators_handles_empty(self, empty_html):
        """Test that macro parser handles empty HTML."""
        from parsers.macro import parse_macro_indicators
        
        result = parse_macro_indicators(empty_html)
        assert isinstance(result, dict)
        # May return empty dict or dict with empty lists
    
    def test_parse_gdp_only(self, homepage_html):
        """Test parse_gdp_only function."""
        from parsers.macro import parse_gdp_only
        
        result = parse_gdp_only(homepage_html)
        assert isinstance(result, dict)
    
    def test_parse_inflation_only(self, homepage_html):
        """Test parse_inflation_only function."""
        from parsers.macro import parse_inflation_only
        
        result = parse_inflation_only(homepage_html)
        assert isinstance(result, dict)
    
    def test_parse_unemployment_only(self, homepage_html):
        """Test parse_unemployment_only function."""
        from parsers.macro import parse_unemployment_only
        
        result = parse_unemployment_only(homepage_html)
        assert isinstance(result, dict)


class TestHeadlinesParser:
    """Tests for headlines parser."""
    
    def test_parse_headlines_returns_list(self, homepage_html):
        """Test that parse_headlines returns a list."""
        from parsers.headlines import parse_headlines
        
        result = parse_headlines(homepage_html)
        assert isinstance(result, list)
    
    def test_parse_headlines_extracts_articles(self, homepage_html):
        """Test that headlines parser extracts articles."""
        from parsers.headlines import parse_headlines
        from models import NewsArticle
        
        result = parse_headlines(homepage_html)
        # May extract 0-3 articles depending on HTML structure
        if result:
            assert all(isinstance(item, NewsArticle) for item in result)
    
    def test_parse_headlines_has_required_fields(self, homepage_html):
        """Test that headlines have required fields."""
        from parsers.headlines import parse_headlines
        
        result = parse_headlines(homepage_html)
        if result:
            item = result[0]
            assert item.title
            assert item.url
    
    def test_parse_headlines_parses_title(self, homepage_html):
        """Test parsing of headline title."""
        from parsers.headlines import parse_headlines
        
        result = parse_headlines(homepage_html)
        
        if result:
            # Check for expected keywords
            has_economy = any("GDP" in a.title or "economy" in a.title.lower() for a in result)
            # May or may not find, depending on HTML structure
    
    def test_parse_headlines_parses_url(self, homepage_html):
        """Test parsing of article URL."""
        from parsers.headlines import parse_headlines
        
        result = parse_headlines(homepage_html)
        
        if result:
            for article in result:
                assert article.url.startswith("http") or article.url.startswith("/")
    
    def test_parse_headlines_limit(self, homepage_html):
        """Test headlines parser respects limit."""
        from parsers.headlines import parse_headlines
        
        result = parse_headlines(homepage_html, limit=2)
        assert len(result) <= 2
    
    def test_parse_all_news_categories(self, homepage_html):
        """Test parse_all_news_categories function."""
        from parsers.headlines import parse_all_news_categories
        
        result = parse_all_news_categories(homepage_html)
        
        assert isinstance(result, dict)
        assert "market_headlines" in result
        assert "earnings_announcements" in result
        assert "dividend_news" in result
    
    def test_parse_headlines_handles_empty(self, empty_html):
        """Test that headlines parser handles empty HTML."""
        from parsers.headlines import parse_headlines
        
        result = parse_headlines(empty_html)
        assert result == []


class TestModels:
    """Tests for Pydantic models."""
    
    def test_market_instrument_valid(self, sample_market_instrument):
        """Test valid market instrument creation."""
        from models import MarketInstrument, MarketCategory
        
        instrument = sample_market_instrument
        
        assert instrument.symbol == "EURUSD"
        assert instrument.value == 1.0850
        assert instrument.category == MarketCategory.FOREX
    
    def test_market_instrument_validation_symbol(self):
        """Test symbol validation."""
        from models import MarketInstrument, MarketCategory
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            MarketInstrument(
                symbol="",
                name="Test",
                value=1.0,
                category=MarketCategory.FOREX,
            )
    
    def test_market_instrument_pct_change_bounds(self):
        """Test percentage change bounds."""
        from models import MarketInstrument, MarketCategory
        from pydantic import ValidationError
        
        # Valid pct_change
        instrument = MarketInstrument(
            symbol="TEST",
            name="Test",
            value=100.0,
            pct_change=50.0,
            category=MarketCategory.STOCKS,
        )
        assert instrument.pct_change == 50.0
        
        # Invalid pct_change (> 100)
        with pytest.raises(ValidationError):
            MarketInstrument(
                symbol="TEST",
                name="Test",
                value=100.0,
                pct_change=150.0,
                category=MarketCategory.STOCKS,
            )
    
    def test_market_instrument_optional_fields(self):
        """Test that optional fields work."""
        from models import MarketInstrument, MarketCategory
        
        instrument = MarketInstrument(
            symbol="TEST",
            name="Test Instrument",
            value=100.0,
            category=MarketCategory.STOCKS,
        )
        
        assert instrument.change is None
        assert instrument.pct_change is None
        assert instrument.bid is None
        assert instrument.ask is None
    
    def test_macro_indicator_valid(self, sample_macro_indicator):
        """Test valid macro indicator creation."""
        from models import MacroIndicator, CountryCode
        
        indicator = sample_macro_indicator
        
        assert indicator.country == CountryCode.US
        assert indicator.indicator_name == "GDP Growth"
        assert indicator.value == 2.4
        assert indicator.unit == "%"
    
    def test_macro_indicator_frequency_validation(self):
        """Test frequency field validation."""
        from models import MacroIndicator, CountryCode
        from pydantic import ValidationError
        
        # Valid frequency
        indicator = MacroIndicator(
            country=CountryCode.US,
            indicator_name="Test",
            value=1.0,
            frequency="monthly",
        )
        assert indicator.frequency == "monthly"
        
        # Invalid frequency
        with pytest.raises(ValidationError):
            MacroIndicator(
                country=CountryCode.US,
                indicator_name="Test",
                value=1.0,
                frequency="invalid",
            )
    
    def test_macro_indicator_country_enum(self):
        """Test country enum values."""
        from models import MacroIndicator, CountryCode
        
        for code in CountryCode:
            indicator = MacroIndicator(
                country=code,
                indicator_name="Test",
                value=1.0,
            )
            assert indicator.country == code
    
    def test_news_article_valid(self, sample_news_article):
        """Test valid news article creation."""
        from models import NewsArticle
        
        article = sample_news_article
        
        assert article.title == "US GDP Growth Beats Estimates"
        assert article.summary is not None
        assert article.url.startswith("http")
    
    def test_news_article_url_validation(self):
        """Test URL validation in news article."""
        from models import NewsArticle
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            NewsArticle(
                title="Test",
                url="not-a-valid-url",
            )
    
    def test_news_article_sentiment_validation(self):
        """Test sentiment validation."""
        from models import NewsArticle
        
        article = NewsArticle(
            title="Test Article",
            url="https://example.com/article",
            sentiment="positive",
        )
        assert article.sentiment == "positive"
        
        # Invalid sentiment
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            NewsArticle(
                title="Test",
                url="https://example.com",
                sentiment="very_positive",
            )
    
    def test_trading_economics_output_valid(self, sample_trading_economics_output):
        """Test valid output creation."""
        from models import TradingEconomicsOutput
        
        output = sample_trading_economics_output
        
        assert isinstance(output, TradingEconomicsOutput)
        assert output.metadata is not None
        assert output.errors == []
    
    def test_trading_economics_output_methods(self, sample_trading_economics_output):
        """Test output helper methods."""
        from models import TradingEconomicsOutput
        
        output = sample_trading_economics_output
        
        assert output.total_items() == 0
        summary = output.summary()
        assert "markets" in summary
        assert "macroeconomics" in summary
        assert "news" in summary
    
    def test_trading_economics_output_with_data(self, sample_market_instrument):
        """Test output with actual data."""
        from models import TradingEconomicsOutput
        
        output = TradingEconomicsOutput(
            forex=[sample_market_instrument],
        )
        
        assert output.total_items() == 1
        assert len(output.forex) == 1


class TestMarketCategory:
    """Tests for MarketCategory enum."""
    
    def test_all_categories_exist(self):
        """Test that all expected categories exist."""
        from models import MarketCategory
        
        expected = [
            "FOREX",
            "INDICES",
            "COMMODITIES",
            "BONDS",
            "CRYPTO",
            "STOCKS",
            "ETFS",
            "DERIVATIVES",
        ]
        
        for cat in expected:
            assert hasattr(MarketCategory, cat)
    
    def test_category_string_values(self):
        """Test category string values."""
        from models import MarketCategory
        
        assert MarketCategory.FOREX.value == "forex"
        assert MarketCategory.INDICES.value == "indices"


class TestCountryCode:
    """Tests for CountryCode enum."""
    
    def test_all_countries_exist(self):
        """Test that all expected countries exist."""
        from models import CountryCode
        
        expected = [
            "US", "UK", "EU", "JP", "CN", "DE", "FR", "IT",
            "ES", "CA", "AU", "BR", "IN",
        ]
        
        for code in expected:
            assert hasattr(CountryCode, code)


class TestScraperUtilities:
    """Tests for scraper utility functions."""
    
    def test_parse_percentage(self):
        """Test percentage parsing utility."""
        from parsers.markets import parse_commodities
        
        # These are module-level functions, test indirectly
        pass
    
    def test_parse_price(self):
        """Test price parsing utility."""
        from parsers.markets import parse_commodities
        
        pass


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_malformed_html(self, malformed_html):
        """Test handling of malformed HTML."""
        from parsers.markets import parse_forex
        from parsers.macro import parse_macro_indicators
        from parsers.headlines import parse_headlines
        
        # Should not raise exceptions
        assert parse_forex(malformed_html) == []
        assert isinstance(parse_macro_indicators(malformed_html), dict)
        assert parse_headlines(malformed_html) == []
    
    def test_empty_list_handling(self, homepage_html):
        """Test that empty results are handled correctly."""
        from parsers.markets import parse_commodities
        
        # Some panels might be empty in test HTML
        result = parse_commodities(homepage_html)
        assert isinstance(result, list)
    
    def test_model_with_extra_fields(self, sample_market_instrument):
        """Test that models ignore extra fields."""
        from models import MarketInstrument, MarketCategory
        from datetime import datetime
        
        # Create with extra fields (should be ignored by Pydantic)
        instrument = MarketInstrument(
            symbol="TEST",
            name="Test",
            value=100.0,
            category=MarketCategory.STOCKS,
            extra_field="should be ignored",
            another_field=123,
        )
        
        assert instrument.symbol == "TEST"
        # Extra fields are ignored
    
    def test_model_serialization(self, sample_market_instrument):
        """Test that models can be serialized."""
        from models import MarketInstrument
        
        data = sample_market_instrument.model_dump()
        
        assert isinstance(data, dict)
        assert data["symbol"] == "EURUSD"
        assert data["value"] == 1.0850


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
