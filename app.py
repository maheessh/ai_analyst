# app.py
import streamlit as st
import os
from dotenv import load_dotenv
import json
import pandas as pd
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Strategic Analyst",
    page_icon="",
    layout="wide"
)

# --- Custom CSS for a Professional Dark Theme with Animations ---
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    /* Headers and titles */
    h1, h2, h3 {
        color: #f0f6fc;
    }
    /* Buttons */
    .stButton>button {
        background-color: #238636;
        color: #FFFFFF;
        border-radius: 6px;
        border: 1px solid #30363d;
        padding: 10px 24px;
        font-weight: 600;
        transition: background-color 0.3s ease, transform 0.1s ease;
    }
    .stButton>button:hover {
        background-color: #2ea043;
    }
    .stButton>button:active {
        transform: scale(0.98);
    }
    /* Metrics and containers */
    .stMetric, .st-emotion-cache-0, .st-emotion-cache-p5msec {
        background-color: #161b22;
        border-radius: 6px;
        padding: 16px;
        border: 1px solid #30363d;
        transition: box-shadow 0.3s ease-in-out;
    }
    .stMetric:hover, .st-emotion-cache-0:hover, .st-emotion-cache-p5msec:hover {
        box-shadow: 0 0 15px rgba(35, 134, 54, 0.3);
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
		gap: 24px;
        border-bottom: 2px solid #30363d;
	}
	.stTabs [data-baseweb="tab"] {
		height: 50px;
        background-color: transparent;
        border-radius: 6px;
        border-bottom: none;
        color: #8b949e;
        padding: 0 16px;
	}
	.stTabs [aria-selected="true"] {
  		border-bottom: 2px solid #238636;
        color: #f0f6fc;
	}
