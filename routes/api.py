from flask import Blueprint, jsonify, request
from flask_login import login_required
from services.stock_service import STOCK_DATA, get_stock_info
import yfinance as yf

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/stocks/search')
@login_required
def search_stocks():
    """Search stocks by symbol or name - used for autocomplete"""
    query = request.args.get('q', '').upper().strip()
    
    if not query or len(query) < 1:
        return jsonify([])
    
    results = []
    
    # Search in our Indian stock database
    for symbol, data in STOCK_DATA.items():
        # Match by symbol or company name
        if query in symbol.upper() or query in data['name'].upper():
            results.append({
                'symbol': symbol,
                'name': data['name'],
                'sector': data['sector']
            })
    
    # Limit results for performance
    return jsonify(results[:15])


@api_bp.route('/stocks/<symbol>')
@login_required
def get_stock_details(symbol):
    """Get comprehensive stock information"""
    try:
        symbol = symbol.upper().strip()
        
        # Add .NS suffix if not present for Indian stocks
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            # Try with .NS first (NSE)
            test_symbol = symbol + '.NS'
            if test_symbol in STOCK_DATA:
                symbol = test_symbol
        
        ticker = yf.Ticker(symbol)
        
        # Get stock info
        info = ticker.info
        fast_info = ticker.fast_info
        
        # Build comprehensive response
        stock_data = {
            'symbol': symbol,
            'name': info.get('longName', info.get('shortName', symbol)),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            
            # Price Information
            'price': {
                'current': fast_info.last_price if hasattr(fast_info, 'last_price') and fast_info.last_price else info.get('currentPrice', 0),
                'open': info.get('open', info.get('regularMarketOpen', 0)),
                'high': info.get('dayHigh', info.get('regularMarketDayHigh', 0)),
                'low': info.get('dayLow', info.get('regularMarketDayLow', 0)),
                'previous_close': info.get('previousClose', info.get('regularMarketPreviousClose', 0)),
                'change': 0,
                'change_percent': 0
            },
            
            # Volume
            'volume': {
                'current': info.get('volume', info.get('regularMarketVolume', 0)),
                'average': info.get('averageVolume', info.get('averageDailyVolume10Day', 0)),
                'average_10d': info.get('averageVolume10days', info.get('averageDailyVolume10Day', 0))
            },
            
            # Market Data
            'market': {
                'cap': info.get('marketCap', 0),
                'enterprise_value': info.get('enterpriseValue', 0),
                'shares_outstanding': info.get('sharesOutstanding', 0),
                'float_shares': info.get('floatShares', 0)
            },
            
            # Valuation Ratios
            'ratios': {
                'pe': info.get('trailingPE', info.get('forwardPE', 0)),
                'pe_forward': info.get('forwardPE', 0),
                'pb': info.get('priceToBook', 0),
                'ps': info.get('priceToSalesTrailing12Months', 0),
                'peg': info.get('pegRatio', 0),
                'eps': info.get('trailingEps', 0),
                'eps_forward': info.get('forwardEps', 0),
                'book_value': info.get('bookValue', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'roe': info.get('returnOnEquity', 0),
                'roa': info.get('returnOnAssets', 0),
                'profit_margin': info.get('profitMargins', 0),
                'operating_margin': info.get('operatingMargins', 0),
                'gross_margin': info.get('grossMargins', 0)
            },
            
            # Dividends
            'dividends': {
                'yield': info.get('dividendYield', 0),
                'rate': info.get('dividendRate', 0),
                'payout_ratio': info.get('payoutRatio', 0),
                'ex_date': str(info.get('exDividendDate', '')) if info.get('exDividendDate') else None
            },
            
            # 52-Week Range
            'week_52': {
                'high': info.get('fiftyTwoWeekHigh', 0),
                'low': info.get('fiftyTwoWeekLow', 0),
                'change': info.get('52WeekChange', 0)
            },
            
            # Moving Averages
            'moving_avg': {
                'ma_50': info.get('fiftyDayAverage', 0),
                'ma_200': info.get('twoHundredDayAverage', 0)
            },
            
            # Company Info
            'company': {
                'website': info.get('website', ''),
                'description': info.get('longBusinessSummary', '')[:500] if info.get('longBusinessSummary') else '',
                'employees': info.get('fullTimeEmployees', 0),
                'city': info.get('city', ''),
                'country': info.get('country', '')
            }
        }
        
        # Calculate price change
        if stock_data['price']['current'] and stock_data['price']['previous_close']:
            change = stock_data['price']['current'] - stock_data['price']['previous_close']
            change_pct = (change / stock_data['price']['previous_close']) * 100 if stock_data['price']['previous_close'] else 0
            stock_data['price']['change'] = round(change, 2)
            stock_data['price']['change_percent'] = round(change_pct, 2)
        
        return jsonify(stock_data)
        
    except Exception as e:
        print(f"Error fetching stock details for {symbol}: {e}")
        
        # Fallback to local data if available
        if symbol in STOCK_DATA:
            data = STOCK_DATA[symbol]
            return jsonify({
                'symbol': symbol,
                'name': data['name'],
                'sector': data['sector'],
                'price': {
                    'current': data['price'],
                    'change': data['change'],
                    'change_percent': round((data['change'] / data['price']) * 100, 2) if data['price'] else 0
                },
                'error': 'Limited data available'
            })
        
        return jsonify({'error': f'Stock not found: {symbol}'}), 404


@api_bp.route('/stocks/<symbol>/history')
@login_required
def get_stock_history(symbol):
    """Get historical price data for charts"""
    try:
        symbol = symbol.upper().strip()
        period = request.args.get('period', '1mo')  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
        interval = request.args.get('interval', None)
        
        # Add .NS suffix if not present for Indian stocks
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            test_symbol = symbol + '.NS'
            if test_symbol in STOCK_DATA:
                symbol = test_symbol
        
        # Determine interval based on period
        if interval is None:
            interval_map = {
                '1d': '5m',
                '5d': '15m',
                '1mo': '1d',
                '3mo': '1d',
                '6mo': '1d',
                '1y': '1wk',
                '2y': '1wk',
                '5y': '1mo',
                'max': '1mo'
            }
            interval = interval_map.get(period, '1d')
        
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period, interval=interval)
        
        if history.empty:
            return jsonify({'error': 'No historical data available'}), 404
        
        # Format data for charts
        data = []
        for date, row in history.iterrows():
            data.append({
                'date': date.strftime('%Y-%m-%d %H:%M') if interval in ['5m', '15m', '30m', '1h'] else date.strftime('%Y-%m-%d'),
                'timestamp': int(date.timestamp() * 1000),
                'open': round(row['Open'], 2) if row['Open'] else 0,
                'high': round(row['High'], 2) if row['High'] else 0,
                'low': round(row['Low'], 2) if row['Low'] else 0,
                'close': round(row['Close'], 2) if row['Close'] else 0,
                'volume': int(row['Volume']) if row['Volume'] else 0
            })
        
        return jsonify({
            'symbol': symbol,
            'period': period,
            'interval': interval,
            'data': data
        })
        
    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500
