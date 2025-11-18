from fastapi import APIRouter

router = APIRouter(prefix="/finance", tags=["finance"])

@router.get("/get_price")
def get_price(ticker: str):
    return {"status": "ok", "price": None}

@router.get("/get_summary")
def get_summary(ticker: str):
    return {"status": "ok", "summary": None}

@router.get("/get_financials")
def get_financials(ticker: str):
    return {"status": "ok", "financials": None}

@router.post("/chatbot_query")
def chatbot_query(query: str):
    return {"status": "ok", "response": None}

@router.get("/run_financial_graph")
def run_financial_graph(ticker: str):
    return {"status": "ok", "graph": None}
