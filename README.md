# FinAnalyst – AI‑Powered Financial Research Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)

FinAnalyst is a full‑stack proof‑of‑concept for an AI‑assisted financial research workspace. It combines real‑time market data, interactive dashboards, automated alerts, and an intelligent research chatbot to help beginner investors and junior analysts understand markets faster and with less manual work.

---

## 🔍 Key Capabilities

- **Market overview dashboard**  
  Global indices, intraday sentiment (bullish/bearish), SPY trend, and a personalized watchlist for quick daily checks.

- **Stock analysis & comparison**  
  Single‑stock deep dives plus multi‑stock comparison with 1‑year relative performance charts and side‑by‑side fundamentals (P/E, ROE, margins, dividend yield, recommendations).

- **NAV / price‑drop alerting workflow**  
  LangGraph workflow that monitors price moves against user‑defined thresholds, classifies severity (LOW / MEDIUM / HIGH), and hands off to n8n for email / chat alerts.

- **LLM‑powered research assistant**  
  Natural‑language interface (Groq / OpenAI) that can answer questions like  
  "Compare TCS and Infosys on 1‑year performance and valuation" or  
  "What's today's market sentiment and top losers in my watchlist?".

- **Beginner‑friendly design**  
  Built for new investors and junior analysts: simple UI, opinionable defaults, and clear visuals instead of complex trading terminals.

---

## 🏗️ Architecture Overview

### Frontend

- Streamlit single‑page app (`ui/streamlit_app.py`)
- Dark / light theme, sidebar navigation:
  - Dashboard
  - Stock Analysis
  - Charts (relative performance & fundamentals)
  - Alert Config

### Backend

- FastAPI service (`backend/`) exposing JSON REST APIs:
  - `POST /get_price` – price, returns, technical snapshot
  - `POST /get_news` – latest news for a ticker
  - `GET  /get_market_summary` – global indices snapshot
  - `POST /compare_stocks` – async multi‑ticker comparison
  - `POST /run_NAV_Alert_Trigger` – LangGraph alert workflow
  - `POST /chatbot_query` – LLM‑driven research Q&A entrypoint

### AI & Workflows

- **LangGraph** state machine for multi‑step logic (fetch → analyze → alert)
- **Groq / OpenAI** LLMs for intent detection, query understanding, and answer generation
- **n8n** workflow for external notifications (email / Slack etc.)

### Data Layer

- `yfinance` for real‑time and historical OHLCV data, fundamentals, and analyst recommendations
- Encapsulated helper utilities so providers can be swapped later without changing API contracts

---

## 📂 Project Structure

```
financial-analyst-poc-/
├── backend/
│   ├── app.py                 # FastAPI app & CORS
│   ├── routers/
│   │   └── finance.py         # All REST endpoints
│   ├── utils/
│   │   └── yf_utils.py        # yfinance data layer (prices, fundamentals, history)
│   ├── NAV_Alert_Trigger.py   # LangGraph NAV / price-drop workflow
│   └── chatbot_logic.py       # LLM intent routing & responses
├── ui/
│   ├── streamlit_app.py       # Main FinAnalyst UI
│   ├── components/            # Reusable UI components
│   └── pages/                 # Additional views (if any)
├── n8n/                       # Alert workflows (email / Slack etc.)
├── config/                    # Settings, constants, ticker maps
├── agent/                     # Experimental agents / research code
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## ⚙️ Setup & Installation

### 1. Clone the repo

```bash
git clone https://github.com/amogh-aziro-18/financial-analyst-poc-.git
cd financial-analyst-poc-
```

### 2. Create & activate virtual environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_key_here
```

`.env` is ignored by Git so that secrets never leak.

---

## 🚀 Running the POC Locally

### 1. Start the backend (FastAPI)

```bash
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

- Swagger / OpenAPI docs: `http://127.0.0.1:8000/docs`

### 2. Start the frontend (Streamlit)

Open a second terminal:

```bash
cd financial-analyst-poc-
.\venv\Scripts\activate   # or source venv/bin/activate

streamlit run ui/streamlit_app.py
```

- UI: `http://localhost:8501`

---

## 🧭 How to Use

### 1. Dashboard

- View overall **market mood** (bullish / bearish) based on major indices
- See intraday moves for S&P 500, NASDAQ, Dow Jones, NIFTY 50 etc.
- Inspect SPY candlestick chart and your watchlist to see which names are moving

Use this as your **morning snapshot**: "What kind of market are we in today?"

---

### 2. Stock Analysis

- Enter a single ticker to get:
  - Current price, absolute and percentage move
  - Volume vs average, 52‑week high/low and distance from each
  - Recent daily history and returns
- Good for quick pre‑trade research on one company

