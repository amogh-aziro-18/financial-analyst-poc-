from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any


class StockPriceRequest(BaseModel):
    '''Request model for stock price queries'''
    ticker: str = Field(..., description='Stock ticker symbol (e.g., AAPL, RELIANCE.NS)')
    period: str = Field('5d', description='Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max')
    interval: Optional[str] = Field(None, description='Data interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo')
    
    @validator('ticker')
    def ticker_must_be_valid(cls, v):
        if not v or len(v) > 15:
            raise ValueError('Invalid ticker symbol')
        return v.upper()
    
    @validator('period')
    def period_must_be_valid(cls, v):
        valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
        if v not in valid_periods:
            raise ValueError(f'Period must be one of: {valid_periods}')
        return v
    
    @validator('interval')
    def interval_must_be_valid(cls, v):
        if v is None:
            return v
        valid_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
        if v not in valid_intervals:
            raise ValueError(f'Interval must be one of: {valid_intervals}')
        return v
class ChatbotQueryRequest(BaseModel):
    '''Request model for chatbot queries'''
    query: str = Field(..., description='Natural language financial query')
    context: Optional[Dict[str, Any]] = Field(None, description='Optional conversation context')
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Query cannot be empty')
        if len(v) > 1000:
            raise ValueError('Query too long (max 1000 characters)')
        return v.strip()


class CompareStocksRequest(BaseModel):
    '''Request model for stock comparison'''
    tickers: List[str] = Field(..., description='List of ticker symbols to compare')
    
    @validator('tickers')
    def validate_tickers(cls, v):
        if not v or len(v) < 2:
            raise ValueError('At least 2 tickers required for comparison')
        if len(v) > 5:
            raise ValueError('Maximum 5 tickers allowed for comparison')
        return [ticker.upper() for ticker in v]


class FinancialGraphRequest(BaseModel):
    '''Request model for NAV Alert with user-defined threshold'''
    ticker: str = Field(..., description='Stock ticker symbol (e.g., AAPL, RELIANCE.NS)')
    threshold: float = Field(5.0, description='NAV drop threshold percentage (default: 5.0)')
    
    @validator('ticker')
    def ticker_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Ticker cannot be empty')
        return v.strip().upper()
    
    @validator('threshold')
    def threshold_valid(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Threshold must be between 0 and 100')
        return v

# Response models (optional but good practice)

class PriceDataResponse(BaseModel):
    '''Response model for price data'''
    ticker: str
    price_data: Dict[str, Any]
    volume: Dict[str, Any]
    historical_data: List[Dict[str, Any]]
    company: Dict[str, Any]
    valuation: Dict[str, Any]
    profitability: Dict[str, Any]
    period: str
    status: str


class FinancialsResponse(BaseModel):
    '''Response model for financial statements'''
    ticker: str
    financial_statements: Dict[str, Any]
    key_ratios: Dict[str, Any]
    status: str


class MarketSummaryResponse(BaseModel):
    '''Response model for market summary'''
    indices: Dict[str, Any]
    market_sentiment: str
    sentiment_score: float
    indices_up: int
    indices_down: int
    timestamp: str
    status: str


class ChatbotResponse(BaseModel):
    '''Response model for chatbot'''
    query: str
    response: str
    data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    status: str


class ErrorResponse(BaseModel):
    '''Standard error response'''
    error: str
    detail: Optional[str] = None
    status: str = 'error'
