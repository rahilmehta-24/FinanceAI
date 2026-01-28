"""
AI Service for portfolio analysis - includes both simulated and Gemini-powered features
"""
import os
import numpy as np
import random
import re
from services.stock_service import STOCK_DATA

# Gemini API integration
try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    load_dotenv()
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_AVAILABLE = bool(GEMINI_API_KEY)
except ImportError:
    GEMINI_AVAILABLE = False
    GEMINI_API_KEY = None


def get_gemini_model():
    """Get configured Gemini model"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel('gemini-flash-latest')


def get_portfolio_review_gemini(holdings_data, portfolio_stats):
    """Generate AI portfolio review using Gemini
    
    Args:
        holdings_data: List of holdings with symbol, company, quantity, value, gain_loss, sector
        portfolio_stats: Dict with total_invested, total_current, total_gain_loss, sector_data
        
    Returns:
        dict: AI review with summary, strengths, risks, recommendations
    """
    if not GEMINI_AVAILABLE:
        return {
            'success': False,
            'error': 'Gemini API not configured. Please add GEMINI_API_KEY to .env file.'
        }
    
    try:
        model = get_gemini_model()
        
        # Build portfolio summary for the prompt
        holdings_summary = []
        for h in holdings_data:
            gain_pct = ((h.get('gain_loss', 0) / h.get('total_invested', 1)) * 100) if h.get('total_invested', 0) > 0 else 0
            holdings_summary.append(
                f"- {h.get('company_name', h.get('symbol'))}: "
                f"₹{h.get('current_value', 0):,.0f} ({gain_pct:+.1f}%), "
                f"Sector: {h.get('sector', 'Unknown')}"
            )
        
        holdings_text = '\n'.join(holdings_summary[:20])  # Limit to 20 stocks
        
        sector_text = '\n'.join([
            f"- {sector}: ₹{value:,.0f}" 
            for sector, value in (portfolio_stats.get('sector_data', {}) or {}).items()
        ])
        
        total_return = 0
        if portfolio_stats.get('total_invested', 0) > 0:
            total_return = ((portfolio_stats.get('total_current', 0) - portfolio_stats.get('total_invested', 0)) / portfolio_stats.get('total_invested', 0)) * 100
        
        prompt = f"""You are a professional financial analyst and portfolio advisor. Analyze this Indian stock portfolio and provide a comprehensive, structured review.

## Portfolio Data
- Total Invested: ₹{portfolio_stats.get('total_invested', 0):,.2f}
- Current Value: ₹{portfolio_stats.get('total_current', 0):,.2f}
- Total Return: {total_return:+.2f}%
- Number of Stocks: {len(holdings_data)}

### Holdings Details:
{holdings_text}

### Sector Allocation:
{sector_text}

## Your Task
Provide a high-quality analysis with these EXACT sections (use these exact headings):

### Summary
Write a 2-3 sentence overview of the portfolio's overall health and performance. Use professional language.

### Strengths
Identify 3-4 key strengths. Use bullet points. Focus on diversification, quality of stocks, or sector exposure.

### Risks
Identify 3-4 potential risks or areas of concern. Use bullet points. Highlight concentration risk, sector headwinds, or volatility.

### Recommendations
Provide 3-4 actionable, specific suggestions to optimize the portfolio for better risk-adjusted returns.

### Formatting Guidelines:
- Use **bold** for key terms and symbols.
- Use ₹ for currency.
- Keep the tone professional but accessible.
- Each bullet point should be concise but insightful."""

        response = model.generate_content(prompt)
        
        if response and response.text:
            text = response.text
            sections = {
                'summary': '',
                'strengths': '',
                'risks': '',
                'recommendations': '',
                'raw': text
            }
            
            # Parse sections
            summary_match = re.search(r'###?\s*Summary\s*\n(.*?)(?=###|$)', text, re.DOTALL | re.IGNORECASE)
            strengths_match = re.search(r'###?\s*Strengths\s*\n(.*?)(?=###|$)', text, re.DOTALL | re.IGNORECASE)
            risks_match = re.search(r'###?\s*Risks\s*\n(.*?)(?=###|$)', text, re.DOTALL | re.IGNORECASE)
            recommendations_match = re.search(r'###?\s*Recommendations\s*\n(.*?)(?=###|$)', text, re.DOTALL | re.IGNORECASE)
            
            if summary_match:
                sections['summary'] = summary_match.group(1).strip()
            if strengths_match:
                sections['strengths'] = strengths_match.group(1).strip()
            if risks_match:
                sections['risks'] = risks_match.group(1).strip()
            if recommendations_match:
                sections['recommendations'] = recommendations_match.group(1).strip()
            
            return {
                'success': True,
                'review': sections
            }
        else:
            return {
                'success': False,
                'error': 'No response from AI'
            }
            
    except ValueError as e:
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        print(f"Error generating portfolio review: {e}")
        return {
            'success': False,
            'error': f'AI analysis failed: {str(e)}'
        }



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
