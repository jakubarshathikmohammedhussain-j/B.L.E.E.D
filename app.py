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
import streamlit as st

st.set_page_config(
    page_title="B.L.E.E.D. Protocol",
    page_icon="https://raw.githubusercontent.com/jakubarshathikmohammedhussain-j/B.L.E.E.D/main/mock_data/1786476130407.png",
    layout="centered",
    initial_sidebar_state="expanded"
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
    confidence_score: int = Field(description="Confidence percentage from 0 to 100 based on certainty of breach match.")
    
class AuditReport(BaseModel):
    total_leakage: float = Field(description="Total sum of financial penalties identified.")
    currency: str = Field(description="Currency code, e.g., USD.")
    violations_found: list[BreachItem] = Field(description="List of distinct SLA breaches identified.")
    briefing_summary: str = Field(description="Executive summary of forensic findings.")

# ------------------------------------------------------------------------------
# 3. HELPER FUNCTIONS: FILE EXTRACTION
# ------------------------------------------------------------------------------
def extract_text_from_pdfs(uploaded_files) -> str:
    """Reads multiple Streamlit uploaded PDF files, extracts, and merges text from all pages."""
    all_text = []
    for file in uploaded_files:
        try:
            reader = pypdf.PdfReader(file)
            text_content = []
            for page in reader.pages:
                text_content.append(page.extract_text())
            all_text.append(f"--- DOCUMENT: {file.name} ---\n" + "\n".join(text_content))
        except Exception as e:
            st.error(f"PDF EXTRACTION ERROR ({file.name}): {str(e)}")
    return "\n\n".join(all_text)


def extract_text_from_csvs(uploaded_files) -> str:
    """Parses multiple CSV files, merges them, and safely converts to a unified string."""
    dfs = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            st.error(f"Error parsing CSV '{file.name}': {e}")
    
    if dfs:
        # Merge all uploaded log files into a single DataFrame
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # We removed the strict Pandas datetime sorting to prevent crash errors.
        # Gemini 3.5 Flash is smart enough to read the timeline naturally!
        return combined_df.to_csv(index=False)
    return ""


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
        
    st.markdown("---")
    st.title("⚙️ ENGINE TUNING")
    
        # Interactive Prompt Editor Accordion
    DEFAULT_SYSTEM_INSTRUCTION = (
        "You are an aggressive Corporate Forensic Auditor searching for missed vendor penalty monies. "
        "Analyze the provided contract SLA clauses against the system logs.\n"
        "STRICT RULES:\n"
        "1. ONLY calculate financial penalties that are EXPLICITLY stated with exact dollar amounts or formulas in the clauses.\n"
        "2. DO NOT invent, assume, or fabricate penalty amounts for clauses that lack defined monetary terms.\n"
        "3. Assign a confidence_score (0-100) reflecting how definitively the log evidence proves the breach.\n"
        "4. Ensure all text in your briefing summary uses proper spacing and formatting."
    )
    
    with st.expander("🛠️ PROMPT EDITOR (AI System Instruction)"):
        system_instruction = st.text_area(
            "Tweak Auditing Instructions:",
            value=DEFAULT_SYSTEM_INSTRUCTION,
            height=200,
            help="Modify the system rules sent to Gemini to calibrate auditing strictness."
        )
        
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
    sla_files = st.file_uploader("UPLOAD MASTER CONTRACTS (.PDF)", type=["pdf"], accept_multiple_files=True)
    sla_text = ""
    if sla_files:
        sla_text = extract_text_from_pdfs(sla_files)
        with st.expander(f"PREVIEW EXTRACTED CONTRACT TEXT ({len(sla_files)} file(s) loaded)"):
            st.text(sla_text[:1000] + "\n\n...[TRUNCATED FOR PREVIEW]...")

with col2:
    log_files = st.file_uploader("UPLOAD SYSTEM LOGS (.CSV)", type=["csv"], accept_multiple_files=True)
    log_text = ""
    if log_files:
        log_text = extract_text_from_csvs(log_files)
        with st.expander(f"PREVIEW MERGED LOG DATA ({len(log_files)} file(s) loaded)"):
            st.text(log_text[:1000] + "\n\n...[TRUNCATED FOR PREVIEW]...")
            


execute_audit = st.button("EXECUTE FORENSIC REVENUE AUDIT", use_container_width=True)

# ------------------------------------------------------------------------------
# 6. EXECUTION & GEMINI API PROCESSING
# ------------------------------------------------------------------------------
if execute_audit:
    if not user_api_key:
        st.error("ACCESS DENIED: Missing Gemini API Key. Provide a valid key in the sidebar.")
    elif not sla_files or not log_files:
        st.warning("INPUT ERROR: You must upload BOTH a PDF contract and CSV log file to run the audit.")
    else:
        with st.spinner("ANALYZING EXTRACTED DOCUMENTS USING GEMINI 3.5 FLASH-LITE..."):
            try:
                # Initialize Google GenAI Client
                client = genai.Client(api_key=user_api_key)
                
                
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
                leakage_amount = sum(item.get("penalty_recovered", 0.0) for item in audit_data.get("violations_found", []))
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
                # Dataframe Display, Charts, and Export for Breaches
                violations = audit_data.get("violations_found", [])
                if violations:
                    st.markdown("---")
                    st.subheader("Identified SLA Breaches")
                    
                    # Convert AI JSON array into a Pandas DataFrame for advanced manipulation
                    df_violations = pd.DataFrame(violations)
                
                    # NEW V4.0 UI FORMATTING: Confidence Score & Column Order
                    if "confidence_score" in df_violations.columns:
                        df_violations["confidence_score"] = df_violations["confidence_score"].apply(lambda x: f"{x}%")
                
                    columns_order = ["clause_ref", "incident_date", "confidence_score", "penalty_recovered", "breach_details"]
                    existing_cols = [col for col in columns_order if col in df_violations.columns]
                    df_violations = df_violations[existing_cols]
                
                    # 1. Render Interactive Data Table
                    st.dataframe(df_violations, use_container_width=True)
                    
                    # 2. Render Cyberpunk Bar Chart (Penalties grouped by Clause)
                    st.subheader("Capital Leakage by Clause")
                    chart_data = df_violations.groupby("clause_ref")["penalty_recovered"].sum().reset_index()
                    st.bar_chart(
                        data=chart_data, 
                        x="clause_ref", 
                        y="penalty_recovered",
                        color="#00F2FE", # Cyberpunk Cyan
                        use_container_width=True
                    )
                    
                    # 3. Generate Downloadable CSV Report
                    csv_export = df_violations.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 DOWNLOAD FORENSIC REPORT (.CSV)",
                        data=csv_export,
                        file_name=f"BLEED_Protocol_Audit_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.success("No SLA breaches or capital leakage identified from the provided documents.")



            except json.JSONDecodeError:
                st.error("FAILED TO PARSE RESPONSE: Model did not return valid JSON structure.")
            except Exception as e:
                st.error(f"SYSTEM FAILURE: {str(e)}")
      
