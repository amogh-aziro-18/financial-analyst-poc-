# LangGraph integration (Vade handles this)
def run_financial_graph(ticker: str):
    """
    Nodes:
        - fetch_stock_price
        - check_NAV_drop
        - trigger_alert_if_drop
    Returns structured JSON for frontend/agent
    """
    return {"ticker": ticker, "reasoning": []}
