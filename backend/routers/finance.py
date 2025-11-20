from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from backend.models.market_data import StockPriceRequest, ChatbotQueryRequest
from backend.utils.yf_utils import YFinanceHelper
from backend.NAV_Alert_Trigger import app as langgraph_app  # LangGraph compiled graph
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 1. Fetch Stock Price
@router.post('/get_price')
def fetch_stock_price(request: StockPriceRequest):
    try:
        logger.info(f'fetch_stock_price called for {request.ticker}')
        price_data = YFinanceHelper.get_price(request.ticker, request.period)
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
class FinancialGraphRequest(BaseModel):
    ticker: str

@router.post("/run_NAV_Alert_Trigger")
async def run_financial_graph(request: FinancialGraphRequest):
    state = {
        "ticker": request.ticker,
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
        query = request.query.lower()

        # Basic list of common tickers with NSE suffix for Indian stocks
        common_tickers = {
            'aapl': 'AAPL',
            'msft': 'MSFT',
            'googl': 'GOOGL',
            'amzn': 'AMZN',
            'tsla': 'TSLA',
            'nvda': 'NVDA',
            'meta': 'META',
            'reliance': 'RELIANCE.NS',
            'tcs': 'TCS.NS',
            'infosys': 'INFY.NS',
            'hdfc': 'HDFC.NS',
            'icici': 'ICICI.NS'
        }

        # Detect ticker in query
        mentioned_ticker = None
        for key, val in common_tickers.items():
            if key in query:
                mentioned_ticker = val
                break

        response_text = ''
        data = {}
        suggestions = []

        if 'compare' in query or 'vs' in query or ' or ' in query:
            response_text = "To compare stocks, please use the comparison feature or the LangGraph agent endpoint."
            suggestions = ["Try: /run_financial_graph?query=compare AAPL and MSFT"]

        elif any(keyword in query for keyword in ['pe', 'p/e', 'ratio']):
            if mentioned_ticker:
                stats = YFinanceHelper.get_key_stats(mentioned_ticker)
                pe = stats.get('trailing_pe', 'N/A')
                response_text = f"The P/E ratio for {mentioned_ticker} is {pe}."
                data = {'pe_ratio': pe, 'ticker': mentioned_ticker}
                suggestions = [f"View full financials for {mentioned_ticker}", 'Compare with sector average']
            else:
                response_text = "Please specify which stock you want to check the P/E ratio for."

        elif any(keyword in query for keyword in ['price', 'cost', 'trading', 'stock', 'show', 'current', 'value', 'worth']):
            if mentioned_ticker:
                price_data = YFinanceHelper.get_price(mentioned_ticker, period='1d')
                if 'error' not in price_data:
                    current = price_data.get('current_price')
                    change = price_data.get('change_pct')
                    direction = 'up' if change > 0 else 'down'
                    response_text = f"{mentioned_ticker} is currently trading at {current}, {direction} {abs(change)}% today."
                    data = price_data
                    suggestions = [f"View {mentioned_ticker} chart", f"Get {mentioned_ticker} financials"]
                else:
                    response_text = price_data['error']
            else:
                response_text = "Please specify which stock price you want to check."

        elif any(keyword in query for keyword in ['financial', 'balance sheet', 'income statement']):
            if mentioned_ticker:
                response_text = f'Fetching financial statements for {mentioned_ticker}...'
                suggestions = [f'GET /get_financials?ticker={mentioned_ticker}']
            else:
                response_text = 'Please specify which company financials you want to see.'

        elif any(keyword in query for keyword in ['news', 'happening', 'update', 'latest', 'recent']):
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
