from backend.langgraph_integration import fetch_stock_price, check_NAV_drop, trigger_alert_if_drop
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

# Define a custom state schema for your workflow
class FinancialState(TypedDict):
    ticker: str
    threshold: float  # ADD THIS LINE
    price_data: dict
    analysis: dict
    alert: dict

# Define node functions that receive and update state
def fetch_node(state: FinancialState):
    """Fetch stock price data"""
    result = fetch_stock_price(state["ticker"])
    return {"price_data": result}

def analyze_node(state: FinancialState):
    """Analyze price data and check against user-defined threshold"""
    price_data = state["price_data"].get("data")
    threshold = state.get("threshold", 5.0)  # Get threshold from state
    
    if price_data:
        # Pass threshold to check_NAV_drop
        result = check_NAV_drop(price_data, threshold)  # ADD threshold parameter
        return {"analysis": result}
    else:
        return {"analysis": {"success": False, "error": "No price data"}}
    
def alert_node(state: FinancialState):
    """Trigger alert if threshold exceeded"""
    analysis = state.get("analysis", {})
    analysis_data = analysis.get("data", {})
    threshold = state.get("threshold", 5.0)
    
    if not analysis.get("success", False):
        return {"alert": {"success": False, "error": "No analysis data"}}

    if analysis_data.get("alert_triggered"):
        drop_pct = analysis_data.get("drop_percentage", 0)
        severity = analysis_data.get("severity", "MEDIUM")
        return {
            "alert": {
                "success": True, 
                "alert_status": "ALERT", 
                "message": f"⚠️ [{severity}] Alert! Drop of {drop_pct:.2f}% exceeds {threshold}% threshold",
                "drop_percentage": drop_pct,
                "threshold": threshold,
                "severity": severity
            }
        }
    else:
        change_pct = analysis_data.get("drop_percentage", 0)
        return {
            "alert": {
                "success": True, 
                "alert_status": "NO ALERT", 
                "message": f"✅ No alert. Price change {change_pct:.2f}% within {threshold}% threshold",
                "threshold": threshold
            }
        }

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
    # Test with custom threshold
    initial_state = {
        "ticker": "RELIANCE.NS",
        "threshold": 3.0,  # Test with 3% threshold
        "price_data": {},
        "analysis": {},
        "alert": {}
    }
    
    result = app.invoke(initial_state)
    print(result)
