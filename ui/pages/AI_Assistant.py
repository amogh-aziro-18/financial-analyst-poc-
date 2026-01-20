import os
import sys
from datetime import datetime

import speech_recognition as sr
from gtts import gTTS
import streamlit as st
import re

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from agent.financial_agent import FinancialAgent

# -------------------------------------------------------------------
#  IMPORT BACKEND (add project root so 'agent' package is visible)
# -------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from agent.financial_agent import FinancialAgent  # noqa: E402

# -------------------------------------------------------------------
#  PAGE CONFIG
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Financial Research Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------
#  SESSION STATE INIT
# -------------------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of dicts: {role, message, time}

if "theme" not in st.session_state:
    st.session_state.theme = "dark"  # or "light"

if "selected_msg_idx" not in st.session_state:
    st.session_state.selected_msg_idx = None

if "last_clicked_suggest" not in st.session_state:
    st.session_state.last_clicked_suggest = None


# remembers the last meaningful finance query,
# so that "yes / ok" can still use context
if "last_finance_query" not in st.session_state:
    st.session_state.last_finance_query = None

if "agent" not in st.session_state:
    st.session_state.agent = FinancialAgent()

# -------------------------------------------------------------------
#  THEME CSS
# -------------------------------------------------------------------
def get_theme_css(theme: str) -> str:
    if theme == "light":
        bg = "#f5f5f5"
        text = "#111827"
        user_bg = "#DCF2FF"
        bot_bg = "#ffffff"
        accent = "#16a34a"  # green
        border = "#e5e7eb"
        sidebar_bg = "#ffffff"
        chat_time = "#6b7280"
    else:  # dark
        bg = "#020617"
        text = "#e5e7eb"
        user_bg = "#0f172a"
        bot_bg = "#020617"
        accent = "#22c55e"
        border = "#1f2933"
        sidebar_bg = "#020617"
        chat_time = "#9ca3af"

        return f"""
    <style>
    body {{
        background-color: {bg};
        color: {text};
    }}

    /* Main app background */
    .stApp {{
        background: {bg};
        color: {text};
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: {sidebar_bg};
        border-right: 1px solid {border};
    }}

    /* Headings */
    h1, h2, h3, h4, h5, h6, label, p, span {{
        color: {text};
    }}

    /* Chat area scroll box */
    .chat-scroll {{
        max-height: calc(100vh - 180px);
        overflow-y: auto;
        padding-right: 8px;
        padding-bottom: 120px !important;
    }}

    /* Each chat row container */
    .chat-row {{
        display: flex;
        margin-bottom: 0.6rem;
        width: 100%;
    }}
    .chat-row.user {{
        justify-content: flex-end;
    }}
    .chat-row.bot {{
        justify-content: flex-start;
    }}

    /* Chat bubble */
    .chat-bubble {{
        padding: 10px 14px;
        border-radius: 16px;
        max-width: 72%;
        border: 1px solid {border};
        font-size: 0.95rem;
        line-height: 1.4;
        word-wrap: break-word;
        word-break: break-word;
    }}
    .chat-bubble.user {{
        background: #1e3a8a22;  /* Subtle blue tint */
        color: {text};
    }}
    .chat-bubble.bot {{
        background: #0f172a55;  /* Subtle grey tint */
        color: {text};
    }}

    /* Timestamp */
    .chat-meta {{
        font-size: 0.7rem;
        color: {chat_time};
        margin-top: 2px;
    }}

    /* Highlighted message */
    .chat-bubble.highlight {{
        box-shadow: 0 0 0 2px {accent};
    }}

    /* Suggested queries */
    .suggest-btn button {{
        border-radius: 999px !important;
        font-size: 0.85rem !important;
        padding: 0.4rem 0.9rem !important;
    }}

    /* FIXED INPUT BAR LIKE CHATGPT */
    .input-area {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: {bg};
        padding: 0.7rem 1rem;
        border-top: 1px solid {border};
        z-index: 1000;
    }}

    /* Prevent chat from going under input */
    .block-container {{
        padding-bottom: 150px !important;
    }}

    /* Microphone and send buttons */
    .stButton>button {{
        border-radius: 999px;
        border: 1px solid {border};
    }}

    /* Toggle appearance */
    .theme-pill {{
        border-radius: 999px;
        padding: 4px 10px;
        border: 1px solid {border};
        font-size: 0.8rem;
    }}
    </style>
    """

