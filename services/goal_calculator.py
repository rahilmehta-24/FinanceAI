from datetime import datetime, timedelta
import math

def calculate_goal_projection(target_amount, current_savings, monthly_contribution, expected_return, goal_type):
    """
    Calculate financial goal projections with compound interest.
    
    Args:
        target_amount: The amount you want to save
        current_savings: Current amount saved
        monthly_contribution: Monthly contribution amount
        expected_return: Expected annual return rate (percentage)
        goal_type: 'short' (< 1 year), 'mid' (1-5 years), 'long' (> 5 years)
    
    Returns:
        Dictionary with projection results
    """
    
    # Monthly interest rate
    monthly_rate = expected_return / 100 / 12
    
    # Calculate months needed to reach goal
    if monthly_contribution <= 0:
        if current_savings >= target_amount:
            months_needed = 0
        else:
            # Only growth from current savings
            if monthly_rate > 0:
                months_needed = math.ceil(
                    math.log(target_amount / current_savings) / math.log(1 + monthly_rate)
                ) if current_savings > 0 else float('inf')
            else:
                months_needed = float('inf')
    else:
        # Use future value formula to find months
        months_needed = calculate_months_to_goal(
            target_amount, current_savings, monthly_contribution, monthly_rate
        )
    
    # Cap months for display
    if months_needed == float('inf') or months_needed > 600:  # 50 years max
        months_needed = -1  # Indicates not achievable
    
    # Generate projection timeline
    projection = generate_projection(
        current_savings, monthly_contribution, monthly_rate, 
        min(months_needed if months_needed > 0 else 60, 120)  # Max 10 years for chart
    )
    
    # Calculate final values
    if months_needed > 0:
        target_date = datetime.now() + timedelta(days=months_needed * 30)
        years = months_needed / 12
    else:
        target_date = None
        years = -1
    
    # Goal type recommendations
    type_info = get_goal_type_info(goal_type)
    
    # Calculate if on track based on goal type
    typical_months = type_info['typical_months']
    if months_needed > 0 and months_needed <= typical_months * 1.2:
        status = 'on_track'
        status_message = 'You are on track to meet your goal!'
    elif months_needed > 0:
        status = 'behind'
        status_message = f'Consider increasing monthly contribution to reach goal faster.'
    else:
        status = 'not_achievable'
        status_message = 'Goal may not be achievable with current parameters.'
    
    # Calculate required contribution to meet typical timeframe
    if months_needed > typical_months:
        required_contribution = calculate_required_contribution(
            target_amount, current_savings, monthly_rate, typical_months
        )
    else:
        required_contribution = monthly_contribution
    
    return {
        'months_needed': months_needed if months_needed > 0 else None,
        'years_needed': round(years, 1) if years > 0 else None,
        'target_date': target_date.strftime('%B %Y') if target_date else None,
        'projection': projection,
        'final_amount': projection[-1]['amount'] if projection else current_savings,
        'total_contributions': monthly_contribution * (months_needed if months_needed > 0 else 0),
        'interest_earned': (projection[-1]['amount'] - current_savings - 
                          monthly_contribution * len(projection)) if projection else 0,
        'status': status,
        'status_message': status_message,
        'required_contribution': round(required_contribution, 2),
        'goal_type_info': type_info
    }

def calculate_months_to_goal(target, principal, monthly_pmt, monthly_rate):
    """Calculate months needed to reach a target amount"""
    if monthly_rate == 0:
        if monthly_pmt <= 0:
            return float('inf')
        return math.ceil((target - principal) / monthly_pmt)
    
    current = principal
    months = 0
    max_months = 600  # 50 years max
    
    while current < target and months < max_months:
        current = current * (1 + monthly_rate) + monthly_pmt
        months += 1
    
    return months if current >= target else float('inf')

def calculate_required_contribution(target, current, monthly_rate, months):
    """Calculate monthly contribution needed to reach goal in given months"""
    if months <= 0:
        return float('inf')
    
    if monthly_rate == 0:
        return (target - current) / months
    
    # Future value of current savings
    fv_current = current * ((1 + monthly_rate) ** months)
    
    # Amount needed from contributions
    amount_needed = target - fv_current
    
    if amount_needed <= 0:
        return 0
    
    # Contribution needed (using annuity formula)
    contribution = amount_needed * monthly_rate / (((1 + monthly_rate) ** months) - 1)
    
    return max(contribution, 0)

def generate_projection(principal, monthly_contribution, monthly_rate, months):
    """Generate month-by-month projection"""
    projection = []
    current = principal
    
    for month in range(int(months) + 1):
        projection.append({
            'month': month,
            'amount': round(current, 2),
            'contributions': round(principal + monthly_contribution * month, 2),
            'interest': round(current - principal - monthly_contribution * month, 2)
        })
        current = current * (1 + monthly_rate) + monthly_contribution
    
    return projection

def get_goal_type_info(goal_type):
    """Get information about goal type"""
    types = {
        'short': {
            'name': 'Short-term Goal',
            'description': 'Goals under 1 year - Emergency fund, vacation, small purchases',
            'typical_months': 12,
            'recommended_return': 4,
            'risk_level': 'Low',
            'suggested_investments': ['High-yield savings account', 'Money market fund', 'Short-term CDs']
        },
        'mid': {
            'name': 'Mid-term Goal',
            'description': 'Goals 1-5 years - Car purchase, home down payment, education',
            'typical_months': 36,
            'recommended_return': 6,
            'risk_level': 'Moderate',
            'suggested_investments': ['Bond funds', 'Balanced funds', 'Certificate of deposits']
        },
        'long': {
            'name': 'Long-term Goal',
            'description': 'Goals 5+ years - Retirement, children education, wealth building',
            'typical_months': 120,
            'recommended_return': 10,
            'risk_level': 'Higher',
            'suggested_investments': ['Stock index funds', 'Diversified equity funds', 'Real estate']
        }
    }
    
    return types.get(goal_type, types['mid'])
