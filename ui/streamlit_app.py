import streamlit as st
import requests

st.set_page_config(page_title="Financial Analyst POC", layout="wide")
st.title("Financial Analyst Research Assistant")

st.sidebar.header("Navigation")
page = st.sidebar.selectbox("Go to", ["Home", "Chatbot", "Stock Dashboard"])

BACKEND_URL = "http://localhost:8000"

def call_get_price(ticker: str):
    return requests.get(f"{BACKEND_URL}/finance/get_price?ticker={ticker}").json()

def call_get_summary(ticker: str):
    return requests.get(f"{BACKEND_URL}/finance/get_summary?ticker={ticker}").json()

def call_chatbot_query(query: str):
    return requests.post(f"{BACKEND_URL}/finance/chatbot_query", json={"query": query}).json()

if page == "Home":
    st.write("Welcome to the Financial Analyst POC!")
elif page == "Chatbot":
    st.write("Chatbot interface goes here")
elif page == "Stock Dashboard":
    st.write("Stock charts and summaries will appear here")
