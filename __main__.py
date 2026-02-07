"""
Main Scraper Orchestrator

Orchestrates the complete scraping pipeline:
    1. Fetch HTML from Trading Economics
    2. Parse market data (forex, indices, commodities, bonds, crypto, stocks)
    3. Parse macroeconomic indicators for 13 countries
    4. Parse news headlines
    5. Validate all data with Pydantic
    6. Output structured JSON
"""

import asyncio
import argparse
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import (
    HEADERS,
    USER_AGENTS,
    RETRY_CONFIG,
    RATE_LIMIT_DELAY,
    HTTP_TIMEOUT,
    SELECTORS,
)

from scraper import (
    scrape_page,
    ScrapingClient,
    ScraperError,
    RobotsTxtError,
    RequestError,
)

from models import (
    MarketInstrument,
    MacroIndicator,
    NewsArticle,
    TradingEconomicsOutput,
    MarketCategory,
    CountryCode,
)

from parsers.markets import (
    parse_commodities,
    parse_indexes,
    parse_stocks,
    parse_forex,
    parse_bonds,
    parse_crypto,
)

from parsers.macro import (
    parse_macro_indicators,
    parse_gdp_only,
    parse_inflation_only,
)

from parsers.headlines import (
    parse_headlines,
    parse_all_news_categories,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Default URLs (configurable)
DEFAULT_URLS = {
    "markets": "https://tradingeconomics.com/markets",
    "forex": "https://tradingeconomics.com/forex",
    "commodities": "https://tradingeconomics.com/commodities",
    "indices": "https://tradingeconomics.com/indices",
    "bonds": "https://tradingeconomics.com/bonds",
    "crypto": "https://tradingeconomics.com/crypto",
    "stocks": "https://tradingeconomics.com/stocks",
    "macro": "https://tradingeconomics.com/macro",
    "news": "https://tradingeconomics.com/news",
}


async def fetch_market_data(client: ScrapingClient, url_key: str) -> list:
    """Fetch and parse market data for a category."""
    url = DEFAULT_URLS.get(url_key)
    if not url:
        logger.warning(f"No URL configured for {url_key}")
        return []
    
    try:
        logger.info(f"Fetching {url_key} data from {url}")
        html = await client.scrape(url)
        
        parser_map = {
            "forex": parse_forex,
            "commodities": parse_commodities,
            "indices": parse_indexes,
            "bonds": parse_bonds,
            "crypto": parse_crypto,
            "stocks": parse_stocks,
        }
        
        parser = parser_map.get(url_key)
        if parser:
            data = parser(html)
            logger.info(f"Parsed {len(data)} {url_key} instruments")
            return data
    except ScraperError as e:
        logger.error(f"Error fetching {url_key}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error parsing {url_key}: {e}")
    
    return []


async def fetch_all_markets(client: ScrapingClient) -> dict:
    """Fetch all market data categories."""
    result = {
        "forex": [],
        "indices": [],
        "commodities": [],
        "bonds": [],
        "crypto": [],
        "stocks": [],
    }
    
    # Fetch in parallel for efficiency
    tasks = []
    for url_key in result.keys():
        task = asyncio.create_task(fetch_market_data(client, url_key))
        tasks.append((url_key, task))
    
    for url_key, task in tasks:
        result[url_key] = await task
    
    return result


async def fetch_macro_data(client: ScrapingClient) -> dict:
    """Fetch and parse macroeconomic indicators."""
    url = DEFAULT_URLS.get("macro")
    if not url:
        logger.warning("No URL configured for macro data")
        return {}
    
    try:
        logger.info(f"Fetching macro data from {url}")
        html = await client.scrape(url)
        data = parse_macro_indicators(html)
        
        total = sum(len(v) for v in data.values())
        logger.info(f"Parsed {total} macro indicators across {len(data)} countries")
        return data
    except ScraperError as e:
        logger.error(f"Error fetching macro data: {e}")
    except Exception as e:
        logger.error(f"Unexpected error parsing macro: {e}")
        logger.debug(traceback.format_exc())
    
    return {}


async def fetch_headlines(client: ScrapingClient) -> dict:
    """Fetch and parse news headlines."""
    url = DEFAULT_URLS.get("news")
    if not url:
        logger.warning("No URL configured for news")
        return {
            "market_headlines": [],
            "earnings_announcements": [],
            "dividend_news": [],
        }
    
    try:
        logger.info(f"Fetching news from {url}")
        html = await client.scrape(url)
        data = parse_all_news_categories(html)
        
        total = sum(len(v) for v in data.values())
        logger.info(f"Parsed {total} news articles")
        return data
    except ScraperError as e:
        logger.error(f"Error fetching news: {e}")
    except Exception as e:
        logger.error(f"Unexpected error parsing news: {e}")
        logger.debug(traceback.format_exc())
    
    return {
        "market_headlines": [],
        "earnings_announcements": [],
        "dividend_news": [],
    }


async def run_pipeline(
    output_path: Optional[str] = None,
    verbose: bool = False,
) -> TradingEconomicsOutput:
    """
    Run the complete scraping pipeline.
    
    Args:
        output_path: Optional path to save JSON output
        verbose: Enable debug logging
        
    Returns:
        TradingEconomicsOutput with all scraped data
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    start_time = datetime.utcnow()
    logger.info("=" * 50)
    logger.info("Trading Economics Scraper - Starting pipeline")
    logger.info("=" * 50)
    
    errors = []
    output = TradingEconomicsOutput()
    
    try:
        async with ScrapingClient() as client:
            # Step 1: Fetch market data (all categories in parallel)
            logger.info("\n[1/4] Fetching market data...")
            markets = await fetch_all_markets(client)
            output.forex = markets.get("forex", [])
            output.indices = markets.get("indices", [])
            output.commodities = markets.get("commodities", [])
            output.bonds = markets.get("bonds", [])
            output.crypto = markets.get("crypto", [])
            output.stocks = markets.get("stocks", [])
            
            # Step 2: Fetch macro data
            logger.info("\n[2/4] Fetching macroeconomic data...")
            macro = await fetch_macro_data(client)
            
            # Map macro dict to output fields
            country_map = {
                "US": output.macro_us,
                "UK": output.macro_uk,
                "EU": output.macro_eu,
                "JP": output.macro_jp,
                "CN": output.macro_cn,
                "DE": output.macro_de,
                "FR": output.macro_fr,
                "IT": output.macro_it,
                "ES": output.macro_es,
                "CA": output.macro_ca,
                "AU": output.macro_au,
                "BR": output.macro_br,
                "IN": output.macro_in,
            }
            
            for country, indicators in macro.items():
                if country in country_map:
                    country_map[country] = indicators
            
            # Step 3: Fetch news headlines
            logger.info("\n[3/4] Fetching news headlines...")
            news = await fetch_headlines(client)
            output.market_headlines = news.get("market_headlines", [])
            output.earnings_announcements = news.get("earnings_announcements", [])
            output.dividend_news = news.get("dividend_news", [])
            
            # Step 4: Add metadata
            logger.info("\n[4/4] Validating and finalizing output...")
            output.metadata = {
                "scraped_at": datetime.utcnow().isoformat(),
                "pipeline_version": "1.0.0",
                "data_sources": list(DEFAULT_URLS.keys()),
                "retry_config": RETRY_CONFIG,
                "rate_limit_delay": RATE_LIMIT_DELAY,
                "http_timeout": HTTP_TIMEOUT,
                "selectors_used": list(SELECTORS.keys()),
            }
            
            output.errors = errors
    
    except KeyboardInterrupt:
        logger.info("\nPipeline interrupted by user")
        errors.append("Pipeline interrupted by user")
        output.errors = errors
    except Exception as e:
        logger.error(f"\nPipeline failed: {e}")
        logger.debug(traceback.format_exc())
        errors.append(str(e))
        output.errors = errors
    
    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info("\n" + "=" * 50)
    logger.info("Pipeline Complete")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Total items: {output.total_items()}")
    logger.info(f"Errors: {len(output.errors)}")
    logger.info("=" * 50)
    
    # Summary
    summary = output.summary()
    logger.info("\nData Summary:")
    logger.info(f"  Markets: {sum(summary['markets'].values())} instruments")
    logger.info(f"  Macro: {sum(summary['macroeconomics'].values())} indicators")
    logger.info(f"  News: {sum(summary['news'].values())} articles")
    
    # Output JSON if path specified
    if output_path:
        output_json = output.model_dump(mode='json')
        
        # Make datetime serializable
        def default_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_json, f, indent=2, default=default_serializer, ensure_ascii=False)
        
        logger.info(f"\nOutput saved to: {output_path}")
    
    return output


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Trading Economics Scraper - Extract market, macro, and news data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m scraper                              # Run with defaults
  python -m scraper --output data.json           # Save to file
  python -m scraper --verbose --output data.json  # Verbose mode
  python -m scraper --help                        # Show this help
        """,
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output JSON file path (default: print to stdout)",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose/debug logging",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        output = asyncio.run(run_pipeline(
            output_path=args.output,
            verbose=args.verbose,
        ))
        
        # Print summary to stdout if no output file
        if not args.output:
            summary = output.summary()
            print("\n" + "=" * 50)
            print("Scraping Complete - Summary")
            print("=" * 50)
            print(json.dumps(summary, indent=2))
            print(f"\nTotal items scraped: {output.total_items()}")
            print(f"Errors: {len(output.errors)}")
        
        # Exit with error code if there were critical errors
        if output.errors and len(output.errors) >= 3:
            sys.exit(1)
        
        sys.exit(0)
        
    except ScraperError as e:
        logger.error(f"Scraper error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
