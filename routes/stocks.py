from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from services.stock_service import get_top_gainers, get_top_losers, get_stock_recommendations, get_sector_distribution
from services.ai_service import get_ai_recommendations

stocks_bp = Blueprint('stocks', __name__, url_prefix='/stocks')

@stocks_bp.route('/')
@login_required
def index():
    top_gainers = get_top_gainers()
    top_losers = get_top_losers()
    recommendations = get_ai_recommendations()
    sector_dist = get_sector_distribution()
    
    return render_template('stocks/index.html',
                         top_gainers=top_gainers,
                         top_losers=top_losers,
                         recommendations=recommendations,
                         sector_distribution=sector_dist)


@stocks_bp.route('/search')
@login_required
def search():
    """Stock search page with detailed information"""
    return render_template('stocks/search.html')


@stocks_bp.route('/screener')
@login_required
def screener():
    """Stock screener page with filters"""
    from services.stock_service import get_screener_sectors
    
    sectors = get_screener_sectors()
    
    return render_template('stocks/screener.html', sectors=sectors)


@stocks_bp.route('/api/screener')
@login_required
def api_screener():
    """API endpoint for screening stocks"""
    from services.stock_service import screen_stocks
    
    try:
        # Get filter parameters
        filters = {}
        
        if request.args.get('min_pe'):
            filters['min_pe'] = float(request.args.get('min_pe'))
        if request.args.get('max_pe'):
            filters['max_pe'] = float(request.args.get('max_pe'))
        if request.args.get('min_market_cap'):
            filters['min_market_cap'] = float(request.args.get('min_market_cap'))
        if request.args.get('min_dividend_yield'):
            filters['min_dividend_yield'] = float(request.args.get('min_dividend_yield'))
        if request.args.get('sector'):
            filters['sector'] = request.args.get('sector')
        
        results = screen_stocks(filters)
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