---

### 3. Charts – Multi‑Stock Comparison

- Enter up to **5 tickers** (e.g., `AAPL, MSFT, GOOGL, NVDA, TCS.NS`)
- The **Relative Performance (1 Year)** chart normalizes all to 0% and shows how each stock has performed over the last year
- Below, a **Fundamental Comparison** table shows:
  - Market cap, P/E ratio, profit margin, ROE
  - Dividend yield and analyst recommendation (buy / strong_buy, etc.)

This answers: **"If I invested in X vs Y a year ago, who won, and whose fundamentals look stronger today?"**

---

### 4. Alerts – NAV / Price Drop Trigger

- Choose a ticker and set a drop threshold (e.g., "Alert me if TCS drops more than 1% vs previous close")
- LangGraph workflow:
  1. Fetches current & previous close via `yfinance`
  2. Computes percentage drop
  3. Compares with user threshold
  4. Classifies severity (LOW / MEDIUM / HIGH)
  5. Returns a structured alert payload and optionally triggers n8n via webhook

This offloads simple risk monitoring so users do not need to stare at charts all day.

---

### 5. Chatbot (Optional / If Enabled)

- Ask questions like:
  - "Compare TCS and INFY on 1‑year performance and valuation."
  - "What's today's market sentiment and which watchlist stocks are down more than 2%?"
- The LLM:
  1. Parses intent and tickers
  2. Calls appropriate backend APIs
  3. Returns a concise, human‑readable answer

---

## 🧠 Design & Implementation Notes

- **Encapsulated data access**  
  All interactions with yfinance live in `yf_utils.py` and return a uniform structure `{success, data, error}` so endpoints and LangGraph nodes stay simple and robust.

- **LangGraph for workflows**  
  NAV/price‑drop alert is modelled as a state graph with pure nodes: `fetch → analyze → alert`. This makes business logic testable, observable, and easy to extend with new steps (e.g., logging, portfolio aggregation).

- **Async backend**  
  Comparison endpoints fetch multiple tickers in parallel using `asyncio`, significantly reducing latency when analysing a basket of symbols.

- **Beginner‑first UX**  
  Streamlit UI focuses on clean charts, simple text, and one‑click actions so that even users new to markets can benefit.

---

## 🧪 Possible Extensions

Ideas if you want to take this beyond a POC:

- News & social‑media sentiment for tracked tickers
- Portfolio tracking and "what‑if" backtesting
- Role‑based dashboards for investor / risk / research personas
- Cloud deployment (Render / Azure / AWS) with CI/CD and monitoring
- Multi‑tenant support for multiple users and teams

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI |
| AI Framework | LangGraph |
| LLM Provider | Groq, OpenAI |
| Market Data | yfinance |
| Automation | n8n |
| Vector DB | Pinecone (optional) |
| Language | Python 3.10+ |

---

## 📸 Screenshots

### Dashboard
![Dashboard](https://img.sanishtech.com/u/0c61f3c563722aea81ce596c9b0e967d.png)

### Charts & Comparison
![Charts](https://img.sanishtech.com/u/110d1b5dd7b16ad9ecedd6eed74166fd.png)

### Alert Configuration
![Alerts](https://img.sanishtech.com/u/fe63c8fe0bbb0b76a7942f42d6215e44.png)



---

## 👥 Contributors

- **Vadde Vignesh** - Complete Backend Development, API Design, LangGraph Workflows
- **Swathikiran K K** - Frontend Development, UI/UX, N8N Alert Configuration, Dashboard, Charts Module
- **Amogh D R** - Agent Development , Chatbot desgin And Ui/Ux , Reasoning Model 

---

## ⚠️ Disclaimer

This project is for **educational and demonstration purposes only**.  
It does **not** constitute financial advice and should not be relied upon for real investment decisions.  
Market data may be delayed or inaccurate depending on upstream providers.

---

## 📄 License

This project is released under the **MIT License**.  
See the [`LICENSE`](LICENSE) file for full details.

---

## 🙏 Acknowledgments

- [yfinance](https://github.com/ranaroussi/yfinance) for market data access
- [LangGraph](https://github.com/langchain-ai/langgraph) for workflow orchestration
- [Streamlit](https://streamlit.io/) for rapid UI prototyping
- [FastAPI](https://fastapi.tiangolo.com/) for high-performance API framework

---

## 📞 Contact

For questions or collaboration:
- GitHub: [@amogh-aziro-18](https://github.com/amogh-aziro-18)
- Project Link: [https://github.com/amogh-aziro-18/financial-analyst-poc-](https://github.com/amogh-aziro-18/financial-analyst-poc-)

---

**⭐ Star this repo if you find it useful!**
