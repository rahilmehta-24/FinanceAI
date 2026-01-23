import yfinance as yf
import random
from datetime import datetime, timedelta
from functools import lru_cache
import time

def get_stock_market(symbol):
    """
    Determine market and currency based on stock symbol
    Application restricted to Indian stocks only
    
    Args:
        symbol: Stock ticker symbol (e.g., 'TCS.NS', 'RELIANCE.NS')
    
    Returns:
        dict: {'market': 'IN', 'currency': '₹', 'currency_code': 'INR'}
    """
    # Always return Indian market - application restricted to Indian stocks only
    return {
        'market': 'IN',
        'currency': '₹',
        'currency_code': 'INR'
    }


def validate_indian_stock(symbol):
    """
    Validate that the stock symbol is an Indian stock
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        bool: True if valid Indian stock, False otherwise
    """
    if not symbol:
        return False
    
    # Must end with .NS (NSE) or .BO (BSE)
    return symbol.upper().endswith('.NS') or symbol.upper().endswith('.BO')



# Cache for storing stock prices with timestamps
_price_cache = {}
_cache_ttl = 300  # 5 minutes cache

# Fallback stock data - Indian NSE stocks only (used when API fails or for unknown symbols)
STOCK_DATA = {
    # Technology / IT Services
    'TCS.NS': {'name': 'Tata Consultancy Services', 'sector': 'Technology', 'price': 3850.00, 'change': 22.30},
    'INFY.NS': {'name': 'Infosys Ltd', 'sector': 'Technology', 'price': 1580.00, 'change': -8.20},
    'WIPRO.NS': {'name': 'Wipro Ltd', 'sector': 'Technology', 'price': 485.00, 'change': -3.20},
    'HCLTECH.NS': {'name': 'HCL Technologies', 'sector': 'Technology', 'price': 1650.00, 'change': 12.50},
    'TECHM.NS': {'name': 'Tech Mahindra', 'sector': 'Technology', 'price': 1280.00, 'change': 8.40},
    'LTIM.NS': {'name': 'LTIMindtree Ltd', 'sector': 'Technology', 'price': 5200.00, 'change': 35.00},
    
    # Financial Services / Banking
    'HDFCBANK.NS': {'name': 'HDFC Bank Ltd', 'sector': 'Financial Services', 'price': 1680.00, 'change': 12.40},
    'ICICIBANK.NS': {'name': 'ICICI Bank Ltd', 'sector': 'Financial Services', 'price': 1120.00, 'change': 8.60},
    'SBIN.NS': {'name': 'State Bank of India', 'sector': 'Financial Services', 'price': 780.00, 'change': 5.80},
    'KOTAKBANK.NS': {'name': 'Kotak Mahindra Bank', 'sector': 'Financial Services', 'price': 1850.00, 'change': -5.20},
    'AXISBANK.NS': {'name': 'Axis Bank Ltd', 'sector': 'Financial Services', 'price': 1150.00, 'change': 7.30},
    'BAJFINANCE.NS': {'name': 'Bajaj Finance Ltd', 'sector': 'Financial Services', 'price': 6850.00, 'change': 45.00},
    
    # Energy / Oil & Gas
    'RELIANCE.NS': {'name': 'Reliance Industries', 'sector': 'Energy', 'price': 2450.00, 'change': 15.50},
    'ONGC.NS': {'name': 'Oil & Natural Gas Corp', 'sector': 'Energy', 'price': 285.00, 'change': 3.20},
    'BPCL.NS': {'name': 'Bharat Petroleum', 'sector': 'Energy', 'price': 620.00, 'change': 8.50},
    'IOC.NS': {'name': 'Indian Oil Corporation', 'sector': 'Energy', 'price': 168.00, 'change': 2.10},
    'POWERGRID.NS': {'name': 'Power Grid Corp', 'sector': 'Energy', 'price': 310.00, 'change': 4.50},
    
    # Consumer Goods / FMCG
    'HINDUNILVR.NS': {'name': 'Hindustan Unilever', 'sector': 'Consumer Defensive', 'price': 2580.00, 'change': -12.50},
    'ITC.NS': {'name': 'ITC Ltd', 'sector': 'Consumer Defensive', 'price': 465.00, 'change': 2.80},
    'NESTLEIND.NS': {'name': 'Nestle India', 'sector': 'Consumer Defensive', 'price': 2450.00, 'change': 18.00},
    'BRITANNIA.NS': {'name': 'Britannia Industries', 'sector': 'Consumer Defensive', 'price': 5100.00, 'change': 25.00},
    'DABUR.NS': {'name': 'Dabur India Ltd', 'sector': 'Consumer Defensive', 'price': 565.00, 'change': 3.20},
    
    # Pharma / Healthcare
    'SUNPHARMA.NS': {'name': 'Sun Pharmaceutical', 'sector': 'Healthcare', 'price': 1480.00, 'change': 12.30},
    'DRREDDY.NS': {'name': 'Dr. Reddys Laboratories', 'sector': 'Healthcare', 'price': 6200.00, 'change': -28.00},
    'CIPLA.NS': {'name': 'Cipla Ltd', 'sector': 'Healthcare', 'price': 1520.00, 'change': 8.50},
    'APOLLOHOSP.NS': {'name': 'Apollo Hospitals', 'sector': 'Healthcare', 'price': 6800.00, 'change': 45.00},
    
    # Automobiles
    'TATAPOWER.NS': {'name': 'Tata Power Ltd', 'sector': 'Energy', 'price': 420.00, 'change': 8.50},
    'MARUTI.NS': {'name': 'Maruti Suzuki India', 'sector': 'Automobiles', 'price': 11500.00, 'change': 85.00},
    'M&M.NS': {'name': 'Mahindra & Mahindra', 'sector': 'Automobiles', 'price': 2850.00, 'change': 22.00},
    'BAJAJ-AUTO.NS': {'name': 'Bajaj Auto Ltd', 'sector': 'Automobiles', 'price': 8500.00, 'change': -35.00},
    
    # Telecom / Communication
    'BHARTIARTL.NS': {'name': 'Bharti Airtel Ltd', 'sector': 'Communication Services', 'price': 1420.00, 'change': 18.90},
    
    # Metals & Mining
    'TATASTEEL.NS': {'name': 'Tata Steel Ltd', 'sector': 'Metals', 'price': 165.00, 'change': 2.80},
    'HINDALCO.NS': {'name': 'Hindalco Industries', 'sector': 'Metals', 'price': 620.00, 'change': 8.50},
    'JSWSTEEL.NS': {'name': 'JSW Steel Ltd', 'sector': 'Metals', 'price': 920.00, 'change': 12.00},
    
    # Infrastructure / Construction
    'LT.NS': {'name': 'Larsen & Toubro', 'sector': 'Infrastructure', 'price': 3550.00, 'change': 28.00},
    'ULTRACEMCO.NS': {'name': 'UltraTech Cement', 'sector': 'Infrastructure', 'price': 11200.00, 'change': 65.00},
    
    # Conglomerates
    'ADANIENT.NS': {'name': 'Adani Enterprises', 'sector': 'Conglomerates', 'price': 2850.00, 'change': -25.00},
    'ADANIPORTS.NS': {'name': 'Adani Ports & SEZ', 'sector': 'Infrastructure', 'price': 1380.00, 'change': 18.50},
}



