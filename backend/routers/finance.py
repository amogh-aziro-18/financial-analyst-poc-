from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.models.market_data import StockPriceRequest, ChatbotQueryRequest
from backend.utils.yf_utils import YFinanceHelper
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# ============= 1. COMPREHENSIVE STOCK PRICE =============

@router.post('/get_price')
def fetch_stock_price(request: StockPriceRequest):
    '''
    Fetch comprehensive stock price data
    
    Returns:
        - Current price with change percentage
        - Historical data for charts
        - 52-week high/low
        - Volume analysis
        - Company basic info
        - Key statistics (P/E, market cap, etc.)
    '''
    try:
        logger.info(f'fetch_stock_price called for {request.ticker}')
        
        # Get price data
        price_data = YFinanceHelper.get_price(request.ticker, request.period)
        
        if 'error' in price_data:
            raise HTTPException(status_code=404, detail=price_data['error'])
        
        # Get company info
        company_info = YFinanceHelper.get_company_info(request.ticker)
        
        # Get key stats
        key_stats = YFinanceHelper.get_key_stats(request.ticker)
        
        # Combine all data
        response = {
            'ticker': request.ticker.upper(),
            'price_data': {
                'current_price': price_data.get('current_price'),
                'change_pct': price_data.get('change_pct'),
                'change_amount': price_data.get('change_amount'),
                'previous_close': price_data.get('previous_price'),
                '52_week_high': price_data.get('52_week_high'),
                '52_week_low': price_data.get('52_week_low'),
                'distance_from_high': price_data.get('distance_from_high'),
                'distance_from_low': price_data.get('distance_from_low'),
            },
            'volume': {
                'current': price_data.get('volume'),
                'average': price_data.get('avg_volume')
            },
            'historical_data': price_data.get('historical_data', []),
            'company': {
                'name': company_info.get('company_name'),
                'sector': company_info.get('sector'),
                'industry': company_info.get('industry')
            },
            'valuation': {
                'market_cap': key_stats.get('market_cap'),
                'pe_ratio': key_stats.get('trailing_pe'),
                'forward_pe': key_stats.get('forward_pe'),
                'price_to_book': key_stats.get('price_to_book'),
                'dividend_yield': key_stats.get('dividend_yield')
            },
            'profitability': {
                'profit_margin': key_stats.get('profit_margins'),
                'roe': key_stats.get('return_on_equity'),
                'roa': key_stats.get('return_on_assets')
            },
            'period': request.period,
            'status': 'success'
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error in fetch_stock_price: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(e)}')

# ============= 2. COMPLETE FINANCIAL STATEMENTS =============

