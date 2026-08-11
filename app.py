import os
import json
import pandas as pd
import pypdf
import streamlit as st
import datetime
import extra_streamlit_components as stx
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# ------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CYBERPUNK THEME (CSS)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="B.L.E.E.D. PROTOCOL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Dark theme background overrides */
    .stApp {
        background-color: #0B0F19;
        color: #E0E6ED;
    }
    
    /* Mission Briefing Header Box */
    .mission-box {
        background-color: #111827;
        border: 2px solid #00F2FE;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.3);
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 25px;
    }
    
    .mission-title {
        color: #00F2FE;
        font-family: 'Courier New', Courier, monospace;
        font-size: 24px;
        font-weight: bold;
        letter-spacing: 2px;
        margin-bottom: 10px;
        text-transform: uppercase;
    }
    
    .mission-prologue {
        color: #A0AEC0;
        font-family: 'Courier New', Courier, monospace;
        font-size: 14px;
        line-height: 1.6;
    }

    /* Red Glowing Financial Card */
    .leakage-card {
        background-color: #1A0505;
        border: 2px solid #FF0055;
        box-shadow: 0 0 20px rgba(255, 0, 85, 0.4);
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .leakage-title {
        color: #FF4D4D;
        font-family: 'Courier New', Courier, monospace;
        font-size: 14px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    
    .leakage-value {
        color: #FF0055;
        font-family: 'Courier New', Courier, monospace;
        font-size: 42px;
        font-weight: bold;
        text-shadow: 0 0 10px rgba(255, 0, 85, 0.6);
    }
    
    /* Holo Earth Branding */
    .holo-earth-brand {
        text-align: center;
        font-family: 'Courier New', Courier, monospace;
        color: #00F2FE;
        font-size: 12px;
        letter-spacing: 3px;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid rgba(0, 242, 254, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------------
# 2. STRUCTURED OUTPUT SCHEMA (Pydantic)
# ------------------------------------------------------------------------------
class BreachItem(BaseModel):
    clause_ref: str = Field(description="Reference ID or title of the violated clause.")
    incident_date: str = Field(description="Date or log marker of the breach event.")
    breach_details: str = Field(description="Summary of how the SLA was breached.")
    penalty_recovered: float = Field(description="Calculated financial credit or penalty owed.")

class AuditReport(BaseModel):
    total_leakage: float = Field(description="Total sum of financial penalties identified.")
    currency: str = Field(description="Currency code, e.g., USD.")
    violations_found: list[BreachItem] = Field(description="List of distinct SLA breaches identified.")
    briefing_summary: str = Field(description="Executive summary of forensic findings.")

# ------------------------------------------------------------------------------
# 3. HELPER FUNCTIONS: FILE EXTRACTION
# ------------------------------------------------------------------------------
def extract_text_from_pdf(uploaded_file) -> str:
    """Reads a Streamlit uploaded PDF file and extracts text from all pages."""
    try:
        reader = pypdf.PdfReader(uploaded_file)
        text_content = []
        for page in reader.pages:
            text_content.append(page.extract_text())
        return "\n".join(text_content)
    except Exception as e:
        return f"[PDF EXTRACTION ERROR: {str(e)}]"

def extract_text_from_csv(uploaded_file) -> str:
    """Reads a Streamlit uploaded CSV file and converts the dataframe to string."""
    try:
        df = pd.read_csv(uploaded_file)
        return df.to_string(index=False)
    except Exception as e:
        return f"[CSV EXTRACTION ERROR: {str(e)}]"

# ------------------------------------------------------------------------------
# 4. SIDEBAR: COMMAND CIPHER TERMINAL (UPGRADED LOCAL STORAGE)
# ------------------------------------------------------------------------------
# Initialize the local browser storage manager
cookie_manager = stx.CookieManager(key="bleed_cookie_manager")

with st.sidebar:
    st.title("⚡ COMMAND CIPHER")
    
    # 1. Fetch the key from the user's local browser cookie (if it exists)
    saved_key = cookie_manager.get("bleed_api_key")
    if saved_key is None:
        saved_key = ""
    
    user_api_key = st.text_input(
        "GEMINI API KEY",
        value=saved_key,
        type="password",
        help="Your key is processed securely and never saved to our servers.",
    )
    
    # 2. Local Storage Checkbox
    remember_me = st.checkbox("Save Key Locally (30 Days)", value=bool(saved_key))
    
    # 3. Execution Logic: Write or Delete the cookie based on user action
    if remember_me and user_api_key and user_api_key != saved_key:
        cookie_manager.set(
            "bleed_api_key", 
            user_api_key, 
            expires_at=datetime.datetime.now() + datetime.timedelta(days=30)
        )
    elif not remember_me and saved_key:
        cookie_manager.delete("bleed_api_key")
    
    st.info(
        "**OPERATIONAL DIRECTIVE:**\n"
        "Upload master contracts (PDF) and system logs (CSV). "
        "The forensic engine will automatically extract text, run compliance analysis, and calculate capital leakage."
    )
    
    st.markdown("---")
    
    st.markdown(
        """
        <div class="holo-earth-brand">
            MADE BY <strong>HOLO EARTH</strong>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
# ------------------------------------------------------------------------------
# 5. MAIN WORKSPACE: FILE UPLOADERS & MISSION BRIEFING
# ------------------------------------------------------------------------------
st.markdown(
    """
    <div class="mission-box">
        <div class="mission-title">CRITICAL ALERT: OPERATIONAL OVERWATCH ACTIVE</div>
        <div class="mission-prologue">
            YEAR 2026. THE CORPORATE SYSTEM IS BLEEDING CAPITAL.<br>
            UNTRACKED SERVICE LEVEL AGREEMENTS ARE DRAINING CASH TO VENDORS IN THE SHADOWS.<br>
            B.L.E.E.D. PROTOCOL STANDS READY. COMBAT UNENFORCED COMPLIANCE LOSS NOW.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

# File Upload Widgets
with col1:
    sla_file = st.file_uploader("UPLOAD MASTER CONTRACT (.PDF)", type=["pdf"])
    sla_text = ""
    if sla_file is not None:
        sla_text = extract_text_from_pdf(sla_file)
        with st.expander("PREVIEW EXTRACTED CONTRACT TEXT"):
            st.text(sla_text[:1000] + "\n\n...[TRUNCATED FOR PREVIEW]...")

with col2:
    log_file = st.file_uploader("UPLOAD SYSTEM LOGS (.CSV)", type=["csv"])
    log_text = ""
    if log_file is not None:
        log_text = extract_text_from_csv(log_file)
        with st.expander("PREVIEW EXTRACTED LOG DATA"):
            st.text(log_text[:1000] + "\n\n...[TRUNCATED FOR PREVIEW]...")

execute_audit = st.button("EXECUTE FORENSIC REVENUE AUDIT", use_container_width=True)

# ------------------------------------------------------------------------------
# 6. EXECUTION & GEMINI API PROCESSING
# ------------------------------------------------------------------------------
if execute_audit:
    if not user_api_key:
        st.error("ACCESS DENIED: Missing Gemini API Key. Provide a valid key in the sidebar.")
    elif not sla_text or not log_text:
        st.warning("INPUT ERROR: You must upload BOTH a PDF contract and CSV log file to run the audit.")
    else:
        with st.spinner("ANALYZING EXTRACTED DOCUMENTS USING GEMINI 3.5 FLASH-LITE..."):
            try:
                # Initialize Google GenAI Client
                client = genai.Client(api_key=user_api_key)
                
                system_instruction = (
                    "You are an aggressive Corporate Forensic Auditor searching for missed vendor penalty monies. "
                    "Analyze the provided contract SLA clauses against the system logs. "
                    "Identify every breach, calculate the associated penalty, and return the structured report."
                )
                
                user_prompt = f"""
                CONTRACT CLAUSES:
                {sla_text}
                
                SYSTEM LOGS:
                {log_text}
                """
                
                # Execute API Call using Gemini 3.5 Flash-Lite
                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=AuditReport,
                    ),
                )
                
                # Parse structured JSON output
                audit_data = json.loads(response.text)
                
                # Display Results
                st.markdown("### AUDIT FORENSIC FINDINGS")
                
                # Metric display
                leakage_amount = audit_data.get("total_leakage", 0.0)
                currency_code = audit_data.get("currency", "USD")
                
                st.markdown(
                    f"""
                    <div class="leakage-card">
                        <div class="leakage-title">Total Capital Recoverable</div>
                        <div class="leakage-value">{currency_code} ${leakage_amount:,.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
                # Summary Callout
                st.info(f"**BRIEFING SUMMARY:** {audit_data.get('briefing_summary', 'N/A')}")
                
                # Dataframe Display for Breaches
                violations = audit_data.get("violations_found", [])
                if violations:
                    st.subheader("Identified SLA Breaches")
                    st.dataframe(violations, use_container_width=True)
                else:
                    st.success("No SLA breaches or capital leakage identified from the provided documents.")

            except json.JSONDecodeError:
                st.error("FAILED TO PARSE RESPONSE: Model did not return valid JSON structure.")
            except Exception as e:
                st.error(f"SYSTEM FAILURE: {str(e)}")
      
