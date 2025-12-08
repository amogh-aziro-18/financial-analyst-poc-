import streamlit as st
import plotly.graph_objects as go
import requests
from ui.components.charts import get_chart_template

BACKEND_URL = "http://localhost:8001"

def get_comparison_data(tickers):
    """Fetch comparison data from backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/compare_stocks",
            json={"tickers": tickers},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_price_history(ticker):
    """Fetch price history for a single ticker"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/get_price",
            json={"ticker": ticker, "period": "1y", "interval": "1d"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            historical = data.get('historical_data', [])
            return {
                "dates": [h['date'] for h in historical],
                "prices": [h['close'] for h in historical]
            }
    except:
        pass
    return None

def render_charts_page(template="plotly_dark"):
    st.markdown("## 📉 Stock Comparison & Charts")
    
    st.markdown("Compare performance of multiple stocks.")
    
    # Input for tickers
    default_tickers = "AAPL, MSFT, GOOGL"
    tickers_input = st.text_input("Enter tickers separated by comma", value=default_tickers)
    
    if tickers_input:
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        
        if len(tickers) < 2:
            st.warning("Please enter at least 2 tickers to compare.")
        else:
            if st.button("Compare Performance"):
                with st.spinner("Fetching data..."):
                    # 1. Comparison Table
                    comp_data = get_comparison_data(tickers)
                    
                    if comp_data and 'comparison' in comp_data:
                        st.markdown("### Fundamental Comparison")
                        
                        # Transform dict to list for dataframe
                        rows = []
                        for ticker, data in comp_data['comparison'].items():
                            row = {'Ticker': ticker}
                            row.update(data)
                            rows.append(row)
                            
                        st.dataframe(rows, use_container_width=True)
                    
                    # 2. Performance Chart (Normalized)
                    st.markdown("### Relative Performance (1 Year)")
                    
                    fig = go.Figure()
                    
                    for ticker in tickers:
                        hist = get_price_history(ticker)
                        if hist and hist['prices']:
                            # Normalize to percentage change
                            start_price = hist['prices'][0]
                            if start_price > 0:
                                norm_prices = [(p - start_price) / start_price * 100 for p in hist['prices']]
                                fig.add_trace(go.Scatter(
                                    x=hist['dates'],
                                    y=norm_prices,
                                    mode='lines',
                                    name=ticker
                                ))
                    
                    fig.update_layout(
                        template=template,
                        title="Relative Performance (%)",
                        xaxis_title="Date",
                        yaxis_title="Change (%)",
                        height=600,
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True)
