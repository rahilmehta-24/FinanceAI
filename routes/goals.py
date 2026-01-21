from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Goal
from datetime import datetime
from services.goal_calculator import calculate_goal_projection

goals_bp = Blueprint('goals', __name__, url_prefix='/goals')

@goals_bp.route('/')
@login_required
def index():
    goals = Goal.query.filter_by(user_id=current_user.id).all()
    
    # Group by type
    short_term = [g for g in goals if g.goal_type == 'short']
    mid_term = [g for g in goals if g.goal_type == 'mid']
    long_term = [g for g in goals if g.goal_type == 'long']
    
    return render_template('goals/index.html',
                         short_term=short_term,
                         mid_term=mid_term,
                         long_term=long_term)

@goals_bp.route('/calculator')
@login_required
def calculator():
    return render_template('goals/calculator.html')

@goals_bp.route('/calculate', methods=['POST'])
@login_required
def calculate():
    goal_type = request.form.get('goal_type')
    target_amount = float(request.form.get('target_amount', 0))
    current_savings = float(request.form.get('current_savings', 0))
    monthly_contribution = float(request.form.get('monthly_contribution', 0))
    expected_return = float(request.form.get('expected_return', 8))
    
    # Calculate projection
    result = calculate_goal_projection(
        target_amount=target_amount,
        current_savings=current_savings,
        monthly_contribution=monthly_contribution,
        expected_return=expected_return,
        goal_type=goal_type
    )
    
    return jsonify(result)

@goals_bp.route('/add', methods=['POST'])
@login_required
def add_goal():
    name = request.form.get('name')
    goal_type = request.form.get('goal_type')
    target_amount = float(request.form.get('target_amount', 0))
    current_savings = float(request.form.get('current_savings', 0))
    monthly_contribution = float(request.form.get('monthly_contribution', 0))
    expected_return = float(request.form.get('expected_return', 8))
    target_date_str = request.form.get('target_date')
    
    target_date = None
    if target_date_str:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    
    goal = Goal(
        user_id=current_user.id,
        name=name,
        goal_type=goal_type,
        target_amount=target_amount,
        current_savings=current_savings,
        monthly_contribution=monthly_contribution,
        expected_return=expected_return,
        target_date=target_date
    )
    
    db.session.add(goal)
    db.session.commit()
    
    flash(f'Goal "{name}" created successfully!', 'success')
    return redirect(url_for('goals.index'))

@goals_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_goal(id):
    goal = Goal.query.get_or_404(id)
    
    if goal.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('goals.index'))
    
    name = goal.name
    db.session.delete(goal)
    db.session.commit()
    
    flash(f'Goal "{name}" deleted', 'success')
    return redirect(url_for('goals.index'))
