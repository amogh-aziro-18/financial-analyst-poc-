import yfinance as yf

class YFinanceHelper:

    @staticmethod
    def get_price(ticker: str, period: str = "5d"):
        '''Get stock/fund price data'''
        try:
            # Download with new yfinance format
            data = yf.download(ticker, period=period, progress=False)
            
            if data.empty or len(data) == 0:
                return {"error": "No data found for ticker"}
            
            # Handle multi-level or single-level columns
            if isinstance(data.columns, tuple) or 'Close' in str(data.columns):
                # Get Close prices (works for both formats)
                if ('Price', 'Close') in data.columns:
                    close_prices = data[('Price', 'Close')]
                elif 'Close' in data.columns:
                    close_prices = data['Close']
                else:
                    close_prices = data.iloc[:, 0]  # Fallback to first column
            else:
                close_prices = data['Close']
            
            current_price = float(close_prices.iloc[-1])
            previous_price = float(close_prices.iloc[-2]) if len(close_prices) > 1 else current_price
            change_pct = ((current_price - previous_price) / previous_price * 100) if previous_price != 0 else 0
            
            return {
                "ticker": ticker,
                "current_price": round(current_price, 2),
                "previous_price": round(previous_price, 2),
                "change_pct": round(change_pct, 2)
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch data: {str(e)}"}