st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# -------------------------------------------------------------------
#  HELPERS
# -------------------------------------------------------------------
def append_chat(role: str, message: str):
    st.session_state.chat_history.append(
        {
            "role": role,
            "message": message,
            "time": datetime.now().strftime("%H:%M"),
        }
    )


def is_confirmation(text: str) -> bool:
    confirmations = {"yes", "yep", "yeah", "ok", "okay", "sure", "fine", "go ahead"}
    return text.strip().lower() in confirmations


def format_bot_response_from_agent(agent_response: dict) -> str:
    """
    Take the structured dict from FinancialAgent and return a clean,
    user-friendly string (NO raw JSON).
    """
    r_type = agent_response.get("type")
    intent = agent_response.get("intent")
    data = agent_response.get("data")
    response_text = agent_response.get("response")
    summary = agent_response.get("summary")

    # Out-of-scope from the agent
    if intent == "out_of_scope":
        return (
            "💼 I’m a **Financial Markets Assistant** focused on stocks & markets.\n\n"
            "I can help you with things like:\n"
            "• Live stock prices (India & US)\n"
            "• Company financials (profitability, valuation)\n"
            "• Comparing stocks for long-term investing\n"
            "• Market updates (NIFTY, SENSEX, global indices)\n\n"
            "Please ask something related to stocks or financial markets. 🙂"
        )

    # LLM general response
    if r_type == "llm":
        return response_text or "I’ve processed your question."

    # Tool: PRICE
    if intent == "price" and isinstance(data, dict) and "current_price" in data:
        t = data.get("ticker", "N/A")
        cp = data.get("current_price")
        ch_pct = data.get("change_pct")
        ch_amt = data.get("change_amount")
        ccy = data.get("currency", "INR")

        arrow = "🔺" if (ch_amt or 0) > 0 else "🔻" if (ch_amt or 0) < 0 else "⏸️"
        return (
            f"**{t} – Live Price**\n\n"
            f"- Price: **{cp} {ccy}** {arrow}\n"
            f"- Change: **{ch_amt} {ccy} ({ch_pct}%)**\n"
        )

    # Tool: FINANCIALS (just summarise that we have them)
    if intent == "financials" and isinstance(data, dict):
        t = data.get("ticker", "N/A")
        currency = data.get("currency", "INR")
        return (
            f"**{t} – Financial Snapshot** ({currency})\n\n"
            "- I’ve fetched the latest income statement, balance sheet and cash flow.\n"
            "- In the full product, this will be shown as nice tables & charts.\n"
            "- For the demo, just mention this in your narration. ✅"
        )

    # Tool: COMPARE
    if intent == "compare" and isinstance(data, dict):
        comp = data.get("comparison", {})
        lines = ["**Stock Comparison – High-Level View**\n"]
        for tk, vals in comp.items():
            cp = vals.get("current_price")
            ccy = vals.get("currency", "INR")
            pe = vals.get("pe_ratio")
            pm = vals.get("profit_margin")
            roe = vals.get("roe")
            dy = vals.get("dividend_yield")
            rec = vals.get("recommendation", "N/A")
            lines.append(
                f"**{tk}**\n"
                f"- Price: {cp} {ccy}\n"
                f"- P/E: {pe}\n"
                f"- Profit Margin: {pm}\n"
                f"- ROE: {roe}\n"
                f"- Dividend Yield: {dy}\n"
                f"- Analyst View: {rec}\n"
            )
        if summary:
            lines.append("\n---\n")
            lines.append(summary)
        return "\n".join(lines)

    # Tool: NEWS
    if intent == "news" and isinstance(data, dict):
        arts = data.get("articles", [])
        tk = data.get("ticker", "")
        if not arts:
            return f"📰 No recent news found for **{tk}**."
        out = [f"📰 **Latest news for {tk}:**\n"]
        for a in arts:
            title = a.get("title", "")
            src = a.get("publisher", "")
            link = a.get("link", "")
            out.append(f"- **{title}**  \n  _{src}_  \n  {link}")
        return "\n".join(out)

    # Tool: MARKET SUMMARY
    if intent == "market_summary" and isinstance(data, dict):
        idx = data.get("indices", {})
        ts = data.get("timestamp", "")
        lines = [f"📊 **Market Summary** *(as of {ts})*\n"]
        for name, vals in idx.items():
            v = vals.get("value")
            ch = vals.get("change_pct")
            arrow = "🔺" if (ch or 0) > 0 else "🔻" if (ch or 0) < 0 else "⏸️"
            lines.append(f"- **{name}**: {v} ({ch}%) {arrow}")
        return "\n".join(lines)

    # Fallback: if some other structured data
    if isinstance(data, dict) and "error" in data:
        return f"⚠️ {data.get('error')}"

    # Last fallback
    return response_text or "I’ve processed your question."


