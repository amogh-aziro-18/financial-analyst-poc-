import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from ui.components.utils_ui import get_price_data, get_stock_summary, calculate_risk_metrics, get_stock_news

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
            df = data['df']
            info = summary_data['info']
            currency_symbol = data.get('currency', '$')
            
            # Header Info
            st.markdown(f"### {data['ticker']} - {currency_symbol}{data['current_price']}")
            
            # Change Indicator
            color = "green" if data['change_percent'] >= 0 else "red"
            st.markdown(
                f"""
                <div style="font-size: 1.2rem; color: {color}; font-weight: bold; margin-bottom: 1rem;">
                    {data['change_percent']}% Today
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
                m1.metric("Open", f"{currency_symbol}{df['Open'].iloc[-1]:.2f}")
                m2.metric("High", f"{currency_symbol}{df['High'].iloc[-1]:.2f}")
                m3.metric("Low", f"{currency_symbol}{df['Low'].iloc[-1]:.2f}")
                m4.metric("Volume", f"{df['Volume'].iloc[-1]:,.0f}")
                
                # Main Chart (Price + SMA)
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
                
                # Candlestick
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                    name='OHLC'
                ), row=1, col=1)
                
                # SMAs
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name='SMA 20', line=dict(color='#00D4FF', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='#FF007A', width=1)), row=1, col=1)
                
                # Volume
                colors = ['#00C853' if c >= o else '#FF3D00' for c, o in zip(df['Close'], df['Open'])]
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=colors), row=2, col=1)
                
                fig.update_layout(height=600, xaxis_rangeslider_visible=False, template=template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"**Business Summary:** {summary_data['summary']}")

            # TAB 2: Technical Analysis
            with tab2:
                col1, col2 = st.columns(2)
                
                # Bollinger Bands
                with col1:
                    st.markdown("#### Bollinger Bands")
                    fig_bb = go.Figure()
                    fig_bb.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close'))
                    fig_bb.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='Upper', line=dict(color='red', dash='dash')))
                    fig_bb.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name='Lower', line=dict(color='green', dash='dash')))
                    fig_bb.update_layout(height=400, template=template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_bb, use_container_width=True)
                
                # Volatility
                with col2:
                    st.markdown("#### Historical Volatility")
                    fig_vol = go.Figure()
                    fig_vol.add_trace(go.Scatter(x=df.index, y=df['Volatility']*100, name='Volatility', fill='tozeroy', line=dict(color='#FFA500')))
                    fig_vol.update_layout(height=400, template=template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_vol, use_container_width=True)
                
                # RSI & MACD
                st.markdown("#### RSI & MACD")
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

            # TAB 3: Fundamentals
            with tab3:
                st.subheader("Key Fundamentals")
                f1, f2, f3 = st.columns(3)
                
                with f1:
                    st.markdown("##### Valuation")
                    st.write(f"**Market Cap:** {summary_data['market_cap']}")
                    st.write(f"**P/E Ratio:** {summary_data['pe_ratio']}")
                    st.write(f"**Forward P/E:** {info.get('forwardPE', 'N/A')}")
                    st.write(f"**PEG Ratio:** {info.get('pegRatio', 'N/A')}")
                
                with f2:
                    st.markdown("##### Profitability")
                    st.write(f"**Profit Margin:** {info.get('profitMargins', 0)*100:.2f}%")
                    st.write(f"**Operating Margin:** {info.get('operatingMargins', 0)*100:.2f}%")
                    st.write(f"**ROA:** {info.get('returnOnAssets', 0)*100:.2f}%")
                    st.write(f"**ROE:** {info.get('returnOnEquity', 0)*100:.2f}%")
                
                with f3:
                    st.markdown("##### Financial Health")
                    st.write(f"**Total Cash:** {info.get('totalCash', 0)/1e9:.2f}B")
                    st.write(f"**Total Debt:** {info.get('totalDebt', 0)/1e9:.2f}B")
                    st.write(f"**Current Ratio:** {info.get('currentRatio', 'N/A')}")
                    st.write(f"**Quick Ratio:** {info.get('quickRatio', 'N/A')}")

            # TAB 4: Risk Analysis
            with tab4:
                st.subheader("Risk Metrics")
                risk = calculate_risk_metrics(df)
                
                r1, r2, r3 = st.columns(3)
                r1.metric("Sharpe Ratio", f"{risk['Sharpe Ratio']:.2f}")
                r2.metric("Max Drawdown", f"{risk['Max Drawdown']*100:.2f}%")
                r3.metric("Ann. Volatility", f"{risk['Annualized Volatility']*100:.2f}%")
                
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

            # TAB 5: Financial Statements
            with tab5:
                st.subheader("Financial Statements")
                stmt_type = st.radio("Select Statement", ["Income Statement", "Balance Sheet", "Cash Flow"], horizontal=True)
                
                if stmt_type == "Income Statement":
                    st.dataframe(summary_data['financials']['income_statement'])
                elif stmt_type == "Balance Sheet":
                    st.dataframe(summary_data['financials']['balance_sheet'])
                else:
                    st.dataframe(summary_data['financials']['cash_flow'])

            # TAB 6: Trading Signals
            with tab6:
                st.subheader("Technical Signals")
                
                current_rsi = df['RSI'].iloc[-1]
                current_macd = df['MACD'].iloc[-1]
                macd_signal = df['MACD_Signal'].iloc[-1]
                current_price = df['Close'].iloc[-1]
                sma_20 = df['SMA_20'].iloc[-1]
                sma_50 = df['SMA_50'].iloc[-1]
                bb_upper = df['BB_Upper'].iloc[-1]
                bb_lower = df['BB_Lower'].iloc[-1]
                
                # RSI Signal
                if current_rsi > 70:
                    st.warning(f"⚠️ RSI is {current_rsi:.2f} - **OVERBOUGHT**")
                elif current_rsi < 30:
                    st.success(f"✅ RSI is {current_rsi:.2f} - **OVERSOLD**")
                else:
                    st.info(f"ℹ️ RSI is {current_rsi:.2f} - **NEUTRAL**")
                
                # MACD Signal
                if current_macd > macd_signal:
                    st.success(f"✅ MACD is above Signal Line - **BULLISH**")
                else:
                    st.warning(f"⚠️ MACD is below Signal Line - **BEARISH**")
                
                # SMA Signal
                if current_price > sma_20 > sma_50:
                    st.success(f"✅ Price > SMA20 > SMA50 - **STRONG UPTREND**")
                elif current_price < sma_20 < sma_50:
                    st.warning(f"⚠️ Price < SMA20 < SMA50 - **STRONG DOWNTREND**")
                else:
                    st.info("ℹ️ Mixed SMA signals - **NO CLEAR TREND**")

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
