"""
Market Panels Parser

Parses market data panels from HTML using BeautifulSoup4 with lxml.
Functions for: Commodities, Stock Indexes, Major Stocks, Forex, Government Bonds, Crypto
"""

from typing import List, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag

from models import MarketInstrument, MarketCategory
from config import SELECTORS


def _parse_percentage(value: str) -> Optional[float]:
    """Parse a percentage string to float (handles ± signs)."""
    if not value or not value.strip():
        return None
    try:
        # Remove %, spaces, and handle ±
        cleaned = value.strip().replace('%', '').replace('−', '-').replace('–', '-')
        cleaned = cleaned.replace('+', '').strip()
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_price(value: str) -> Optional[float]:
    """Parse a price/number string to float."""
    if not value or not value.strip():
        return None
    try:
        # Remove currency symbols, commas, spaces
        cleaned = value.strip().replace('$', '').replace('€', '').replace('£', '')
        cleaned = cleaned.replace(',', '').replace(' ', '')
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _find_instrument_rows(
    soup: BeautifulSoup,
    panel_selector: str,
    row_selector: str = "tr, .row, .data-row"
) -> List[Tag]:
    """Find all instrument rows within a panel."""
    panel = soup.select_one(panel_selector)
    if not panel:
        return []
    return panel.select(row_selector)


def _extract_row_cells(row: Tag) -> List[str]:
    """Extract text from table cells or div columns in a row."""
    cells = row.select("td, th, .cell, .col")
    if cells:
        return [cell.get_text(strip=True) for cell in cells]
    # Fallback: get all text from row
    return [row.get_text(strip=True)]


def parse_commodities(html: str) -> List[MarketInstrument]:
    """
    Parse commodities panel (Gold, Silver, Oil, Natural Gas, etc.)
    
    Expected columns: Symbol/Name, Price, Change, % Change
    """
    instruments = []
    soup = BeautifulSoup(html, "lxml")
    
    panel_selector = SELECTORS.get("product_list", ".commodity-row, .commodity-item")
    rows = _find_instrument_rows(soup, panel_selector)
    
    for row in rows:
        try:
            cells = _extract_row_cells(row)
            if len(cells) < 2:
                continue
            
            # First cell usually contains symbol/name
            name_cell = cells[0]
            
            # Try to extract symbol from text or data attribute
            symbol = row.get("data-symbol", name_cell[:6].upper())
            
            # Parse price (usually 2nd or 3rd column)
            price = None
            for cell in cells[1:4]:
                price = _parse_price(cell)
                if price is not None:
                    break
            
            # Parse change (usually 4th or 3rd column)
            change = None
            pct_change = None
            for i, cell in enumerate(cells):
                pct = _parse_percentage(cell)
                if pct is not None:
                    if i == len(cells) - 2:
                        pct_change = pct
                    elif i == len(cells) - 1:
                        pct_change = pct
            
            if price is not None:
                instruments.append(MarketInstrument(
                    symbol=symbol,
                    name=name_cell,
                    value=price,
                    change=change,
                    pct_change=pct_change,
                    category=MarketCategory.COMMODITIES,
                ))
        except (ValueError, TypeError, AttributeError):
            continue
    
    return instruments


def parse_indexes(html: str) -> List[MarketInstrument]:
    """
    Parse stock indexes panel (S&P 500, Dow Jones, NASDAQ, etc.)
    
    Expected columns: Index Name, Value, Change, % Change
    """
    instruments = []
    soup = BeautifulSoup(html, "lxml")
    
    panel_selector = SELECTORS.get("product_list", ".index-row, .index-item, .indices-item")
    rows = _find_instrument_rows(soup, panel_selector)
    
    for row in rows:
        try:
            cells = _extract_row_cells(row)
            if len(cells) < 2:
                continue
            
            name_cell = cells[0]
            symbol = row.get("data-symbol", name_cell[:4].upper())
            
            # Parse value (may have comma separators for thousands)
            value = None
            for cell in cells[1:4]:
                value = _parse_price(cell)
                if value is not None:
                    break
            
            # Parse percentage change
            pct_change = None
            for cell in cells:
                pct = _parse_percentage(cell)
                if pct is not None and abs(pct) <= 10:  # Index changes are typically smaller %
                    pct_change = pct
                    break
            
            if value is not None:
                instruments.append(MarketInstrument(
                    symbol=symbol,
                    name=name_cell,
                    value=value,
                    pct_change=pct_change,
                    category=MarketCategory.INDICES,
                ))
        except (ValueError, TypeError, AttributeError):
            continue
    
    return instruments


