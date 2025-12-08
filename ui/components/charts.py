import plotly.graph_objects as go
from plotly.subplots import make_subplots

def get_chart_template(is_light_mode=False):
    """Return the appropriate plotly template based on theme"""
    return "plotly_white" if is_light_mode else "plotly_dark"

def candlestick_chart(data, ticker, template="plotly_dark"):
    """
    Create a candlestick chart with volume if available, otherwise a line chart.
    data: dict with 'history' key containing 'dates', 'opens', 'highs', 'lows', 'closes', 'volumes'
          OR 'dates', 'prices' (fallback)
    """
    if not data or 'history' not in data:
        return go.Figure()
        
    history = data['history']
    dates = history.get('dates', [])
    
    # Check if we have full OHLC data
    has_ohlc = all(k in history for k in ['opens', 'highs', 'lows', 'closes'])
    
    if has_ohlc:
        opens = history['opens']
        highs = history['highs']
        lows = history['lows']
        closes = history['closes']
        volumes = history.get('volumes', [])
        
        # Create subplots: 2 rows, 1 col. Row 1 is price (70%), Row 2 is volume (30%)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.03, subplot_titles=(f'{ticker} Price', 'Volume'),
                            row_heights=[0.7, 0.3])

        # Candlestick trace
        fig.add_trace(go.Candlestick(
            x=dates,
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            name='Price'
        ), row=1, col=1)

        # Volume trace
        if volumes:
            colors = ['red' if c < o else 'green' for o, c in zip(opens, closes)]
            fig.add_trace(go.Bar(
                x=dates,
                y=volumes,
                marker_color=colors,
                name='Volume'
            ), row=2, col=1)
            
        fig.update_layout(height=600)
        
    else:
        # Fallback to Line Chart
        prices = history.get('prices', history.get('closes', []))
        if not prices:
            return go.Figure()
            
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode='lines',
            name='Price',
            line=dict(color='#00D4FF', width=2)
        ))
        fig.update_layout(title=f'{ticker} Price History', height=500)

    fig.update_layout(
        template=template,
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False
    )
    
    return fig

def moving_average_chart(data, ticker, window=20, template="plotly_dark"):
    """
    Create a line chart with moving average
    """
    if not data or 'history' not in data:
        return go.Figure()

    history = data['history']
    dates = history.get('dates', [])
    # Use prices or closes
    prices = history.get('prices', history.get('closes', []))
    
    if not prices:
        return go.Figure()
    
    # Calculate MA manually if not provided
    ma = []
    for i in range(len(prices)):
        if i < window - 1:
            ma.append(None)
        else:
            ma.append(sum(prices[i-window+1:i+1]) / window)

    fig = go.Figure()
    
    # Price Line
    fig.add_trace(go.Scatter(
        x=dates, 
        y=prices, 
        mode='lines', 
        name='Price',
        line=dict(color='#00D4FF', width=2)
    ))
    
    # MA Line
    fig.add_trace(go.Scatter(
        x=dates, 
        y=ma, 
        mode='lines', 
        name=f'{window}-Day MA',
        line=dict(color='#FF007A', width=2, dash='dash')
    ))

    fig.update_layout(
        title=f'{ticker} - Price vs {window}-Day Moving Average',
        template=template,
        height=500,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Date",
        yaxis_title="Price"
    )
    
    return fig
