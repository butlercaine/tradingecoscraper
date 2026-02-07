"""
Headlines Parser

Parses news headlines and articles from HTML.
Extracts title, summary, timestamp, and URL into NewsArticle objects.
"""

from typing import List, Optional
from bs4 import BeautifulSoup
from bs4.element import Tag
from datetime import datetime
import re

from models import NewsArticle


def _parse_datetime(value: str) -> Optional[datetime]:
    """Parse various datetime formats into datetime object."""
    if not value or not value.strip():
        return None
    
    value = value.strip()
    
    # Common formats to try
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",      # ISO with timezone
        "%Y-%m-%dT%H:%M:%S",         # ISO without timezone
        "%Y-%m-%d %H:%M:%S",         # Space separator
        "%Y-%m-%d",                  # Date only
        "%B %d, %Y %H:%M",           # "January 15, 2024 14:30"
        "%B %d, %Y",                 # "January 15, 2024"
        "%d %B %Y %H:%M",            # "15 January 2024 14:30"
        "%d %B %Y",                  # "15 January 2024"
        "%m/%d/%Y %H:%M",            # "01/15/2024 14:30"
        "%m/%d/%Y",                  # "01/15/2024"
        "%d/%m/%Y %H:%M",            # "15/01/2024 14:30"
        "%d/%m/%Y",                  # "15/01/2024"
        "%d-%m-%Y %H:%M",            # "15-01-2024 14:30"
        "%d-%m-%Y",                  # "15-01-2024"
    ]
    
    # Try parsing with various formats
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    
    # Handle relative time like "2 hours ago", "Yesterday", etc.
    now = datetime.now()
    value_lower = value.lower()
    
    if 'hour' in value_lower or 'hr' in value_lower:
        match = re.search(r'(\d+)', value)
        if match:
            hours = int(match.group(1))
            return now.replace(minute=0, second=0, microsecond=0)
    
    if 'minute' in value_lower or 'min' in value_lower:
        match = re.search(r'(\d+)', value)
        if match:
            minutes = int(match.group(1))
            return now.replace(second=0, microsecond=0)
    
    if 'yesterday' in value_lower:
        return now.replace(day=now.day - 1, hour=0, minute=0, second=0, microsecond=0)
    
    if 'day' in value_lower:
        match = re.search(r'(\d+)', value)
        if match:
            days = int(match.group(1))
            return now.replace(day=now.day - days, hour=0, minute=0, second=0, microsecond=0)
    
    return None


def _extract_timestamp_from_element(element: Tag) -> Optional[datetime]:
    """Try to extract timestamp from element attributes or children."""
    # Check common attributes
    for attr in ['data-time', 'datetime', 'timestamp', 'pubdate']:
        if element.has_attr(attr):
            dt = _parse_datetime(element[attr])
            if dt:
                return dt
    
    # Check for time tag
    time_tag = element.find('time')
    if time_tag and time_tag.has_attr('datetime'):
        dt = _parse_datetime(time_tag['datetime'])
        if dt:
            return dt
        # Check datetime attribute
        dt = _parse_datetime(time_tag.get_text(strip=True))
        if dt:
            return dt
    
    # Look for time-like text in element
    text = element.get_text(strip=True)
    time_patterns = [
        r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2})',  # ISO-like
        r'(\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?)',    # Time only
        r'(\d{1,2}\s*(?:hours?|hrs?|minutes?|mins?)\s*ago)',  # Relative
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            dt = _parse_datetime(match.group(1))
            if dt:
                return dt
    
    return None


def _find_headline_articles(soup: BeautifulSoup) -> List[Tag]:
    """Find all headline article elements."""
    # Strategy 1: Look for article tags
    articles = soup.find_all('article')
    if articles:
        return articles
    
    # Strategy 2: Look for common headline classes
    headline_classes = [
        'headline',
        'news-item',
        'article-item',
        'news-article',
        'headline-item',
        'story',
        'news-story',
        'feed-item',
        'post-preview',
    ]
    
    for cls in headline_classes:
        elements = soup.find_all(class_=lambda c: c and cls in str(c).lower())
        if elements:
            return elements
    
    # Strategy 3: Look for h1, h2, h3 with links (headline pattern)
    headline_tags = soup.find_all(['h1', 'h2', 'h3'])
    headlines = []
    for tag in headline_tags:
        if tag.find('a') and len(tag.get_text(strip=True)) > 10:
            # Get parent article/container
            parent = tag.find_parent(['div', 'section', 'article', 'li'])
            if parent and parent not in headlines:
                headlines.append(parent)
    
    if headlines:
        return headlines
    
    # Strategy 4: Look for links in news sections
    news_sections = soup.find_all(string=lambda t: t and 'news' in t.lower())
    for section_text in news_sections:
        parent = section_text.find_parent()
        if parent:
            links = parent.find_all('a')
            if links:
                containers = []
                for link in links[:5]:  # Limit to first 5
                    container = link.find_parent(['div', 'li', 'article'])
                    if container and container not in containers:
                        containers.append(container)
                if containers:
                    return containers
    
    # Fallback: Return all links that look like articles
    all_links = soup.find_all('a', href=lambda h: h and any(x in h for x in ['/news/', '/article', '/story', '/2024', '/2025']))
    if all_links:
        containers = []
        for link in all_links[:5]:
            container = link.find_parent(['div', 'li', 'article'])
            if container and container not in containers:
                containers.append(container)
        if containers:
            return containers
    
    return []


