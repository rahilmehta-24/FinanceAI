"""
News Service for fetching financial news
Uses yfinance for news (no API key required) with optional NewsAPI fallback
"""
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
NEWS_API_KEY = os.getenv('NEWS_API_KEY')


def get_stock_news_yf(symbol, limit=5):
    """Get news for a stock using yfinance (no API key required)
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE.NS')
        limit: Maximum number of news items
        
    Returns:
        list: List of news items with title, link, source, date
    """
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        news = ticker.news
        
        if not news:
            return []
        
        news_items = []
        for item in news[:limit]:
            published = datetime.fromtimestamp(item.get('providerPublishTime', 0))
            
            news_items.append({
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'source': item.get('publisher', 'Unknown'),
                'published': published.strftime('%Y-%m-%d %H:%M'),
                'published_display': published.strftime('%d %b, %I:%M %p'),
                'thumbnail': item.get('thumbnail', {}).get('resolutions', [{}])[0].get('url', ''),
                'symbol': symbol
            })
        
        return news_items
        
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        return []


def get_portfolio_news(symbols, limit_per_stock=3, total_limit=15):
    """Get aggregated news for portfolio holdings
    
    Args:
        symbols: List of stock symbols
        limit_per_stock: Max news per stock
        total_limit: Max total news items
        
    Returns:
        list: Aggregated and sorted news items
    """
    all_news = []
    
    for symbol in symbols[:10]:  # Limit to 10 stocks to avoid timeouts
        news = get_stock_news_yf(symbol, limit_per_stock)
        all_news.extend(news)
    
    # Sort by date (most recent first)
    all_news.sort(key=lambda x: x.get('published', ''), reverse=True)
    
    # Deduplicate by title
    seen_titles = set()
    unique_news = []
    for item in all_news:
        title = item.get('title', '').lower()
        if title not in seen_titles:
            seen_titles.add(title)
            unique_news.append(item)
    
    return unique_news[:total_limit]


def get_market_news(limit=10):
    """Get general market news (Indian market focus)
    
    Uses index symbols to get market-wide news
    """
    market_symbols = ['^NSEI', '^BSESN']  # Nifty 50, Sensex
    
    all_news = []
    for symbol in market_symbols:
        news = get_stock_news_yf(symbol, limit // 2)
        all_news.extend(news)
    
    # Sort and deduplicate
    all_news.sort(key=lambda x: x.get('published', ''), reverse=True)
    
    seen_titles = set()
    unique_news = []
    for item in all_news:
        title = item.get('title', '').lower()
        if title not in seen_titles:
            seen_titles.add(title)
            unique_news.append(item)
    
    return unique_news[:limit]


def search_news(query, limit=10):
    """Search for news by keyword (uses NewsAPI if available)
    
    Args:
        query: Search term
        limit: Max results
        
    Returns:
        list: Search results
    """
    if not NEWS_API_KEY:
        # Fall back to yfinance market news
        return get_market_news(limit)
    
    try:
        import requests
        
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': query,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': limit,
            'apiKey': NEWS_API_KEY
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('status') != 'ok':
            return get_market_news(limit)
        
        news_items = []
        for article in data.get('articles', []):
            news_items.append({
                'title': article.get('title', ''),
                'link': article.get('url', ''),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'published': article.get('publishedAt', '')[:16].replace('T', ' '),
                'published_display': article.get('publishedAt', '')[:10],
                'thumbnail': article.get('urlToImage', ''),
                'symbol': 'MARKET'
            })
        
        return news_items
        
    except Exception as e:
        print(f"Error searching news: {e}")
        return get_market_news(limit)
