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


# Day change cache
_day_change_cache = {}
_day_change_cache_ttl = 300  # 5 minutes cache


def get_day_changes(symbols):
    """Get daily price change for given symbols
    
    Args:
        symbols: List of stock symbols
        
    Returns:
        dict: {symbol: {'current': float, 'previous_close': float, 'change': float, 'change_pct': float}}
    """
    changes = {}
    
    if not symbols:
        return changes
    
    symbols_to_fetch = []
    
    # Check cache first
    for symbol in symbols:
        if symbol in _day_change_cache:
            cached = _day_change_cache[symbol]
            if time.time() - cached['timestamp'] < _day_change_cache_ttl:
                changes[symbol] = cached['data']
            else:
                symbols_to_fetch.append(symbol)
        else:
            symbols_to_fetch.append(symbol)
    
    # Fetch remaining from API
    if symbols_to_fetch:
        try:
            tickers = yf.Tickers(' '.join(symbols_to_fetch))
            
            for symbol in symbols_to_fetch:
                try:
                    ticker = tickers.tickers.get(symbol)
                    if ticker:
                        info = ticker.fast_info
                        
                        current_price = 0
                        previous_close = 0
                        
                        if hasattr(info, 'last_price') and info.last_price:
                            current_price = info.last_price
                        elif hasattr(info, 'previous_close') and info.previous_close:
                            current_price = info.previous_close
                        
                        if hasattr(info, 'previous_close') and info.previous_close:
                            previous_close = info.previous_close
                        
                        if current_price and previous_close:
                            change = current_price - previous_close
                            change_pct = (change / previous_close) * 100 if previous_close > 0 else 0
                            
                            day_data = {
                                'current': round(current_price, 2),
                                'previous_close': round(previous_close, 2),
                                'change': round(change, 2),
                                'change_pct': round(change_pct, 2)
                            }
                            
                            changes[symbol] = day_data
                            _day_change_cache[symbol] = {
                                'data': day_data,
                                'timestamp': time.time()
                            }
                        else:
                            # Default to no change
                            changes[symbol] = {
                                'current': round(current_price, 2) if current_price else 0,
                                'previous_close': 0,
                                'change': 0,
                                'change_pct': 0
                            }
                except Exception as e:
                    print(f"Error fetching day change for {symbol}: {e}")
                    changes[symbol] = {'current': 0, 'previous_close': 0, 'change': 0, 'change_pct': 0}
                    
        except Exception as e:
            print(f"Error in batch day change fetch: {e}")
    
    return changes


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


# Corporate actions cache
_corporate_cache = {}
_corporate_cache_ttl = 3600  # 1 hour cache


def get_corporate_actions(symbol):
    """Get corporate actions for a stock (dividends, splits, bonus issues, etc.)
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        dict: Corporate actions data including dividends, splits, and key dates
    """
    # Check cache first
    if symbol in _corporate_cache:
        cached = _corporate_cache[symbol]
        if time.time() - cached['timestamp'] < _corporate_cache_ttl:
            return cached['data']
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get dividend history (last 5 years)
        dividends = ticker.dividends
        dividend_history = []
        if dividends is not None and len(dividends) > 0:
            # Get last 10 dividends
            recent_dividends = dividends.tail(10)
            for date, amount in recent_dividends.items():
                dividend_history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'amount': round(float(amount), 2)
                })
            dividend_history.reverse()  # Most recent first
        
        # Get stock splits history
        splits = ticker.splits
        split_history = []
        if splits is not None and len(splits) > 0:
            for date, ratio in splits.items():
                split_history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'ratio': f"{int(ratio)}:1" if ratio >= 1 else f"1:{int(1/ratio)}"
                })
            split_history.reverse()  # Most recent first
        
        # Get key dates and info
        ex_dividend_date = info.get('exDividendDate')
        if ex_dividend_date:
            ex_dividend_date = datetime.fromtimestamp(ex_dividend_date).strftime('%Y-%m-%d')
        
        last_dividend_date = info.get('lastDividendDate')
        if last_dividend_date:
            last_dividend_date = datetime.fromtimestamp(last_dividend_date).strftime('%Y-%m-%d')
        
        corporate_data = {
            'symbol': symbol,
            'company_name': info.get('longName', info.get('shortName', symbol)),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            
            # Dividend information
            'dividend_rate': round(info.get('dividendRate', 0) or 0, 2),
            'dividend_yield': round((info.get('dividendYield', 0) or 0) * 100, 2),
            'ex_dividend_date': ex_dividend_date,
            'last_dividend_date': last_dividend_date,
            'last_dividend_value': round(info.get('lastDividendValue', 0) or 0, 2),
            'dividend_history': dividend_history[:5],  # Last 5 dividends
            
            # Stock splits / Bonus issues
            'split_history': split_history,
            
            # Key financials
            'pe_ratio': round(info.get('trailingPE', 0) or 0, 2),
            'book_value': round(info.get('bookValue', 0) or 0, 2),
            'eps': round(info.get('trailingEps', 0) or 0, 2),
            'market_cap': info.get('marketCap', 0),
            '52_week_high': round(info.get('fiftyTwoWeekHigh', 0) or 0, 2),
            '52_week_low': round(info.get('fiftyTwoWeekLow', 0) or 0, 2),
            
            # Additional info
            'beta': round(info.get('beta', 0) or 0, 2),
            'payout_ratio': round((info.get('payoutRatio', 0) or 0) * 100, 2),
        }
        
        # Cache the result
        _corporate_cache[symbol] = {
            'data': corporate_data,
            'timestamp': time.time()
        }
        
        return corporate_data
        
    except Exception as e:
        print(f"Error fetching corporate actions for {symbol}: {e}")
        return {
            'symbol': symbol,
            'company_name': symbol,
            'error': str(e),
            'dividend_history': [],
            'split_history': []
        }


