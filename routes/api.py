from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services.stock_service import STOCK_DATA, get_stock_info, validate_indian_stock, fetch_real_time_price
from services.ai_service import predict_stock_price
from models import Watchlist
from extensions import db
import yfinance as yf

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/stocks/search')
@login_required
def search_stocks():
    """Search stocks by symbol or name - used for autocomplete"""
    from services.stock_service import NIFTY_50_STOCKS
    query = request.args.get('q', '').upper().strip()
    
    if not query or len(query) < 1:
        return jsonify([])
    
    results = []
    seen = set()
    
    # 1. Search in our Indian stock database (STOCK_DATA)
    for symbol, data in STOCK_DATA.items():
        if query in symbol.upper() or query in data['name'].upper():
            if symbol not in seen:
                results.append({
                    'symbol': symbol,
                    'name': data['name'],
                    'sector': data['sector']
                })
                seen.add(symbol)
    
    # 2. Search in NIFTY_50_STOCKS list
    for symbol in NIFTY_50_STOCKS:
        if symbol not in seen:
            if query in symbol.upper():
                name = symbol.replace('.NS', '').replace('.BO', '')
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'sector': 'Equity'
                })
                seen.add(symbol)
    
    # 3. Quick fallback if no results and looks like a symbol
    if not results and len(query) >= 3 and query.isalpha():
        results.append({
            'symbol': f"{query}.NS",
            'name': query,
            'sector': 'Potential Match'
        })
    
    # Limit results for performance
    return jsonify(results[:15])


@api_bp.route('/stocks/info/<symbol>')
@login_required
def get_stock_info_api(symbol):
    """Get basic stock info for autocomplete - Indian stocks only"""
    try:
        from services.stock_service import validate_indian_stock, fetch_real_time_price
        
        symbol = symbol.upper().strip()
        
        # Validate it's an Indian stock
        if not validate_indian_stock(symbol):
            return jsonify({'error': 'Only Indian stocks (NSE/BSE) are supported. Symbol must end with .NS or .BO'}), 400
        
        # Try to get stock info from yfinance
        ticker = yf.Ticker(symbol)
        info = ticker.info
        fast_info = ticker.fast_info
        
        # Get current price
        current_price = None
        if hasattr(fast_info, 'last_price') and fast_info.last_price:
            current_price = round(fast_info.last_price, 2)
        elif hasattr(fast_info, 'previous_close') and fast_info.previous_close:
            current_price = round(fast_info.previous_close, 2)
        else:
            # Fallback to fetch_real_time_price
            current_price = fetch_real_time_price(symbol)
        
        # Get company name and sector
        company_name = info.get('longName', info.get('shortName', ''))
        sector = info.get('sector', '')
        
        # Fallback to STOCK_DATA if available
        if not company_name and symbol in STOCK_DATA:
            company_name = STOCK_DATA[symbol]['name']
            sector = STOCK_DATA[symbol]['sector']
            if not current_price:
                current_price = STOCK_DATA[symbol]['price']
        
        return jsonify({
            'symbol': symbol,
            'name': company_name,
            'sector': sector,
            'current_price': current_price if current_price else 0
        })
        
    except Exception as e:
        print(f"Error fetching stock info for {symbol}: {e}")
        return jsonify({'error': f'Could not fetch stock information: {str(e)}'}), 500



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
            'data': data,
            'predictions': predict_stock_price(data)
        })
        
    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/watchlist', methods=['GET'])
@login_required
def get_watchlist():
    """Get user's watchlist items with current prices"""
    try:
        items = Watchlist.query.filter_by(user_id=current_user.id).all()
        results = []
        
        if not items:
            return jsonify([])
            
        # Batch fetch prices and day changes
        symbols = [item.symbol for item in items]
        from services.stock_service import get_day_changes
        changes_data = get_day_changes(symbols)
        
        for item in items:
            day_data = changes_data.get(item.symbol, {})
            results.append({
                'symbol': item.symbol,
                'name': item.company_name,
                'sector': item.sector,
                'price': day_data.get('current', 0),
                'currency': '₹',
                'change_pct': day_data.get('change_pct', 0)
            })
        return jsonify(results)
    except Exception as e:
        print(f"Error fetching watchlist: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/watchlist', methods=['POST'])
@login_required
def add_to_watchlist():
    """Add a stock to user's watchlist"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper().strip()
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
            
        # Add .NS if missing and it's not .BO
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            symbol += '.NS'
            
        # Check if already in watchlist
        existing = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first()
        if existing:
            return jsonify({'message': 'Already in watchlist', 'success': True}), 200
            
        # Try to get stock info to save name/sector
        company_name = symbol.replace('.NS', '').replace('.BO', '')
        sector = 'Equity'
        
        # 1. Try local STOCK_DATA first (fast)
        if symbol in STOCK_DATA:
            company_name = STOCK_DATA[symbol]['name']
            sector = STOCK_DATA[symbol]['sector']
        else:
            # 2. Try yfinance with timeout fallback
            try:
                ticker = yf.Ticker(symbol)
                # Use faster access for basic info if possible
                info = ticker.history(period="1d")
                if not info.empty:
                    # If we can get history, the symbol is likely valid
                    # We can try to get detailed info but don't block too long
                    long_info = ticker.info
                    company_name = long_info.get('longName', long_info.get('shortName', company_name))
                    sector = long_info.get('sector', sector)
            except Exception as e:
                print(f"yfinance info fetch failed for {symbol}: {e}")
                # Keep defaults
        
        item = Watchlist(
            user_id=current_user.id,
            symbol=symbol,
            company_name=company_name,
            sector=sector
        )
        db.session.add(item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{symbol} added to watchlist'})
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/watchlist/<symbol>', methods=['DELETE'])
@login_required
def remove_from_watchlist(symbol):
    """Remove a stock from user's watchlist"""
    try:
        symbol = symbol.upper().strip()
        item = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol).first()
        
        if not item:
            return jsonify({'error': 'Item not found'}), 404
            
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{symbol} removed from watchlist'})
    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        return jsonify({'error': str(e)}), 500
