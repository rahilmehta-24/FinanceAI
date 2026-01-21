import numpy as np
from services.stock_service import STOCK_DATA
import random

def get_ai_recommendations():
    """
    Generate AI-powered stock recommendations based on simulated analysis.
    NOTE: These are informational recommendations only - no buy/hold/sell commands.
    """
    recommendations = []
    
    # Analyze each stock with AI-like scoring
    for symbol, data in STOCK_DATA.items():
        score = calculate_stock_score(data)
        
        recommendations.append({
            'symbol': symbol,
            'name': data['name'],
            'sector': data['sector'],
            'price': data['price'],
            'change': data['change'],
            'ai_score': score,
            'momentum': get_momentum_indicator(data),
            'volatility': get_volatility_indicator(data),
            'trend': get_trend_indicator(data),
            'analysis': generate_ai_analysis(data, score)
        })
    
    # Sort by AI score
    recommendations.sort(key=lambda x: x['ai_score'], reverse=True)
    
    return recommendations

def calculate_stock_score(data):
    """Calculate an AI-based score for a stock (0-100)"""
    # Simulated scoring based on multiple factors
    base_score = 50
    
    # Factor 1: Price change impact
    change_pct = (data['change'] / data['price']) * 100
    change_score = min(max(change_pct * 5, -20), 20)
    
    # Factor 2: Sector premium
    sector_scores = {
        'Technology': 10,
        'Healthcare': 8,
        'Financial Services': 5,
        'Consumer Defensive': 7,
        'Energy': 3,
        'Consumer Cyclical': 6,
        'Communication Services': 4,
    }
    sector_score = sector_scores.get(data['sector'], 5)
    
    # Factor 3: Random AI variance (simulating complex analysis)
    ai_variance = random.uniform(-10, 15)
    
    final_score = base_score + change_score + sector_score + ai_variance
    return round(min(max(final_score, 0), 100), 1)

def get_momentum_indicator(data):
    """Get momentum indicator for a stock"""
    change_pct = (data['change'] / data['price']) * 100
    
    if change_pct > 2:
        return {'value': 'Strong', 'color': 'green', 'icon': '↑↑'}
    elif change_pct > 0.5:
        return {'value': 'Positive', 'color': 'light-green', 'icon': '↑'}
    elif change_pct > -0.5:
        return {'value': 'Neutral', 'color': 'gray', 'icon': '→'}
    elif change_pct > -2:
        return {'value': 'Negative', 'color': 'orange', 'icon': '↓'}
    else:
        return {'value': 'Weak', 'color': 'red', 'icon': '↓↓'}

def get_volatility_indicator(data):
    """Get volatility indicator for a stock"""
    # Simulated volatility based on sector and price
    base_volatility = abs(data['change']) / data['price'] * 100
    
    if base_volatility > 2:
        return {'value': 'High', 'color': 'red', 'level': 3}
    elif base_volatility > 1:
        return {'value': 'Medium', 'color': 'orange', 'level': 2}
    else:
        return {'value': 'Low', 'color': 'green', 'level': 1}

def get_trend_indicator(data):
    """Get trend indicator for a stock"""
    # Simulated trend analysis
    trends = ['Upward', 'Stable', 'Consolidating', 'Mixed']
    weights = [0.3, 0.3, 0.2, 0.2]
    
    if data['change'] > 0:
        weights = [0.5, 0.3, 0.1, 0.1]
    elif data['change'] < 0:
        weights = [0.1, 0.2, 0.3, 0.4]
    
    trend = random.choices(trends, weights)[0]
    
    trend_data = {
        'Upward': {'color': 'green', 'icon': '📈'},
        'Stable': {'color': 'blue', 'icon': '➡️'},
        'Consolidating': {'color': 'orange', 'icon': '📊'},
        'Mixed': {'color': 'gray', 'icon': '🔄'}
    }
    
    return {'value': trend, **trend_data.get(trend, {})}

def generate_ai_analysis(data, score):
    """Generate AI-powered analysis text for a stock"""
    
    analyses_high = [
        f"{data['name']} shows strong institutional interest with consistent growth patterns.",
        f"Technical indicators suggest favorable conditions for {data['name']}.",
        f"{data['name']} demonstrates resilient fundamentals in the {data['sector']} sector.",
        f"Market analysis indicates positive sentiment around {data['name']}.",
    ]
    
    analyses_mid = [
        f"{data['name']} maintains stable performance with balanced risk profile.",
        f"Current market conditions show neutral outlook for {data['name']}.",
        f"{data['name']} is consolidating with potential for movement in {data['sector']}.",
        f"Technical analysis shows {data['name']} is in a holding pattern.",
    ]
    
    analyses_low = [
        f"{data['name']} faces sector headwinds but maintains core fundamentals.",
        f"Market volatility affecting {data['name']}, watch for stabilization.",
        f"{data['name']} showing mixed signals in current market conditions.",
        f"Technical indicators suggest caution for {data['name']} in short term.",
    ]
    
    if score >= 70:
        return random.choice(analyses_high)
    elif score >= 40:
        return random.choice(analyses_mid)
    else:
        return random.choice(analyses_low)

def analyze_portfolio_with_ai(holdings):
    """Analyze entire portfolio with AI insights"""
    if not holdings:
        return {
            'overall_health': 'N/A',
            'diversification_score': 0,
            'risk_level': 'N/A',
            'insights': ['Add stocks to your portfolio to see AI analysis.']
        }
    
    # Calculate sector diversification
    sectors = {}
    total_value = 0
    
    for h in holdings:
        sector = h.sector or 'Other'
        value = h.quantity * h.buy_price
        sectors[sector] = sectors.get(sector, 0) + value
        total_value += value
    
    # Diversification score (more sectors = better)
    num_sectors = len(sectors)
    max_sectors = 8
    diversification_score = min(num_sectors / max_sectors * 100, 100)
    
    # Check for over-concentration
    concentration_risk = False
    for sector, value in sectors.items():
        if total_value > 0 and (value / total_value) > 0.5:
            concentration_risk = True
            break
    
    # Generate insights
    insights = []
    
    if diversification_score < 30:
        insights.append("Consider diversifying across more sectors to reduce risk.")
    elif diversification_score > 70:
        insights.append("Portfolio shows good sectoral diversification.")
    
    if concentration_risk:
        insights.append("High concentration detected in one sector. Consider rebalancing.")
    
    if len(holdings) < 5:
        insights.append("Small portfolio size may increase volatility risk.")
    elif len(holdings) > 20:
        insights.append("Large portfolio with good diversification potential.")
    
    # Overall health assessment
    if diversification_score > 60 and not concentration_risk:
        overall_health = 'Good'
    elif diversification_score > 30:
        overall_health = 'Moderate'
    else:
        overall_health = 'Needs Attention'
    
    # Risk level
    if concentration_risk or diversification_score < 30:
        risk_level = 'High'
    elif diversification_score < 60:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'
    
    return {
        'overall_health': overall_health,
        'diversification_score': round(diversification_score, 1),
        'risk_level': risk_level,
        'insights': insights,
        'sector_breakdown': sectors
    }
