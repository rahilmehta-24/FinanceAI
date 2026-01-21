from flask import Blueprint, render_template
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
