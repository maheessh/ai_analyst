# financial_analyzer.py
import google.generativeai as genai
import os
import fitz # PyMuPDF
from sec_api import QueryApi
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
query_api = QueryApi(api_key=os.getenv("SEC_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_10k_report_text(ticker):
    """Fetches the latest 10-K report filing URL from SEC EDGAR."""
    query = {
        "query": { "query_string": {
            "query": f"ticker:{ticker} AND formType:\"10-K\""
        }},
        "from": "0",
        "size": "1",
        "sort": [{ "filedAt": { "order": "desc" }}]
    }
    try:
        filings = query_api.get_filings(query)
        if not filings['filings']:
            return "No 10-K filings found for this ticker.", None
        filing_url = filings['filings'][0]['linkToFilingDetails']
        # Also return the raw text for deeper analysis if needed
        full_text = filings['filings'][0]['documentFormatFiles'][0]['documentUrl']
        return filing_url, full_text # We return both now
    except Exception as e:
        print(f"Error fetching SEC data: {e}")
        return f"Could not fetch data from SEC EDGAR. Error: {e}", None

def conduct_financial_analysis(document_content, is_url=False):
    """Uses Gemini to analyze key financial data from a report."""
    input_prompt = f"From the 10-K report at the URL: {document_content}" if is_url else f"From the following 10-K report text: {document_content[:30000]}"
    prompt = f"""
    {input_prompt}
    Perform a financial analysis. Extract key data points in a structured JSON format.
    1.  **Revenue Analysis**: Identify total revenue for the last two fiscal years and calculate the year-over-year growth rate.
    2.  **Profitability**: Find the Gross Profit and Net Income for the last two years. Calculate the gross margin and net profit margin for the most recent year.
    3.  **Cost Structure**: Detail R&D, and SG&A as a percentage of total revenue for the most recent year.
    Provide the output ONLY in valid JSON format. Example:
    {{
      "revenue_analysis": {{ "current_year_revenue": "100B", "previous_year_revenue": "90B", "growth_rate": "11.1%" }},
      "profitability": {{ "net_income": "20B", "net_margin": "20%" }},
      "cost_structure": {{ "R&D": "15%", "SG&A": "25%" }}
    }}
    """
    response = model.generate_content(prompt)
    return response.text

def conduct_swot_analysis(document_content, company_name, is_url=False):
    """Generates a SWOT analysis from a 10-K report."""
    input_prompt = f"From the 10-K report for {company_name} at the URL: {document_content}" if is_url else f"From the following 10-K report text for {company_name}: {document_content[:30000]}"
    prompt = f"""
    {input_prompt}
    Analyze the 'Business Overview', 'Competition', and 'Risk Factors' sections to create a SWOT analysis.
    For each category (Strengths, Weaknesses, Opportunities, Threats), provide 3 concise bullet points.
    
    Provide the output ONLY in valid JSON format. Example:
    {{
      "strengths": ["Strong brand recognition", "Diverse product portfolio", "Large user base"],
      "weaknesses": ["High dependence on a single product", "Recent data privacy concerns", "Slower growth in emerging markets"],
      "opportunities": ["Expansion into AI and cloud services", "Strategic acquisitions of startups", "Growing demand for digital entertainment"],
      "threats": ["Intense competition from tech giants", "Evolving regulatory landscape", "Global economic downturn impacting consumer spending"]
    }}
    """
    response = model.generate_content(prompt)
    return response.text

def conduct_risk_simulation(document_content, company_name, market_shock, is_url=False):
    """Simulates the impact of a market shock based on stated risks."""
    input_prompt = f"From the 10-K report for {company_name} at the URL: {document_content}" if is_url else f"From the following 10-K report text for {company_name}: {document_content[:30000]}"
    prompt = f"""
    You are a strategic advisor to a CFO.
    CONTEXT:
    - **Company's 10-K Report**: {input_prompt}
    - **Hypothetical Market Shock**: "{market_shock}"

    TASK:
    Analyze the 'Risk Factors' section of the report. Identify the most relevant stated risk. Then, generate three potential impact scenarios (Best Case, Likely Case, Worst Case) from this market shock.
    For each scenario, provide:
    1. A brief description of the outcome.
    2. An estimated quantitative impact on revenue or margins.
    3. One strategic action to mitigate the damage or capitalize on the situation.

    Provide the output ONLY in valid JSON format. Example:
    {{
      "relevant_risk": "Dependence on international supply chains.",
      "best_case": {{
        "scenario": "Minor supply chain disruptions are quickly rerouted with minimal delay.",
        "impact": "-1% impact on gross margin for one quarter.",
        "mitigation": "Activate secondary supplier agreements and increase short-term inventory."
      }},
      "likely_case": {{
        "scenario": "Significant delays and increased logistics costs for two quarters.",
        "impact": "-5% revenue and -3% gross margin for the next six months.",
        "mitigation": "Absorb costs and communicate transparently with customers about delays. Expedite diversification of supplier base."
      }},
      "worst_case": {{
        "scenario": "A key supplier halts production, causing major product shortages.",
        "impact": "-15% revenue for the fiscal year.",
        "mitigation": "Immediately seek alternative sourcing and consider a temporary price increase on existing inventory to manage demand."
      }}
    }}
    """
    response = model.generate_content(prompt)
    return response.text