@router.get('/get_financials')
def fetch_financials(
    ticker: str = Query(..., description='Stock ticker symbol'),
    include_news: bool = Query(False, description='Include recent news'),
    include_recommendations: bool = Query(False, description='Include analyst recommendations')
):
    '''
    Fetch complete financial data
    
    Returns:
        - Income statement, balance sheet, cash flow
        - Key financial ratios
        - Financial health metrics
        - Optional: News and analyst recommendations
    '''
    try:
        logger.info(f'fetch_financials called for {ticker}')
        
        # Get financial statements
        financials = YFinanceHelper.get_financials(ticker)
        
        if 'error' in financials:
            raise HTTPException(status_code=404, detail=financials['error'])
        
        # Get key stats for ratios
        key_stats = YFinanceHelper.get_key_stats(ticker)
        
        # Build response
        response = {
            'ticker': ticker.upper(),
            'financial_statements': {
                'income_statement': financials.get('income_statement', {}),
                'balance_sheet': financials.get('balance_sheet', {}),
                'cash_flow': financials.get('cash_flow', {}),
                'currency': financials.get('currency', 'USD')
            },
            'key_ratios': {
                'valuation': {
                    'pe_ratio': key_stats.get('trailing_pe'),
                    'forward_pe': key_stats.get('forward_pe'),
                    'peg_ratio': key_stats.get('peg_ratio'),
                    'price_to_book': key_stats.get('price_to_book'),
                    'price_to_sales': key_stats.get('price_to_sales'),
                    'ev_to_revenue': key_stats.get('enterprise_to_revenue'),
                    'ev_to_ebitda': key_stats.get('enterprise_to_ebitda')
                },
                'profitability': {
                    'profit_margin': key_stats.get('profit_margins'),
                    'operating_margin': key_stats.get('operating_margins'),
                    'gross_margin': key_stats.get('gross_margins'),
                    'roe': key_stats.get('return_on_equity'),
                    'roa': key_stats.get('return_on_assets')
                },
                'financial_health': {
                    'debt_to_equity': key_stats.get('debt_to_equity'),
                    'current_ratio': key_stats.get('current_ratio'),
                    'quick_ratio': key_stats.get('quick_ratio'),
                    'total_debt': key_stats.get('total_debt'),
                    'total_cash': key_stats.get('total_cash')
                },
                'growth': {
                    'revenue_growth': key_stats.get('revenue_growth'),
                    'earnings_growth': key_stats.get('earnings_growth')
                },
                'cash_flow': {
                    'operating_cashflow': key_stats.get('operating_cashflow'),
                    'free_cashflow': key_stats.get('free_cashflow')
                }
            },
            'status': 'success'
        }
        
        # Add news if requested
        if include_news:
            news_data = YFinanceHelper.get_news(ticker, limit=5)
            response['news'] = news_data.get('articles', [])
        
        # Add recommendations if requested
        if include_recommendations:
            recs = YFinanceHelper.get_recommendations(ticker)
            response['recommendations'] = recs.get('recommendations', [])
            response['analyst_rating'] = key_stats.get('recommendation', 'N/A')
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error in fetch_financials: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(e)}')

# ============= 3. COMPREHENSIVE MARKET SUMMARY =============

@router.get('/get_summary')
def fetch_market_summary():
    '''
    Get comprehensive market overview
    
    Returns:
        - Major indices (S&P500, NASDAQ, NIFTY, SENSEX, etc.)
        - Market sentiment indicators
        - Timestamp of data
    '''
    try:
        logger.info('fetch_market_summary called')
        
        # Get market summary
        summary = YFinanceHelper.get_market_summary()
        
        if 'error' in summary:
            raise HTTPException(status_code=500, detail=summary['error'])
        
        # Analyze market sentiment
        indices = summary.get('indices', {})
        positive_count = sum(1 for idx in indices.values() if idx.get('change_pct', 0) > 0)
        total_count = len(indices)
        
        if total_count > 0:
            positive_pct = (positive_count / total_count) * 100
            if positive_pct >= 70:
                sentiment = 'Bullish'
            elif positive_pct >= 40:
                sentiment = 'Neutral'
            else:
                sentiment = 'Bearish'
        else:
            sentiment = 'Unknown'
        
        response = {
            'indices': indices,
            'market_sentiment': sentiment,
            'sentiment_score': round(positive_pct, 1) if total_count > 0 else 0,
            'indices_up': positive_count,
            'indices_down': total_count - positive_count,
            'timestamp': summary.get('timestamp'),
            'status': 'success'
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error in fetch_market_summary: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(e)}')

# ============= 4. LANGGRAPH AGENT (Placeholder) =============

@router.get('/run_financial_graph')
def run_financial_graph(query: str = Query(..., description='Financial analysis query')):
    '''
    Run LangGraph financial agent for complex queries
    
    This endpoint will invoke the LangGraph agent for:
        - Multi-step financial analysis
        - Investment recommendations
        - Complex comparisons
        - Natural language queries
    
    TODO: Implement LangGraph agent in backend/langgraph_integration.py
    '''
    try:
        logger.info(f'run_financial_graph called with query: {query}')
        
        # TODO: Import and call LangGraph agent
        # from backend.langgraph_integration import FinancialAgent
        # agent = FinancialAgent()
        # result = agent.run(query)
        # return result
        
        # Placeholder response
        return {
            'query': query,
            'status': 'pending',
            'message': 'LangGraph agent integration in progress',
            'placeholder_response': f'Analysis for: {query}',
            'note': 'This will be replaced with actual LangGraph agent logic'
        }
        
    except Exception as e:
        logger.error(f'Error in run_financial_graph: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(e)}')

