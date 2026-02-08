"""
ETFs Parser

Parses ETF (Exchange-Traded Fund) market data from HTML.
"""

from typing import List, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag

from models import MarketInstrument, MarketCategory


def _parse_price(value: str) -> Optional[float]:
    """Parse a price string to float."""
    if not value or not value.strip():
        return None
    try:
        cleaned = value.strip().replace('$', '').replace(',', '').replace(' ', '')
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_percentage(value: str) -> Optional[float]:
    """Parse a percentage string to float."""
    if not value or not value.strip():
        return None
    try:
        cleaned = value.strip().replace('%', '').replace('−', '-').replace('–', '-')
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _find_etf_rows(soup: BeautifulSoup) -> List[Tag]:
    """Find all ETF rows in the HTML."""
    # Try panel ID first
    panel = soup.find(id='etf') or soup.find(id='etfs') or soup.find(id='exchange-traded-funds')
    if panel:
        return panel.select('tbody tr.row-data, tbody tr')
    
    # Try table with ETF-related class
    tables = soup.find_all('table', class_=lambda c: c and 'etf' in str(c).lower())
    if tables:
        rows = []
        for table in tables:
            rows.extend(table.select('tbody tr.row-data, tbody tr'))
        return rows
    
    # Try finding by selector pattern
    rows = soup.select('.etf-table tbody tr, #etfs tbody tr')
    if rows:
        return rows
    
    # Fallback: look for common ETF symbols in first column
    all_rows = soup.select('table tbody tr')
    etf_rows = []
    etf_symbols = {'SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'IVV', 'DIA', 'EEM', 'EFA', 'VWO', 
                   'AGG', 'BND', 'TLT', 'SHY', 'IEI', 'LQD', 'VCIT', 'VCSH', 'HYG', 'JNK',
                   'GLD', 'SLV', 'USO', 'UNG', 'DBA', 'DBC', 'GSG', 'CRB', 'PDBC', 'GSG'}
    
    for row in all_rows:
        cells = row.find_all(['td', 'th'])
        if cells and cells[0].get_text(strip=True).upper() in etf_symbols:
            etf_rows.append(row)
    
    return etf_rows


def parse_etfs(html: str) -> List[MarketInstrument]:
    """
    Parse ETF data from HTML.
    
    Args:
        html: HTML content containing ETF data
        
    Returns:
        List of MarketInstrument objects with MarketCategory.ETFS
    """
    instruments = []
    soup = BeautifulSoup(html, "lxml")
    
    rows = _find_etf_rows(soup)
    
    for row in rows:
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            # Extract symbol from first cell
            symbol_cell = cells[0].get_text(strip=True)
            # Try to get from link if present
            link = cells[0].find('a')
            if link:
                symbol = link.get_text(strip=True)
            else:
                symbol = symbol_cell
            
            if not symbol or len(symbol) > 10:
                continue
            
            # Extract name
            name = symbol_cell
            if len(cells) > 1:
                name = cells[1].get_text(strip=True)
                if not name or name == symbol:
                    name = f"{symbol} ETF"
            
            # Parse price (usually column 2 or 3)
            price = None
            for cell in cells[2:4]:
                price = _parse_price(cell.get_text(strip=True))
                if price is not None:
                    break
            
            # Parse change and pct_change
            change = None
            pct_change = None
            
            # Try to find percentage change in later columns
            for i, cell in enumerate(cells[3:], start=3):
                text = cell.get_text(strip=True)
                pct = _parse_percentage(text)
                if pct is not None:
                    # Typically the last numeric column with % is pct_change
                    if i == len(cells) - 1:
                        pct_change = pct
                    elif i == len(cells) - 2:
                        pct_change = pct
                    # Check if it's a change value (smaller number)
                    elif abs(pct) < 50:  # Change values are typically small
                        change = pct
            
            if price is not None:
                instrument = MarketInstrument(
                    symbol=symbol.upper(),
                    name=name,
                    value=price,
                    change=change,
                    pct_change=pct_change,
                    category=MarketCategory.ETFS,
                )
                instruments.append(instrument)
                
        except (ValueError, TypeError, AttributeError, IndexError):
            continue
    
    return instruments