def voice_input() -> str:
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... please speak clearly.")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
    except Exception as e:
        st.error(f"Mic error: {e}")
        return ""

    try:
        text = recognizer.recognize_google(audio)
        st.success(f"Recognized: **{text}**")
        return text
    except Exception:
        st.error("Sorry, I couldn't understand that audio. Please try again.")
        return ""


def voice_output(text: str):
    """
    Optional: If you want spoken answers, call this for the last bot reply.
    Currently not auto-used to avoid repeating audio on reruns.
    """
    try:
        tts = gTTS(text)
        file = "voice_output.mp3"
        tts.save(file)
        st.audio(file)
        os.remove(file)
    except Exception:
        pass


# -------------------------------------------------------------------
#  SIDEBAR – THEME TOGGLE + HISTORY
# -------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button(
            "🌑 Dark", key="theme_dark_btn",
            type="secondary" if st.session_state.theme == "dark" else "primary"
        ):
            st.session_state.theme = "dark"
            st.rerun()
    with col_t2:
        if st.button(
            "🌕 Light", key="theme_light_btn",
            type="secondary" if st.session_state.theme == "light" else "primary"
        ):
            st.session_state.theme = "light"
            st.rerun()

    st.markdown("---")
    st.markdown("### 🕒 Chat History")

    if not st.session_state.chat_history:
        st.caption("No messages yet. Start by asking about a stock price!")
    else:
        for idx, chat in enumerate(st.session_state.chat_history):
            if chat["role"] != "user":
                continue

            label = chat["message"]
            short = (label[:32] + "…") if len(label) > 32 else label
            if st.button(short, key=f"hist_{idx}"):
                st.session_state.selected_msg_idx = idx
                # just rerun – and main chat will highlight that message
                st.rerun()

# -------------------------------------------------------------------
#  MAIN LAYOUT
# -------------------------------------------------------------------
st.title("💬 Financial Research Assistant")
st.caption("Smart, Indian-market-focused stock assistant powered by **Groq + YFinance**.")

# Suggested queries row
st.markdown("#### ✨ Try asking:")
sugs = [
    "Price of INFY",
    "Is TCS a good stock?",
    "Compare INFY and TCS",
    "Give me market updates",
    "Best stock for long term in India",
    "INFY news",
]