def _get_cached_price(symbol):
    """Get price from cache if it's still valid"""
    if symbol in _price_cache:
        cached_data = _price_cache[symbol]
        if time.time() - cached_data['timestamp'] < _cache_ttl:
            return cached_data['price']
    return None


def _set_cached_price(symbol, price):
    """Store price in cache"""
    _price_cache[symbol] = {
        'price': price,
        'timestamp': time.time()
    }


def fetch_real_time_price(symbol):
    """Fetch real-time price for a single stock using yfinance"""
    try:
        # Check cache first
        cached_price = _get_cached_price(symbol)
        if cached_price is not None:
            return cached_price
        
        # Fetch from yfinance
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        
        # Try to get current price
        current_price = None
        if hasattr(info, 'last_price') and info.last_price:
            current_price = info.last_price
        elif hasattr(info, 'previous_close') and info.previous_close:
            current_price = info.previous_close
        
        if current_price and current_price > 0:
            _set_cached_price(symbol, round(current_price, 2))
            return round(current_price, 2)
        
        return None
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None


def fetch_multiple_stocks(symbols):
    """Batch fetch prices for multiple symbols (more efficient)"""
    prices = {}
    symbols_to_fetch = []
    
    # Check cache first
    for symbol in symbols:
        cached_price = _get_cached_price(symbol)
        if cached_price is not None:
            prices[symbol] = cached_price
        else:
            symbols_to_fetch.append(symbol)
    
    # Fetch remaining from API
    if symbols_to_fetch:
        try:
            # Batch download using yfinance
            tickers = yf.Tickers(' '.join(symbols_to_fetch))
            
            for symbol in symbols_to_fetch:
                try:
                    ticker = tickers.tickers.get(symbol)
                    if ticker:
                        info = ticker.fast_info
                        current_price = None
                        
                        if hasattr(info, 'last_price') and info.last_price:
                            current_price = info.last_price
                        elif hasattr(info, 'previous_close') and info.previous_close:
                            current_price = info.previous_close
                        
                        if current_price and current_price > 0:
                            prices[symbol] = round(current_price, 2)
                            _set_cached_price(symbol, round(current_price, 2))
                except Exception as e:
                    print(f"Error fetching {symbol}: {e}")
                    
        except Exception as e:
            print(f"Error in batch fetch: {e}")
    
    return prices


