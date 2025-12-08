import streamlit as st
import re
import requests  # NEW: for calling the n8n webhook


# --- Webhook config ---
WEBHOOK_URL = "http://localhost:5679/webhook-test/alert"


def send_alert_config(email, ticker, threshold_type, threshold_value):
    """
    Send alert configuration to n8n webhook as a POST JSON payload.
    Returns: (success: bool, message: str)
    """
    try:
        payload = {
            "email": email,
            "ticker": ticker,
            "threshold_type": threshold_type,
            "threshold_value": threshold_value,
        }

        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)

        # You can adjust this depending on how your n8n webhook responds
        if response.status_code in (200, 201, 202):
            # Try to parse JSON message if available
            try:
                data = response.json()
                msg = data.get("message") or data.get("status") or "Alert configuration saved successfully!"
            except Exception:
                msg = "Alert configuration saved successfully!"
            return True, msg
        else:
            return False, f"Webhook error {response.status_code}: {response.text}"

    except Exception as e:
        return False, f"Request failed: {e}"


def render_alert_config():
    st.markdown("## 🔔 Configure Stock Price Alerts")
    st.markdown(
        "Set up automated alerts for stock price movements. "
        "You'll receive notifications via email when your conditions are met."
    )

    st.markdown("---")

    # Create form
    with st.form("alert_config_form", clear_on_submit=False):
        st.markdown("### Alert Configuration")

        col1, col2 = st.columns(2)

        with col1:
            email = st.text_input(
                "Email Address *",
                placeholder="your.email@example.com",
                help="Email address where you'll receive alerts",
            )

            ticker = st.text_input(
                "Stock Ticker *",
                placeholder="RELIANCE.NS or AAPL",
                help="Stock symbol to monitor (e.g., RELIANCE.NS for Indian stocks, AAPL for US stocks)",
            ).upper()

        with col2:
            threshold_type = st.selectbox(
                "Threshold Type *",
                ["Percentage Drop"],
                help="Choose how you want to define the alert threshold",
            )

            if threshold_type == "Percentage Drop":
                threshold_value = st.number_input(
                    "Threshold Value (%) *",
                    min_value=0.1,
                    max_value=100.0,
                    value=5.0,
                    step=0.1,
                    help="Alert when price drops by this percentage",
                )

        st.markdown("---")

        # Submit button
        submitted = st.form_submit_button("🚀 Configure Alert", use_container_width=True)

        if submitted:
            # Validation
            errors = []

            # Email validation
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not email:
                errors.append("Email address is required")
            elif not re.match(email_pattern, email):
                errors.append("Invalid email address format")

            # Ticker validation
            if not ticker:
                errors.append("Stock ticker is required")
            elif len(ticker) < 1:
                errors.append("Invalid ticker symbol")

            # Threshold validation
            if threshold_value <= 0:
                errors.append("Threshold value must be greater than 0")

            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Send to webhook
                with st.spinner("Configuring alert..."):
                    success, message = send_alert_config(
                        email=email,
                        ticker=ticker,
                        threshold_type=threshold_type,
                        threshold_value=threshold_value,
                    )

                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")

    # Info section
    st.markdown("---")
    st.info(
        """
    **How it works:**
    1. Enter your email address and the stock ticker you want to monitor  
    2. Choose your alert threshold (percentage drop or absolute price)  
    3. Click "Configure Alert" to activate monitoring  
    4. n8n receives this data via webhook and stores it in your database  

    **Note:** Make sure your n8n workflow with the POST webhook
    at `/webhook-test/alert` is running to receive and process alerts.
    """
    )
