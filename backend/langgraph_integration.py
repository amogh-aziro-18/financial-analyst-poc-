from backend.utils.yf_utils import YFinanceHelper
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def fetch_stock_price(ticker: str):
    """Fetch stock price data for given ticker"""
    try:
        logger.info(f"Fetching stock price for ticker: {ticker}")
        price_data = YFinanceHelper.get_price(ticker)
        if 'error' in price_data:
            return {"success": False, "error": price_data['error']}
        return {"success": True, "data": price_data}
    except Exception as e:
        logger.error(f"Error fetching stock price: {e}")
        return {"success": False, "error": str(e)}


def check_NAV_drop(price_data: dict, threshold: float = 5.0):
    """
    Analyze if the NAV or price has dropped beyond user-defined threshold.
    
    Args:
        price_data: Dict containing current_price and previous_price
        threshold: Drop percentage threshold (default: 5.0%)
    
    Returns:
        Dict with analysis results and alert flag
    """
    try:
        current_price = price_data.get("current_price")
        previous_price = price_data.get("previous_price")

        if current_price is None or previous_price is None:
            return {"success": False, "error": "Missing price data"}

        # Calculate drop percentage
        drop_percentage = ((previous_price - current_price) / previous_price) * 100
        
        # Check against user-defined threshold
        alert_triggered = drop_percentage >= threshold
        
        # Determine severity
        if drop_percentage >= threshold * 1.5:
            severity = "HIGH"
        elif drop_percentage >= threshold:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        analysis = {
            "drop_percentage": round(drop_percentage, 2),
            "threshold": threshold,
            "alert_triggered": alert_triggered,
            "severity": severity,
            "current_price": current_price,
            "previous_price": previous_price,
            "message": f"⚠️ Price dropped {drop_percentage:.2f}% (threshold: {threshold}%)" if alert_triggered 
                      else f"✅ Price change {drop_percentage:.2f}% within {threshold}% threshold"
        }

        logger.info(f"NAV Analysis: {analysis['message']}")
        return {"success": True, "data": analysis}
    except Exception as e:
        logger.error(f"Error in check_NAV_drop: {e}")
        return {"success": False, "error": str(e)}


def trigger_alert_if_drop(analysis_result: dict):
    """
    Trigger an alert message if NAV drop alert flag is set.
    
    Args:
        analysis_result: Result from check_NAV_drop
    
    Returns:
        Alert info dict with success flag and message
    """
    try:
        if not analysis_result.get("success"):
            return {"success": False, "error": "Invalid analysis result"}

        data = analysis_result.get("data", {})
        
        if data.get("alert_triggered"):
            drop_pct = data.get("drop_percentage", 0)
            threshold = data.get("threshold", 5.0)
            severity = data.get("severity", "UNKNOWN")
            
            message = f"🚨 ALERT [{severity}]: NAV dropped by {drop_pct}%, exceeding {threshold}% threshold!"
            logger.warning(message)
            
            return {
                "success": True, 
                "alert": True, 
                "message": message,
                "severity": severity,
                "drop_percentage": drop_pct,
                "threshold": threshold
            }
        else:
            message = f"✅ No alert triggered. Price change within acceptable range."
            logger.info(message)
            return {"success": True, "alert": False, "message": message}
            
    except Exception as e:
        logger.error(f"Error in trigger_alert_if_drop: {e}")
        return {"success": False, "error": str(e)}
