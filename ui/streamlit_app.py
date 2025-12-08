import streamlit as st
import os
import sys

# Add the project root to sys.path to allow absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set page config MUST be the first Streamlit command
st.set_page_config(
    page_title="Financial Analyst POC",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import components after page config
from ui.components.dashboard import render_dashboard
from ui.components.stock_page import render_stock_page
from ui.components.alert_config import render_alert_config
from ui.components.charts_page import render_charts_page

# Theme Configuration
DARK_THEME = {
    "--primary-color": "#00D4FF",
    "--secondary-color": "#FF007A",
    "--bg-color": "#0E1117",
    "--card-bg": "#1E212B",
    "--sidebar-bg": "#161920",
    "--text-color": "#FAFAFA",
    "--text-muted": "#9CA3AF",
    "--border-color": "#2B2F3B",
    "--input-bg": "#161920",
    "--font-family": "'Inter', sans-serif"
}

LIGHT_THEME = {
    "--primary-color": "#007AFF",
    "--secondary-color": "#FF2D55",
    "--bg-color": "#F5F7FA",
    "--card-bg": "#FFFFFF",
    "--sidebar-bg": "#FFFFFF",
    "--text-color": "#1A1A1A",
    "--text-muted": "#666666",
    "--border-color": "#D1D5DB",
    "--input-bg": "#FFFFFF",
    "--font-family": "'Inter', sans-serif"
}

# Load Custom CSS with Theme
def load_css(file_path, theme):
    with open(file_path) as f:
        css_content = f.read()
    
    # Generate :root variables
    root_vars = ":root {\n"
    for var, value in theme.items():
        root_vars += f"    {var}: {value};\n"
    root_vars += "}\n"
    
    st.markdown(f"<style>{root_vars}{css_content}</style>", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("🚀 FinAnalyst")

# Theme Toggle
is_light_mode = st.sidebar.toggle("☀️ Light Mode", value=False)
current_theme = LIGHT_THEME if is_light_mode else DARK_THEME
plotly_template = "plotly_white" if is_light_mode else "plotly_dark"

# Path to CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    load_css(css_path, current_theme)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Stock Analysis", "Charts", "Alert Config"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Financial Analyst POC**\n\n"
    "Powered by:\n"
    "- LangGraph\n"
    "- OpenAI/Groq\n"
    "- Streamlit"
)

# Main Content Routing
if page == "Dashboard":
    render_dashboard(plotly_template)
elif page == "Stock Analysis":
    render_stock_page(plotly_template)
elif page == "Charts":
    render_charts_page(plotly_template)
elif page == "Alert Config":
    render_alert_config()