def get_current_prices(symbols):
    """Get current prices for given symbols - uses real API with fallback
    
    Returns:
        dict: {symbol: {'price': float, 'currency': str, 'currency_code': str, 'market': str}}
    """
    prices = {}
    
    if not symbols:
        return prices
    
    # Try to fetch real prices
    real_prices = fetch_multiple_stocks(symbols)
    
    for symbol in symbols:
        market_info = get_stock_market(symbol)
        
        if symbol in real_prices and real_prices[symbol]:
            price = real_prices[symbol]
        elif symbol in STOCK_DATA:
            # Fallback to simulated data with slight variation
            base_price = STOCK_DATA[symbol]['price']
            variation = random.uniform(-0.02, 0.02)
            price = round(base_price * (1 + variation), 2)
        else:
            # For completely unknown symbols, try individual fetch
            price = fetch_real_time_price(symbol)
            if not price:
                # Last resort: generate a placeholder
                price = round(random.uniform(50, 500), 2)
        
        prices[symbol] = {
            'price': price,
            'currency': market_info['currency'],
            'currency_code': market_info['currency_code'],
            'market': market_info['market']
        }
    
    return prices


# Dividend cache
_dividend_cache = {}
_dividend_cache_ttl = 3600  # 1 hour cache for dividends (changes less frequently)


def get_dividend_info(symbols):
    """Get annual dividend per share for given symbols
    
    Args:
        symbols: List of stock symbols
        
    Returns:
        dict: {symbol: dividend_per_share} - Annual dividend amount per share
    """
    dividends = {}
    
    if not symbols:
        return dividends
    
    symbols_to_fetch = []
    
    # Check cache first
    for symbol in symbols:
        if symbol in _dividend_cache:
            cached = _dividend_cache[symbol]
            if time.time() - cached['timestamp'] < _dividend_cache_ttl:
                dividends[symbol] = cached['dividend']
            else:
                symbols_to_fetch.append(symbol)
        else:
            symbols_to_fetch.append(symbol)
    
    # Fetch remaining from API
    for symbol in symbols_to_fetch:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get annual dividend rate (per share)
            # dividendRate is the annual dividend amount per share
            dividend_rate = info.get('dividendRate', 0) or 0
            
            dividends[symbol] = round(dividend_rate, 2)
            _dividend_cache[symbol] = {
                'dividend': round(dividend_rate, 2),
                'timestamp': time.time()
            }
        except Exception as e:
            print(f"Error fetching dividend for {symbol}: {e}")
            dividends[symbol] = 0
            _dividend_cache[symbol] = {
                'dividend': 0,
                'timestamp': time.time()
            }
    
    return dividends


