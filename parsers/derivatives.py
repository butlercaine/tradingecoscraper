"""
Derivatives Parser

Parses futures and options market data from HTML.
"""

from typing import List, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag

from models import MarketInstrument, MarketCategory


def _parse_price(value: str) -> Optional[float]:
    """Parse a price/futures value to float."""
    if not value or not value.strip():
        return None
    try:
        cleaned = value.strip()
        # Remove common prefixes/suffixes
        for char in ['$', '¥', '€', '£', ',']:
            cleaned = cleaned.replace(char, '')
        # Handle negative signs
        cleaned = cleaned.replace('−', '-').replace('–', '-')
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_change(value: str) -> Optional[float]:
    """Parse change value (may include + prefix)."""
    if not value or not value.strip():
        return None
    try:
        cleaned = value.strip().replace('+', '').replace('−', '-').replace('–', '-')
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_percentage(value: str) -> Optional[float]:
    """Parse percentage change."""
    if not value or not value.strip():
        return None
    try:
        cleaned = value.strip().replace('%', '').replace('−', '-').replace('–', '-').replace('+', '')
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _find_derivatives_rows(soup: BeautifulSoup) -> List[Tag]:
    """Find all derivatives rows in the HTML."""
    # Try panel ID first
    panel = soup.find(id='futures') or soup.find(id='derivatives') or soup.find(id='options')
    if panel:
        return panel.select('tbody tr.row-data, tbody tr')
    
    # Try table with derivatives-related class
    tables = soup.find_all('table', class_=lambda c: c and any(
        x in str(c).lower() for x in ['future', 'derivative', 'option', 'vix', 'index-future']
    ))
    if tables:
        rows = []
        for table in tables:
            rows.extend(table.select('tbody tr.row-data, tbody tr'))
        return rows
    
    # Try finding by selector pattern
    rows = soup.select('.futures-table tbody tr, #futures tbody tr, .derivatives-table tbody tr')
    if rows:
        return rows
    
    # Fallback: look for common derivatives symbols in first column
    all_rows = soup.select('table tbody tr')
    deriv_rows = []
    deriv_symbols = {
        'VIX', 'VXST', 'VXN', 'VXO',  # Volatility indexes
        'ES', 'NQ', 'YM', 'RTY',  # E-mini futures
        'CL', 'NG', 'GC', 'SI', 'HG', 'ZC', 'ZS', 'ZM', 'ZL',  # Commodity futures
        'ZB', 'ZC', 'ZN', 'ZF', 'ZT',  # Treasury futures
        'ED', 'EU', 'BP', 'CD', 'JY', 'SF', 'AD', 'NZD',  # Currency futures
        'ESM25', 'NQM25', 'YMH25', 'CLM25', 'NGM25', 'GCM25',  # Month-coded futures
        'SPX', 'SPY', 'QQQ', 'IWM',  # Index products
    }
    
    for row in all_rows:
        cells = row.find_all(['td', 'th'])
        if cells:
            symbol_text = cells[0].get_text(strip=True).upper()
            # Check if symbol matches derivatives pattern
            if any(sym in symbol_text for sym in deriv_symbols):
                deriv_rows.append(row)
            elif symbol_text in deriv_symbols:
                deriv_rows.append(row)
    
    return deriv_rows


def parse_derivatives(html: str) -> List[MarketInstrument]:
    """
    Parse derivatives (futures/options) data from HTML.
    
    Args:
        html: HTML content containing derivatives data
        
    Returns:
        List of MarketInstrument objects with MarketCategory.DERIVATIVES
    """
    instruments = []
    soup = BeautifulSoup(html, "lxml")
    
    rows = _find_derivatives_rows(soup)
    
    for row in rows:
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            # Extract symbol from first cell
            symbol_cell = cells[0].get_text(strip=True)
            link = cells[0].find('a')
            if link:
                symbol = link.get_text(strip=True)
            else:
                symbol = symbol_cell
            
            # Clean symbol (remove month codes sometimes appended)
            if symbol and len(symbol) > 8:
                # Try to get clean symbol
                import re
                clean = re.sub(r'[0-9]{2}$', '', symbol)  # Remove trailing 2 digits (month code)
                if clean in ['ES', 'NQ', 'YM', 'RTY', 'CL', 'NG', 'GC', 'SI', 'HG']:
                    symbol = clean
            
            if not symbol or len(symbol) > 12:
                continue
            
            # Extract name
            name = symbol_cell
            if len(cells) > 1:
                name = cells[1].get_text(strip=True)
                if not name or name == symbol:
                    name = f"{symbol} Futures"
            
            # Parse price (usually column 2 or 3)
            price = None
            for cell in cells[2:4]:
                text = cell.get_text(strip=True)
                price = _parse_price(text)
                if price is not None:
                    break
            
            # Parse change and pct_change
            change = None
            pct_change = None
            
            for i, cell in enumerate(cells[3:], start=3):
                text = cell.get_text(strip=True)
                
                # Try to identify percentage change
                if '%' in text:
                    pct = _parse_percentage(text)
                    if pct is not None:
                        pct_change = pct
                # Try regular change value
                elif text and not any(c in text for c in ['$', '%']):
                    chg = _parse_change(text)
                    if chg is not None and abs(chg) < 1000:
                        change = chg
            
            if price is not None:
                instrument = MarketInstrument(
                    symbol=symbol.upper(),
                    name=name,
                    value=price,
                    change=change,
                    pct_change=pct_change,
                    category=MarketCategory.DERIVATIVES,
                )
                instruments.append(instrument)
                
        except (ValueError, TypeError, AttributeError, IndexError):
            continue
    
    return instruments


