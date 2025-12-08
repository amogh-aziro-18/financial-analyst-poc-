import requests
import pandas as pd
import numpy as np
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8001"
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/stock-alert"

def get_currency_symbol(ticker: str):
    """Determine currency symbol based on ticker"""
    ticker = ticker.upper()
    if ticker.endswith(".NS") or ticker.endswith(".BO"):
        return "₹"
    return "$"

# ===========================
# TECHNICAL ANALYSIS FUNCTIONS
# ===========================

def calculate_moving_averages(df):
    """Calculate various moving averages"""
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    return df

def calculate_rsi(df, period=14):
    """Calculate Relative Strength Index"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def calculate_macd(df):
    """Calculate MACD indicator"""
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    return df

def calculate_bollinger_bands(df, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    df['BB_Middle'] = df['Close'].rolling(window=period).mean()
    df['BB_Std'] = df['Close'].rolling(window=period).std()
    df['BB_Upper'] = df['BB_Middle'] + (std_dev * df['BB_Std'])
    df['BB_Lower'] = df['BB_Middle'] - (std_dev * df['BB_Std'])
    return df

def calculate_volatility(df, period=20):
    """Calculate historical volatility"""
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Returns'].rolling(window=period).std() * np.sqrt(252)
    return df

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=period).mean()
    return df

def calculate_obv(df):
    """Calculate On-Balance Volume"""
    df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
    return df

def calculate_risk_metrics(df):
    """Calculate various risk metrics"""
    returns = df['Close'].pct_change().dropna()
    
    if returns.empty:
        return {
            'Sharpe Ratio': 0, 'Max Drawdown': 0, 'VaR (95%)': 0,
            'CVaR (95%)': 0, 'Annualized Volatility': 0, 'Annualized Return': 0
        }

    risk_free_rate = 0.02
    excess_returns = returns - risk_free_rate/252
    sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns.std() if returns.std() != 0 else 0
    
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    var_95 = np.percentile(returns, 5)
    cvar_95 = returns[returns <= var_95].mean()
    
    return {
        'Sharpe Ratio': sharpe_ratio,
        'Max Drawdown': max_drawdown,
        'VaR (95%)': var_95,
        'CVaR (95%)': cvar_95,
        'Annualized Volatility': returns.std() * np.sqrt(252),
        'Annualized Return': returns.mean() * 252
    }

# ===========================
# BACKEND API CALLS
# ===========================

def get_price_data(ticker: str, period="1y", interval="1d"):
    """
    Fetches price data from backend API.
    NOTE: Backend currently only provides closing prices, not full OHLCV data.
    This limits technical analysis capabilities.
    """
    try:
        print(f"[DEBUG] Fetching data for {ticker} from backend...")
        
        # Call backend API
        response = requests.post(
            f"{BACKEND_URL}/get_price",
            json={"ticker": ticker, "period": period, "interval": interval},
            timeout=10
        )
        
        print(f"[DEBUG] Backend response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[ERROR] Backend error: {response.status_code}")
            print(f"[ERROR] Response: {response.text}")
            return None
        
        data = response.json()
        print(f"[DEBUG] Response keys: {data.keys()}")
        
        # Backend only provides closing prices in historical_data
        historical = data.get('historical_data', [])
        print(f"[DEBUG] Historical data length: {len(historical)}")
        
        if not historical:
            print("[ERROR] No historical data received from backend")
            return None
        
        # Create DataFrame with available data
        df = pd.DataFrame(historical)
        print(f"[DEBUG] DataFrame columns: {df.columns.tolist()}")
        
        df['Date'] = pd.to_datetime(df['date'])
        df.set_index('Date', inplace=True)
        
        # Map backend keys to DataFrame columns (Capitalized for consistency with indicators)
        df['Open'] = df['open']
        df['High'] = df['high']
        df['Low'] = df['low']
        df['Close'] = df['close']
        df['Volume'] = df['volume']
        
        # Calculate technical indicators
        df = calculate_moving_averages(df)
        df = calculate_rsi(df)
        df = calculate_macd(df)
        df = calculate_bollinger_bands(df)
        df = calculate_volatility(df)
        
        # Calculate ATR and OBV now that we have full OHLCV data
        df = calculate_atr(df)
        df = calculate_obv(df)
        
        price_data = data.get('price_data', {})
        currency = get_currency_symbol(ticker)
        
        result = {
            "ticker": ticker.upper(),
            "currency": currency,
            "current_price": price_data.get('current_price', 0),
            "change_percent": price_data.get('change_pct', 0),
            "df": df,
            "history": {
                "dates": df.index.strftime('%Y-%m-%d').tolist(),
                "closes": df['Close'].tolist(),
                "opens": df['Open'].tolist(),
                "highs": df['High'].tolist(),
                "lows": df['Low'].tolist(),
                "volumes": df['Volume'].tolist()
            }
        }
        
        print(f"[DEBUG] Successfully processed data for {ticker}")
        print(f"[DEBUG] Current price: {result['current_price']}, Change: {result['change_percent']}%")
        
        return result
        
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to backend. Is it running on http://localhost:8000?")
        return None
    except Exception as e:
        print(f"[ERROR] Error fetching data for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_stock_summary(ticker: str):
    """
    Fetches stock summary/fundamentals from backend API.
    """
    try:
        response = requests.get(
            f"{BACKEND_URL}/get_financials",
            params={"ticker": ticker, "include_news": False},
            timeout=10
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        key_ratios = data.get('key_ratios', {})
        financial_statements = data.get('financial_statements', {})
        
        # Extract key metrics
        valuation = key_ratios.get('valuation', {})
        profitability = key_ratios.get('profitability', {})
        financial_health = key_ratios.get('financial_health', {})
        
        return {
            "summary": f"Financial data for {ticker}",
            "sector": "N/A",  # Backend doesn't provide this in current response
            "market_cap": "N/A",
            "pe_ratio": valuation.get('pe_ratio', 'N/A'),
            "info": {
                "trailingPE": valuation.get('pe_ratio'),
                "forwardPE": valuation.get('forward_pe'),
                "pegRatio": valuation.get('peg_ratio'),
                "priceToBook": valuation.get('price_to_book'),
                "profitMargins": profitability.get('profit_margin'),
                "operatingMargins": profitability.get('operating_margin'),
                "returnOnAssets": profitability.get('roa'),
                "returnOnEquity": profitability.get('roe'),
                "totalCash": financial_health.get('total_cash'),
                "totalDebt": financial_health.get('total_debt'),
                "currentRatio": financial_health.get('current_ratio'),
                "quickRatio": financial_health.get('quick_ratio'),
            },
            "financials": {
                "income_statement": pd.DataFrame([financial_statements.get('income_statement', {})]),
                "balance_sheet": pd.DataFrame([financial_statements.get('balance_sheet', {})]),
                "cash_flow": pd.DataFrame([financial_statements.get('cash_flow', {})])
            }
        }
    except Exception as e:
        print(f"Error fetching summary for {ticker}: {e}")
        return None

def get_chatbot_response(query: str, history: list):
    """
    Sends a query to the chatbot backend.
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/chatbot_query",
            json={"query": query},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return {"answer": data.get('response', 'No response')}
    except Exception as e:
        pass
    
    return {"answer": "I am currently running in offline mode. Please connect the backend for AI responses."}

# ===========================
# N8N WEBHOOK INTEGRATION
# ===========================

def send_alert_config(email: str, ticker: str, threshold_type: str, threshold_value: float):
    """
    Sends alert configuration to n8n webhook.
    Returns (success: bool, message: str)
    """
    try:
        payload = {
            "email": email,
            "ticker": ticker.upper(),
            "threshold_type": threshold_type,
            "threshold_value": threshold_value,
            "timestamp": datetime.now().isoformat()
        }
        
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True, f"Alert configured successfully for {ticker}!"
        else:
            return False, f"Failed to configure alert. Status code: {response.status_code}"
    
    except requests.exceptions.ConnectionError:
        return False, "Could not connect to n8n webhook. Please ensure n8n is running."
    except requests.exceptions.Timeout:
        return False, "Request timed out. Please try again."
    except Exception as e:
        return False, f"Error: {str(e)}"