def _extract_article_from_element(element: Tag) -> Optional[NewsArticle]:
    """Extract NewsArticle data from an article element."""
    try:
        # Find title - look for h1, h2, h3, or strong text
        title = None
        for tag in ['h1', 'h2', 'h3', 'h4']:
            title_elem = element.find(tag)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        # If no heading, try first substantial text
        if not title:
            text_elem = element.find(['strong', 'b', '.title', '.headline'])
            if text_elem:
                title = text_elem.get_text(strip=True)
        
        if not title:
            # Last resort: use link text
            link = element.find('a')
            if link:
                title = link.get_text(strip=True)
        
        if not title or len(title) < 5:
            return None
        
        # Find URL
        url = None
        link = element.find('a', href=True)
        if link:
            href = link['href']
            # Make absolute URL
            if href.startswith('/'):
                # Try to find base URL
                base = element.find_parent('html')
                if base:
                    base_tag = base.find('base', href=True)
                    if base_tag:
                        url = base_tag['href'] + href
                    else:
                        # Use a reasonable default
                        url = f"https://tradingeconomics.com{href}"
                else:
                    url = f"https://tradingeconomics.com{href}"
            elif href.startswith('http'):
                url = href
        
        if not url:
            return None
        
        # Find summary - look for paragraph, div, or excerpt
        summary = None
        for tag in ['p', '.summary', '.excerpt', '.description', '.snippet']:
            elem = element.find(tag)
            if elem:
                summary = elem.get_text(strip=True)
                # Limit summary length
                if summary and len(summary) > 500:
                    summary = summary[:497] + "..."
                break
        
        # Find timestamp
        timestamp = _extract_timestamp_from_element(element)
        if not timestamp:
            timestamp = datetime.utcnow()
        
        # Extract source if available
        source = None
        source_elem = element.find(['span', 'div', 'a'], class_=lambda c: c and 'source' in str(c).lower())
        if source_elem:
            source = source_elem.get_text(strip=True)
        
        # Extract category if available
        category = None
        cat_elem = element.find(['span', 'div', 'a'], class_=lambda c: c and any(x in str(c).lower() for x in ['category', 'tag', 'topic']))
        if cat_elem:
            category = cat_elem.get_text(strip=True)
        
        return NewsArticle(
            title=title,
            summary=summary,
            timestamp=timestamp,
            url=url,
            source=source,
            category=category,
        )
    except (ValueError, TypeError, AttributeError, KeyError):
        return None


def parse_headlines(html: str, limit: int = 3) -> List[NewsArticle]:
    """
    Parse news headlines from HTML.
    
    Args:
        html: HTML content to parse
        limit: Maximum number of headlines to return (default 3)
        
    Returns:
        List of NewsArticle objects (may be fewer than limit if unavailable)
    """
    articles = []
    soup = BeautifulSoup(html, "lxml")
    
    # Remove unwanted elements (ads, scripts, styles)
    for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()
    
    # Find all headline elements
    headline_elements = _find_headline_articles(soup)
    
    for element in headline_elements[:limit]:
        article = _extract_article_from_element(element)
        if article:
            articles.append(article)
    
    return articles


def parse_all_news_categories(html: str) -> dict:
    """
    Parse news into categories: market_headlines, earnings_announcements, dividend_news.
    
    Returns:
        dict with keys: 'market_headlines', 'earnings_announcements', 'dividend_news'
    """
    soup = BeautifulSoup(html, "lxml")
    
    result = {
        "market_headlines": [],
        "earnings_announcements": [],
        "dividend_news": [],
    }
    
    # Find main news sections
    news_sections = soup.find_all(['section', 'div'], class_=lambda c: c and any(
        x in str(c).lower() for x in ['news', 'headlines', 'articles', 'stories']
    ))
    
    for section in news_sections:
        section_text = section.get_text(strip=True).lower()
        
        # Determine category
        category = "market_headlines"
        if any(x in section_text for x in ['earning', 'quarterly results', 'q1', 'q2', 'q3', 'q4', 'eps']):
            category = "earnings_announcements"
        elif any(x in section_text for x in ['dividend', 'payout', 'yield']):
            category = "dividend_news"
        
        # Parse articles in this section
        articles = section.find_all(['article', 'div', 'li'], class_=lambda c: c and any(
            x in str(c).lower() for x in ['item', 'article', 'story', 'post', 'headline']
        ))
        
        for elem in articles[:5]:  # Limit per section
            article = _extract_article_from_element(elem)
            if article:
                result[category].append(article)
    
    # If no structured sections found, parse all headlines and categorize by keywords
    if not result["market_headlines"] and not result["earnings_announcements"] and not result["dividend_news"]:
        all_articles = parse_headlines(html, limit=10)
        
        for article in all_articles:
            text = (article.title + " " + (article.summary or "")).lower()
            
            if any(x in text for x in ['earning', 'quarterly', 'eps', 'profit', 'revenue']):
                result["earnings_announcements"].append(article)
            elif any(x in text for x in ['dividend', 'payout', 'shareholder', 'yield']):
                result["dividend_news"].append(article)
            else:
                result["market_headlines"].append(article)
    
    return result
