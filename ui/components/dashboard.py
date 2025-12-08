import streamlit as st
import plotly.graph_objects as go
import requests
from ui.components.charts import candlestick_chart

BACKEND_URL = "http://localhost:8001"

@st.cache_data(ttl=300)
def get_market_summary():
    """Fetch market summary from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/get_summary", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

@st.cache_data(ttl=300)
def get_price_from_backend(ticker):
    """Fetch individual stock price from backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/get_price",
            json={"ticker": ticker, "period": "1y", "interval": "1d"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            price_data = data.get('price_data', {})
            historical = data.get('historical_data', [])
            
            # Backend returns 'close' in historical data
            prices = [h['close'] for h in historical]
            dates = [h['date'] for h in historical]
            
            # We now have OHLC data available if needed, but for dashboard simple line/candle is fine
            # If candlestick_chart expects 'opens', 'highs', 'lows', we should provide them
            opens = [h.get('open', p) for h, p in zip(historical, prices)]
            highs = [h.get('high', p) for h, p in zip(historical, prices)]
            lows = [h.get('low', p) for h, p in zip(historical, prices)]
            
            return {
                "current_price": price_data.get('current_price', 0),
                "change_percent": price_data.get('change_pct', 0),
                "currency": "$",
                "history": {
                    "dates": dates,
                    "prices": prices,
                    "closes": prices,
                    "opens": opens,
                    "highs": highs,
                    "lows": lows
                }
            }
    except Exception as e:
        # print(f"Error fetching {ticker}: {e}")
        pass
    return None

def render_dashboard(template="plotly_dark"):
    st.markdown("## 📊 Market Overview")
    
    # Fetch market summary from backend
    market_data = get_market_summary()
    
    if market_data:
        indices_data = market_data.get('indices', {})
        
        # Market Sentiment Section
        st.markdown("### 🌡️ Market Sentiment")
        
        # Extract sentiment data
        sentiment = market_data.get('market_sentiment', 'Neutral')
        score = market_data.get('sentiment_score', 50)
        up_count = market_data.get('indices_up', 0)
        down_count = market_data.get('indices_down', 0)
        
        # Determine color based on sentiment
        if sentiment == 'Bullish':
            sent_color = "green"
        elif sentiment == 'Bearish':
            sent_color = "red"
        else:
            sent_color = "orange"
            
        # Display Sentiment Metrics
        s1, s2, s3, s4 = st.columns(4)
        
        with s1:
            st.markdown(f"**Mood:** <span style='color:{sent_color}; font-weight:bold; font-size:1.2em'>{sentiment}</span>", unsafe_allow_html=True)
        
        with s2:
            st.metric("Bullish Score", f"{score}%")
            
        with s3:
            st.metric("Indices Up", f"{up_count} 🟢")
            
        with s4:
            st.metric("Indices Down", f"{down_count} 🔴")
            
        st.markdown("---")

        # Top Metrics Row - Display major indices
        col1, col2, col3, col4 = st.columns(4)
        cols = [col1, col2, col3, col4]
        index_names = list(indices_data.keys())[:4]  # Get first 4 indices
        
        for idx_name, col in zip(index_names, cols):
            idx_data = indices_data.get(idx_name, {})
            with col:
                st.metric(
                    label=idx_name,
                    value=f"${idx_data.get('value', 0):.2f}",
                    delta=f"{idx_data.get('change_pct', 0):.2f}%"
                )
    else:
        st.warning("⚠️ Could not connect to backend. Please ensure the backend is running.")
        return
    
    st.markdown("---")
    
    # Main Dashboard Content
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown("### 📈 Market Trends (SPY)")
        
        # Get SPY data for chart
        spy_data = get_price_from_backend("SPY")
        if spy_data and spy_data['history']['dates']:
            # Use the shared chart component
            # It will fallback to Line Chart since we only have prices
            fig = candlestick_chart(spy_data, "SPY", template=template)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Loading chart data...")
            
    with c2:
        st.markdown("### 👁️ Watchlist")
        watchlist = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
        
        for ticker in watchlist:
            data = get_price_from_backend(ticker)
            if data:
                color = "green" if data['change_percent'] >= 0 else "red"
                st.markdown(
                    f"""
                    <div class="css-card" style="padding: 1rem; display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; background-color: var(--card-bg); border-radius: 0.5rem; border: 1px solid var(--border-color);">
                        <div>
                            <div style="font-weight: bold; font-size: 1.1rem;">{ticker}</div>
                            <div style="font-size: 0.9rem; color: var(--text-muted);">${data['current_price']:.2f}</div>
                        </div>
                        <div style="color: {color}; font-weight: bold;">
                            {data['change_percent']:.2f}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