def parse_etfs_with_fallback(html: str, fallback_etfs: List[dict] = None) -> List[MarketInstrument]:
    """
    Parse ETF data with fallback to sample data if no ETFs found.
    
    Args:
        html: HTML content
        fallback_etfs: List of ETF dicts to use if no ETFs found
        
    Returns:
        List of MarketInstrument objects
    """
    instruments = parse_etfs(html)
    
    # If no ETFs found, use fallback data
    if not instruments and fallback_etfs:
        for etf_data in fallback_etfs:
            try:
                instrument = MarketInstrument(
                    symbol=etf_data.get('symbol', '').upper(),
                    name=etf_data.get('name', f"{etf_data.get('symbol', '')} ETF"),
                    value=etf_data.get('value', 0.0),
                    change=etf_data.get('change'),
                    pct_change=etf_data.get('pct_change'),
                    category=MarketCategory.ETFS,
                )
                instruments.append(instrument)
            except (ValueError, TypeError):
                continue
    
    return instruments


# Default fallback ETFs (10+ popular US ETFs)
DEFAULT_ETFS = [
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "value": 478.50, "change": 2.35, "pct_change": 0.49},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "value": 405.20, "change": 5.80, "pct_change": 1.45},
    {"symbol": "IWM", "name": "iShares Russell 2000 ETF", "value": 198.50, "change": -1.20, "pct_change": -0.60},
    {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "value": 242.30, "change": 1.85, "pct_change": 0.77},
    {"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "value": 445.80, "change": 2.10, "pct_change": 0.47},
    {"symbol": "IVV", "name": "iShares Core S&P 500 ETF", "value": 475.60, "change": 2.25, "pct_change": 0.48},
    {"symbol": "DIA", "name": "SPDR Dow Jones Industrial Average ETF", "value": 375.40, "change": 1.50, "pct_change": 0.40},
    {"symbol": "EEM", "name": "iShares MSCI Emerging Markets ETF", "value": 42.15, "change": 0.35, "pct_change": 0.84},
    {"symbol": "EFA", "name": "iShares MSCI EAFE ETF", "value": 72.80, "change": -0.25, "pct_change": -0.34},
    {"symbol": "VWO", "name": "Vanguard FTSE Emerging Markets ETF", "value": 41.20, "change": 0.28, "pct_change": 0.68},
    {"symbol": "AGG", "name": "iShares Core US Aggregate Bond ETF", "value": 98.50, "change": 0.15, "pct_change": 0.15},
    {"symbol": "BND", "name": "Vanguard Total Bond Market ETF", "value": 72.30, "change": 0.10, "pct_change": 0.14},
    {"symbol": "GLD", "name": "SPDR Gold Shares", "value": 185.50, "change": 1.20, "pct_change": 0.65},
    {"symbol": "SLV", "name": "iShares Silver Trust", "value": 22.45, "change": 0.35, "pct_change": 1.58},
    {"symbol": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "value": 92.15, "change": -0.30, "pct_change": -0.32},
]


if __name__ == "__main__":
    # Test the parser
    sample_html = """
    <html><body>
    <div id="etfs">
        <table>
            <tbody>
                <tr>
                    <td><a href="/etf/spy">SPY</a></td>
                    <td>SPDR S&P 500 ETF Trust</td>
                    <td class="data-table">478.50</td>
                    <td class="data-table">2.35</td>
                    <td class="data-table">0.49%</td>
                </tr>
                <tr>
                    <td><a href="/etf/qqq">QQQ</a></td>
                    <td>Invesco QQQ Trust</td>
                    <td class="data-table">405.20</td>
                    <td class="data-table">5.80</td>
                    <td class="data-table">1.45%</td>
                </tr>
            </tbody>
        </table>
    </div>
    </body></html>
    """
    
    etfs = parse_etfs(sample_html)
    print(f"Parsed {len(etfs)} ETFs:")
    for etf in etfs:
        print(f"  {etf.symbol}: ${etf.value} ({etf.pct_change}%)")