def parse_stocks(html: str) -> List[MarketInstrument]:
    """
    Parse major stocks panel (Apple, Microsoft, Google, etc.)
    
    Expected columns: Symbol, Company Name, Price, Change, % Change
    """
    instruments = []
    soup = BeautifulSoup(html, "lxml")
    
    panel_selector = SELECTORS.get("product_list", ".stock-row, .stock-item, .equity-item")
    rows = _find_instrument_rows(soup, panel_selector)
    
    for row in rows:
        try:
            cells = _extract_row_cells(row)
            if len(cells) < 3:
                continue
            
            # Usually: Symbol (col 0), Name (col 1), Price (col 2), Change (col 3), % (col 4)
            symbol = cells[0] if len(cells) > 0 else ""
            name = cells[1] if len(cells) > 1 else cells[0]
            
            # Parse price
            price = None
            for cell in cells[2:4]:
                price = _parse_price(cell)
                if price is not None:
                    break
            
            # Parse change and pct_change
            change = None
            pct_change = None
            for i, cell in enumerate(cells[3:], start=3):
                val = _parse_price(cell)
                pct = _parse_percentage(cell)
                if val is not None and i >= 3:
                    change = val
                if pct is not None:
                    pct_change = pct
            
            if price is not None:
                instruments.append(MarketInstrument(
                    symbol=symbol,
                    name=name,
                    value=price,
                    change=change,
                    pct_change=pct_change,
                    category=MarketCategory.STOCKS,
                ))
        except (ValueError, TypeError, AttributeError):
            continue
    
    return instruments


def parse_forex(html: str) -> List[MarketInstrument]:
    """
    Parse forex panel (EUR/USD, GBP/USD, USD/JPY, etc.)
    
    Expected columns: Pair, Price, Change, % Change
    """
    instruments = []
    soup = BeautifulSoup(html, "lxml")
    
    panel_selector = SELECTORS.get("product_list", ".forex-row, .fx-row, .currency-item")
    rows = _find_instrument_rows(soup, panel_selector)
    
    for row in rows:
        try:
            cells = _extract_row_cells(row)
            if len(cells) < 2:
                continue
            
            # First cell is the currency pair
            pair = cells[0].replace('/', '').replace(' ', '').upper()
            
            # Parse price (typically 4 decimal places for major pairs)
            price = None
            for cell in cells[1:3]:
                price = _parse_price(cell)
                if price is not None:
                    break
            
            # Parse change (small values, typically)
            change = None
            pct_change = None
            for cell in cells:
                pct = _parse_percentage(cell)
                if pct is not None:
                    pct_change = pct
            
            if price is not None:
                instruments.append(MarketInstrument(
                    symbol=pair,
                    name=cells[0],
                    value=price,
                    change=change,
                    pct_change=pct_change,
                    category=MarketCategory.FOREX,
                ))
        except (ValueError, TypeError, AttributeError):
            continue
    
    return instruments


def parse_bonds(html: str) -> List[MarketInstrument]:
    """
    Parse government bonds panel (US 10Y, UK Gilts, German Bund, etc.)
    
    Expected columns: Bond, Yield, Change, % Change
    """
    instruments = []
    soup = BeautifulSoup(html, "lxml")
    
    panel_selector = SELECTORS.get("product_list", ".bond-row, .bonds-item, .yield-row")
    rows = _find_instrument_rows(soup, panel_selector)
    
    for row in rows:
        try:
            cells = _extract_row_cells(row)
            if len(cells) < 2:
                continue
            
            name_cell = cells[0]
            # Extract country and term from name
            symbol = row.get("data-symbol", name_cell[:6].upper())
            
            # Parse yield (percentage)
            yield_val = None
            for cell in cells[1:3]:
                yield_val = _parse_price(cell)
                if yield_val is not None:
                    break
            
            # Parse change
            change = None
            pct_change = None
            for cell in cells:
                pct = _parse_percentage(cell)
                if pct is not None:
                    pct_change = pct
            
            if yield_val is not None:
                instruments.append(MarketInstrument(
                    symbol=symbol,
                    name=name_cell,
                    value=yield_val,
                    change=change,
                    pct_change=pct_change,
                    category=MarketCategory.BONDS,
                ))
        except (ValueError, TypeError, AttributeError):
            continue
    
    return instruments


def parse_crypto(html: str) -> List[MarketInstrument]:
    """
    Parse cryptocurrency panel (Bitcoin, Ethereum, Solana, etc.)
    
    Expected columns: Coin, Price, 24h Change, Market Cap
    """
    instruments = []
    soup = BeautifulSoup(html, "lxml")
    
    panel_selector = SELECTORS.get("product_list", ".crypto-row, .crypto-item, .coin-row")
    rows = _find_instrument_rows(soup, panel_selector)
    
    for row in rows:
        try:
            cells = _extract_row_cells(row)
            if len(cells) < 2:
                continue
            
            name_cell = cells[0]
            # Extract symbol from text or data attribute
            symbol = row.get("data-symbol", name_cell[:4].upper())
            
            # Parse price (may be large numbers for BTC)
            price = None
            for cell in cells[1:3]:
                price = _parse_price(cell)
                if price is not None:
                    break
            
            # Parse 24h change
            change = None
            pct_change = None
            for cell in cells:
                pct = _parse_percentage(cell)
                if pct is not None:
                    pct_change = pct
            
            if price is not None:
                instruments.append(MarketInstrument(
                    symbol=symbol,
                    name=name_cell,
                    value=price,
                    change=change,
                    pct_change=pct_change,
                    category=MarketCategory.CRYPTO,
                ))
        except (ValueError, TypeError, AttributeError):
            continue
    
    return instruments


# Aliases for backward compatibility
parse_major_stocks = parse_stocks
parse_major_indexes = parse_indexes
