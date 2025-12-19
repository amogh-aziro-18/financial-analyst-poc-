import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from ui.components.utils_ui import get_price_data, get_stock_summary, calculate_risk_metrics, get_stock_news

def safe_format_metric(value, format_str="{:.2f}", multiplier=1.0, suffix=""):
    """Safely format a metric value, handling strings or None."""
    if value is None or value == "N/A":
        return "N/A"
    try:
        # Try to convert to float if it's a string
        num_value = float(value)
        return f"{format_str.format(num_value * multiplier)}{suffix}"
    except (ValueError, TypeError):
        return "N/A"

def render_stock_page(template="plotly_dark"):
    st.markdown("## 📈 Professional Stock Analysis")
    
    # Search Bar & Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ticker = st.text_input("Enter Stock Ticker (e.g., RELIANCE.NS, AAPL)", value="RELIANCE.NS")
    with col2:
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    with col3:
        interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)
            
    if ticker:
        with st.spinner(f"Fetching data for {ticker}..."):
            data = get_price_data(ticker, period=period, interval=interval)
            summary_data = get_stock_summary(ticker)
        
        if data and summary_data:
            df = data.get('df', pd.DataFrame())
            info = summary_data.get('info', {})
            currency_symbol = data.get('currency', '$')
            
            # Header Info
            current_price = data.get('current_price', 0)
            ticker_name = data.get('ticker', ticker)
            st.markdown(f"### {ticker_name} - {currency_symbol}{current_price:.2f}" if current_price else f"### {ticker_name}")
            
            # Change Indicator
            change_percent = data.get('change_percent', 0)
            color = "green" if change_percent >= 0 else "red"
            st.markdown(
                f"""
                <div style="font-size: 1.2rem; color: {color}; font-weight: bold; margin-bottom: 1rem;">
                    {change_percent:.2f}% Today
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # TABS
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "📊 Overview", 
                "📈 Technicals", 
                "💰 Fundamentals", 
                "⚠️ Risk",
                "📉 Financials",
                "🎯 Signals",
                "📰 News"
            ])
            
            # TAB 1: Overview
            with tab1:
                # Metrics Row
                m1, m2, m3, m4 = st.columns(4)
                try:
                    if not df.empty and 'Open' in df.columns:
                        m1.metric("Open", f"{currency_symbol}{df['Open'].iloc[-1]:.2f}")
                        m2.metric("High", f"{currency_symbol}{df['High'].iloc[-1]:.2f}")
                        m3.metric("Low", f"{currency_symbol}{df['Low'].iloc[-1]:.2f}")
                        m4.metric("Volume", f"{df['Volume'].iloc[-1]:,.0f}")
                    else:
                        m1.metric("Open", "N/A")
                        m2.metric("High", "N/A")
                        m3.metric("Low", "N/A")
                        m4.metric("Volume", "N/A")
                except Exception as e:
                    m1.metric("Open", "N/A")
                    m2.metric("High", "N/A")
                    m3.metric("Low", "N/A")
                    m4.metric("Volume", "N/A")
                
                # Main Chart (Price + SMA)
                try:
                    if not df.empty and all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
                        
                        # Candlestick
                        fig.add_trace(go.Candlestick(
                            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                            name='OHLC'
                        ), row=1, col=1)
                        
                        # SMAs (if available)
                        if 'SMA_20' in df.columns:
                            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name='SMA 20', line=dict(color='#00D4FF', width=1)), row=1, col=1)
                        if 'SMA_50' in df.columns:
                            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='#FF007A', width=1)), row=1, col=1)
                        
                        # Volume
                        colors = ['#00C853' if c >= o else '#FF3D00' for c, o in zip(df['Close'], df['Open'])]
                        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=colors), row=2, col=1)
                        
                        fig.update_layout(height=600, xaxis_rangeslider_visible=False, template=template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("📊 Chart data is currently unavailable")
                except Exception as e:
                    st.warning("📊 Unable to display chart at this time")
                
                business_summary = summary_data.get('summary', 'Business summary not available')
                st.info(f"**Business Summary:** {business_summary}")

            # TAB 2: Technical Analysis
            with tab2:
                col1, col2 = st.columns(2)
                
                # Bollinger Bands
                with col1:
                    st.markdown("#### Bollinger Bands")
                    try:
                        if not df.empty and all(col in df.columns for col in ['Close', 'BB_Upper', 'BB_Lower']):
                            fig_bb = go.Figure()
                            fig_bb.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close'))
                            fig_bb.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='Upper', line=dict(color='red', dash='dash')))
                            fig_bb.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name='Lower', line=dict(color='green', dash='dash')))
                            fig_bb.update_layout(height=400, template=template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_bb, use_container_width=True)
                        else:
                            st.info("Bollinger Bands data not available")
                    except Exception:
                        st.info("Bollinger Bands data not available")
                
                # Volatility
                with col2:
                    st.markdown("#### Historical Volatility")
                    try:
                        if not df.empty and 'Volatility' in df.columns:
                            fig_vol = go.Figure()
                            fig_vol.add_trace(go.Scatter(x=df.index, y=df['Volatility']*100, name='Volatility', fill='tozeroy', line=dict(color='#FFA500')))
                            fig_vol.update_layout(height=400, template=template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_vol, use_container_width=True)
                        else:
                            st.info("Volatility data not available")
                    except Exception:
                        st.info("Volatility data not available")
                
                # RSI & MACD
                st.markdown("#### RSI & MACD")
                try:
                    if not df.empty and all(col in df.columns for col in ['RSI', 'MACD', 'MACD_Signal', 'MACD_Hist']):
                        fig_ind = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, subplot_titles=('RSI', 'MACD'))
                        
                        # RSI
                        fig_ind.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#AB47BC')), row=1, col=1)
                        fig_ind.add_hline(y=70, line_dash="dash", line_color="red", row=1, col=1)
                        fig_ind.add_hline(y=30, line_dash="dash", line_color="green", row=1, col=1)
                        
                        # MACD
                        fig_ind.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='#29B6F6')), row=2, col=1)
                        fig_ind.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal', line=dict(color='#FF7043')), row=2, col=1)
                        fig_ind.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Hist'), row=2, col=1)
                        
                        fig_ind.update_layout(height=500, template=template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_ind, use_container_width=True)
                    else:
                        st.info("RSI & MACD data not available")
                except Exception:
                    st.info("RSI & MACD data not available")

            # TAB 3: Fundamentals
            with tab3:
                st.subheader("Key Fundamentals")
                f1, f2, f3 = st.columns(3)
                
                with f1:
                    st.markdown("##### Valuation")
                    st.write(f"**Market Cap:** {summary_data.get('market_cap', 'N/A')}")
                    st.write(f"**P/E Ratio:** {summary_data.get('pe_ratio', 'N/A')}")
                    st.write(f"**Forward P/E:** {info.get('forwardPE', 'N/A')}")
                    st.write(f"**PEG Ratio:** {info.get('pegRatio', 'N/A')}")
                
                with f2:
                    st.markdown("##### Profitability")
                    st.write(f"**Profit Margin:** {safe_format_metric(info.get('profitMargins'), multiplier=100, suffix='%')}")
                    st.write(f"**Operating Margin:** {safe_format_metric(info.get('operatingMargins'), multiplier=100, suffix='%')}")
                    st.write(f"**ROA:** {safe_format_metric(info.get('returnOnAssets'), multiplier=100, suffix='%')}")
                    st.write(f"**ROE:** {safe_format_metric(info.get('returnOnEquity'), multiplier=100, suffix='%')}")
                
                with f3:
                    st.markdown("##### Financial Health")
                    total_cash = info.get('totalCash')
                    total_debt = info.get('totalDebt')
                    
                    st.write(f"**Total Cash:** {safe_format_metric(total_cash, multiplier=1e-9, suffix='B')}")
                    st.write(f"**Total Debt:** {safe_format_metric(total_debt, multiplier=1e-9, suffix='B')}")
                    st.write(f"**Current Ratio:** {info.get('currentRatio', 'N/A')}")
                    st.write(f"**Quick Ratio:** {info.get('quickRatio', 'N/A')}")

            # TAB 4: Risk Analysis
            with tab4:
                st.subheader("Risk Metrics")
                try:
                    if not df.empty and 'Close' in df.columns:
                        risk = calculate_risk_metrics(df)
                        
                        r1, r2, r3 = st.columns(3)
                        r1.metric("Sharpe Ratio", f"{risk.get('Sharpe Ratio', 0):.2f}")
                        r2.metric("Max Drawdown", f"{risk.get('Max Drawdown', 0)*100:.2f}%")
                        r3.metric("Ann. Volatility", f"{risk.get('Annualized Volatility', 0)*100:.2f}%")
                        
                        st.markdown("---")
                        
                        # Drawdown Chart
                        returns = df['Close'].pct_change()
                        cumulative = (1 + returns).cumprod()
                        running_max = cumulative.expanding().max()
                        drawdown = (cumulative - running_max) / running_max
                        
                        fig_dd = go.Figure()
                        fig_dd.add_trace(go.Scatter(x=df.index, y=drawdown*100, fill='tozeroy', name='Drawdown', line=dict(color='#FF3D00')))
                        fig_dd.update_layout(title='Drawdown Over Time (%)', height=400, template=template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_dd, use_container_width=True)
                    else:
                        st.info("Risk metrics data not available")
                except Exception:
                    st.info("Risk metrics data not available")

            # TAB 5: Financial Statements
            with tab5:
                st.subheader("Financial Statements")
                stmt_type = st.radio("Select Statement", ["Income Statement", "Balance Sheet", "Cash Flow"], horizontal=True)
                
                try:
                    financials = summary_data.get('financials', {})
                    if stmt_type == "Income Statement":
                        income_stmt = financials.get('income_statement', pd.DataFrame())
                        if not income_stmt.empty:
                            # Sort columns (dates) descending
                            cols = sorted(income_stmt.columns, reverse=True)[:3]
                            st.dataframe(income_stmt[cols], use_container_width=True)
                        else:
                            st.info("Income statement data not available")
                    elif stmt_type == "Balance Sheet":
                        balance_sheet = financials.get('balance_sheet', pd.DataFrame())
                        if not balance_sheet.empty:
                            # Sort columns (dates) descending
                            cols = sorted(balance_sheet.columns, reverse=True)[:3]
                            st.dataframe(balance_sheet[cols], use_container_width=True)
                        else:
                            st.info("Balance sheet data not available")
                    else:
                        cash_flow = financials.get('cash_flow', pd.DataFrame())
                        if not cash_flow.empty:
                            # Sort columns (dates) descending
                            cols = sorted(cash_flow.columns, reverse=True)[:3]
                            st.dataframe(cash_flow[cols], use_container_width=True)
                        else:
                            st.info("Cash flow data not available")
                except Exception:
                    st.info("Financial statement data not available")

            # TAB 6: Trading Signals
            with tab6:
                st.subheader("Technical Signals")
                
                try:
                    if not df.empty and all(col in df.columns for col in ['RSI', 'MACD', 'MACD_Signal', 'Close', 'SMA_20', 'SMA_50']):
                        current_rsi = df['RSI'].iloc[-1]
                        current_macd = df['MACD'].iloc[-1]
                        macd_signal = df['MACD_Signal'].iloc[-1]
                        current_price = df['Close'].iloc[-1]
                        sma_20 = df['SMA_20'].iloc[-1]
                        sma_50 = df['SMA_50'].iloc[-1]
                        
                        # RSI Signal
                        if pd.notna(current_rsi):
                            if current_rsi > 70:
                                st.warning(f"⚠️ RSI is {current_rsi:.2f} - **OVERBOUGHT**")
                            elif current_rsi < 30:
                                st.success(f"✅ RSI is {current_rsi:.2f} - **OVERSOLD**")
                            else:
                                st.info(f"ℹ️ RSI is {current_rsi:.2f} - **NEUTRAL**")
                        else:
                            st.info("ℹ️ RSI data not available")
                        
                        # MACD Signal
                        if pd.notna(current_macd) and pd.notna(macd_signal):
                            if current_macd > macd_signal:
                                st.success(f"✅ MACD is above Signal Line - **BULLISH**")
                            else:
                                st.warning(f"⚠️ MACD is below Signal Line - **BEARISH**")
                        else:
                            st.info("ℹ️ MACD data not available")
                        
                        # SMA Signal
                        if pd.notna(current_price) and pd.notna(sma_20) and pd.notna(sma_50):
                            if current_price > sma_20 > sma_50:
                                st.success(f"✅ Price > SMA20 > SMA50 - **STRONG UPTREND**")
                            elif current_price < sma_20 < sma_50:
                                st.warning(f"⚠️ Price < SMA20 < SMA50 - **STRONG DOWNTREND**")
                            else:
                                st.info("ℹ️ Mixed SMA signals - **NO CLEAR TREND**")
                        else:
                            st.info("ℹ️ SMA data not available")
                    else:
                        st.info("Technical signals data not available")
                except Exception:
                    st.info("Technical signals data not available")

            # TAB 7: News
            with tab7:
                st.subheader("📰 Latest News")
                
                news_data = get_stock_news(ticker)
                
                if news_data and news_data.get('count', 0) > 0:
                    articles = news_data.get('articles', [])
                    
                    for article in articles:
                        title = article.get('title', 'No Title')
                        publisher = article.get('publisher', 'Unknown')
                        link = article.get('link', '#')
                        published = article.get('published', '')
                        
                        # Format published date if available
                        pub_date_str = ""
                        if published:
                            try:
                                from datetime import datetime
                                pub_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                                pub_date_str = pub_dt.strftime('%Y-%m-%d %H:%M')
                            except:
                                pub_date_str = published
                        
                        # Display article card
                        st.markdown(
                            f"""
                            <div style="padding: 1rem; margin-bottom: 1rem; background-color: var(--card-bg); border-radius: 0.5rem; border: 1px solid var(--border-color);">
                                <h4 style="margin-top: 0; margin-bottom: 0.5rem;">
                                    <a href="{link}" target="_blank" style="color: var(--primary-color); text-decoration: none;">{title}</a>
                                </h4>
                                <div style="color: var(--text-muted); font-size: 0.9rem;">
                                    <span>📰 {publisher}</span>
                                    {f' • <span>🕒 {pub_date_str}</span>' if pub_date_str else ''}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    st.info("No news articles available for this ticker.")
                    
        else:
            st.error("Could not fetch data. Please check the ticker symbol.")
