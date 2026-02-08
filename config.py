# Trading Economics Scraper Configuration

# HTTP Timeout Configuration (seconds)
HTTP_TIMEOUT = 30.0

# Retry Configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 0.5,
    "status_forcelist": [429, 500, 502, 503, 504],
}

# Rate Limiting (seconds between requests)
RATE_LIMIT_DELAY = 5.0

# User-Agent Rotation List
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Base Headers (User-Agent will be rotated)
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Page Element Selectors
SELECTORS = {
    # Core selector for all market panels
    "product_list": ".product-item, .product-card, .ec-product",
    "product_name": ".product-title, .name, h3, h2",
    "product_price": ".price, .amount, [class*='price']",
    "product_image": "img[data-src], img.lazy, img",
    "next_page": ".pagination .next, a[rel='next'], .pagination a:last-child",
    
    # Forex selectors
    "forex_panel": "#fx, .forex-panel, #currencies",
    "forex_rows": "#fx tbody tr, .forex-panel tbody tr",
    "forex_symbol": "td:nth-child(1), .symbol, [data-symbol]",
    "forex_name": "td:nth-child(2), .name",
    "forex_price": "td:nth-child(3), .price, .last",
    "forex_change": "td:nth-child(4), .change",
    "forex_pct_change": "td:nth-child(5), .pct-change, [data-pct]",
    
    # Indices selectors
    "indices_panel": "#indexes, .indices-panel",
    "indices_rows": "#indexes tbody tr, .indices-panel tbody tr",
    "indices_symbol": "td:nth-child(1), .symbol",
    "indices_name": "td:nth-child(2), .name",
    "indices_price": "td:nth-child(3), .price",
    
    # Commodities selectors
    "commodities_panel": "#commodities, .commodities-panel",
    "commodities_rows": "#commodities tbody tr, .commodities-panel tbody tr",
    
    # Bonds selectors
    "bonds_panel": "#bonds, .bonds-panel",
    "bonds_rows": "#bonds tbody tr, .bonds-panel tbody tr",
    "bonds_yield": "td:nth-child(3), .yield",
    
    # Crypto selectors
    "crypto_panel": "#crypto, .crypto-panel",
    "crypto_rows": "#crypto tbody tr, .crypto-panel tbody tr",
    
    # Stocks selectors
    "stocks_panel": "#stocks, .stocks-panel",
    "stocks_rows": "#stocks tbody tr, .stocks-panel tbody tr",
    
    # ETFs selectors
    "etfs_panel": "#etfs, #etf, .etfs-panel, .etf-panel",
    "etfs_rows": "#etfs tbody tr, #etf tbody tr, .etfs-panel tbody tr",
    "etfs_symbol": "td:nth-child(1), .symbol, a:first-child",
    "etfs_name": "td:nth-child(2), .name",
    "etfs_price": "td:nth-child(3), .price",
    "etfs_change": "td:nth-child(4), .change",
    "etfs_pct_change": "td:nth-child(5), .pct-change",
    
    # Derivatives selectors
    "derivatives_panel": "#futures, #derivatives, #options, .futures-panel, .derivatives-panel",
    "derivatives_rows": "#futures tbody tr, #derivatives tbody tr, .futures-panel tbody tr",
    "derivatives_symbol": "td:nth-child(1), .symbol",
    "derivatives_name": "td:nth-child(2), .name",
    "derivatives_price": "td:nth-child(3), .price, .future-price",
    "derivatives_change": "td:nth-child(4), .change",
    "derivatives_pct_change": "td:nth-child(5), .pct-change",
    
    # Macro selectors
    "macro_panel": "#macro, .macro-panel",
    "macro_table": ".macro-table, #macro table",
    "macro_country": "td:nth-child(1), .country",
    "macro_indicator": "th:nth-child(n+2), .indicator",
    "macro_value": ".data-table, td:not(.country)",
    
    # News selectors
    "news_panel": ".news-section, #news",
    "news_article": ".news-item, article.news, .article-item",
    "news_title": "h3, h2, .title, .headline",
    "news_summary": ".summary, .excerpt, .description, p",
    "news_date": ".news-date, time, .date",
    "news_url": "a[href]",
    
    # Common table selectors
    "table_header": "thead th, tr:first-child th",
    "table_row": "tbody tr, tr.row-data",
    "table_cell": "td, th",
}
