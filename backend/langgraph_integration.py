from backend.utils.yf_utils import YFinanceHelper
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def fetch_stock_price(ticker: str):
    try:
        logger.info(f"Fetching stock price for ticker: {ticker}")
        price_data = YFinanceHelper.get_price(ticker)
        if 'error' in price_data:
            return {"success": False, "error": price_data['error']}
        return {"success": True, "data": price_data}
    except Exception as e:
        logger.error(f"Error fetching stock price: {e}")
        return {"success": False, "error": str(e)}

def check_NAV_drop(price_data: dict):
    """
    Analyze if the NAV or price has dropped beyond a certain threshold (e.g., 5%).
    Returns a dict with analysis results and alert flag.
    """
    try:
        current_price = price_data.get("current_price")
        previous_price = price_data.get("previous_price")

        if current_price is None or previous_price is None:
            return {"success": False, "error": "Missing price data"}

        drop_percentage = ((previous_price - current_price) / previous_price) * 100
        alert_triggered = drop_percentage >= 5.0  # example threshold 5%

        analysis = {
            "drop_percentage": round(drop_percentage, 2),
            "alert_triggered": alert_triggered,
            "message": "Price dropped significantly." if alert_triggered else "No significant drop."
        }

        return {"success": True, "data": analysis}
    except Exception as e:
        return {"success": False, "error": str(e)}

def trigger_alert_if_drop(analysis_result: dict):
    """
    Trigger an alert message if NAV drop alert flag is set.
    Returns alert info dict with success flag and optional message.
    """
    try:
        if not analysis_result.get("success"):
            return {"success": False, "error": "Invalid analysis result"}

        data = analysis_result.get("data", {})
        if data.get("alert_triggered"):
            message = f"Alert! NAV dropped by {data.get('drop_percentage')}%."
            return {"success": True, "alert": True, "message": message}
        else:
            return {"success": True, "alert": False, "message": "No alert triggered."}
    except Exception as e:
        return {"success": False, "error": str(e)}