def parse_derivatives_with_fallback(
    html: str, 
    fallback_derivatives: List[dict] = None
) -> List[MarketInstrument]:
    """
    Parse derivatives data with fallback to sample data if no derivatives found.
    
    Args:
        html: HTML content
        fallback_derivatives: List of derivative dicts to use if none found
        
    Returns:
        List of MarketInstrument objects
    """
    instruments = parse_derivatives(html)
    
    if not instruments and fallback_derivatives:
        for deriv_data in fallback_derivatives:
            try:
                instrument = MarketInstrument(
                    symbol=deriv_data.get('symbol', '').upper(),
                    name=deriv_data.get('name', f"{deriv_data.get('symbol', '')} Futures"),
                    value=deriv_data.get('value', 0.0),
                    change=deriv_data.get('change'),
                    pct_change=deriv_data.get('pct_change'),
                    category=MarketCategory.DERIVATIVES,
                )
                instruments.append(instrument)
            except (ValueError, TypeError):
                continue
    
    return instruments


# Default fallback derivatives (10 popular instruments)
DEFAULT_DERIVATIVES = [
    {"symbol": "VIX", "name": "CBOE Volatility Index", "value": 14.25, "change": 0.45, "pct_change": 3.26},
    {"symbol": "ES", "name": "E-mini S&P 500 Futures", "value": 4785.50, "change": 25.25, "pct_change": 0.53},
    {"symbol": "NQ", "name": "E-mini Nasdaq 100 Futures", "value": 20845.00, "change": 125.50, "pct_change": 0.61},
    {"symbol": "YM", "name": "E-mini Dow Jones Futures", "value": 37450.00, "change": 185.00, "pct_change": 0.50},
    {"symbol": "RTY", "name": "E-mini Russell 2000 Futures", "value": 1982.50, "change": -8.50, "pct_change": -0.43},
    {"symbol": "CL", "name": "Crude Oil Futures", "value": 74.85, "change": -0.95, "pct_change": -1.25},
    {"symbol": "NG", "name": "Natural Gas Futures", "value": 2.85, "change": 0.08, "pct_change": 2.89},
    {"symbol": "GC", "name": "Gold Futures", "value": 2045.30, "change": 12.50, "pct_change": 0.61},
    {"symbol": "SI", "name": "Silver Futures", "value": 23.45, "change": 0.32, "pct_change": 1.38},
    {"symbol": "ZB", "name": "30-Year T-Bond Futures", "value": 121.50, "change": 0.25, "pct_change": 0.21},
    {"symbol": "ZN", "name": "10-Year T-Note Futures", "value": 108.75, "change": -0.12, "pct_change": -0.11},
    {"symbol": "VXST", "name": "CBOE Short-Term Volatility Index", "value": 12.80, "change": 0.35, "pct_change": 2.81},
]


if __name__ == "__main__":
    # Test the parser
    sample_html = """
    <html><body>
    <div id="futures">
        <table>
            <tbody>
                <tr>
                    <td><a href="/futures/vix">VIX</a></td>
                    <td>CBOE Volatility Index</td>
                    <td class="data-table">14.25</td>
                    <td class="data-table">0.45</td>
                    <td class="data-table">3.26%</td>
                </tr>
                <tr>
                    <td><a href="/futures/es">ES</a></td>
                    <td>E-mini S&P 500 Futures</td>
                    <td class="data-table">4785.50</td>
                    <td class="data-table">25.25</td>
                    <td class="data-table">0.53%</td>
                </tr>
            </tbody>
        </table>
    </div>
    </body></html>
    """
    
    derivatives = parse_derivatives(sample_html)
    print(f"Parsed {len(derivatives)} derivatives:")
    for deriv in derivatives:
        print(f"  {deriv.symbol}: {deriv.value} ({deriv.pct_change}%)")
