from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from backend.utils.yf_utils import YFinanceHelper
from backend.NAV_Alert_Trigger import app as langgraph_app 
from backend.models.market_data import FinancialGraphRequest 
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()


# ========== PYDANTIC MODELS ==========

class StockPriceRequest(BaseModel):
    ticker: str
    period: str = "5d"
    interval: Optional[str] = "1d"


class ChatbotQueryRequest(BaseModel):
    query: str


class CompareStocksRequest(BaseModel):
    tickers: list[str]


# ========== ENDPOINTS ==========

# 1. Fetch Stock Price
@router.post('/get_price')
def fetch_stock_price(request: StockPriceRequest):
    try:
        logger.info(f'fetch_stock_price called for {request.ticker}, period: {request.period}, interval: {request.interval}')
        
        price_data = YFinanceHelper.get_price(request.ticker, request.period, request.interval)
        
        if 'error' in price_data:
            raise HTTPException(status_code=404, detail=price_data['error'])
        
        company_info = YFinanceHelper.get_company_info(request.ticker)
        key_stats = YFinanceHelper.get_key_stats(request.ticker)
        
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
            'interval': request.interval,
            'status': 'success'
        }
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error in fetch_stock_price: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(e)}')


# 2. Fetch Financials
@router.get("/get_financials")
def fetch_financials(
    ticker: str = Query(..., description="Stock ticker symbol"),
    include_news: bool = Query(False, description="Include recent news"),
    include_recommendations: bool = Query(False, description="Include analyst rating summary"),
):
    try:
        logger.info(f"fetch_financials called for {ticker}")
        financials = YFinanceHelper.get_financials(ticker)
        if "error" in financials:
            raise HTTPException(status_code=404, detail=financials["error"])
        key_stats = YFinanceHelper.get_key_stats(ticker)

        response = {
            "ticker": ticker.upper(),
            "financial_statements": {
                "income_statement": financials.get("income_statement", {}),
                "balance_sheet": financials.get("balance_sheet", {}),
                "cash_flow": financials.get("cash_flow", {}),
                "currency": financials.get("currency", "USD"),
            },
            "key_ratios": {
                "valuation": {
                    "pe_ratio": key_stats.get("trailing_pe"),
                    "forward_pe": key_stats.get("forward_pe"),
                    "peg_ratio": key_stats.get("peg_ratio"),
                    "price_to_book": key_stats.get("price_to_book"),
                    "price_to_sales": key_stats.get("price_to_sales"),
                    "ev_to_revenue": key_stats.get("enterprise_to_revenue"),
                    "ev_to_ebitda": key_stats.get("enterprise_to_ebitda"),
                },
                "profitability": {
                    "profit_margin": key_stats.get("profit_margins"),
                    "operating_margin": key_stats.get("operating_margins"),
                    "gross_margin": key_stats.get("gross_margins"),
                    "roe": key_stats.get("return_on_equity"),
                    "roa": key_stats.get("return_on_assets"),
                },
                "financial_health": {
                    "debt_to_equity": key_stats.get("debt_to_equity"),
                    "current_ratio": key_stats.get("current_ratio"),
                    "quick_ratio": key_stats.get("quick_ratio"),
                    "total_debt": key_stats.get("total_debt"),
                    "total_cash": key_stats.get("total_cash"),
                },
                "growth": {
                    "revenue_growth": key_stats.get("revenue_growth"),
                    "earnings_growth": key_stats.get("earnings_growth"),
                },
                "cash_flow": {
                    "operating_cashflow": key_stats.get("operating_cashflow"),
                    "free_cashflow": key_stats.get("free_cashflow"),
                },
            },
            "status": "success",
        }

        if include_news:
            news_data = YFinanceHelper.get_news(ticker, limit=5)
            response["news"] = news_data.get("articles", [])

        if include_recommendations:
            rec_summary = YFinanceHelper.get_recommendation_summary(ticker)
            response["analyst_rating"] = rec_summary.get("analyst_rating", "N/A")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in fetch_financials: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# 3. Market Summary
