from backend.langgraph_integration import fetch_stock_price, check_NAV_drop, trigger_alert_if_drop
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

# Define a custom state schema for your workflow
class FinancialState(TypedDict):
    ticker: str
    price_data: dict
    analysis: dict
    alert: dict

# Define node functions that receive and update state
def fetch_node(state: FinancialState):
    """Fetch stock price data"""
    result = fetch_stock_price(state["ticker"])
    return {"price_data": result}

def analyze_node(state: FinancialState):
    price_data = state["price_data"].get("data")
    if price_data:
        result = check_NAV_drop(price_data)
        return {"analysis": result}
    else:
        return {"analysis": {"success": False, "error": "No price data"}}
    
def alert_node(state: FinancialState):
    analysis = state.get("analysis", {})
    analysis_data = analysis.get("data", {})
    if not analysis.get("success", False):
        return {"alert": {"success": False, "error": "No analysis data"}}

    if analysis_data.get("alert_triggered"):
        return {"alert": {"success": True, "alert_status": "ALERT", "message": "Alert triggered due to drop."}}
    else:
        return {"alert": {"success": True, "alert_status": "NO ALERT", "message": "No alert triggered."}}
# Create the StateGraph
graph = StateGraph(FinancialState)

# Add nodes
graph.add_node("fetch", fetch_node)
graph.add_node("analyze", analyze_node)
graph.add_node("alert", alert_node)

# Define edges (workflow)
graph.add_edge(START, "fetch")
graph.add_edge("fetch", "analyze")
graph.add_edge("analyze", "alert")
graph.add_edge("alert", END)

# Compile the graph
app = graph.compile()

if __name__ == "__main__":
    # Run the workflow
    initial_state = {
        "ticker": "RELIANCE.NS",
        "price_data": {},
        "analysis": {},
        "alert": {}
    }
    
    result = app.invoke(initial_state)
    print(result)
