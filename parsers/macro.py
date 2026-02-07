"""
Macro Indicators Parser

Parses macroeconomic indicators for 13 major countries from HTML matrix.
Returns Dict[str, List[MacroIndicator]] keyed by ISO country code.

Countries: US, UK, EU, JP, CN, DE, FR, IT, ES, CA, AU, BR, IN
Indicators: GDP, Inflation, Unemployment, Interest Rate, PMI, etc.
"""

from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag

from models import MacroIndicator, CountryCode


# Common macro indicators across all countries
DEFAULT_MACRO_INDICATORS = [
    "GDP Growth",
    "Inflation Rate",
    "Unemployment Rate",
    "Interest Rate",
    "Manufacturing PMI",
    "Consumer Confidence",
    "Retail Sales",
    "Industrial Production",
    "Trade Balance",
    "Government Debt to GDP",
    "Current Account",
    "Housing Starts",
    "Consumer Price Index",
    "Producer Price Index",
    "Purchasing Managers Index",
    "Business Confidence",
    "Public Debt",
    "Wage Growth",
    "Disposable Income",
    "Retail Sales YoY",
]


# Country name mappings (HTML often uses full names)
COUNTRY_NAME_MAP = {
    "united states": CountryCode.US,
    "us": CountryCode.US,
    "america": CountryCode.US,
    "usa": CountryCode.US,
    "united kingdom": CountryCode.UK,
    "uk": CountryCode.UK,
    "britain": CountryCode.UK,
    "great britain": CountryCode.UK,
    "european union": CountryCode.EU,
    "eu": CountryCode.EU,
    "euro area": CountryCode.EU,
    "eurozone": CountryCode.EU,
    "japan": CountryCode.JP,
    "china": CountryCode.CN,
    "germany": CountryCode.DE,
    "france": CountryCode.FR,
    "italy": CountryCode.IT,
    "spain": CountryCode.ES,
    "canada": CountryCode.CA,
    "australia": CountryCode.AU,
    "brazil": CountryCode.BR,
    "india": CountryCode.IN,
}


def _parse_number(value: str) -> Optional[float]:
    """Parse a number string to float (handles %, billions, etc.)."""
    if not value or not value.strip():
        return None
    try:
        cleaned = value.strip()
        # Remove common prefixes/suffixes
        for char in ['$', '€', '£', '¥', '%', '−', '–', '−', '(', ')', ',']:
            cleaned = cleaned.replace(char, '')
        cleaned = cleaned.replace(' ', '')
        # Handle "n/a" or similar
        if cleaned.lower() in ['n/a', 'na', 'n.a.', '-', '...', '']:
            return None
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_indicator_value(value: str) -> Optional[float]:
    """Parse indicator value with unit awareness."""
    if not value or not value.strip():
        return None
    cleaned = value.strip()
    # Remove unit if present
    for suffix in ['%', 'bps', 'basis points', 'bln', 'bn', 'billion', 'trillion', 't']:
        if cleaned.lower().endswith(' ' + suffix):
            cleaned = cleaned[:-len(suffix)-1]
            break
    return _parse_number(cleaned)


def _clean_indicator_name(name: str) -> str:
    """Clean and standardize indicator name."""
    name = name.strip()
    # Normalize common variations
    mappings = {
        "gdp yoy": "GDP Growth",
        "gdp growth rate": "GDP Growth",
        "annual gdp growth": "GDP Growth",
        "cpi inflation": "Inflation Rate",
        "consumer price index": "Inflation Rate",
        "inflation yoy": "Inflation Rate",
        "unemployment rate": "Unemployment Rate",
        "jobless rate": "Unemployment Rate",
        "policy rate": "Interest Rate",
        "central bank rate": "Interest Rate",
        "manufacturing pmi": "Manufacturing PMI",
        "pmi manufacturing": "Manufacturing PMI",
        "consumer confidence index": "Consumer Confidence",
        "retail sales yoy": "Retail Sales",
        "industrial production yoy": "Industrial Production",
        "trade balance yoy": "Trade Balance",
        "govt debt gdp": "Government Debt to GDP",
        "public debt gdp": "Government Debt to GDP",
        "current account balance": "Current Account",
        "housing starts yoy": "Housing Starts",
        "ppi": "Producer Price Index",
        "business climate": "Business Confidence",
    }
    return mappings.get(name.lower(), name)


def _find_macro_table(soup: BeautifulSoup, country: str) -> Optional[Tag]:
    """Find the macro indicators table for a specific country."""
    # Try multiple selector strategies
    
    # Strategy 1: Find table with country header
    tables = soup.find_all('table')
    for table in tables:
        headers = table.find_all('th')
        for header in headers:
            if country.lower() in header.get_text(strip=True).lower():
                return table
    
    # Strategy 2: Find by country name in page
    country_elements = soup.find_all(string=lambda t: t and country.lower() in t.lower())
    for elem in country_elements:
        parent = elem.find_parent()
        if parent:
            table = parent.find_parent('table')
            if table:
                return table
            # Look for table nearby
            for sibling in parent.find_next_siblings():
                if sibling.name == 'table':
                    return sibling
    
    # Strategy 3: Look for common macro table classes
    macro_selectors = [
        '.macro-table',
        '.indicators-table',
        '.country-indicators',
        '.macro-data',
        '[class*="macro"]',
        '[class*="indicators"]',
    ]
    for selector in macro_selectors:
        table = soup.select_one(selector)
        if table:
            return table
    
    return None