s_cols = st.columns(3)
for i, s in enumerate(sugs):
    with s_cols[i % 3]:
        if st.button(s, key=f"suggest_{i}"):
            append_chat("user", s)

            agent_resp = st.session_state.agent.run(s)
            intent = agent_resp.get("intent")

            # track finance context only when actually finance
            if intent != "out_of_scope":
                st.session_state.last_finance_query = s
            else:
                st.session_state.last_finance_query = None

            bot_text = format_bot_response_from_agent(agent_resp)
            append_chat("bot", bot_text)

            st.session_state.selected_msg_idx = len(st.session_state.chat_history) - 1

            # FIX: Avoid infinite loop on out_of_scope
            if intent != "out_of_scope":
                st.rerun()


# -------------------------------------------------------------------
# -------------------------------------------------------------------
#  CHAT DISPLAY (SCROLLABLE)
# -------------------------------------------------------------------
st.markdown("#### 💭 Conversation")

chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)

    for idx, msg in enumerate(st.session_state.chat_history):
        role = msg["role"]
        bubble_classes = ["chat-bubble"]

        if role == "user":
            row_class = "chat-row user"
        else:
            row_class = "chat-row bot"

        if idx == st.session_state.selected_msg_idx:
            bubble_classes.append("highlight")

        bubble_class_str = " ".join(bubble_classes)

        # ✅ SAFE MESSAGE HANDLING
        if msg["role"] == "bot":
            safe_msg = msg["message"]
            safe_msg = safe_msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            safe_msg = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", safe_msg)
            safe_msg = re.sub(
                r"(https?://[^\s<]+)",
                r'<a href="\1" target="_blank">\1</a>',
                safe_msg,
            )
            safe_msg = safe_msg.replace("\n", "<br/>")
        else:
            safe_msg = msg["message"].replace("\n", "<br/>")

        # ✅ THIS MUST BE INSIDE THE LOOP
        st.markdown(
            f"""
            <div class="{row_class}">
                <div class="{bubble_class_str}">
                    <div>{safe_msg}</div>
                    <div class="chat-meta">{msg['time']} • {role.capitalize()}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------------------------------------------------
#  INPUT BAR (FIXED POSITION EFFECT)
# -------------------------------------------------------------------
st.markdown("")

st.markdown('<div class="input-area">', unsafe_allow_html=True)
input_cols = st.columns([8, 1, 1])

with input_cols[0]:
    user_query = st.text_input(
        "Ask about Indian or US stocks…",
        key="chat_text_input",
        label_visibility="collapsed",
        placeholder="e.g., Price of INFY, Compare TCS and INFY, NIFTY today…",
    )

with input_cols[1]:
    voice_clicked = st.button("🎤", help="Use voice input")

with input_cols[2]:
    send_clicked = st.button("➤", help="Send message")

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------
#  HANDLE INPUT (TEXT + VOICE) — FIXED
# -------------------------------------------------------------------
final_query = None

# Voice
if voice_clicked:
    spoken = voice_input()
    if spoken:
        final_query = spoken

# Typed input
if (user_query and send_clicked) or (user_query and not send_clicked and not voice_clicked):
    final_query = user_query

# One-shot rerun blocker
if "processing" not in st.session_state:
    st.session_state.processing = False

if final_query and not st.session_state.processing:

    st.session_state.processing = True  # 🔒 prevent auto loop
    effective_query = final_query

    # confirmations like "yes"
    if is_confirmation(final_query) and st.session_state.last_finance_query:
        effective_query = st.session_state.last_finance_query

    append_chat("user", final_query)

    agent_resp = st.session_state.agent.run(effective_query)
    intent = agent_resp.get("intent")

    if intent != "out_of_scope":
        st.session_state.last_finance_query = effective_query
    else:
        st.session_state.last_finance_query = None

    bot_text = format_bot_response_from_agent(agent_resp)
    append_chat("bot", bot_text)

    st.session_state.selected_msg_idx = len(st.session_state.chat_history) - 1

    if intent != "out_of_scope":
        st.rerun()
    else:
        st.session_state.processing = False  # allow next message
else:
    # Reset flag once cycle completed
    st.session_state.processing = False
