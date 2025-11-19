import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YFinanceHelper:
    '''
    Comprehensive yfinance helper for production-grade financial data
    Handles: prices, company info, financials, ratios, news, recommendations
    '''
    
    # ============= PRICE & HISTORICAL DATA =============
    
    @staticmethod
    def get_price(ticker: str, period: str = '5d') -> Dict[str, Any]:
        '''
        Get comprehensive stock price data with historical context
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'RELIANCE.NS')
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
        Returns:
            Dict with current price, change, volume, historical data
        '''
        try:
            logger.info(f'Fetching price data for {ticker}, period: {period}')
            
            # Download historical data
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            
            if data.empty or len(data) == 0:
                return {'error': f'No data found for ticker: {ticker}'}
            
            # Extract Close and Volume columns (guaranteed to be 1D Series with .history())
            close_prices = data['Close']
            volumes = data['Volume'] if 'Volume' in data.columns else None
            
            # Calculate metrics
            current_price = float(close_prices.iloc[-1])
            previous_price = float(close_prices.iloc[-2]) if len(close_prices) > 1 else current_price
            change_pct = ((current_price - previous_price) / previous_price * 100) if previous_price != 0 else 0
            
            # Get 52-week high/low
            high_52w = float(close_prices.max()) if len(close_prices) > 1 else current_price
            low_52w = float(close_prices.min()) if len(close_prices) > 1 else current_price
            
            # Average volume
            avg_volume = 0
            current_volume = 0
            if volumes is not None and len(volumes) > 0:
                avg_volume = int(volumes.mean())
                current_volume = int(volumes.iloc[-1])
            
            # Historical data for charts
            historical = []
            for idx in range(len(close_prices)):
                date = close_prices.index[idx]
                price = close_prices.iloc[idx]
                
                # Handle different date formats
                if isinstance(date, str):
                    date_str = date
                elif hasattr(date, 'strftime'):
                    date_str = date.strftime('%Y-%m-%d')
                else:
                    date_str = str(date)[:10]
                
                historical.append({
                    'date': date_str,
                    'price': round(float(price), 2)
                })
            
            return {
                'ticker': ticker.upper(),
                'current_price': round(current_price, 2),
                'previous_price': round(previous_price, 2),
                'change_pct': round(change_pct, 2),
                'change_amount': round(current_price - previous_price, 2),
                'volume': current_volume,
                'avg_volume': avg_volume,
                '52_week_high': round(high_52w, 2),
                '52_week_low': round(low_52w, 2),
                'distance_from_high': round(((current_price - high_52w) / high_52w) * 100, 2),
                'distance_from_low': round(((current_price - low_52w) / low_52w) * 100, 2),
                'historical_data': historical[-30:],  # Last 30 data points
                'period': period
            }
            
        except Exception as e:
            logger.error(f'Error fetching price for {ticker}: {str(e)}')
            return {'error': f'Failed to fetch price data: {str(e)}'}
    
    
    # ============= COMPANY INFORMATION =============
    
    @staticmethod
    def get_company_info(ticker: str) -> Dict[str, Any]:
        '''Get comprehensive company information'''
        try:
            logger.info(f'Fetching company info for {ticker}')
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'ticker': ticker.upper(),
                'company_name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'description': info.get('longBusinessSummary', 'N/A'),
                'website': info.get('website', 'N/A'),
                'employees': info.get('fullTimeEmployees', 'N/A'),
                'city': info.get('city', 'N/A'),
                'state': info.get('state', 'N/A'),
                'country': info.get('country', 'N/A'),
                'phone': info.get('phone', 'N/A')
            }
        except Exception as e:
            logger.error(f'Error fetching company info for {ticker}: {str(e)}')
            return {'error': f'Failed to fetch company info: {str(e)}'}
    
    
    # ============= KEY STATISTICS & RATIOS =============
    
    @staticmethod
    def get_key_stats(ticker: str) -> Dict[str, Any]:
        '''Get key financial statistics and valuation metrics'''
        try:
            logger.info(f'Fetching key stats for {ticker}')
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'ticker': ticker.upper(),
                'market_cap': info.get('marketCap', 'N/A'),
                'enterprise_value': info.get('enterpriseValue', 'N/A'),
                'trailing_pe': info.get('trailingPE', 'N/A'),
                'forward_pe': info.get('forwardPE', 'N/A'),
                'peg_ratio': info.get('pegRatio', 'N/A'),
                'price_to_book': info.get('priceToBook', 'N/A'),
                'price_to_sales': info.get('priceToSalesTrailing12Months', 'N/A'),
                'enterprise_to_revenue': info.get('enterpriseToRevenue', 'N/A'),
                'enterprise_to_ebitda': info.get('enterpriseToEbitda', 'N/A'),
                'eps_trailing': info.get('trailingEps', 'N/A'),
                'eps_forward': info.get('forwardEps', 'N/A'),
                'book_value': info.get('bookValue', 'N/A'),
                'dividend_rate': info.get('dividendRate', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'payout_ratio': info.get('payoutRatio', 'N/A'),
                'profit_margins': info.get('profitMargins', 'N/A'),
                'operating_margins': info.get('operatingMargins', 'N/A'),
                'gross_margins': info.get('grossMargins', 'N/A'),
                'return_on_assets': info.get('returnOnAssets', 'N/A'),
                'return_on_equity': info.get('returnOnEquity', 'N/A'),
                'revenue_growth': info.get('revenueGrowth', 'N/A'),
                'earnings_growth': info.get('earningsGrowth', 'N/A'),
                'total_cash': info.get('totalCash', 'N/A'),
                'total_debt': info.get('totalDebt', 'N/A'),
                'debt_to_equity': info.get('debtToEquity', 'N/A'),
                'current_ratio': info.get('currentRatio', 'N/A'),
                'quick_ratio': info.get('quickRatio', 'N/A'),
                'operating_cashflow': info.get('operatingCashflow', 'N/A'),
                'free_cashflow': info.get('freeCashflow', 'N/A'),
                'target_high_price': info.get('targetHighPrice', 'N/A'),
                'target_low_price': info.get('targetLowPrice', 'N/A'),
                'target_mean_price': info.get('targetMeanPrice', 'N/A'),
                'recommendation': info.get('recommendationKey', 'N/A')
            }
        except Exception as e:
            logger.error(f'Error fetching stats for {ticker}: {str(e)}')
            return {'error': f'Failed to fetch statistics: {str(e)}'}
    
    
    # ============= FINANCIAL STATEMENTS =============
    
    @staticmethod
    def get_financials(ticker: str) -> Dict[str, Any]:
        '''Get complete financial statements'''
        try:
            logger.info(f'Fetching financials for {ticker}')
            stock = yf.Ticker(ticker)
            
            income_stmt = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
            
            def extract_latest(df):
                if df is None or df.empty:
                    return {}
                latest_col = df.columns[0]
                return {str(idx): float(val) if pd.notna(val) else None 
                       for idx, val in df[latest_col].items()}
            
            return {
                'ticker': ticker.upper(),
                'income_statement': extract_latest(income_stmt),
                'balance_sheet': extract_latest(balance_sheet),
                'cash_flow': extract_latest(cash_flow),
                'currency': stock.info.get('currency', 'USD')
            }
        except Exception as e:
            logger.error(f'Error fetching financials for {ticker}: {str(e)}')
            return {'error': f'Failed to fetch financial statements: {str(e)}'}
    
    
    # ============= NEWS & RECOMMENDATIONS =============
    
    @staticmethod
    def get_news(ticker: str, limit: int = 10) -> Dict[str, Any]:
        '''Get recent news articles for a stock'''
        try:
            logger.info(f'Fetching news for {ticker}, limit: {limit}')
            stock = yf.Ticker(ticker)
            news = stock.news
            
            articles = []
            for article in news[:limit]:
                articles.append({
                    'title': article.get('title', 'N/A'),
                    'publisher': article.get('publisher', 'N/A'),
                    'link': article.get('link', 'N/A'),
                    'published': datetime.fromtimestamp(
                        article.get('providerPublishTime', 0)
                    ).strftime('%Y-%m-%d %H:%M:%S') if article.get('providerPublishTime') else 'N/A'
                })
            
            return {
                'ticker': ticker.upper(),
                'news_count': len(articles),
                'articles': articles
            }
        except Exception as e:
            logger.error(f'Error fetching news for {ticker}: {str(e)}')
            return {'error': f'Failed to fetch news: {str(e)}'}
    
    
    @staticmethod
    def get_recommendations(ticker: str) -> Dict[str, Any]:
        '''Get analyst recommendations'''
        try:
            logger.info(f'Fetching recommendations for {ticker}')
            stock = yf.Ticker(ticker)
            recommendations = stock.recommendations
            
            if recommendations is None or recommendations.empty:
                return {'ticker': ticker.upper(), 'recommendations': []}
            
            recent = recommendations.tail(10)
            recs = []
            for idx, row in recent.iterrows():
                if hasattr(idx, 'strftime'):
                    date_str = idx.strftime('%Y-%m-%d')
                else:
                    date_str = str(idx)[:10]
                
                recs.append({
                    'date': date_str,
                    'firm': row.get('Firm', 'N/A'),
                    'to_grade': row.get('To Grade', 'N/A'),
                    'from_grade': row.get('From Grade', 'N/A'),
                    'action': row.get('Action', 'N/A')
                })
            
            return {
                'ticker': ticker.upper(),
                'recommendations': recs
            }
        except Exception as e:
            logger.error(f'Error fetching recommendations for {ticker}: {str(e)}')
            return {'error': f'Failed to fetch recommendations: {str(e)}'}
    
    
    # ============= COMPARISON & ANALYSIS =============
    
    @staticmethod
    def compare_stocks(tickers: List[str]) -> Dict[str, Any]:
        '''Compare multiple stocks side by side'''
        try:
            logger.info(f'Comparing stocks: {tickers}')
            comparison = {}
            
            for ticker in tickers:
                stats = YFinanceHelper.get_key_stats(ticker)
                price = YFinanceHelper.get_price(ticker, period='1mo')
                
                comparison[ticker.upper()] = {
                    'current_price': price.get('current_price'),
                    'change_pct': price.get('change_pct'),
                    'market_cap': stats.get('market_cap'),
                    'pe_ratio': stats.get('trailing_pe'),
                    'profit_margin': stats.get('profit_margins'),
                    'roe': stats.get('return_on_equity'),
                    'dividend_yield': stats.get('dividend_yield'),
                    'recommendation': stats.get('recommendation')
                }
            
            return {
                'comparison': comparison,
                'tickers': [t.upper() for t in tickers]
            }
        except Exception as e:
            logger.error(f'Error comparing stocks: {str(e)}')
            return {'error': f'Failed to compare stocks: {str(e)}'}
    
    
    # ============= MARKET SUMMARY =============
    
    @staticmethod
    def get_market_summary() -> Dict[str, Any]:
        '''Get overall market summary with major indices'''
        try:
            logger.info('Fetching market summary')
            
            indices = {
                'S&P 500': '^GSPC',
                'NASDAQ': '^IXIC',
                'Dow Jones': '^DJI',
                'NIFTY 50': '^NSEI',
                'SENSEX': '^BSESN',
                'Russell 2000': '^RUT'
            }
            
            summary = {}
            for name, ticker in indices.items():
                try:
                    stock = yf.Ticker(ticker)
                    data = stock.history(period='5d')
                    if not data.empty:
                        closes = data['Close']
                        current = float(closes.iloc[-1])
                        previous = float(closes.iloc[-2]) if len(closes) > 1 else current
                        change_pct = ((current - previous) / previous * 100) if previous != 0 else 0
                        
                        summary[name] = {
                            'value': round(current, 2),
                            'change_pct': round(change_pct, 2),
                            'ticker': ticker
                        }
                except:
                    continue
            
            return {
                'indices': summary,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f'Error fetching market summary: {str(e)}')
            return {'error': f'Failed to fetch market summary: {str(e)}'}
    
    
    # ============= INDIAN MARKET SUPPORT =============
    
    @staticmethod
    def search_indian_ticker(company_name: str) -> Dict[str, Any]:
        '''Search for Indian stock ticker by company name'''
        try:
            suffixes = ['.NS', '.BO']
            clean_name = company_name.upper().replace(' ', '')
            
            results = []
            for suffix in suffixes:
                ticker = clean_name + suffix
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    if info.get('longName'):
                        results.append({
                            'ticker': ticker,
                            'name': info.get('longName'),
                            'exchange': 'NSE' if suffix == '.NS' else 'BSE'
                        })
                except:
                    continue
            
            return {
                'query': company_name,
                'results': results
            }
        except Exception as e:
            logger.error(f'Error searching ticker: {str(e)}')
            return {'error': f'Failed to search ticker: {str(e)}'}

    
    # ============= SMART TICKER DETECTION =============
    
    @staticmethod
    def find_ticker(query: str) -> Optional[str]:
        """
        Intelligently find ticker symbol from user query
        Handles: company names, ticker symbols, fuzzy matching
        
        Returns: Ticker symbol if found, None otherwise
        """
        try:
            # First, check if query contains a valid ticker (all caps 1-5 letters)
            import re
            words = query.upper().split()
            for word in words:
                # Check if it looks like a ticker (1-5 uppercase letters)
                if re.match(r'^[A-Z]{1,5}$', word):
                    # Validate it exists
                    try:
                        stock = yf.Ticker(word)
                        info = stock.info
                        if info.get('symbol') or info.get('longName'):
                            logger.info(f'Found valid ticker: {word}')
                            return word
                    except:
                        pass
            
            # If no direct ticker found, try to extract company name and search
            # Remove common query words
            stop_words = ['what', 'is', 'the', 'price', 'of', 'stock', 'show', 'me', 
                         'get', 'tell', 'about', 'current', 'today', 'trading', 'at']
            
            clean_query = query.lower()
            for word in stop_words:
                clean_query = clean_query.replace(word, '')
            
            clean_query = clean_query.strip()
            
            if not clean_query:
                return None
            
            # Try common company name patterns
            # Example: "apple" -> AAPL, "microsoft" -> MSFT
            possible_tickers = []
            
            # Try the cleaned query as ticker directly
            ticker_candidate = clean_query.upper().replace(' ', '')[:5]
            try:
                stock = yf.Ticker(ticker_candidate)
                info = stock.info
                if info.get('longName'):
                    possible_tickers.append(ticker_candidate)
            except:
                pass
            
            # Try first word capitalized + common suffixes
            first_word = clean_query.split()[0] if clean_query else ''
            if first_word:
                # Try direct ticker
                try:
                    stock = yf.Ticker(first_word.upper())
                    info = stock.info
                    if info.get('longName'):
                        possible_tickers.append(first_word.upper())
                except:
                    pass
                
                # For Indian companies, try with .NS suffix
                try:
                    ticker_ns = first_word.upper() + '.NS'
                    stock = yf.Ticker(ticker_ns)
                    info = stock.info
                    if info.get('longName'):
                        possible_tickers.append(ticker_ns)
                except:
                    pass
            
            # Return first valid ticker found
            if possible_tickers:
                logger.info(f'Found ticker from query: {possible_tickers[0]}')
                return possible_tickers[0]
            
            # If still nothing, log and return None
            logger.warning(f'Could not find ticker for query: {query}')
            return None
            
        except Exception as e:
            logger.error(f'Error in find_ticker: {str(e)}')
            return None