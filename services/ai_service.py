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


def get_stock_recommendations_gemini(holdings_data):
    """Generate buy/sell/hold recommendations for each stock using Gemini
    
    Args:
        holdings_data: List of holdings with symbol, company_name, quantity, buy_price, 
                      current_price, current_value, gain_loss, sector
    
    Returns:
        dict: Stock recommendations with action, target price, profit amount, reasoning
    """
    if not GEMINI_AVAILABLE:
        return {
            'success': False,
            'error': 'Gemini API not configured. Please add GEMINI_API_KEY to .env file.'
        }
    
    try:
        model = get_gemini_model()
        
        # Build detailed stock information for the prompt
        stocks_info = []
        for h in holdings_data:
            buy_price = h.get('total_invested', 0) / h.get('quantity', 1) if h.get('quantity', 0) > 0 else 0
            current_price = h.get('current_price', buy_price)
            gain_loss_pct = ((h.get('gain_loss', 0) / h.get('total_invested', 1)) * 100) if h.get('total_invested', 0) > 0 else 0
            
            stocks_info.append(
                f"""
Stock: {h.get('company_name', h.get('symbol'))} ({h.get('symbol')})
- Sector: {h.get('sector', 'Unknown')}
- Quantity: {h.get('quantity', 0):.0f} shares
- Buy Price: ₹{buy_price:,.2f}
- Current Price: ₹{current_price:,.2f}
- Invested Amount: ₹{h.get('total_invested', 0):,.2f}
- Current Value: ₹{h.get('current_value', 0):,.2f}
- Gain/Loss: ₹{h.get('gain_loss', 0):,.2f} ({gain_loss_pct:+.1f}%)
"""
            )
        
        stocks_text = '\n---\n'.join(stocks_info[:15])  # Limit to 15 stocks for token management
        
        prompt = f"""You are an expert stock market analyst and investment advisor. Analyze each stock in this portfolio and provide SPECIFIC, ACTIONABLE recommendations.

## Portfolio Holdings:
{stocks_text}

## Your Task:
For EACH stock listed above, provide recommendations in this EXACT format:

**[STOCK SYMBOL]**
- **Recommendation**: [Choose ONE: BUY_MORE / HOLD / BOOK_PROFITS_20 / BOOK_PROFITS_50 / EXIT]
- **Target Price**: ₹[specific price for profit booking, or "N/A" if HOLD/BUY_MORE]
- **Action**: [Short description like "Book 50% profits at ₹2900" or "Hold for long-term" or "Exit position"]
- **Reasoning**: [2-3 sentences explaining why based on gain/loss, sector trends, and market conditions]

## Recommendation Guidelines:
1. **BUY_MORE**: Stock is underperforming (<-10%) but has strong fundamentals
2. **HOLD**: Stock is performing well (0-15% gain) with good long-term prospects
3. **BOOK_PROFITS_20**: Stock gained 15-25%, book 20% to secure partial profits
4. **BOOK_PROFITS_50**: Stock gained 25-40%, book 50% to lock in gains
5. **EXIT**: Stock gained >40% OR sector facing major headwinds OR loss >20%
6. **Target Price**: Should be slightly above current price (2-5% premium) for profit booking

Be specific, actionable, and professional. Focus on risk management and profit optimization."""

        response = model.generate_content(prompt)
        
        if response and response.text:
            text = response.text
            recommendations = []
            
            # Parse each stock recommendation
            for h in holdings_data:
                symbol = h.get('symbol')
                # Try to find this stock's recommendation in the response
                pattern = rf'\*\*\[?{re.escape(symbol)}\]?\*\*\s*\n-\s*\*\*Recommendation\*\*:\s*([^\n]+)\n-\s*\*\*Target Price\*\*:\s*([^\n]+)\n-\s*\*\*Action\*\*:\s*([^\n]+)\n-\s*\*\*Reasoning\*\*:\s*([^\n]+(?:\n(?![\*-])[^\n]+)*)'
                
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                
                if match:
                    recommendation_type = match.group(1).strip()
                    target_price_str = match.group(2).strip()
                    action = match.group(3).strip()
                    reasoning = match.group(4).strip()
                    
                    # Parse target price
                    target_price = None
                    if '₹' in target_price_str:
                        price_match = re.search(r'₹\s*([0-9,]+(?:\.[0-9]+)?)', target_price_str)
                        if price_match:
                            target_price = float(price_match.group(1).replace(',', ''))
                    
                    # Calculate profit booking amount
                    profit_amount = 0
                    percent_to_book = 0
                    
                    if 'BOOK_PROFITS_20' in recommendation_type:
                        percent_to_book = 20
                    elif 'BOOK_PROFITS_50' in recommendation_type:
                        percent_to_book = 50
                    elif 'EXIT' in recommendation_type:
                        percent_to_book = 100
                    
                    if percent_to_book > 0 and h.get('gain_loss', 0) > 0:
                        # Calculate profit on the portion being booked
                        position_value = h.get('current_value', 0)
                        position_cost = h.get('total_invested', 0)
                        portion_value = position_value * (percent_to_book / 100)
                        portion_cost = position_cost * (percent_to_book / 100)
                        profit_amount = portion_value - portion_cost
                    
                    recommendations.append({
                        'symbol': symbol,
                        'company_name': h.get('company_name', symbol),
                        'recommendation': recommendation_type,
                        'action': action,
                        'target_price': target_price,
                        'percent_to_book': percent_to_book,
                        'profit_amount': profit_amount,
                        'current_price': h.get('current_price', 0),
                        'gain_loss_pct': ((h.get('gain_loss', 0) / h.get('total_invested', 1)) * 100) if h.get('total_invested', 0) > 0 else 0,
                        'reasoning': reasoning
                    })
                else:
                    # Fallback: couldn't parse, use basic logic
                    gain_loss_pct = ((h.get('gain_loss', 0) / h.get('total_invested', 1)) * 100) if h.get('total_invested', 0) > 0 else 0
                    
                    if gain_loss_pct > 40:
                        rec_type = 'EXIT'
                        action_text = 'Exit entire position and book profits'
                        percent = 100
                    elif gain_loss_pct > 25:
                        rec_type = 'BOOK_PROFITS_50'
                        action_text = 'Book 50% profits, hold rest'
                        percent = 50
                    elif gain_loss_pct > 15:
                        rec_type = 'BOOK_PROFITS_20'
                        action_text = 'Book 20% profits, hold rest'
                        percent = 20
                    elif gain_loss_pct < -10:
                        rec_type = 'BUY_MORE'
                        action_text = 'Consider averaging down if fundamentals strong'
                        percent = 0
                    else:
                        rec_type = 'HOLD'
                        action_text = 'Hold for long-term growth'
                        percent = 0
                    
                    profit_amount = 0
                    if percent > 0 and h.get('gain_loss', 0) > 0:
                        position_value = h.get('current_value', 0)
                        position_cost = h.get('total_invested', 0)
                        portion_value = position_value * (percent / 100)
                        portion_cost = position_cost * (percent / 100)
                        profit_amount = portion_value - portion_cost
                    
                    recommendations.append({
                        'symbol': symbol,
                        'company_name': h.get('company_name', symbol),
                        'recommendation': rec_type,
                        'action': action_text,
                        'target_price': None,
                        'percent_to_book': percent,
                        'profit_amount': profit_amount,
                        'current_price': h.get('current_price', 0),
                        'gain_loss_pct': gain_loss_pct,
                        'reasoning': f'Based on current performance of {gain_loss_pct:+.1f}%'
                    })
            
            return {
                'success': True,
                'recommendations': recommendations,
                'raw': text
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
        print(f"Error generating stock recommendations: {e}")
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


def predict_stock_price(history_data, steps=5):
    """
    Generate future price predictions based on historical data trends.
    
    Args:
        history_data: List of dicts with 'close' price
        steps: Number of future points to predict
        
    Returns:
        list: Predicted price points
    """
    if not history_data or len(history_data) < 2:
        return []
        
    prices = [float(d['close']) for d in history_data]
    
    # Calculate simple trend (average of last 5 changes)
    changes = []
    for i in range(1, min(len(prices), 6)):
        changes.append(prices[-i] - prices[-i-1])
        
    avg_change = sum(changes) / len(changes) if changes else 0
    
    predictions = []
    last_price = prices[-1]
    
    for i in range(1, steps + 1):
        # Add some noise to the prediction
        noise = random.uniform(-abs(avg_change)*0.5, abs(avg_change)*0.5)
        next_price = last_price + avg_change + noise
        
        # Ensure price doesn't go below zero
        next_price = max(0.01, next_price)
        
        predictions.append(round(next_price, 2))
        last_price = next_price
        
    return predictions