</style>
""", unsafe_allow_html=True)


# --- Helper Function ---
def parse_financial_value(value_str):
    """Parses financial strings like '100B', '$20.5M', '15%' into numbers."""
    if isinstance(value_str, (int, float)):
        return value_str
    if not isinstance(value_str, str):
        return 0
    value_str = value_str.lower().replace('$', '').replace(',', '').replace('%', '')
    multiplier = 1
    if 'b' in value_str:
        multiplier = 1_000_000_000
        value_str = value_str.replace('b', '')
    elif 'm' in value_str:
        multiplier = 1_000_000
        value_str = value_str.replace('m', '')
    try:
        return float(value_str) * multiplier
    except (ValueError, TypeError):
        return 0

# --- Load environment variables and check for keys FIRST ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEC_API_KEY = os.getenv("SEC_API_KEY")

st.title("Strategic AI-nalyst")

# --- Main Application Logic ---
if not GOOGLE_API_KEY or not SEC_API_KEY:
    st.error("API Key Error: Please make sure your .env file is in the project's root directory and contains your GOOGLE_API_KEY and SEC_API_KEY.")
else:
    from financial_analyzer import (
        get_10k_report_text, conduct_financial_analysis, 
        conduct_swot_analysis, conduct_risk_simulation
    )

    # Initialize session state to hold data
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = {}

    # --- Sidebar for User Input ---
    with st.sidebar:
        st.header("Analysis Controls")
        primary_ticker = st.text_input("Enter Primary Company Ticker", "MSFT")
        
        if st.button("Run Full Analysis"):
            st.session_state.analysis_data = {} # Reset data
            with st.spinner(f"Fetching 10-K report for {primary_ticker.upper()}..."):
                filing_url, full_text_url = get_10k_report_text(primary_ticker)
                if "Could not fetch" in filing_url:
                    st.error(filing_url)
                else:
                    st.session_state.analysis_data['filing_url'] = filing_url
                    st.session_state.analysis_data['company_name'] = primary_ticker
                    st.success(f"Report found for {primary_ticker.upper()}!")

    # --- Main Dashboard Display ---
    if 'filing_url' in st.session_state.analysis_data:
        company = st.session_state.analysis_data['company_name']
        url = st.session_state.analysis_data['filing_url']

        st.header(f"Strategic Dashboard for {company.upper()}")
        st.markdown(f"[Link to 10-K Filing]({url})")

        tab1, tab2, tab3 = st.tabs(["Financial Snapshot", "SWOT Analysis", "Risk Simulation"])

        with tab1:
            if 'financials' not in st.session_state.analysis_data:
                with st.spinner("Analyzing financial data..."):
                    json_str = conduct_financial_analysis(url, is_url=True)
                    try:
                        st.session_state.analysis_data['financials'] = json.loads(json_str.strip().replace("```json", "").replace("```", ""))
                    except json.JSONDecodeError:
                        st.error("Could not decode financial analysis from AI.")
                        st.code(json_str)
            
            if 'financials' in st.session_state.analysis_data:
                data = st.session_state.analysis_data['financials']
                c1, c2, c3 = st.columns(3)
                c1.metric("Revenue", data.get('revenue_analysis', {}).get('current_year_revenue', 'N/A'), delta=data.get('revenue_analysis', {}).get('growth_rate', ''))
                c2.metric("Net Income", data.get('profitability', {}).get('net_income', 'N/A'))
                c3.metric("Net Margin", data.get('profitability', {}).get('net_margin', 'N/A'))

                st.markdown("---") 

                chart1, chart2 = st.columns(2)

                with chart1:
                    st.subheader("2-Year Performance")
                    rev_data = data.get('revenue_analysis', {})
                    profit_data = data.get('profitability', {})
                    
                    if 'previous_year_revenue' in rev_data:
                        perf_data = {
                            'Metric': ['Revenue', 'Net Income'],
                            'Current Year': [parse_financial_value(rev_data.get('current_year_revenue')), parse_financial_value(profit_data.get('net_income'))],
                            'Previous Year': [parse_financial_value(rev_data.get('previous_year_revenue')), parse_financial_value(profit_data.get('previous_year_net_income', '0'))]
                        }
                        perf_df = pd.DataFrame(perf_data)
                        
                        fig = go.Figure()
                        fig.add_trace(go.Bar(x=perf_df['Metric'], y=perf_df['Previous Year'], name='Previous Year', marker_color='#484f58'))
                        fig.add_trace(go.Bar(x=perf_df['Metric'], y=perf_df['Current Year'], name='Current Year', marker_color='#238636'))
                        fig.update_layout(barmode='group', template='plotly_dark', paper_bgcolor='#161b22', plot_bgcolor='#161b22', yaxis_title='Amount (in USD)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Not enough historical data from the report for a 2-year comparison chart.")

                with chart2:
                    st.subheader("Cost Structure")
                    cost_data = data.get('cost_structure', {})
                    if cost_data:
                        cost_df = pd.DataFrame(list(cost_data.items()), columns=['Component', 'Percentage'])
                        cost_df['Value'] = cost_df['Percentage'].apply(parse_financial_value)

                        fig = go.Figure(data=[go.Pie(labels=cost_df['Component'], values=cost_df['Value'], hole=.4, marker_colors=['#238636', '#2ea043', '#3fb950'])])
                        fig.update_layout(template='plotly_dark', paper_bgcolor='#161b22', plot_bgcolor='#161b22', showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Cost structure data not available in the report.")

        with tab2:
            if 'swot' not in st.session_state.analysis_data:
                 with st.spinner("Generating SWOT Analysis..."):
                    json_str = conduct_swot_analysis(url, company, is_url=True)
                    try:
                        st.session_state.analysis_data['swot'] = json.loads(json_str.strip().replace("```json", "").replace("```", ""))
                    except json.JSONDecodeError:
                        st.error("Could not decode SWOT analysis from AI.")
                        st.code(json_str)

            if 'swot' in st.session_state.analysis_data:
                swot = st.session_state.analysis_data['swot']
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Strengths")
                    for item in swot.get('strengths', []): st.markdown(f"- {item}")
                    st.subheader("Weaknesses")
                    for item in swot.get('weaknesses', []): st.markdown(f"- {item}")
                with c2:
                    st.subheader("Opportunities")
                    for item in swot.get('opportunities', []): st.markdown(f"- {item}")
                    st.subheader("Threats")
                    for item in swot.get('threats', []): st.markdown(f"- {item}")

        with tab3:
            st.subheader("Simulate a Future Market Shock")
            market_shock = st.text_input("Describe a hypothetical event (e.g., 'A new AI breakthrough makes our primary product obsolete')", key="shock_input")
            
            if st.button("Simulate Impact"):
                with st.spinner("Running risk simulation..."):
                    json_str = conduct_risk_simulation(url, company, market_shock, is_url=True)
                    try:
                         st.session_state.analysis_data['simulation'] = json.loads(json_str.strip().replace("```json", "").replace("```", ""))
                    except json.JSONDecodeError:
                        st.error("Could not decode simulation from AI.")
                        st.code(json_str)
            
            if 'simulation' in st.session_state.analysis_data:
                sim = st.session_state.analysis_data['simulation']
                st.info(f"Identified Risk: {sim.get('relevant_risk', 'N/A')}")
                
                with st.expander("Best Case Scenario", expanded=True):
                    bc = sim.get('best_case', {})
                    st.markdown(f"**Outcome:** {bc.get('scenario')}")
                    st.markdown(f"**Impact:** {bc.get('impact')}")
                    st.markdown(f"**Mitigation:** {bc.get('mitigation')}")
                
                with st.expander("Likely Case Scenario", expanded=True):
                    lc = sim.get('likely_case', {})
                    st.markdown(f"**Outcome:** {lc.get('scenario')}")
                    st.markdown(f"**Impact:** {lc.get('impact')}")
                    st.markdown(f"**Mitigation:** {lc.get('mitigation')}")
                
                with st.expander("Worst Case Scenario", expanded=True):
                    wc = sim.get('worst_case', {})
                    st.markdown(f"**Outcome:** {wc.get('scenario')}")
                    st.markdown(f"**Impact:** {wc.get('impact')}")
                    st.markdown(f"**Mitigation:** {wc.get('mitigation')}")