# ============= 5. INTELLIGENT CHATBOT =============

@router.post('/chatbot_query')
def chatbot_query(request: ChatbotQueryRequest):
    '''
    Intelligent chatbot that understands financial queries
    
    Handles queries like:
        - "What's the P/E ratio of Apple?"
        - "Compare AAPL and MSFT"
        - "Show me RELIANCE financials"
        - "Is Tesla overvalued?"
    
    Returns natural language responses with supporting data
    '''
    try:
        logger.info(f'chatbot_query called: {request.query}')
        
        query = request.query.lower()
        
        # Simple intent detection (can be enhanced with LLM)
        response_text = ''
        data = {}
        suggestions = []
        
        # Detect ticker mentions
        common_tickers = ['aapl', 'msft', 'googl', 'amzn', 'tsla', 'nvda', 'meta', 
                         'reliance', 'tcs', 'infosys', 'hdfc', 'icici']
        mentioned_ticker = None
        for ticker in common_tickers:
            if ticker in query:
                mentioned_ticker = ticker.upper()
                if ticker in ['reliance', 'tcs', 'infosys', 'hdfc', 'icici']:
                    mentioned_ticker += '.NS'
                break
        
        # Handle different query types
        if 'compare' in query or 'vs' in query or ' or ' in query:
            response_text = f'To compare stocks, please use the comparison feature or the LangGraph agent endpoint.'
            suggestions = ['Try: /run_financial_graph?query=compare AAPL and MSFT']
            
        elif 'pe' in query or 'p/e' in query or 'ratio' in query:
            if mentioned_ticker:
                stats = YFinanceHelper.get_key_stats(mentioned_ticker)
                pe = stats.get('trailing_pe', 'N/A')
                response_text = f"The P/E ratio for {mentioned_ticker} is {pe}"
                if pe != 'N/A':
                    response_text += f". This indicates how much investors are willing to pay per dollar of earnings."
                data = {'pe_ratio': pe, 'ticker': mentioned_ticker}
                suggestions = [f'View full financials for {mentioned_ticker}', 'Compare with sector average']
            else:
                response_text = 'Please specify which stock you want to check the P/E ratio for.'
                
        elif any(word in query for word in ['price', 'cost', 'trading', 'stock', 'show', 'current', 'value', 'worth']):
            if mentioned_ticker:
                price_data = YFinanceHelper.get_price(mentioned_ticker, period='1d')
                if 'error' not in price_data:
                    current = price_data.get('current_price')
                    change = price_data.get('change_pct')
                    response_text = f"{mentioned_ticker} is currently trading at , "
                    response_text += f"{'up' if change > 0 else 'down'} {abs(change)}% today."
                    data = price_data
                    suggestions = [f'View {mentioned_ticker} chart', f'Get {mentioned_ticker} financials']
                else:
                    response_text = price_data['error']
            else:
                response_text = 'Please specify which stock price you want to check.'
                
        elif 'financial' in query or 'balance sheet' in query or 'income statement' in query:
            if mentioned_ticker:
                response_text = f'Fetching financial statements for {mentioned_ticker}...'
                suggestions = [f'GET /get_financials?ticker={mentioned_ticker}']
            else:
                response_text = 'Please specify which company financials you want to see.'
                
        elif any(word in query for word in ['news', 'happening', 'update', 'latest', 'recent']):
            if mentioned_ticker:
                news = YFinanceHelper.get_news(mentioned_ticker, limit=3)
                if 'error' not in news:
                    articles = news.get('articles', [])
                    response_text = f'Here are the latest news for {mentioned_ticker}:'
                    data = {'news': articles}
                else:
                    response_text = news['error']
            else:
                response_text = 'Please specify which stock news you want to see.'
                
        else:
            # Generic response
            response_text = f'I understand you asked: "{request.query}". For complex analysis, try the LangGraph agent endpoint.'
            suggestions = [
                'Ask about stock prices',
                'Request financial ratios',
                'Get company news',
                'Compare multiple stocks'
            ]
        
        return {
            'query': request.query,
            'response': response_text,
            'data': data,
            'suggestions': suggestions,
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f'Error in chatbot_query: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(e)}')