def get_stock_info(symbol):
    """Get detailed stock information"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        fast_info = ticker.fast_info
        
        return {
            'symbol': symbol,
            'name': info.get('longName', info.get('shortName', symbol)),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'price': fast_info.last_price if hasattr(fast_info, 'last_price') else 0,
            'previous_close': fast_info.previous_close if hasattr(fast_info, 'previous_close') else 0,
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0),
        }
    except Exception as e:
        print(f"Error getting stock info for {symbol}: {e}")
        if symbol in STOCK_DATA:
            return {
                'symbol': symbol,
                'name': STOCK_DATA[symbol]['name'],
                'sector': STOCK_DATA[symbol]['sector'],
                'price': STOCK_DATA[symbol]['price'],
            }
        return None


def get_top_gainers(limit=10):
    """Get top gaining stocks from predefined list"""
    stocks = []
    
    # Get real prices for all stocks
    symbols = list(STOCK_DATA.keys())
    current_prices = fetch_multiple_stocks(symbols)
    
    for symbol, data in STOCK_DATA.items():
        market_info = get_stock_market(symbol)
        current_price = current_prices.get(symbol, data['price'])
        base_price = data['price']
        change = current_price - base_price
        change_pct = (change / base_price) * 100 if base_price > 0 else 0
        
        stocks.append({
            'symbol': symbol,
            'name': data['name'],
            'price': current_price,
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
            'sector': data['sector'],
            'currency': market_info['currency']
        })
    
    # Sort by change percentage descending
    stocks.sort(key=lambda x: x['change_pct'], reverse=True)
    return stocks[:limit]


def get_top_losers(limit=10):
    """Get top losing stocks from predefined list"""
    stocks = []
    
    # Get real prices for all stocks
    symbols = list(STOCK_DATA.keys())
    current_prices = fetch_multiple_stocks(symbols)
    
    for symbol, data in STOCK_DATA.items():
        market_info = get_stock_market(symbol)
        current_price = current_prices.get(symbol, data['price'])
        base_price = data['price']
        change = current_price - base_price
        change_pct = (change / base_price) * 100 if base_price > 0 else 0
        
        stocks.append({
            'symbol': symbol,
            'name': data['name'],
            'price': current_price,
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
            'sector': data['sector'],
            'currency': market_info['currency']
        })
    
    # Sort by change percentage ascending
    stocks.sort(key=lambda x: x['change_pct'])
    return stocks[:limit]


def get_stock_recommendations():
    """Get stock recommendations (informational only, no buy/hold/sell)"""
    recommendations = []
    symbols = list(STOCK_DATA.keys())[:15]
    current_prices = fetch_multiple_stocks(symbols)
    
    for symbol in symbols:
        data = STOCK_DATA[symbol]
        market_info = get_stock_market(symbol)
        current_price = current_prices.get(symbol, data['price'])
        
        recommendations.append({
            'symbol': symbol,
            'name': data['name'],
            'sector': data['sector'],
            'price': current_price,
            'daily_change': data['change'],
            'analysis': get_stock_analysis(symbol),
            'currency': market_info['currency']
        })
    return recommendations


def get_stock_analysis(symbol):
    """Get AI-generated analysis text for a stock (informational only)"""
    analyses = [
        "Strong fundamentals with consistent revenue growth.",
        "Market leader in its sector with competitive advantages.",
        "Stable dividend history and solid balance sheet.",
        "Growing market share with innovative products.",
        "Well-positioned for long-term sector growth.",
        "Diversified revenue streams reduce volatility.",
        "Strong institutional investor interest.",
        "Resilient business model with recurring revenue.",
    ]
    return random.choice(analyses)


def get_sector_distribution():
    """Get sector distribution of all stocks"""
    sectors = {}
    for symbol, data in STOCK_DATA.items():
        sector = data['sector']
        sectors[sector] = sectors.get(sector, 0) + 1
    return sectors


def get_portfolio_summary(holdings):
    """Calculate portfolio summary statistics with real-time prices"""
    if not holdings:
        return {
            'total_invested': 0,
            'current_value': 0,
            'total_gain_loss': 0,
            'total_gain_loss_pct': 0,
            'holdings_count': 0,
            'sectors': {}
        }
    
    current_prices = get_current_prices([h.symbol for h in holdings])
    
    total_invested = 0
    current_value = 0
    sectors = {}
    
    for h in holdings:
        invested = h.quantity * h.buy_price
        
        # Handle new price data structure
        price_data = current_prices.get(h.symbol, {'price': h.buy_price})
        price = price_data['price'] if isinstance(price_data, dict) else price_data
        current = h.quantity * price
        
        total_invested += invested
        current_value += current
        
        sector = h.sector or 'Other'
        sectors[sector] = sectors.get(sector, 0) + current
    
    total_gain_loss = current_value - total_invested
    total_gain_loss_pct = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
    
    return {
        'total_invested': round(total_invested, 2),
        'current_value': round(current_value, 2),
        'total_gain_loss': round(total_gain_loss, 2),
        'total_gain_loss_pct': round(total_gain_loss_pct, 2),
        'holdings_count': len(holdings),
        'sectors': sectors
    }


def clear_price_cache():
    """Clear the price cache - useful for forcing fresh data"""
    global _price_cache
    _price_cache = {}