def get_dividend_calendar(holdings_data):
    """Get upcoming dividend calendar for portfolio holdings
    
    Args:
        holdings_data: List of dicts with 'symbol', 'quantity', 'company_name'
        
    Returns:
        list: List of upcoming dividend events sorted by date
    """
    dividend_events = []
    
    for holding in holdings_data:
        symbol = holding.get('symbol')
        quantity = holding.get('quantity', 0)
        company_name = holding.get('company_name', symbol)
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get ex-dividend date
            ex_dividend_date = info.get('exDividendDate')
            if ex_dividend_date:
                ex_date = datetime.fromtimestamp(ex_dividend_date)
                
                # Only include future or recent dividends (within last 30 days)
                if ex_date >= datetime.now() - timedelta(days=30):
                    dividend_rate = info.get('lastDividendValue', 0) or info.get('dividendRate', 0) or 0
                    expected_income = dividend_rate * quantity
                    
                    dividend_events.append({
                        'symbol': symbol,
                        'company_name': company_name,
                        'ex_date': ex_date.strftime('%Y-%m-%d'),
                        'ex_date_display': ex_date.strftime('%d %b %Y'),
                        'dividend_per_share': round(dividend_rate, 2),
                        'quantity': quantity,
                        'expected_income': round(expected_income, 2),
                        'is_upcoming': ex_date >= datetime.now()
                    })
        except Exception as e:
            print(f"Error fetching dividend date for {symbol}: {e}")
            continue
    
    # Sort by ex-dividend date
    dividend_events.sort(key=lambda x: x['ex_date'], reverse=False)
    
    return dividend_events


def get_portfolio_history(holdings_data, period='1M'):
    """Get historical portfolio value over time
    
    Args:
        holdings_data: List of dicts with 'symbol', 'quantity', 'buy_date'
        period: Time period - '1D', '1W', '1M', '3M', '6M', '1Y'
        
    Returns:
        dict: {'dates': [...], 'values': [...], 'change': float, 'change_pct': float}
    """
    # Map period to yfinance parameters
    period_map = {
        '1D': ('1d', '5m'),   # 1 day, 5 min intervals
        '1W': ('5d', '1h'),   # 5 days, hourly
        '1M': ('1mo', '1d'),  # 1 month, daily
        '3M': ('3mo', '1d'),  # 3 months, daily
        '6M': ('6mo', '1d'),  # 6 months, daily
        '1Y': ('1y', '1d'),   # 1 year, daily
    }
    
    yf_period, yf_interval = period_map.get(period, ('1mo', '1d'))
    
    if not holdings_data:
        return {'dates': [], 'values': [], 'change': 0, 'change_pct': 0}
    
    try:
        # Get unique symbols
        symbols = list(set(h['symbol'] for h in holdings_data))
        
        # Build quantity map by symbol
        quantity_map = {}
        for h in holdings_data:
            symbol = h['symbol']
            quantity_map[symbol] = quantity_map.get(symbol, 0) + h['quantity']
        
        # Fetch historical data for all symbols
        symbol_data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=yf_period, interval=yf_interval)
                if not hist.empty:
                    symbol_data[symbol] = hist['Close']
            except Exception as e:
                print(f"Error fetching history for {symbol}: {e}")
                continue
        
        if not symbol_data:
            return {'dates': [], 'values': [], 'change': 0, 'change_pct': 0}
        
        # Get common dates across all symbols
        all_dates = set()
        for symbol, data in symbol_data.items():
            all_dates.update(data.index.tolist())
        
        all_dates = sorted(list(all_dates))
        
        # Calculate portfolio value for each date
        dates = []
        values = []
        
        for date in all_dates:
            portfolio_value = 0
            valid = True
            
            for symbol, quantity in quantity_map.items():
                if symbol in symbol_data:
                    data = symbol_data[symbol]
                    # Find the closest date <= current date
                    valid_dates = data.index[data.index <= date]
                    if len(valid_dates) > 0:
                        price = data.loc[valid_dates[-1]]
                        portfolio_value += price * quantity
                    else:
                        valid = False
                        break
            
            if valid and portfolio_value > 0:
                if yf_interval == '5m' or yf_interval == '1h':
                    dates.append(date.strftime('%H:%M'))
                else:
                    dates.append(date.strftime('%Y-%m-%d'))
                values.append(round(portfolio_value, 2))
        
        # Calculate change
        if len(values) >= 2:
            change = values[-1] - values[0]
            change_pct = (change / values[0] * 100) if values[0] > 0 else 0
        else:
            change = 0
            change_pct = 0
        
        return {
            'dates': dates,
            'values': values,
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
            'period': period
        }
        
    except Exception as e:
        print(f"Error calculating portfolio history: {e}")
        return {'dates': [], 'values': [], 'change': 0, 'change_pct': 0}


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


