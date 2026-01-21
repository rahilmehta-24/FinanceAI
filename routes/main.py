from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Holding
from services.stock_service import get_portfolio_summary

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    holdings = Holding.query.filter_by(user_id=current_user.id).all()
    summary = get_portfolio_summary(holdings)
    return render_template('dashboard.html', summary=summary, holdings=holdings)