def _extract_indicator_row(row: Tag) -> Dict[str, str]:
    """Extract indicator name and value from a table row."""
    cells = row.find_all(['td', 'th'])
    if len(cells) >= 2:
        name = cells[0].get_text(strip=True)
        # Try to get value from second cell, or next sibling
        value = cells[1].get_text(strip=True)
        return {"name": name, "value": value}
    elif len(cells) == 1:
        # Might be split across multiple elements
        text = cells[0].get_text(strip=True)
        # Try to split on common separators
        for sep in ['......', '—', '--', '→', '|', '\t']:
            if sep in text:
                parts = text.split(sep)
                return {"name": parts[0].strip(), "value": parts[-1].strip()}
    return {"name": "", "value": ""}


def _determine_actual(value: str, forecast: Optional[float]) -> Optional[str]:
    """Determine actual vs forecast relationship."""
    val = _parse_indicator_value(value)
    if val is None or forecast is None:
        return None
    diff = val - forecast
    if abs(diff) < 0.01:
        return "inline"
    elif diff > 0:
        return "better"
    else:
        return "worse"


def _determine_frequency(name: str) -> str:
    """Determine update frequency based on indicator name."""
    if any(word in name.lower() for word in ['gdp', 'quarterly', 'q1', 'q2', 'q3', 'q4']):
        return "quarterly"
    elif any(word in name.lower() for word in ['annual', 'yearly', 'yoy']):
        return "yearly"
    elif any(word in name.lower() for word in ['weekly', 'weekly']:
        return "weekly"
    elif any(word in name.lower() for word in ['daily', 'today']):
        return "daily"
    return "monthly"


def parse_country_macro(
    html: str,
    country: str,
    country_code: CountryCode
) -> List[MacroIndicator]:
    """
    Parse macro indicators for a single country.
    
    Args:
        html: HTML content
        country: Country name (e.g., "United States")
        country_code: ISO country code enum
        
    Returns:
        List of MacroIndicator objects
    """
    indicators = []
    soup = BeautifulSoup(html, "lxml")
    
    table = _find_macro_table(soup, country)
    if not table:
        return indicators
    
    rows = table.find_all('tr')
    for row in rows:
        try:
            data = _extract_indicator_row(row)
            name = data.get("name", "")
            value_str = data.get("value", "")
            
            if not name or not value_str:
                continue
            
            name = _clean_indicator_name(name)
            value = _parse_indicator_value(value_str)
            
            # Try to extract previous value (often in parentheses or next column)
            previous = None
            # Check for pattern like "1.5 (1.4)" or "1.5 vs 1.4"
            import re
            prev_match = re.search(r'\(([\d\.\-]+)\)|vs\s*([\d\.\-]+)|previous[:\s]*([\d\.\-]+)', value_str)
            if prev_match:
                prev_str = prev_match.group(1) or prev_match.group(2) or prev_match.group(3)
                previous = _parse_number(prev_str)
            
            # Determine unit from context
            unit = "%"
            if any(word in value_str.lower() for word in ['bln', 'bn', 'billion', 'trillion']):
                unit = "billions"
            elif 'yoy' in value_str.lower() or 'year' in value_str.lower():
                unit = "% YoY"
            
            indicator = MacroIndicator(
                country=country_code,
                indicator_name=name,
                value=value,
                previous=previous,
                unit=unit,
                frequency=_determine_frequency(name),
            )
            indicators.append(indicator)
        except (ValueError, TypeError, AttributeError):
            continue
    
    return indicators


def parse_macro_indicators(html: str) -> Dict[str, List[MacroIndicator]]:
    """
    Parse macro indicators for all 13 countries from HTML.
    
    Expected structure: Matrix with countries as rows/columns
    or separate tables per country.
    
    Returns:
        Dict mapping country code (str) to List[MacroIndicator]
        Keys: "US", "UK", "EU", "JP", "CN", "DE", "FR", "IT", "ES", "CA", "AU", "BR", "IN"
    """
    result: Dict[str, List[MacroIndicator]] = {
        "US": [],
        "UK": [],
        "EU": [],
        "JP": [],
        "CN": [],
        "DE": [],
        "FR": [],
        "IT": [],
        "ES": [],
        "CA": [],
        "AU": [],
        "BR": [],
        "IN": [],
    }
    
    soup = BeautifulSoup(html, "lxml")
    
    # Try to find all country sections
    countries_to_parse = [
        ("United States", CountryCode.US),
        ("United Kingdom", CountryCode.UK),
        ("European Union", CountryCode.EU),
        ("Euro Area", CountryCode.EU),
        ("Japan", CountryCode.JP),
        ("China", CountryCode.CN),
        ("Germany", CountryCode.DE),
        ("France", CountryCode.FR),
        ("Italy", CountryCode.IT),
        ("Spain", CountryCode.ES),
        ("Canada", CountryCode.CA),
        ("Australia", CountryCode.AU),
        ("Brazil", CountryCode.BR),
        ("India", CountryCode.IN),
    ]
    
    # Strategy 1: Find individual country tables
    for country_name, country_code in countries_to_parse:
        indicators = parse_country_macro(html, country_name, country_code)
        if indicators:
            result[country_code.value] = indicators
    
    # Strategy 2: If no individual tables, try to parse single matrix table
    if all(len(v) == 0 for v in result.values()):
        # Look for matrix format: countries as rows, indicators as columns
        tables = soup.find_all('table')
        for table in tables:
            try:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                # First row might be header with indicator names
                header_cells = rows[0].find_all(['td', 'th'])
                indicator_names = [cell.get_text(strip=True) for cell in header_cells[1:]]
                
                # Remaining rows are countries
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue
                    
                    country_text = cells[0].get_text(strip=True)
                    # Match country text to code
                    for name, code in countries_to_parse:
                        if name.lower() in country_text.lower() or code.value.lower() in country_text.lower():
                            code_str = code.value
                            for i, cell in enumerate(cells[1:], start=0):
                                if i < len(indicator_names):
                                    value_str = cell.get_text(strip=True)
                                    value = _parse_indicator_value(value_str)
                                    
                                    if value is not None:
                                        indicator = MacroIndicator(
                                            country=code,
                                            indicator_name=indicator_names[i],
                                            value=value,
                                            unit="%",
                                            frequency=_determine_frequency(indicator_names[i]),
                                        )
                                        result[code_str].append(indicator)
                            break
            except (ValueError, TypeError, AttributeError, IndexError):
                continue
    
    return result


def parse_all_countries_separate(html: str) -> Dict[str, List[MacroIndicator]]:
    """
    Parse macro data when each country has its own section/table.
    
    Useful for pages with collapsible country sections.
    """
    result: Dict[str, List[MacroIndicator]] = {}
    soup = BeautifulSoup(html, "lxml")
    
    # Find all country sections
    country_sections = soup.find_all(['div', 'section', 'article'], 
                                       class_=lambda c: c and any(x in str(c).lower() 
                                                                for x in ['country', 'nation', 'region']))
    
    for section in country_sections:
        try:
            # Extract country from section title
            title_elem = section.find(['h2', 'h3', 'h4', '.title', '.header'])
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            
            # Match to country
            matched_country = None
            for name, code in COUNTRY_NAME_MAP.items():
                if name in title.lower():
                    matched_country = code
                    break
            
            if not matched_country:
                continue
            
            # Parse indicators within this section
            indicators = []
            rows = section.find_all('tr')
            for row in rows:
                try:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        name = cells[0].get_text(strip=True)
                        value_str = cells[1].get_text(strip=True)
                        
                        if name and value_str:
                            name = _clean_indicator_name(name)
                            value = _parse_indicator_value(value_str)
                            
                            if value is not None:
                                indicator = MacroIndicator(
                                    country=matched_country,
                                    indicator_name=name,
                                    value=value,
                                    unit="%",
                                    frequency=_determine_frequency(name),
                                )
                                indicators.append(indicator)
                except (ValueError, TypeError, AttributeError):
                    continue
            
            if indicators:
                result[matched_country.value] = indicators
        except (ValueError, TypeError, AttributeError):
            continue
    
    return result


# Convenience functions for specific indicator parsing
def parse_gdp_only(html: str) -> Dict[str, Optional[float]]:
    """Extract only GDP growth rates for all countries."""
    macro_data = parse_macro_indicators(html)
    gdp_data = {}
    for country, indicators in macro_data.items():
        for ind in indicators:
            if 'gdp' in ind.indicator_name.lower():
                gdp_data[country] = ind.value
                break
        else:
            gdp_data[country] = None
    return gdp_data


def parse_inflation_only(html: str) -> Dict[str, Optional[float]]:
    """Extract only inflation rates for all countries."""
    macro_data = parse_macro_indicators(html)
    inflation_data = {}
    for country, indicators in macro_data.items():
        for ind in indicators:
            if 'inflation' in ind.indicator_name.lower() or 'cpi' in ind.indicator_name.lower():
                inflation_data[country] = ind.value
                break
        else:
            inflation_data[country] = None
    return inflation_data


def parse_unemployment_only(html: str) -> Dict[str, Optional[float]]:
    """Extract only unemployment rates for all countries."""
    macro_data = parse_macro_indicators(html)
    unemployment_data = {}
    for country, indicators in macro_data.items():
        for ind in indicators:
            if 'unemployment' in ind.indicator_name.lower() or 'jobless' in ind.indicator_name.lower():
                unemployment_data[country] = ind.value
                break
        else:
            unemployment_data[country] = None
    return unemployment_data
