from fastapi import APIRouter
from backend.models.market_data import PriceRequest, PriceResponse, ChatbotQuery
from backend.utils.yf_utils import YFinanceHelper

router = APIRouter(prefix="/finance", tags=["finance"])

@router.post("/get_price")
def get_price(request: PriceRequest):
    '''Get stock/fund price data'''
    result = YFinanceHelper.get_price(request.ticker, request.period)
    return result

@router.get("/get_summary")
def get_summary(ticker: str):
    return {"status": "ok", "summary": None}

@router.get("/get_financials")
def get_financials(ticker: str):
    return {"status": "ok", "financials": None}

@router.post("/chatbot_query")
def chatbot_query(request: ChatbotQuery):
    '''Handle chatbot queries'''
    if request.ticker:
        data = YFinanceHelper.get_price(request.ticker)
        return {
            "query": request.query,
            "response": f"Current NAV for {request.ticker}: Rs.{data['current_price']:.2f}",
            "data": data
        }
    else:
        return {
            "query": request.query,
            "response": "Please provide a ticker symbol",
            "data": {}
        }

@router.get("/run_financial_graph")
def run_financial_graph(ticker: str):
    return {"status": "ok", "graph": None}
