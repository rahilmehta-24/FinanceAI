from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Holding
from datetime import datetime
import csv
import io

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/portfolio')

@portfolio_bp.route('/')
@login_required
def index():
    holdings = Holding.query.filter_by(user_id=current_user.id).all()
    
    # Calculate portfolio stats
    total_invested = sum(h.quantity * h.buy_price for h in holdings)
    
    # Simulated current prices (in production, fetch from API)
    from services.stock_service import get_current_prices
    current_prices = get_current_prices([h.symbol for h in holdings])
    
    holdings_data = []
    total_current = 0
    for h in holdings:
        current_price = current_prices.get(h.symbol, h.buy_price)
        current_value = h.quantity * current_price
        gain_loss = current_value - (h.quantity * h.buy_price)
        gain_loss_pct = ((current_price - h.buy_price) / h.buy_price) * 100 if h.buy_price > 0 else 0
        
        total_current += current_value
        holdings_data.append({
            'id': h.id,
            'symbol': h.symbol,
            'company_name': h.company_name,
            'quantity': h.quantity,
            'buy_price': h.buy_price,
            'current_price': current_price,
            'current_value': current_value,
            'gain_loss': gain_loss,
            'gain_loss_pct': gain_loss_pct,
            'sector': h.sector,
            'buy_date': h.buy_date
        })
    
    # Sector distribution
    sector_data = {}
    for h in holdings_data:
        sector = h['sector'] or 'Other'
        sector_data[sector] = sector_data.get(sector, 0) + h['current_value']
    
    return render_template('portfolio/index.html', 
                         holdings=holdings_data,
                         total_invested=total_invested,
                         total_current=total_current,
                         total_gain_loss=total_current - total_invested,
                         sector_data=sector_data)

@portfolio_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_stock():
    if request.method == 'POST':
        symbol = request.form.get('symbol', '').upper().strip()
        company_name = request.form.get('company_name', '').strip()
        quantity = float(request.form.get('quantity', 0))
        buy_price = float(request.form.get('buy_price', 0))
        buy_date = datetime.strptime(request.form.get('buy_date'), '%Y-%m-%d').date()
        sector = request.form.get('sector', '').strip()
        
        if not symbol or quantity <= 0 or buy_price <= 0:
            flash('Please fill in all required fields correctly', 'error')
            return redirect(url_for('portfolio.add_stock'))
        
        holding = Holding(
            user_id=current_user.id,
            symbol=symbol,
            company_name=company_name,
            quantity=quantity,
            buy_price=buy_price,
            buy_date=buy_date,
            sector=sector
        )
        
        db.session.add(holding)
        db.session.commit()
        
        flash(f'{symbol} added to your portfolio!', 'success')
        return redirect(url_for('portfolio.index'))
    
    return render_template('portfolio/add_stock.html')

@portfolio_bp.route('/batch', methods=['GET', 'POST'])
@login_required
def batch_upload():
    if request.method == 'POST':
        stocks_data = request.form.get('stocks_data', '')
        
        lines = stocks_data.strip().split('\n')
        added = 0
        
        for line in lines:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 4:
                try:
                    holding = Holding(
                        user_id=current_user.id,
                        symbol=parts[0].upper(),
                        company_name=parts[1] if len(parts) > 4 else '',
                        quantity=float(parts[2] if len(parts) > 4 else parts[1]),
                        buy_price=float(parts[3] if len(parts) > 4 else parts[2]),
                        buy_date=datetime.strptime(parts[4] if len(parts) > 4 else parts[3], '%Y-%m-%d').date(),
                        sector=parts[5] if len(parts) > 5 else ''
                    )
                    db.session.add(holding)
                    added += 1
                except (ValueError, IndexError):
                    continue
        
        db.session.commit()
        flash(f'Successfully added {added} stocks to your portfolio!', 'success')
        return redirect(url_for('portfolio.index'))
    
    return render_template('portfolio/batch_upload.html')

@portfolio_bp.route('/upload-csv', methods=['POST'])
@login_required
def upload_csv():
    if 'csv_file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('portfolio.batch_upload'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('portfolio.batch_upload'))
    
    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file', 'error')
        return redirect(url_for('portfolio.batch_upload'))
    
    try:
        content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        
        added = 0
        for row in csv_reader:
            try:
                holding = Holding(
                    user_id=current_user.id,
                    symbol=row.get('symbol', row.get('Symbol', '')).upper().strip(),
                    company_name=row.get('company_name', row.get('Company', '')),
                    quantity=float(row.get('quantity', row.get('Quantity', 0))),
                    buy_price=float(row.get('buy_price', row.get('Price', row.get('Buy Price', 0)))),
                    buy_date=datetime.strptime(
                        row.get('buy_date', row.get('Date', row.get('Buy Date', datetime.now().strftime('%Y-%m-%d')))),
                        '%Y-%m-%d'
                    ).date(),
                    sector=row.get('sector', row.get('Sector', ''))
                )
                db.session.add(holding)
                added += 1
            except (ValueError, KeyError):
                continue
        
        db.session.commit()
        flash(f'Successfully imported {added} stocks from CSV!', 'success')
    except Exception as e:
        flash(f'Error processing CSV: {str(e)}', 'error')
    
    return redirect(url_for('portfolio.index'))

@portfolio_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_stock(id):
    holding = Holding.query.get_or_404(id)
    
    if holding.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('portfolio.index'))
    
    symbol = holding.symbol
    db.session.delete(holding)
    db.session.commit()
    
    flash(f'{symbol} removed from your portfolio', 'success')
    return redirect(url_for('portfolio.index'))