@router.get('/get_summary')
def fetch_market_summary():
    try:
        logger.info('fetch_market_summary called')
        summary = YFinanceHelper.get_market_summary()
        if 'error' in summary:
            raise HTTPException(status_code=500, detail=summary['error'])
        
        indices = summary.get('indices', {})
        positive_count = sum(1 for idx in indices.values() if idx.get('change_pct', 0) > 0)
        total_count = len(indices)
        positive_pct = (positive_count / total_count) * 100 if total_count > 0 else 0
        
        if positive_pct >= 70:
            sentiment = 'Bullish'
        elif positive_pct >= 40:
            sentiment = 'Neutral'
        else:
            sentiment = 'Bearish'
        
        response = {
            'indices': indices,
            'market_sentiment': sentiment,
            'sentiment_score': round(positive_pct, 1),
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


# 4. Run LangGraph Financial Graph
@router.post("/run_NAV_Alert_Trigger")
async def run_financial_graph(request: FinancialGraphRequest):
    state = {
        "ticker": request.ticker,
        "threshold": request.threshold,
        "price_data": {},
        "analysis": {},
        "alert": {}
    }
    try:
        result = langgraph_app.invoke(state)
        return result
    except Exception as e:
        logger.error(f"Error invoking LangGraph: {str(e)}")
        raise HTTPException(status_code=500, detail="Error running LangGraph workflow.")


# 5. Intelligent Chatbot Query
@router.post('/chatbot_query')
def chatbot_query(request: ChatbotQueryRequest):
    try:
        logger.info(f'chatbot_query called: {request.query}')
        query = request.query.upper()  # Work with uppercase for ticker detection

        # === SIMPLE & RELIABLE TICKER DETECTION ===
        import re
        
        # Find all potential ticker symbols (2-5 uppercase letters, optional .NS/.BO suffix)
        potential_tickers = re.findall(r'\b[A-Z]{2,5}(?:\.[A-Z]{2})?\b', query)
        
        # Filter out common English words
        stop_words = ['IS', 'AT', 'TO', 'OR', 'IN', 'ON', 'IT', 'AS', 'BY', 'AN', 'IF', 'NO', 'SO', 'UP', 
                      'DO', 'GO', 'THE', 'HOW', 'WHAT', 'SHOW', 'GET', 'TELL', 'MUCH', 'BETTER']
        
        # Validate tickers with yfinance
        mentioned_tickers = []
        for ticker in potential_tickers:
            if ticker not in stop_words:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    if info.get('symbol') or info.get('longName'):
                        mentioned_tickers.append(ticker)
                except:
                    pass
        
        mentioned_ticker = mentioned_tickers[0] if mentioned_tickers else None
        
        response_text = ''
        data = {}
        suggestions = []
        intent = 'unknown'
        endpoint_hint = None

        # === SIMPLE INTENT DETECTION ===
        query_lower = request.query.lower()

        # COMPARISON
        if ('compare' in query_lower or 'vs' in query_lower or 'versus' in query_lower or 
            'better' in query_lower or 'difference' in query_lower):
            intent = 'comparison'
            endpoint_hint = '/compare_stocks'
            
            if len(mentioned_tickers) >= 2:
                comparison_data = YFinanceHelper.compare_stocks(mentioned_tickers)
                if 'error' not in comparison_data:
                    response_text = f"Comparison of {', '.join(mentioned_tickers)}:"
                    data = comparison_data.get('comparison', {})
                    suggestions = ["View detailed analysis"]
                else:
                    response_text = comparison_data['error']
            else:
                response_text = f"For comparison, please specify tickers explicitly (e.g., 'Compare AAPL and MSFT')"

        # FINANCIALS
        elif any(kw in query_lower for kw in ['financial', 'balance', 'income', 'cash flow', 'profitable', 'earnings']):
            intent = 'financials'
            endpoint_hint = '/get_financials'
            
            if mentioned_ticker:
                stats = YFinanceHelper.get_key_stats(mentioned_ticker)
                if 'error' not in stats:
                    response_text = f"Financial metrics for {mentioned_ticker}:"
                    data = {
                        'ticker': mentioned_ticker,
                        'profit_margin': stats.get('profit_margins'),
                        'revenue_growth': stats.get('revenue_growth'),
                        'debt_to_equity': stats.get('debt_to_equity'),
                        'roe': stats.get('return_on_equity')
                    }
                else:
                    response_text = stats['error']
            else:
                response_text = "Please specify ticker (e.g., 'Is TSLA profitable?')"

        # NEWS
        elif any(kw in query_lower for kw in ['news', 'happening', 'update', 'latest']):
            intent = 'news'
            endpoint_hint = '/get_financials?include_news=true'
            
            if mentioned_ticker:
                news = YFinanceHelper.get_news(mentioned_ticker, limit=5)
                if 'error' not in news:
                    response_text = f"Latest news for {mentioned_ticker}:"
                    data = {'news': news.get('articles', []), 'ticker': mentioned_ticker}
                else:
                    response_text = news['error']
            else:
                response_text = "Please specify ticker for news"

        # RATIOS
        elif any(kw in query_lower for kw in ['pe', 'p/e', 'ratio', 'valuation']):
            intent = 'ratios'
            endpoint_hint = '/get_financials'
            
            if mentioned_ticker:
                stats = YFinanceHelper.get_key_stats(mentioned_ticker)
                if 'error' not in stats:
                    response_text = f"Valuation metrics for {mentioned_ticker}:"
                    data = {
                        'ticker': mentioned_ticker,
                        'pe_ratio': stats.get('trailing_pe'),
                        'forward_pe': stats.get('forward_pe'),
                        'price_to_book': stats.get('price_to_book')
                    }
                else:
                    response_text = stats['error']
            else:
                response_text = "Please specify ticker for ratios"

        # PRICE (most common)
        elif any(kw in query_lower for kw in ['price', 'trading', 'worth', 'cost', 'stock']):
            intent = 'price'
            endpoint_hint = '/get_price'
            
            if mentioned_ticker:
                price_data = YFinanceHelper.get_price(mentioned_ticker, period='1d')
                if 'error' not in price_data:
                    current = price_data.get('current_price')
                    change = price_data.get('change_pct', 0)
                    direction = 'up' if change > 0 else 'down'
                    response_text = f"{mentioned_ticker} is trading at {current}, {direction} {abs(change):.2f}% today."
                    data = {
                        'ticker': mentioned_ticker,
                        'current_price': current,
                        'change_pct': change
                    }
                else:
                    response_text = price_data['error']
            else:
                response_text = "Please specify ticker (e.g., 'What is AAPL price?')"

        # MARKET SUMMARY
        elif any(kw in query_lower for kw in ['market', 'indices', 'summary', 'sentiment']):
            intent = 'market_summary'
            endpoint_hint = '/get_summary'
            summary = YFinanceHelper.get_market_summary()
            if 'error' not in summary:
                response_text = f"Market summary retrieved."
                data = summary
            else:
                response_text = summary['error']

        # FALLBACK
        else:
            intent = 'general'
            response_text = "Please use explicit ticker symbols (e.g., AAPL, MSFT, TSLA, RELIANCE.NS) for best results."
            suggestions = [
                "Try: 'What is AAPL price?'",
                "Try: 'Compare AAPL and MSFT'",
                "Try: 'Show me TSLA news'"
            ]

        return {
            'query': request.query,
            'response': response_text,
            'data': data,
            'metadata': {
                'intent': intent,
                'detected_ticker': mentioned_ticker,
                'all_tickers': mentioned_tickers,
                'suggested_endpoint': endpoint_hint
            },
            'suggestions': suggestions,
            'status': 'success'
        }

    except Exception as e:
        logger.error(f'Error in chatbot_query: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(e)}')

# 6. Compare Multiple Stocks
@router.post('/compare_stocks')
def compare_multiple_stocks(request: CompareStocksRequest):
    try:
        logger.info(f'compare_stocks called for: {request.tickers}')
        
        if not request.tickers or len(request.tickers) < 2:
            raise HTTPException(status_code=400, detail="Please provide at least 2 tickers to compare")
        
        if len(request.tickers) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 stocks can be compared at once")
        
        comparison_data = YFinanceHelper.compare_stocks(request.tickers)
        
        if 'error' in comparison_data:
            raise HTTPException(status_code=404, detail=comparison_data['error'])
        
        return {
            'comparison': comparison_data.get('comparison', {}),
            'tickers': comparison_data.get('tickers', []),
            'status': 'success'
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error in compare_stocks: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(e)}')