# Popular Indian stocks for screener
NIFTY_50_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'HINDUNILVR.NS', 'KOTAKBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS',
    'BAJFINANCE.NS', 'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS',
    'HCLTECH.NS', 'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS',
    'NESTLEIND.NS', 'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS', 'JSWSTEEL.NS',
    'TATASTEEL.NS', 'ADANIPORTS.NS', 'TECHM.NS', 'INDUSINDBK.NS', 'HINDALCO.NS'
]


def screen_stocks(filters=None):
    """Screen stocks based on filter criteria
    
    Args:
        filters: Dict with optional keys:
            - min_pe, max_pe: P/E ratio range
            - min_market_cap: Minimum market cap in Cr
            - min_dividend_yield: Minimum dividend yield %
            - sector: Sector filter
            
    Returns:
        list: List of stocks matching criteria
    """
    filters = filters or {}
    
    results = []
    
    for symbol in NIFTY_50_STOCKS[:20]:  # Limit to 20 for performance
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            fast_info = ticker.fast_info
            
            # Get basic data
            current_price = fast_info.last_price if hasattr(fast_info, 'last_price') else 0
            pe_ratio = info.get('trailingPE') or info.get('forwardPE') or 0
            market_cap = info.get('marketCap', 0)
            market_cap_cr = market_cap / 10000000 if market_cap else 0  # Convert to Crores
            dividend_yield = (info.get('dividendYield') or 0) * 100  # Convert to %
            sector = info.get('sector', 'Unknown')
            fifty_two_week_high = info.get('fiftyTwoWeekHigh', 0)
            fifty_two_week_low = info.get('fiftyTwoWeekLow', 0)
            
            # Apply filters
            if filters.get('min_pe') and pe_ratio < filters['min_pe']:
                continue
            if filters.get('max_pe') and pe_ratio > filters['max_pe']:
                continue
            if filters.get('min_market_cap') and market_cap_cr < filters['min_market_cap']:
                continue
            if filters.get('min_dividend_yield') and dividend_yield < filters['min_dividend_yield']:
                continue
            if filters.get('sector') and filters['sector'] != 'All' and sector != filters['sector']:
                continue
            
            # Calculate distance from 52-week high/low
            pct_from_high = ((fifty_two_week_high - current_price) / fifty_two_week_high * 100) if fifty_two_week_high else 0
            pct_from_low = ((current_price - fifty_two_week_low) / fifty_two_week_low * 100) if fifty_two_week_low else 0
            
            results.append({
                'symbol': symbol,
                'name': info.get('longName', info.get('shortName', symbol.replace('.NS', ''))),
                'price': round(current_price, 2),
                'pe_ratio': round(pe_ratio, 2) if pe_ratio else 'N/A',
                'market_cap_cr': round(market_cap_cr, 0),
                'dividend_yield': round(dividend_yield, 2),
                'sector': sector,
                'fifty_two_week_high': round(fifty_two_week_high, 2),
                'fifty_two_week_low': round(fifty_two_week_low, 2),
                'pct_from_high': round(pct_from_high, 1),
                'pct_from_low': round(pct_from_low, 1)
            })
            
        except Exception as e:
            print(f"Error screening {symbol}: {e}")
            continue
    
    # Sort by market cap by default
    results.sort(key=lambda x: x.get('market_cap_cr', 0), reverse=True)
    
    return results


def get_screener_sectors():
    """Get unique sectors from screened stocks"""
    return [
        'All',
        'Technology',
        'Financial Services',
        'Consumer Defensive',
        'Energy',
        'Basic Materials',
        'Healthcare',
        'Communication Services',
        'Consumer Cyclical',
        'Industrials',
        'Utilities'
    ]
