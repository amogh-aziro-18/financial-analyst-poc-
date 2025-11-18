from pydantic import BaseModel
from typing import Optional

class PriceRequest(BaseModel):
    ticker: str
    period: Optional[str] = "5d"

class PriceResponse(BaseModel):
    ticker: str
    current_price: float
    previous_price: float
    change_pct: float

class ChatbotQuery(BaseModel):
    query: str
    ticker: Optional[str] = None
