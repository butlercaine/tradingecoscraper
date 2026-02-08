"""
Parsers Package

Market data parsers using BeautifulSoup4 with lxml.
"""

from parsers.markets import (
    parse_commodities,
    parse_indexes,
    parse_stocks,
    parse_forex,
    parse_bonds,
    parse_crypto,
    # Aliases
    parse_major_stocks,
    parse_major_indexes,
)

from parsers.macro import (
    parse_macro_indicators,
    parse_country_macro,
    parse_all_countries_separate,
    parse_gdp_only,
    parse_inflation_only,
    parse_unemployment_only,
)

from parsers.headlines import (
    parse_headlines,
    parse_all_news_categories,
)

from parsers.etfs import (
    parse_etfs,
    parse_etfs_with_fallback,
    DEFAULT_ETFS,
)

from parsers.derivatives import (
    parse_derivatives,
    parse_derivatives_with_fallback,
    DEFAULT_DERIVATIVES,
)

__all__ = [
    # Markets
    "parse_commodities",
    "parse_indexes",
    "parse_stocks",
    "parse_forex",
    "parse_bonds",
    "parse_crypto",
    "parse_major_stocks",
    "parse_major_indexes",
    # Macro
    "parse_macro_indicators",
    "parse_country_macro",
    "parse_all_countries_separate",
    "parse_gdp_only",
    "parse_inflation_only",
    "parse_unemployment_only",
    # Headlines
    "parse_headlines",
    "parse_all_news_categories",
    # ETFs
    "parse_etfs",
    "parse_etfs_with_fallback",
    "DEFAULT_ETFS",
    # Derivatives
    "parse_derivatives",
    "parse_derivatives_with_fallback",
    "DEFAULT_DERIVATIVES",
]
