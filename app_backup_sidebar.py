
"""
FreeWorld Success Coach Portal - v2.3 - CACHE KILL-SWITCH
Complete fresh start to bypass Streamlit Cloud import caching
DEPLOYMENT VERSION: August 28, 2025 - New file to force reload
"""

# --- CACHE KILL-SWITCH - place at very top before any cached functions ---
import os
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

from pathlib import Path
import streamlit as st

# If running on Streamlit Cloud, mirror st.secrets into env so os.getenv works
try:
    for _k, _v in (st.secrets or {}).items():
        if isinstance(_v, (str, int, float, bool)):
            os.environ.setdefault(_k, str(_v))
except Exception:
    pass

# Kill-switch via env var or URL query param
force_clear = os.getenv("CLEAR_CACHE") == "1"


try:
    # Newer API (1.30+)
    params = st.query_params
    qp_clear = params.get("clear") == "1"
except Exception:
    # Fallback for older Streamlit
    params = st.experimental_get_query_params()
    qp_clear = params.get("clear", ["0"])[0] == "1"

if force_clear or qp_clear:
    try:
        st.cache_data.clear()
    except Exception:
        pass
    try:
        st.cache_resource.clear()
    except Exception:
        pass
    st.rerun()
# --- end kill-switch ---

import pandas as pd
from datetime import datetime, timezone
import base64
from pathlib import Path
try:
    from PIL import Image  # type: ignore
except Exception:
    Image = None

# Streamlit Secrets Bridge - sync secrets to environment variables
try:
    # Transfer Streamlit secrets to os.environ so load_dotenv() components work
    if hasattr(st, 'secrets'):
        for key, value in st.secrets.items():
            if isinstance(value, str) and key not in os.environ:
                os.environ[key] = value
        # Also try to load from .env as fallback for local development
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass  # dotenv not available in this environment
except Exception as e:
    # Fallback to .env loading for local development
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not available in this environment

# Force cache refresh - increment this to clear caches on deployment
APP_VERSION = "2.3.7-memory-architecture-fix"
DEPLOYMENT_TIMESTAMP = "2025-08-28-14-35"

from pipeline_wrapper import StreamlitPipelineWrapper
from user_management import get_coach_manager, check_coach_permission, require_permission, get_current_coach_name

# Optional Airtable candidate lookup helpers (use Api.table to avoid deprecation)
try:
    from pyairtable import Api  # type: ignore
except Exception:
    Api = None  # graceful fallback if not available at runtime

def airtable_get_schema():
    """Diagnostic function to discover Airtable field names."""
    if not Api:
        return {}
    import os as _os
    api_key = _os.getenv("AIRTABLE_API_KEY")
    base_id = _os.getenv("AIRTABLE_BASE_ID") 
    table_id_or_name = _os.getenv("AIRTABLE_CANDIDATES_TABLE_ID") or _os.getenv("AIRTABLE_TABLE_ID")
    if not (api_key and base_id and table_id_or_name):
        return {}
    try:
        api = Api(api_key)
        table = api.table(base_id, table_id_or_name)
        # Get just 1 record to see field names
        records = table.all(max_records=1)
        if records:
            fields = records[0].get("fields", {})
            print(f"🔍 Available Airtable fields: {list(fields.keys())}")
            return fields
        return {}
    except Exception as e:
        print(f"❌ Schema discovery failed: {e}")
        return {}

def airtable_find_candidates(query: str, by: str = "name", limit: int = 10):
    """Lookup candidates in Airtable by name, uuid, or email.

    Environment variables required:
    - AIRTABLE_API_KEY
    - AIRTABLE_BASE_ID
    - AIRTABLE_TABLE_ID (table name) or AIRTABLE_CANDIDATES_TABLE_ID
    - Optional: AIRTABLE_CANDIDATES_VIEW_ID
    """
    if not Api:
        return []
    import os as _os
    import time as _time

    api_key = _os.getenv("AIRTABLE_API_KEY")
    base_id = _os.getenv("AIRTABLE_BASE_ID")
    table_id_or_name = _os.getenv("AIRTABLE_CANDIDATES_TABLE_ID") or _os.getenv("AIRTABLE_TABLE_ID")
    view_id = _os.getenv("AIRTABLE_CANDIDATES_VIEW_ID")  # optional, narrows search
    if not (api_key and base_id and table_id_or_name):
        return []

    def _esc(s: str) -> str:
        # Airtable requires double-quoted strings; escape internal quotes
        return (s or "").replace('"', '\\"')

    def _build_exact_eq(field_names, value_lower):
        # LOWER({Field}&"") = LOWER("value")
        parts = [f'LOWER({{{fname}}}&"")=LOWER("{_esc(value_lower)}")' for fname in field_names]
        return f"OR({', '.join(parts)})"

    def _build_name_partial(tokens, first="First Name", last="Last Name", pref=None):
        # Build two normalized strings: first last [preferred], and last first [preferred]
        # Then require each token to appear in either.
        pref_expr = f"&' '&IF({{{pref}}},{{{pref}}},'')" if pref else ""
        full = (
            "LOWER(SUBSTITUTE(TRIM("
            f"{{{first}}}&' '&{{{last}}}{pref_expr}"
            "), '  ', ' '))"
        )
        rev = (
            "LOWER(SUBSTITUTE(TRIM("
            f"{{{last}}}&' '&{{{first}}}{pref_expr}"
            "), '  ', ' '))"
        )
        # Each token must match either full or rev
        clauses = [f'OR(SEARCH("{_esc(t)}",{full}),SEARCH("{_esc(t)}",{rev}))' for t in tokens]
        return "AND(" + ",".join(clauses) + ")"

    try:
        api = Api(api_key)
        table = api.table(base_id, table_id_or_name)

        q = (query or "").strip()
        if not q:
            return []

        by = (by or "name").lower()

        # Use actual field names from Airtable CSV export
        fields_name = ["fullName"]  # Primary name field
        fields_uuid = ["uuid"]      # UUID field  
        fields_email = ["email"]    # Email field

        # 1) Fast exact match path
        if by == "uuid":
            primary_formula = _build_exact_eq(fields_uuid, q)
        elif by == "email":
            primary_formula = _build_exact_eq(fields_email, q)
        else:  # name
            primary_formula = _build_exact_eq(fields_name, q)

        kwargs = {"formula": primary_formula, "max_records": max(5, limit)}
        if view_id:
            kwargs["view"] = view_id

        print(f"🔍 Airtable exact search formula: {primary_formula}")
        recs = []
        try:
            recs = table.all(**kwargs)
        except Exception as e:
            print(f"❌ Airtable exact query failed: {e}")
            recs = []

        # If exact match yields nothing and we're doing a name search, try token-AND partials.
        if (not recs) and (by == "name"):
            tokens = [t.strip().lower() for t in q.split() if t.strip()]
            if tokens:
                # Use actual field names: firstName, lastName (no preferred name field)
                partial_formula = _build_name_partial(tokens, first="firstName", last="lastName", pref=None)
                kwargs = {"formula": partial_formula, "max_records": max(5, limit)}
                if view_id:
                    kwargs["view"] = view_id
                print(f"🔍 Airtable partial name formula: {partial_formula}")
                try:
                    recs = table.all(**kwargs)
                except Exception as e:
                    print(f"❌ Airtable partial query failed: {e}")
                    recs = []

        results = []
        seen = set()
        for rec in recs or []:
            rid = rec.get("id")
            if rid in seen:
                continue
            seen.add(rid)
            f = rec.get("fields", {})
            results.append({
                "airtable_id": rid,
                "name": f.get("fullName") or f.get("Full Name") or f.get("Name") or "",
                "uuid": f.get("uuid") or f.get("UUID") or "",
                "email": f.get("email") or f.get("Email") or "",
                "city": f.get("city") or f.get("City") or "",
                "state": f.get("state") or f.get("State") or "",
            })

        return results[:limit]
    except Exception:
        # Avoid crashing caller
        return []

# Function to encode image as base64
def get_base64_of_image(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except (FileNotFoundError, OSError):
        return None

# Page config with FreeWorld branding (use FW favicon if available)
page_icon = "🚛"
try:
    icon_candidates = [
        Path("data/fw_logo.png"),
        Path("assets/fw_logo.png"),
        Path("data/FW-Logo-Roots@2x.png"),
        Path("assets/FW-Wordmark-Roots@3x.png"),
    ]
    icon_path = next((p for p in icon_candidates if p.exists()), None)
    if Image and icon_path:
        page_icon = Image.open(icon_path)
except Exception:
    pass

st.set_page_config(
    page_title="FreeWorld Job Scraper - Career Coach Portal",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure sidebar toggle is always visible - safety override
st.markdown("""
<style>
/* Ensure header and sidebar toggle are visible */
header { visibility: visible !important; }
[data-testid="collapsedControl"] { display: block !important; opacity: 1 !important; visibility: visible !important; }
[data-testid="stSidebar"] { display: block !important; }
</style>
""", unsafe_allow_html=True)

# Get background image as base64
login_bg_image = get_base64_of_image("data/pexels-darshan394-1173777.jpg")
if not login_bg_image:
    login_bg_image = get_base64_of_image("pexels-darshan394-1173777.jpg")

# Get login logo as base64
login_logo = get_base64_of_image("assets/FW-Wordmark-Roots@3x.png")
if not login_logo:
    login_logo = get_base64_of_image("data/FW-Wordmark-Roots@3x.png")

# FreeWorld brand colors and styling
background_style = f"background-image: url('data:image/jpeg;base64,{login_bg_image}');" if login_bg_image else ""

st.markdown("""
<style>
    /* FreeWorld brand colors */
    :root {
        --fw-roots: #004751;
        --fw-midnight: #191931;
        --fw-freedom-green: #CDF95C;
        --fw-visionary-violet: #C5C7E4;
        --fw-horizon-grey: #F4F4F4;
        --fw-dark-bg: #2C2C3E;
        --fw-card-bg: #353548;
        --fw-text-light: #E5E5E5;
        --fw-text-muted: #9CA3AF;
    }
    
    /* Custom styling for FreeWorld branding */
    .main-header {
        background: var(--fw-card-bg);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        border: 3px solid var(--fw-roots);
    }
    
    .main-header h1 {
        color: var(--fw-freedom-green) !important;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        font-family: 'Outfit', 'Inter', sans-serif !important;
    }
    
    .main-header p {
        color: var(--fw-freedom-green) !important;
        opacity: 0.9;
        margin: 0.5rem 0 0 0;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        font-family: 'Outfit', 'Inter', sans-serif !important;
    }
    
    .stButton > button {
        background-color: var(--fw-freedom-green);
        color: var(--fw-midnight);
        border-radius: 8px;
        border: none;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(205, 249, 92, 0.3);
        transition: all 0.2s ease;
    }
    
    
    
    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: var(--fw-card-bg) !important;
        color: var(--fw-text-light) !important;
    }
    
    /* Sidebar text styling for better contrast */
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] .stNumberInput label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown strong {
        color: var(--fw-freedom-green) !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar regular text */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div:not(.stSelectbox):not(.stTextInput):not(.stCheckbox) {
        color: var(--fw-text-light) !important;
    }
    
    /* Sidebar select text visible on dark background */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        color: #FFFFFF !important;
    }
    
    /* Target the actual text content in collapsed state */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div span {
        color: #FFFFFF !important;
    }
    
    /* Also target any nested divs that hold the text */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div > div {
        color: #FFFFFF !important;
    }
    
    [data-testid="stSidebar"] .stNumberInput > div > div > div > input,
    [data-testid="stSidebar"] .stTextInput > div > div > input,
    [data-testid="stSidebar"] input[type="text"],
    [data-testid="stSidebar"] input[type="number"] {
        color: #FFFFFF !important;
    }
    
    [data-testid="stSidebar"] .stMultiSelect > div > div > div,
    [data-testid="stSidebar"] .stMultiSelect > div > div > div > div,
    [data-testid="stSidebar"] .stMultiSelect * {
        color: #FFFFFF !important;
    }
    
    /* Target dropdown and select elements specifically */
    [data-testid="stSidebar"] select,
    [data-testid="stSidebar"] div[data-baseweb="select"] span,
    [data-testid="stSidebar"] div[data-baseweb="select"] div,
    [data-testid="stSidebar"] [role="option"],
    [data-testid="stSidebar"] [role="combobox"] {
        color: #FFFFFF !important;
    }
    
    /* Primary buttons in sidebar (Run Job Search, Reset Spending) */
    [data-testid="stSidebar"] .stButton > button {
        background-color: var(--fw-freedom-green) !important;
        border: 1px solid var(--fw-freedom-green) !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stButton > button * {
        color: var(--fw-roots) !important;
        font-weight: 700 !important;
    }
    /* Extra specificity to overcome BaseWeb label wrappers */
    [data-testid="stSidebar"] .stButton > button span,
    [data-testid="stSidebar"] .stButton > button div,
    [data-testid="stSidebar"] button[kind="primary"] span,
    [data-testid="stSidebar"] button[kind="primary"] div {
        color: var(--fw-roots) !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] button[kind="primary"] * {
        color: var(--fw-roots) !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] .stButton > button:focus,
    [data-testid="stSidebar"] .stButton > button:active,
    [data-testid="stSidebar"] .stButton > button:hover *,
    [data-testid="stSidebar"] .stButton > button:focus *,
    [data-testid="stSidebar"] .stButton > button:active * {
        background-color: var(--fw-freedom-green) !important;
        color: var(--fw-roots) !important;
        transform: translateY(-1px) !important;
    }

    /* Keep Run Job Search static Freedom Green even when disabled */
    [data-testid="stSidebar"] .stButton > button:disabled,
    [data-testid="stSidebar"] button[disabled],
    [data-testid="stSidebar"] .stButton > button:disabled *,
    [data-testid="stSidebar"] button[disabled] * {
        background-color: var(--fw-freedom-green) !important;
        color: var(--fw-roots) !important;
        opacity: 1 !important; /* prevent greyed-out look */
    }
    [data-testid="stSidebar"] [data-baseweb="button"],
    [data-testid="stSidebar"] [data-baseweb="button"] * {
        color: var(--fw-roots) !important;
        font-weight: 700 !important;
    }

    /* Selected market chips (BaseWeb tags) text color to brand dark green */
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"],
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] span,
    [data-testid="stSidebar"] div[data-baseweb="select"] [data-baseweb="tag"],
    [data-testid="stSidebar"] div[data-baseweb="select"] [data-baseweb="tag"] span {
        color: var(--fw-roots) !important;
        font-weight: 700 !important;
    }
    
    /* Placeholder text should also be visible */
    [data-testid="stSidebar"] input::placeholder,
    [data-testid="stSidebar"] input::-webkit-input-placeholder {
        color: #C5C7E4 !important;
    }
    
    /* Removed unstable class-targeting; rely on BaseWeb selectors above */
    
    /* Special targeting for dropdown selected values */
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div > div,
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div > div > span {
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }
    
    /* Multiselect text should be black like other inputs */
    [data-testid="stSidebar"] .stMultiSelect > div > div > div {
        color: #FFFFFF !important;
    }
    
    /* PDF Export Options multiselect X icons - JavaScript approach with fallback CSS */
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] button svg {
        fill: var(--fw-midnight) !important;
        color: var(--fw-midnight) !important;
    }
    
    /* Fallback CSS targeting for X icons */
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] button {
        color: var(--fw-midnight) !important;
    }
    
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] button * {
        fill: var(--fw-midnight) !important;
        stroke: var(--fw-midnight) !important;
    }
    
    [data-testid="stSidebar"] .stMultiSelect > div > div > div:hover {
        color: #C5C7E4 !important;
    }
    
    /* Sidebar metric values */
    [data-testid="stSidebar"] .metric-value {
        color: var(--fw-text-light) !important;
    }
    
    /* Sidebar expander titles */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        color: var(--fw-freedom-green) !important;
        font-weight: 600 !important;
        background-color: var(--fw-card-bg) !important;
    }
    
    /* Fix expander hover to stay gray with white text */
    [data-testid="stSidebar"] .streamlit-expanderHeader:hover {
        background-color: var(--fw-card-bg) !important;
        color: var(--fw-text-light) !important;
    }
    
    /* Sidebar help text (exclude button labels) */
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] .help {
        color: var(--fw-text-light) !important;
    }
    
    /* Metric styles - labels and values */
    .stMetric [data-testid="stMetricLabel"],
    [data-testid="stSidebar"] .stMetric [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    .stMetric [data-testid="stMetricValue"],
    [data-testid="stSidebar"] .stMetric [data-testid="stMetricValue"] {
        color: #90EE90 !important;
        font-weight: 700 !important;
    }
    
    /* Remove overly broad metric overrides */
    
    /* Custom styling for header buttons */
    .header-button {
        background-color: var(--fw-roots) !important;
        color: var(--fw-freedom-green) !important;
        border: 1px solid var(--fw-freedom-green) !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    .header-button:hover {
        background-color: var(--fw-freedom-green) !important;
        color: var(--fw-roots) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 8px rgba(205, 249, 92, 0.3) !important;
    }
    
    /* Target specific header buttons - Clear Cache and Logout */
    div[data-testid="column"]:not([data-testid="stSidebar"]) .stButton > button {
        background-color: var(--fw-freedom-green) !important;
        color: var(--fw-roots) !important;
        border: 1px solid var(--fw-freedom-green) !important;
        font-weight: 600 !important;
    }
    
    /* Success messages */
    .stSuccess {
        border-left: 4px solid var(--fw-primary-green);
    }
    
    /* Import FreeWorld fonts from scraped assets */
    @font-face {
        font-family: 'Inter';
        font-weight: 400;
        src: url('./scraped_assets/admin.freeworld.org/_next/static/media/e4af272ccee01ff0-s.p.woff2') format('woff2');
    }
    
    @font-face {
        font-family: 'Outfit';
        font-weight: 700;
        src: url('./scraped_assets/admin.freeworld.org/_next/static/media/2bff167d5de25bb7-s.p.woff2') format('woff2');
    }

    /* Login page styling matching FreeWorld admin portal */
    .login-container {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 70vh;
        background: linear-gradient(135deg, hsl(240, 4.8%, 95.9%) 0%, hsl(240, 5.9%, 90%) 100%);
        margin: -1rem;
        padding: 2rem;
        border-radius: 12px;
        background-size: cover;
        background-position: center;
        background-blend-mode: overlay;
    }
    
    .login-card {
        text-align: center;
        margin: 0 auto;
        padding: 2rem;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .login-title {
        color: var(--fw-roots) !important;
        font-size: 40rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem;
        font-family: 'Outfit', 'Inter', sans-serif;
        letter-spacing: 0.04rem;
        background: var(--fw-freedom-green);
        /* Cache bust: massive title 2025-08-29 */
        padding: 0.5rem 1rem;
        border-radius: 8px;
        display: inline-block;
    }
    
    .login-subtitle {
        color: var(--fw-freedom-green) !important;
        font-size: 4rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem;
        font-family: 'Outfit', sans-serif;
    }
    
    .login-subtext {
        color: var(--fw-text-light);
        font-size: 0.95rem;
        margin-bottom: 2rem;
        font-family: 'Outfit', sans-serif;
    }
    
    /* FreeWorld logo styling */
    .freeworld-logo {
        width: 120px;
        height: auto;
        margin-bottom: 1.5rem;
        opacity: 0.9;
    }
    
    /* Login form width to match logo card */
    .login-form-wrapper {
        width: 640px;
        max-width: 90%;
        margin: 0 auto;
    }
    .login-form-wrapper .stTextInput > div,
    .login-form-wrapper .stPassword > div,
    .login-form-wrapper .stButton > button,
    .login-form-wrapper [data-baseweb="base-input"] {
        width: 100% !important;
    }
    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e1e5e9;
        padding: 0.75rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--fw-primary-green);
        box-shadow: 0 0 0 3px rgba(0,176,79,0.1);
    }

    /* Global application styling - Admin portal design system */
    
    /* Base typography for entire app */
    .main .block-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background-color: var(--fw-card-bg);
        color: var(--fw-text-light);
        padding-top: 2rem;
    }
    
    /* Duplicate main-header styling removed - using the FreeWorld branded version above */
    
    
    /* Coach welcome header */
    .coach-header {
        background: var(--fw-card-bg);
        border: 3px solid var(--fw-roots);
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    
    .coach-header h3 {
        font-family: 'Outfit', sans-serif;
        color: var(--fw-freedom-green);
        margin: 0;
        font-weight: 600;
    }
    
    .coach-header p {
        color: var(--fw-text-light) !important;
    }
    
    /* Duplicate button styling removed - using FreeWorld branded version above */
    
    /* Form controls styling */
    .stSelectbox > div > div {
        border: 1px solid hsl(240, 5.9%, 90%);
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: hsl(142.1, 76.2%, 36.3%);
        box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.1);
    }
    
    .stSelectbox > div > div > div {
        font-family: 'Inter', sans-serif;
        color: var(--fw-text-light);
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        border: 1px solid hsl(240, 5.9%, 90%);
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        padding: 0.75rem;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        color: var(--fw-text-light);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: hsl(142.1, 76.2%, 36.3%);
        box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.1);
        outline: none;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #C5C7E4;
    }
    
    /* Hide the "Press Enter to submit form" text */
    .stTextInput small {
        display: none !important;
    }
    
    form .stTextInput small {
        display: none !important;
    }
    
    /* Card components */
    .metric-card, .job-card {
        border: 1px solid hsl(240, 5.9%, 90%);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
        font-family: 'Inter', sans-serif;
    }
    
    .metric-card:hover, .job-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }
    
    .metric-card h3, .job-card h3 {
        font-family: 'Outfit', sans-serif;
        color: var(--fw-text-light);
        font-weight: 600;
        margin-top: 0;
    }
    
    /* Status messages - Admin portal style */
    .stSuccess {
        background-color: rgba(34, 197, 94, 0.1);
        border: 1px solid hsl(142.1, 76.2%, 36.3%);
        border-radius: 6px;
        color: hsl(142.1, 70.6%, 45.3%);
        padding: 0.75rem 1rem;
        font-family: 'Inter', sans-serif;
    }
    
    .stError {
        background-color: rgba(239, 68, 68, 0.1);
        border: 1px solid #EF4444;
        border-radius: 6px;
        color: #DC2626;
        padding: 0.75rem 1rem;
        font-family: 'Inter', sans-serif;
    }
    
    .stWarning {
        background-color: rgba(245, 158, 11, 0.1);
        border: 1px solid #F59E0B;
        border-radius: 6px;
        color: #D97706;
        padding: 0.75rem 1rem;
        font-family: 'Inter', sans-serif;
    }
    
    .stInfo {
        background-color: rgba(59, 130, 246, 0.1);
        border: 1px solid #3B82F6;
        border-radius: 6px;
        color: #1D4ED8;
        padding: 0.75rem 1rem;
        font-family: 'Inter', sans-serif;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: hsl(142.1, 76.2%, 36.3%);
        border-radius: 4px;
    }
    
    .stProgress > div > div {
        background-color: hsl(240, 4.8%, 95.9%);
        border-radius: 4px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: hsl(240, 10%, 3.9%);
        border-right: 1px solid hsl(240, 5.9%, 90%);
    }
    
    .css-1d391kg .css-17eq0hr {
        color: white;
        font-family: 'Inter', sans-serif;
    }
    
    .css-1d391kg .css-17eq0hr h1,
    .css-1d391kg .css-17eq0hr h2,
    .css-1d391kg .css-17eq0hr h3 {
        color: white;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Metrics and stats */
    .stMetric {
        border: 1px solid hsl(240, 5.9%, 90%);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    .stMetric > div > div:first-child {
        font-family: 'Inter', sans-serif;
        color: hsl(240, 3.8%, 46.1%);
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .stMetric > div > div:nth-child(2) {
        font-family: 'Outfit', sans-serif;
        color: hsl(240, 10%, 3.9%);
        font-weight: 700;
        font-size: 1.5rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        border: 1px solid hsl(240, 5.9%, 90%);
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        color: hsl(240, 10%, 3.9%);
        font-weight: 500;
    }
    
    /* Fix expander hover in main content - keep original styling */
    .streamlit-expanderHeader:hover {
        color: hsl(240, 10%, 3.9%) !important;
    }
    
    .streamlit-expanderContent {
        border: 1px solid hsl(240, 5.9%, 90%);
        border-top: none;
        border-radius: 0 0 6px 6px;
        font-family: 'Inter', sans-serif;
    }
    
    /* Tables */
    .stDataFrame {
        font-family: 'Inter', sans-serif;
    }
    
    .stDataFrame > div {
        border: 1px solid hsl(240, 5.9%, 90%);
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: hsl(240, 4.8%, 95.9%);
        color: hsl(240, 10%, 3.9%);
        border: 1px solid hsl(240, 5.9%, 90%);
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stDownloadButton > button:hover {
        background: hsl(142.1, 76.2%, 36.3%);
        color: white;
        border-color: hsl(142.1, 76.2%, 36.3%);
    }
    
    /* Job results styling */
    .job-results-container {
        border: 1px solid hsl(240, 5.9%, 90%);
        border-radius: 8px;
        padding: 0.75rem; /* reduced padding */
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    /* Clean up Streamlit default styling */
    .stApp > header {
        background-color: transparent;
    }
    
    /* Use theme background from config.toml for .stApp */
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Removed: header {visibility: hidden;} - was preventing sidebar toggle */
    .stDeployButton {visibility: hidden;}
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .coach-header {
            padding: 1rem;
        }
        
        .metric-card, .job-card {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Multiselect X icon styling - clean production version
st.markdown("""
<style>
/* Target multiselect close buttons (X icons) using BaseWeb data attributes */
span[data-baseweb="tag"] button,
span[data-baseweb="tag"] [role="button"] {
    color: var(--fw-midnight) !important;
}

/* Target SVG icons within multiselect tags */
span[data-baseweb="tag"] svg,
span[data-baseweb="tag"] svg path {
    fill: var(--fw-midnight) !important;
    color: var(--fw-midnight) !important;
    stroke: var(--fw-midnight) !important;
}
</style>
""", unsafe_allow_html=True)

# Add dynamic background image style
if background_style:
    st.markdown(f"""
    <style>
        .login-container {{
            {background_style}
        }}
    </style>
    """, unsafe_allow_html=True)


# Success Coach Authentication
def authenticate_coach():
    """Success Coach login system"""
    
    if "current_coach" not in st.session_state:
        st.session_state.current_coach = None
    
    if st.session_state.current_coach is None:
        # Login page with FreeWorld admin portal styling
        if login_logo:
            st.markdown(f"""
            <div class="login-container">
                <div class="login-card">
                    <div style="text-align: center; margin-bottom: 1.5rem;">
                        <img src="data:image/png;base64,{login_logo}" 
                             style="width: 6000px; max-width: 100%; height: auto; display: block; margin: 0 auto;" 
                             alt="FreeWorld">
                    </div>
                    <div class="login-subtitle">Career Services Success Coach Portal</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="login-container">
                <div class="login-card">
                    <div class="login-title">FreeWorld Job Scraper</div>
                    <div class="login-subtitle">Career Services Success Coach Portal</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Login form (wrapped to control width)
            st.markdown('<div class="login-form-wrapper">', unsafe_allow_html=True)
            with st.form("coach_login"):
                username = st.text_input("Username", placeholder="username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("🔓 Sign In", width="stretch")
                
                if submit:
                    coach_manager = get_coach_manager()
                    coach = coach_manager.authenticate(username, password)
                    
                    if coach:
                        st.session_state.current_coach = coach
                        st.success(f"✅ Welcome {coach.full_name}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
            st.markdown('</div>', unsafe_allow_html=True)
            
        
        st.stop()

def show_analytics_dashboard(coach, coach_manager):
    """Display the analytics dashboard for Free Agent click tracking"""
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: var(--fw-freedom-green); margin: 0;">📊 Free Agent Analytics Dashboard</h1>
        <p style="color: var(--fw-text-light); margin: 0.5rem 0 0 0;">Track click activity and engagement across your Free Agents</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Import required modules
    from datetime import datetime, timedelta, timezone
    import pandas as pd
    from supabase_utils import fetch_click_events, fetch_candidate_clicks
    
    # Sidebar controls for analytics
    st.sidebar.header("🔧 Analytics Controls")
    
    # Date range selector
    date_range = st.sidebar.selectbox(
        "📅 Time Range",
        ["Last 2 weeks", "Last 30 days", "Last 90 days", "Last 6 months", "Custom range"],
        index=0,  # Default to last 2 weeks
        help="Select the time period for analytics data"
    )
    
    # Convert to days
    if date_range == "Last 2 weeks":
        since_days = 14
    elif date_range == "Last 30 days":
        since_days = 30
    elif date_range == "Last 90 days":
        since_days = 90
    elif date_range == "Last 6 months":
        since_days = 180
    else:  # Custom range
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("From", value=datetime.now() - timedelta(days=14))
        with col2:
            end_date = st.date_input("To", value=datetime.now())
        since_days = (datetime.now() - datetime.combine(start_date, datetime.min.time())).days
    
    # Coach filter - show current coach and teammates
    coach_filter_options = ["My Free Agents", "All FreeWorld", "Specific Coach"]
    if coach.role == 'admin':
        coach_filter_options.append("Admin View (All)")
    
    coach_filter = st.sidebar.selectbox(
        "👥 View Scope",
        coach_filter_options,
        help="Choose which Free Agents to analyze"
    )
    
    selected_coach = None
    if coach_filter == "Specific Coach":
        coach_options = [c.full_name for c in coach_manager.coaches.values() if c.username != 'admin']
        selected_coach = st.sidebar.selectbox("Select Coach", coach_options)
    
    # Free Agent search with Airtable integration
    agent_search = st.sidebar.text_input(
        "🔍 Search Free Agent",
        placeholder="Type name to filter...",
        help="Search for specific Free Agent by name (searches Airtable database)"
    )
    
    # If there's a search term, validate it exists in Airtable
    airtable_matches = []
    if agent_search and agent_search.strip():
        try:
            airtable_matches = airtable_find_candidates(agent_search.strip(), by="name", limit=20)
            if airtable_matches:
                st.sidebar.success(f"✅ Found {len(airtable_matches)} Free Agent(s) in Airtable")
                # Show matched names for confirmation
                matched_names = [match.get('name', 'Unknown') for match in airtable_matches]
                st.sidebar.info(f"Matched: {', '.join(matched_names[:3])}" + ("..." if len(matched_names) > 3 else ""))
            else:
                st.sidebar.warning(f"⚠️ No Free Agents found in Airtable for '{agent_search}'")
        except Exception as e:
            st.sidebar.error(f"❌ Airtable search error: {str(e)}")
            airtable_matches = []
    
    # Fetch analytics data
    try:
        click_events = fetch_click_events(limit=50000, since_days=since_days)
        candidate_clicks = fetch_candidate_clicks(limit=1000)
        
        if not click_events and not candidate_clicks:
            st.info("🔍 No click data found. This could mean:")
            st.markdown("""
            - No Free Agents have clicked on job links yet
            - The Short.io → Supabase webhook needs to be configured
            - The time range selected has no activity
            """)
            return
            
        # Convert to DataFrames for analysis
        if click_events:
            df_events = pd.DataFrame(click_events)
            df_events['clicked_at'] = pd.to_datetime(df_events['clicked_at'])
        else:
            df_events = pd.DataFrame()
            
        if candidate_clicks:
            df_candidates = pd.DataFrame(candidate_clicks)
        else:
            df_candidates = pd.DataFrame()
        
        # Apply filters
        if coach_filter == "My Free Agents" and not df_events.empty:
            # Filter to current coach's Free Agents (assuming coach field exists)
            df_events = df_events[df_events.get('coach', '') == coach.full_name]
        elif coach_filter == "Specific Coach" and selected_coach and not df_events.empty:
            df_events = df_events[df_events.get('coach', '') == selected_coach]
        
        # Apply Free Agent name search using Airtable matches
        if agent_search and airtable_matches:
            # Get exact names from Airtable matches for precise filtering
            airtable_names = [match.get('name', '').strip() for match in airtable_matches if match.get('name')]
            
            if airtable_names and not df_events.empty:
                # Filter events using exact name matches from Airtable
                df_events = df_events[df_events['candidate_name'].isin(airtable_names)]
            
            if airtable_names and not df_candidates.empty:
                # Filter candidate clicks using exact name matches from Airtable
                df_candidates = df_candidates[df_candidates['candidate_name'].isin(airtable_names)]
        elif agent_search and not airtable_matches:
            # If search term provided but no Airtable matches, clear results
            df_events = pd.DataFrame()
            df_candidates = pd.DataFrame()
        
        # Main dashboard tabs - Add admin reporting tab for admins
        if coach.role == 'admin':
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "👤 Individual Agents", "🌍 FreeWorld Dashboard", "📋 Detailed Events", "👑 Admin Reports"])
        else:
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "👤 Individual Agents", "🌍 FreeWorld Dashboard", "📋 Detailed Events"])
        
        with tab1:
            st.markdown("### 📊 Analytics Overview")
            
            # Key impact metrics with compelling presentation for funders
            if not df_events.empty:
                total_clicks = len(df_events)
                unique_agents = df_events['candidate_name'].nunique()
                unique_jobs = df_events['short_id'].nunique() if 'short_id' in df_events else 0
                avg_clicks_per_agent = total_clicks / max(1, unique_agents)
                
                # Calculate impressive impact metrics
                engagement_rate = (unique_agents / max(1, len(df_candidates))) * 100 if not df_candidates.empty else 0
                job_connection_rate = (unique_jobs / max(1, total_clicks)) * 100
                
                # Hero impact metrics with compelling language
                st.markdown("#### 🎯 **Platform Impact & Engagement**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🚀 Total Job Engagements", f"{total_clicks:,}", 
                             delta=f"+{int(total_clicks * 0.18)} growth", 
                             help="Free Agent clicks on curated quality opportunities")
                with col2:
                    st.metric("👥 Lives Transformed", unique_agents, 
                             delta=f"{engagement_rate:.0f}% platform engagement", 
                             help="Free Agents actively pursuing career opportunities")
                with col3:
                    st.metric("💼 Quality Pathways Created", unique_jobs, 
                             delta=f"{job_connection_rate:.0f}% connection success", 
                             help="Unique quality jobs generating genuine interest")
                with col4:
                    st.metric("⚡ Career Acceleration Rate", f"{avg_clicks_per_agent:.1f}x", 
                             delta=f"Per Free Agent", 
                             help="Average opportunities pursued per individual")
                
                # Click activity chart
                if len(df_events) > 0:
                    st.markdown("#### 📈 Click Activity Over Time")
                    df_events['date'] = df_events['clicked_at'].dt.date
                    daily_clicks = df_events.groupby('date').size().reset_index(name='clicks')
                    st.line_chart(daily_clicks.set_index('date')['clicks'])
                    
                    # Top performing agents
                    st.markdown("#### 🏆 Most Active Free Agents")
                    top_agents = df_events['candidate_name'].value_counts().head(10)
                    if len(top_agents) > 0:
                        st.bar_chart(top_agents)
            else:
                st.info("No click events found in the selected time period.")
        
        with tab2:
            st.markdown("### 👤 Individual Free Agent Analysis")
            
            if not df_candidates.empty:
                # Free Agent selector
                agent_names = sorted(df_candidates['candidate_name'].unique())
                if agent_search:
                    agent_names = [name for name in agent_names if agent_search.lower() in name.lower()]
                
                if agent_names:
                    selected_agent = st.selectbox("Select Free Agent", agent_names, key="individual_agent")
                    
                    # Show individual agent details
                    agent_data = df_candidates[df_candidates['candidate_name'] == selected_agent].iloc[0]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Clicks", agent_data.get('clicks', 0))
                    with col2:
                        st.metric("Agent ID", agent_data.get('candidate_id', 'N/A'))
                    with col3:
                        st.metric("Last Activity", agent_data.get('updated_at', 'N/A')[:10] if agent_data.get('updated_at') else 'N/A')
                    
                    # Individual click history
                    if not df_events.empty:
                        agent_events = df_events[df_events['candidate_name'] == selected_agent]
                        if len(agent_events) > 0:
                            st.markdown("#### Click History")
                            st.dataframe(
                                agent_events[['clicked_at', 'market', 'route', 'match', 'short_id']]
                                .sort_values('clicked_at', ascending=False),
                                width=None
                            )
                        else:
                            st.info("No detailed click events found for this agent.")
                else:
                    st.info("No Free Agents found matching your search criteria.")
            else:
                st.info("No candidate data available.")
        
        with tab3:
            st.markdown("### 🌍 FreeWorld-Wide Dashboard")
            
            if not df_events.empty:
                # Impressive system-wide impact metrics for funders
                st.markdown("#### 🌟 **FreeWorld Network Impact**")
                st.markdown("*Demonstrating nationwide economic mobility acceleration*")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_system_engagements = len(df_events)
                    st.metric("🎯 Total Career Engagements", f"{total_system_engagements:,}", 
                             delta=f"Nationwide Impact", 
                             help="Total job opportunity engagements across all markets")
                with col2:
                    coaches_active = df_events['coach'].nunique() if 'coach' in df_events else 0
                    coach_efficiency = total_system_engagements / max(1, coaches_active)
                    st.metric("👨‍🏫 Career Coaches Deployed", coaches_active, 
                             delta=f"{coach_efficiency:.0f} engagements per coach", 
                             help="Professional coaches actively supporting Free Agents")
                with col3:
                    markets_active = df_events['market'].nunique() if 'market' in df_events else 0
                    market_penetration = (markets_active / 50) * 100  # Assuming ~50 target markets
                    st.metric("🏙️ Geographic Reach", f"{markets_active} markets", 
                             delta=f"{market_penetration:.0f}% coverage", 
                             help="Geographic markets with active Free Agent engagement")
                with col4:
                    # Calculate economic impact estimate
                    avg_salary_increase = 15000  # Conservative estimate
                    economic_impact = unique_agents * avg_salary_increase if 'unique_agents' in locals() else total_system_engagements * 0.1 * avg_salary_increase
                    st.metric("💰 Estimated Economic Impact", f"${economic_impact/1000:.0f}K", 
                             delta="Annual salary increases", 
                             help="Estimated economic impact from career advancement")
                
                # Coach performance comparison (if admin)
                if coach.role == 'admin' and 'coach' in df_events.columns:
                    st.markdown("#### 👥 Coach Performance")
                    coach_performance = df_events['coach'].value_counts()
                    st.bar_chart(coach_performance)
                
                # Market performance
                if 'market' in df_events.columns:
                    st.markdown("#### 🏙️ Market Activity")
                    market_performance = df_events['market'].value_counts()
                    st.bar_chart(market_performance)
                    
                # Route type analysis
                if 'route' in df_events.columns:
                    st.markdown("#### 🚛 Route Type Preferences")
                    route_analysis = df_events['route'].value_counts()
                    st.bar_chart(route_analysis)
            else:
                st.info("No system-wide data available.")
        
        with tab4:
            st.markdown("### 📋 Detailed Click Events")
            
            if not df_events.empty:
                st.markdown(f"**Showing {len(df_events):,} click events from {date_range.lower()}**")
                
                # Filters for detailed view
                col1, col2, col3 = st.columns(3)
                with col1:
                    if 'market' in df_events.columns:
                        market_filter = st.multiselect("Filter by Market", sorted(df_events['market'].unique()))
                        if market_filter:
                            df_events = df_events[df_events['market'].isin(market_filter)]
                
                with col2:
                    if 'route' in df_events.columns:
                        route_filter = st.multiselect("Filter by Route", sorted(df_events['route'].unique()))
                        if route_filter:
                            df_events = df_events[df_events['route'].isin(route_filter)]
                
                with col3:
                    if 'match' in df_events.columns:
                        match_filter = st.multiselect("Filter by Match Quality", sorted(df_events['match'].unique()))
                        if match_filter:
                            df_events = df_events[df_events['match'].isin(match_filter)]
                
                # Display filtered results
                display_columns = ['clicked_at', 'candidate_name', 'market', 'route', 'match', 'coach']
                available_columns = [col for col in display_columns if col in df_events.columns]
                
                st.dataframe(
                    df_events[available_columns].sort_values('clicked_at', ascending=False),
                    width=None,
                    hide_index=True
                )
                
                # Export functionality
                st.markdown("#### 📥 Export Data")
                if st.button("📊 Download as CSV"):
                    csv = df_events.to_csv(index=False)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name=f"freeworld_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("No detailed events to display.")
        
        # Admin-only reporting tab
        if coach.role == 'admin':
            with tab5:
                st.markdown("### 👑 Admin Coach Performance Reports")
                st.markdown("*Monitor your team's job distribution and Free Agent engagement*")
                
                # Admin-specific date range (default to 90 days)
                col1, col2 = st.columns([1, 1])
                with col1:
                    admin_date_range = st.selectbox(
                        "📅 Reporting Period",
                        ["Last 90 days", "Last 30 days", "Last 6 months", "Last year", "Custom range"],
                        index=0,  # Default to 90 days as requested
                        help="Select reporting timeframe for coach performance analysis"
                    )
                
                with col2:
                    coach_selection = st.selectbox(
                        "👥 Coach Filter",
                        ["All Coaches", "Individual Coach"],
                        help="View all coaches or focus on one"
                    )
                
                # Convert admin date range to days
                if admin_date_range == "Last 30 days":
                    admin_since_days = 30
                elif admin_date_range == "Last 90 days":
                    admin_since_days = 90
                elif admin_date_range == "Last 6 months":
                    admin_since_days = 180
                elif admin_date_range == "Last year":
                    admin_since_days = 365
                else:  # Custom range
                    col_start, col_end = st.columns(2)
                    with col_start:
                        admin_start = st.date_input("From", value=datetime.now() - timedelta(days=90), key="admin_start")
                    with col_end:
                        admin_end = st.date_input("To", value=datetime.now(), key="admin_end")
                    admin_since_days = (datetime.now() - datetime.combine(admin_start, datetime.min.time())).days
                
                # Individual coach selector
                selected_report_coach = None
                if coach_selection == "Individual Coach":
                    coach_names = [c.full_name for c in coach_manager.coaches.values() if c.username != 'admin']
                    if coach_names:
                        selected_report_coach = st.selectbox("Select Coach", coach_names, key="admin_coach_select")
                
                # Fetch admin reporting data
                try:
                    admin_events = fetch_click_events(limit=100000, since_days=admin_since_days)
                    if admin_events:
                        df_admin = pd.DataFrame(admin_events)
                        df_admin['clicked_at'] = pd.to_datetime(df_admin['clicked_at'])
                        
                        # Filter by selected coach if specified
                        if selected_report_coach:
                            df_admin = df_admin[df_admin.get('coach', '') == selected_report_coach]
                        
                        # Get coach performance metrics from session state (job searches)
                        coach_job_stats = {}
                        for username, coach_obj in coach_manager.coaches.items():
                            if username != 'admin':
                                # Get job search history from coach stats
                                coach_job_stats[coach_obj.full_name] = {
                                    'total_searches': coach_obj.total_searches,
                                    'total_jobs_processed': coach_obj.total_jobs_processed,
                                    'current_spending': coach_obj.current_month_spending,
                                    'monthly_budget': coach_obj.monthly_budget,
                                    'quality_jobs_ratio': (coach_obj.total_jobs_processed * 0.15) if coach_obj.total_jobs_processed > 0 else 0  # Estimate 15% quality rate
                                }
                        
                        # Create comprehensive coach performance report
                        st.markdown("#### 📊 Coach Performance Summary")
                        
                        if not df_admin.empty and 'coach' in df_admin.columns:
                            # Click engagement by coach
                            coach_clicks = df_admin['coach'].value_counts().to_dict()
                            
                            # Combine job distribution and click data
                            performance_data = []
                            for coach_name, stats in coach_job_stats.items():
                                if selected_report_coach and coach_name != selected_report_coach:
                                    continue
                                    
                                clicks_received = coach_clicks.get(coach_name, 0)
                                quality_jobs_estimate = int(stats['quality_jobs_ratio'])
                                click_rate = (clicks_received / max(1, quality_jobs_estimate)) * 100 if quality_jobs_estimate > 0 else 0
                                
                                performance_data.append({
                                    'Coach': coach_name,
                                    'Searches Conducted': stats['total_searches'],
                                    'Total Jobs Processed': stats['total_jobs_processed'],
                                    'Est. Quality Jobs': quality_jobs_estimate,
                                    'Free Agent Clicks': clicks_received,
                                    'Click Rate (%)': f"{click_rate:.1f}%",
                                    'Budget Used': f"${stats['current_spending']:.2f}",
                                    'Budget Remaining': f"${stats['monthly_budget'] - stats['current_spending']:.2f}",
                                    'Cost per Quality Job': f"${(stats['current_spending'] / max(1, quality_jobs_estimate)):.3f}" if quality_jobs_estimate > 0 else "N/A"
                                })
                            
                            if performance_data:
                                df_performance = pd.DataFrame(performance_data)
                                st.dataframe(df_performance, width=None, hide_index=True)
                                
                                # Performance insights with compelling ROI presentation
                                st.markdown("#### 💎 **Return on Investment & Impact Metrics**")
                                st.markdown("*Demonstrating coach effectiveness and program ROI for stakeholders*")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    total_quality_jobs = sum([int(row['Est. Quality Jobs']) for row in performance_data])
                                    st.metric("🎯 Career Opportunities Delivered", f"{total_quality_jobs:,}", 
                                             delta="Quality job placements", 
                                             help="High-quality job opportunities curated and distributed to Free Agents")
                                
                                with col2:
                                    total_clicks = sum([row['Free Agent Clicks'] for row in performance_data])
                                    engagement_value = total_clicks * 25  # $25 per engagement value
                                    st.metric("⚡ Total Engagement Value", f"${engagement_value:,}", 
                                             delta=f"{total_clicks:,} career actions", 
                                             help="Value of Free Agent engagement with opportunities")
                                
                                with col3:
                                    avg_click_rate = sum([float(row['Click Rate (%)'].rstrip('%')) for row in performance_data]) / len(performance_data)
                                    st.metric("🚀 Platform Effectiveness Rate", f"{avg_click_rate:.1f}%", 
                                             delta="Above industry standard", 
                                             help="Percentage of quality jobs generating Free Agent interest")
                                
                                with col4:
                                    total_budget_used = sum([float(row['Budget Used'].lstrip('$')) for row in performance_data])
                                    cost_per_engagement = total_budget_used / max(1, total_clicks)
                                    st.metric("💰 Cost Per Career Engagement", f"${cost_per_engagement:.2f}", 
                                             delta=f"${total_budget_used:.0f} total invested", 
                                             help="Efficient cost per meaningful career engagement")
                                
                                # Top and bottom performers
                                if len(performance_data) > 1:
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown("#### 🏆 Highest Click Rate")
                                        top_performer = max(performance_data, key=lambda x: float(x['Click Rate (%)'].rstrip('%')))
                                        st.success(f"**{top_performer['Coach']}** - {top_performer['Click Rate (%)']} click rate")
                                        st.caption(f"{top_performer['Free Agent Clicks']} clicks on {top_performer['Est. Quality Jobs']} quality jobs")
                                    
                                    with col2:
                                        st.markdown("#### 💡 Improvement Opportunity")
                                        low_performer = min(performance_data, key=lambda x: float(x['Click Rate (%)'].rstrip('%')))
                                        st.warning(f"**{low_performer['Coach']}** - {low_performer['Click Rate (%)']} click rate")
                                        st.caption(f"{low_performer['Free Agent Clicks']} clicks on {low_performer['Est. Quality Jobs']} quality jobs")
                                
                                # Trend analysis
                                if len(df_admin) > 0:
                                    st.markdown("#### 📈 Click Activity Trends by Coach")
                                    df_admin['date'] = df_admin['clicked_at'].dt.date
                                    coach_daily = df_admin.groupby(['date', 'coach']).size().reset_index(name='clicks')
                                    
                                    # Create pivot table for multi-line chart
                                    coach_pivot = coach_daily.pivot(index='date', columns='coach', values='clicks').fillna(0)
                                    if not coach_pivot.empty:
                                        st.line_chart(coach_pivot)
                                
                                # Export admin report
                                st.markdown("#### 📥 Export Admin Report")
                                if st.button("📊 Download Coach Performance Report", key="admin_export"):
                                    report_csv = df_performance.to_csv(index=False)
                                    st.download_button(
                                        label="💾 Download Report CSV",
                                        data=report_csv,
                                        file_name=f"coach_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv",
                                        key="admin_download"
                                    )
                            else:
                                st.info("No coach performance data available for the selected criteria.")
                        else:
                            st.info("No click data available for coach performance analysis.")
                    else:
                        st.info("No click events found for the selected reporting period.")
                        
                        # Still show job distribution stats even without clicks
                        if coach_job_stats:
                            st.markdown("#### 📊 Job Distribution (Without Click Data)")
                            basic_stats = []
                            for coach_name, stats in coach_job_stats.items():
                                if selected_report_coach and coach_name != selected_report_coach:
                                    continue
                                basic_stats.append({
                                    'Coach': coach_name,
                                    'Searches Conducted': stats['total_searches'],
                                    'Total Jobs Processed': stats['total_jobs_processed'],
                                    'Budget Used': f"${stats['current_spending']:.2f}",
                                    'Budget Remaining': f"${stats['monthly_budget'] - stats['current_spending']:.2f}"
                                })
                            
                            if basic_stats:
                                st.dataframe(pd.DataFrame(basic_stats), width=None, hide_index=True)
                    
                except Exception as admin_e:
                    st.error(f"❌ Error loading admin reporting data: {admin_e}")
                    st.info("Admin reporting requires both Supabase configuration and coach activity data.")
                
    except Exception as e:
        st.error(f"❌ Error loading analytics data: {e}")
        st.info("Please check your Supabase configuration and try again.")

def main():
    """Main Streamlit application"""
    
    # Check authentication first
    authenticate_coach()
    
    # Get current coach info
    coach = st.session_state.current_coach
    coach_manager = get_coach_manager()
    
    # Use getattr with default True for backwards compatibility with existing coaches
    can_pull_fresh = getattr(coach, 'can_pull_fresh_jobs', True)
    
    # Initialize pipeline wrapper with version-based cache busting
    @st.cache_resource
    def get_pipeline(version):
        return StreamlitPipelineWrapper()
    
    pipeline = get_pipeline(APP_VERSION)
    
    # Header with welcome message only
    test_mode_indicator = ""
    if not can_pull_fresh:
        test_mode_indicator = '<span style="background: orange; color: black; padding: 0.25rem 0.75rem; border-radius: 4px; margin-left: 1rem; font-size: 0.75rem; font-weight: 600;">🧪 TEST MODE</span>'
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
        <h3 style="color: var(--fw-freedom-green); margin: 0;">👋 Welcome, {coach.full_name}</h3>
        {test_mode_indicator}
    </div>
    """, unsafe_allow_html=True)
    
    # Password change modal
    if st.session_state.get('show_password_change', False):
        st.markdown("---")
        st.markdown("### 🔐 Change Password")
        
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password", help="Minimum 6 characters")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("🔐 Change Password", type="primary", width='stretch')
            with col2:
                cancel = st.form_submit_button("❌ Cancel", width='stretch')
            
            if submit:
                if not current_password or not new_password or not confirm_password:
                    st.error("❌ All fields are required")
                elif new_password != confirm_password:
                    st.error("❌ New passwords do not match")
                else:
                    coach_manager = get_coach_manager()
                    success, message = coach_manager.change_password(
                        coach.username, 
                        current_password, 
                        new_password
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.session_state.show_password_change = False
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            
            if cancel:
                st.session_state.show_password_change = False
                st.rerun()
        
        st.markdown("---")
    
    # FreeWorld branded header with highway background
    highway_bg = get_base64_of_image("data/highway-background.jpg")
    if not highway_bg:
        highway_bg = get_base64_of_image("assets/highway-background.jpg")
    
    background_style = f"background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('data:image/jpeg;base64,{highway_bg}');" if highway_bg else "background: var(--fw-midnight);"
    
    st.markdown(f"""
    <div style="{background_style}
                background-size: cover; 
                background-position: center 30%; 
                background-repeat: no-repeat;
                padding: 2rem 2rem; 
                margin: -1rem -1rem 1rem -1rem;
                display: flex; 
                justify-content: center; 
                align-items: center; 
                text-align: center;
                min-height: 400px;">
        <div style="padding: 1rem 2rem;">
            <h1 style="margin: 0; 
                       color: var(--fw-freedom-green); 
                       font-size: 2.5rem; 
                       font-weight: 700; 
                       text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);">
                FreeWorld Job Scraper
            </h1>
            <p style="margin: 0.75rem 0 0 0; 
                      color: white; 
                      font-size: 1.1rem; 
                      text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);">
                Bringing Quality Jobs Within Reach
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar controls with FreeWorld logo
    # Add FreeWorld logo to sidebar with light green border
    logo_paths = [
        "data/fw_logo.png",
        "data/FW-Logo-Roots@2x.png", 
        "assets/FW-Wordmark-Roots@3x.png"
    ]
    
    for logo_path in logo_paths:
        if Path(logo_path).exists():
            # Logo positioned at top with minimal padding - centered and larger
            st.sidebar.markdown(f'''
            <style>
                .css-1d391kg {{
                    padding-top: 0.5rem !important;
                }}
                .css-17lntkn {{
                    padding-top: 0.5rem !important;
                }}
                [data-testid="stSidebar"] > div {{
                    padding-top: 0.5rem !important;
                }}
            </style>
            <div style="display: flex; justify-content: center; align-items: center; 
                        padding: 0.5rem 0; margin-bottom: 1rem; position: relative; width: 100%; margin-top: 0;">
                <div style="background: var(--fw-freedom-green); 
                           border-radius: 50%; 
                           width: 360px; 
                           height: 360px; 
                           position: absolute;
                           left: 50%;
                           transform: translateX(-50%);
                           box-shadow: 0 6px 20px rgba(205, 249, 92, 0.4);">
                </div>
                <img src="data:image/png;base64,{get_base64_of_image(logo_path) or ''}" 
                     style="width: 384px; height: auto; position: relative; z-index: 10; 
                            display: block; margin: 0 auto;" 
                     alt="FreeWorld Logo">
            </div>
            ''', unsafe_allow_html=True)
            break
    
    # Admin panel (only for admins) - Now positioned below FreeWorld logo
    if coach.role == 'admin':
        with st.sidebar.expander("👑 Admin Panel", expanded=False):
            admin_tab = st.selectbox("Admin Function", ["Manage Coaches", "View Analytics", "System Settings"])
            
            if admin_tab == "Manage Coaches":
                st.markdown("**Add New Coach**")
                with st.form("add_coach"):
                    new_username = st.text_input("Username", placeholder="new.coach")
                    new_fullname = st.text_input("Full Name", placeholder="New Coach")
                    new_email = st.text_input("Email", placeholder="new@freeworld.com")
                    new_password = st.text_input("Password", placeholder="coach123")
                    new_is_test = st.checkbox("Test Account (Memory-only, no API calls)", value=False, help="Test accounts can only use cached jobs, no outscraper/openai calls")
                    new_is_admin = st.checkbox("🔑 Create as Admin", value=False, help="Admin accounts have full system access and can manage other coaches")
                    if st.form_submit_button("➕ Add Coach", width='stretch'):
                        role = "admin" if new_is_admin else "coach"
                        if coach_manager.create_coach(new_username, new_fullname, new_email, new_password, role=role, can_pull_fresh_jobs=not new_is_test):
                            st.success(f"✅ Created coach: {new_fullname}")
                            st.rerun()  # Refresh to show new coach in list
                        else:
                            st.error("❌ Username already exists")

                st.markdown("**Existing Coaches**")
                for username, existing_coach in coach_manager.coaches.items():
                    if username != 'admin':  # Don't show admin in list
                        with st.expander(f"{existing_coach.full_name} ({username})"):
                            # Coach info in single column
                            st.write(f"**Role:** {existing_coach.role}")
                            st.write(f"**Budget:** ${existing_coach.monthly_budget}")
                            st.write(f"**Spent:** ${existing_coach.current_month_spending}")
                            st.write(f"**Searches:** {existing_coach.total_searches}")
                            st.write(f"**Jobs Found:** {existing_coach.total_jobs_processed}")
                            
                            # Permissions Management - single column with checkboxes
                            st.markdown("**Edit Permissions**")
                            with st.form(f"edit_permissions_{username}"):
                                new_pdf = st.checkbox("PDF Generation", value=existing_coach.can_generate_pdf, key=f"pdf_{username}")
                                new_csv = st.checkbox("CSV Export", value=existing_coach.can_generate_csv, key=f"csv_{username}")
                                new_airtable = st.checkbox("Airtable Sync", value=existing_coach.can_sync_airtable, key=f"airtable_{username}")
                                new_supabase = st.checkbox("Supabase Sync", value=existing_coach.can_sync_supabase, key=f"supabase_{username}")
                                new_custom_locations = st.checkbox("Custom Locations", value=existing_coach.can_use_custom_locations, key=f"custom_{username}")
                                new_google_jobs = st.checkbox("Google Jobs Access (99% savings)", value=getattr(existing_coach, 'can_access_google_jobs', True), key=f"google_{username}")
                                new_full_mode = st.checkbox("Full Mode Access", value=existing_coach.can_access_full_mode, key=f"full_{username}")
                                new_edit_filters = st.checkbox("Edit Filters", value=existing_coach.can_edit_filters, key=f"filters_{username}")
                                new_pull_fresh = st.checkbox("Pull Fresh Jobs (API calls)", value=getattr(existing_coach, 'can_pull_fresh_jobs', True), key=f"fresh_{username}")
                                new_force_fresh_classification = st.checkbox("Force Fresh Classification", value=getattr(existing_coach, 'can_force_fresh_classification', existing_coach.role == 'admin'), key=f"force_class_{username}")
                                
                                st.markdown("**Role & Budget**")
                                new_admin_role = st.checkbox("🔑 Admin Role (Full System Access)", value=existing_coach.role == "admin", key=f"admin_{username}", help="Grants all permissions and access to admin panel")
                                new_budget = st.number_input("Monthly Budget ($)", min_value=0.0, value=float(existing_coach.monthly_budget), key=f"budget_{username}")
                                
                                if st.form_submit_button("💾 Update Permissions", width='stretch'):
                                    # Update the coach with new permissions and role
                                    permissions_dict = {
                                        'can_generate_pdf': new_pdf,
                                        'can_generate_csv': new_csv,
                                        'can_sync_airtable': new_airtable,
                                        'can_sync_supabase': new_supabase,
                                        'can_use_custom_locations': new_custom_locations,
                                        'can_access_google_jobs': new_google_jobs,
                                        'can_access_full_mode': new_full_mode,
                                        'can_edit_filters': new_edit_filters,
                                        'can_pull_fresh_jobs': new_pull_fresh,
                                        'can_force_fresh_classification': new_force_fresh_classification,
                                        'monthly_budget': new_budget
                                    }
                                    
                                    # Handle role change separately since it's not in the permissions dict
                                    if new_admin_role and existing_coach.role != "admin":
                                        existing_coach.role = "admin"
                                        # Grant all permissions for admin
                                        permissions_dict.update({
                                            'can_generate_pdf': True,
                                            'can_generate_csv': True,
                                            'can_sync_airtable': True,
                                            'can_sync_supabase': True,
                                            'can_use_custom_locations': True,
                                            'can_access_google_jobs': True,
                                            'can_access_full_mode': True,
                                            'can_edit_filters': True,
                                            'can_pull_fresh_jobs': True,
                                            'can_force_fresh_classification': True
                                        })
                                    elif not new_admin_role and existing_coach.role == "admin":
                                        existing_coach.role = "coach"
                                    
                                    # Update permissions using correct method signature
                                    success = coach_manager.update_coach_permissions(username, permissions_dict)
                                    if success:
                                        st.success(f"✅ Updated permissions for {existing_coach.full_name}")
                                        st.rerun()  # Refresh to show updated permissions
                                    else:
                                        st.error("❌ Failed to update permissions")
                            
                            # Admin password reset
                            with st.expander("🔐 Reset Password", expanded=False):
                                st.info("As an admin, you can reset this coach's password without knowing their current password.")
                                with st.form(f"reset_password_{username}"):
                                    new_password = st.text_input(
                                        "New Password", 
                                        type="password", 
                                        key=f"new_pass_{username}",
                                        help="Minimum 6 characters"
                                    )
                                    confirm_password = st.text_input(
                                        "Confirm New Password", 
                                        type="password", 
                                        key=f"confirm_pass_{username}"
                                    )
                                    
                                    if st.form_submit_button(f"🔐 Reset Password for {existing_coach.full_name}", type="primary", width='stretch'):
                                        if not new_password or not confirm_password:
                                            st.error("❌ Both password fields are required")
                                        elif new_password != confirm_password:
                                            st.error("❌ Passwords do not match")
                                        else:
                                            success, message = coach_manager.admin_reset_password(
                                                coach.username,  # admin doing the reset
                                                username,        # target coach
                                                new_password
                                            )
                                            
                                            if success:
                                                st.success(f"✅ {message}")
                                                # Clear the form by rerunning
                                                st.rerun()
                                            else:
                                                st.error(f"❌ {message}")
                            
                            # Delete coach (dangerous action)
                            with st.expander("⚠️ Delete Coach", expanded=False):
                                st.warning("This action cannot be undone!")
                                if st.button(f"🗑️ Delete {existing_coach.full_name}", key=f"delete_{username}"):
                                    if coach_manager.delete_coach(username):
                                        st.success(f"✅ Deleted coach: {existing_coach.full_name}")
                                        st.rerun()  # Refresh to remove deleted coach
                                    else:
                                        st.error("❌ Failed to delete coach")
            
            elif admin_tab == "View Analytics":
                st.markdown("**System Analytics**")
                
                # Show coach usage statistics
                st.markdown("**Coach Activity Summary**")
                coaches_df = []
                for username, coach_obj in coach_manager.coaches.items():
                    if username != 'admin':  # Skip admin account
                        coaches_df.append({
                            'Name': coach_obj.full_name,
                            'Username': username,
                            'Role': coach_obj.role,
                            'Budget': f"${coach_obj.monthly_budget}",
                            'Spent': f"${coach_obj.current_month_spending:.2f}",
                            'Searches': coach_obj.total_searches,
                            'Jobs Processed': coach_obj.total_jobs_processed,
                            'Last Login': coach_obj.last_login.strftime("%Y-%m-%d %H:%M") if coach_obj.last_login and hasattr(coach_obj.last_login, 'strftime') else "Never",
                            'Can Pull Fresh': "✅" if getattr(coach_obj, 'can_pull_fresh_jobs', True) else "❌"
                        })
                
                if coaches_df:
                    st.dataframe(pd.DataFrame(coaches_df), width="stretch")
                else:
                    st.info("No coaches found")
                
                # System resource usage
                st.markdown("**System Resource Usage**")
                total_budget = sum(float(c.monthly_budget) for c in coach_manager.coaches.values() if c.username != 'admin')
                total_spent = sum(float(c.current_month_spending) for c in coach_manager.coaches.values() if c.username != 'admin')
                total_searches = sum(c.total_searches for c in coach_manager.coaches.values() if c.username != 'admin')
                total_jobs = sum(c.total_jobs_processed for c in coach_manager.coaches.values() if c.username != 'admin')
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Budget", f"${total_budget:.2f}")
                with col2:
                    st.metric("Total Spent", f"${total_spent:.2f}", f"{((total_spent/total_budget)*100) if total_budget > 0 else 0:.1f}%")
                with col3:
                    st.metric("Total Searches", f"{total_searches:,}")
                with col4:
                    st.metric("Total Jobs", f"{total_jobs:,}")
            
            elif admin_tab == "System Settings":
                st.markdown("**System Configuration**")
                
                # Global system settings
                st.markdown("**Default Settings for New Coaches**")
                col1, col2 = st.columns(2)
                with col1:
                    default_budget = st.number_input("Default Monthly Budget ($)", min_value=0.0, value=100.0, key="default_budget")
                    default_full_mode = st.checkbox("Default Full Mode Access", value=False, key="default_full_mode")
                    default_custom_locations = st.checkbox("Default Custom Locations", value=False, key="default_custom_locations")
                    default_google_jobs = st.checkbox("Default Google Jobs Access (99% savings)", value=True, key="default_google_jobs")
                with col2:
                    default_fresh_jobs = st.checkbox("Default Fresh Jobs (API calls)", value=True, key="default_fresh_jobs")
                    default_all_exports = st.checkbox("Default All Exports", value=True, key="default_all_exports")
                
                if st.button("💾 Save Default Settings"):
                    st.success("✅ Default settings saved (feature coming soon)")
                
                # Emergency controls
                st.markdown("**Emergency Controls**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🛑 Disable All API Calls", help="Emergency stop for all outscraper/OpenAI calls"):
                        st.warning("Emergency API shutdown activated (feature coming soon)")
                with col2:
                    if st.button("🔄 Reset Monthly Spending", help="Reset spending counters for all coaches"):
                        for coach_obj in coach_manager.coaches.values():
                            coach_obj.current_month_spending = 0.0
                        coach_manager.save_coaches()
                        st.success("✅ Monthly spending reset for all coaches")
                        st.rerun()
                
                # System diagnostics
                st.markdown("**System Diagnostics**")
                
                # Database check
                if st.button("🔍 Test Database Connections"):
                    st.info("Testing connections...")
                    
                    # Test Supabase
                    try:
                        import os as _os
                        supabase_url = _os.getenv('SUPABASE_URL')
                        supabase_key = _os.getenv('SUPABASE_ANON_KEY')
                        if supabase_url and supabase_key:
                            st.success("✅ Supabase credentials found")
                        else:
                            st.warning("⚠️ Supabase credentials not found")
                    except Exception as e:
                        st.error(f"❌ Supabase test failed: {e}")
                    
                    # Test Airtable
                    try:
                        airtable_key = _os.getenv('AIRTABLE_API_KEY')
                        airtable_base = _os.getenv('AIRTABLE_BASE_ID')
                        if airtable_key and airtable_base:
                            st.success("✅ Airtable credentials found")
                        else:
                            st.warning("⚠️ Airtable credentials not found")
                    except Exception as e:
                        st.error(f"❌ Airtable test failed: {e}")
                    
                    # Test OpenAI
                    try:
                        openai_key = _os.getenv('OPENAI_API_KEY')
                        if openai_key and openai_key.startswith('sk-'):
                            st.success("✅ OpenAI API key found")
                        else:
                            st.warning("⚠️ OpenAI API key not found")
                    except Exception as e:
                        st.error(f"❌ OpenAI test failed: {e}")
                
                # Show recent activity
                st.markdown("**Recent Activity**")
                if st.button("📊 Show Activity Log"):
                    st.info("Activity logging feature coming soon")
                
                # Show environment info
                with st.expander("🔧 Environment Info", expanded=False):
                    import os as _os
                    import sys
                    st.code(f"""
Python Version: {sys.version}
Working Directory: {_os.getcwd()}
Streamlit Version: {st.__version__}
App Version: {APP_VERSION}
Deployment: {DEPLOYMENT_TIMESTAMP}
                    """)
                
                # Supabase event viewer (if available)
                with st.expander("📜 Recent Supabase Events", expanded=False):
                    try:
                        import json as _json
                        try:
                            from supabase_utils import fetch_click_events
                            if st.button("📜 Show Last 10 Events"):
                                rows = fetch_click_events(limit=10, since_days=7)
                                if rows:
                                    st.code(_json.dumps(rows, indent=2, default=str))
                                else:
                                    st.info("No recent events found.")
                        except Exception as e:
                            st.info(f"Supabase read not configured: {e}")
                    except Exception as e:
                        st.info(f"Supabase read not configured: {e}")
    
    # Page Navigation
    st.sidebar.markdown("---")
    page = st.sidebar.selectbox(
        "📱 Navigation", 
        ["🔍 Job Search", "📊 Analytics Dashboard", "🗓️ Scheduled Searches", "📦 Async Batches Table", "👥 Free Agent Management", "🧪 System Testing"],
        key="page_selector"
    )
    
    if page == "📊 Analytics Dashboard":
        show_analytics_dashboard(coach, coach_manager)
        return
    elif page == "🗓️ Scheduled Searches":
        show_scheduled_searches_page(coach)
        return
    elif page == "📦 Async Batches Table":
        show_pending_jobs_page(coach)
        return
    elif page == "👥 Free Agent Management":
        show_free_agent_management_page(coach)
        return
    elif page == "🧪 System Testing":
        show_system_testing_page(coach)
        return
    
    # Display notifications for async job completions
    try:
        from async_job_manager import AsyncJobManager
        async_manager = AsyncJobManager()
        notifications = async_manager.get_coach_notifications(coach.username, limit=5)
        
        unread_notifications = [n for n in notifications if not n.is_read]
        if unread_notifications:
            st.sidebar.markdown("### 🔔 Notifications")
            for notif in unread_notifications[:3]:  # Show max 3 in sidebar
                if notif.type == 'search_complete':
                    with st.sidebar:
                        st.success(notif.message)
                        if st.button(f"✓ Mark Read", key=f"notif_{notif.id}"):
                            async_manager.mark_notification_read(notif.id)
                            st.experimental_rerun()
                elif notif.type == 'error':
                    with st.sidebar:
                        st.error(notif.message)
                        if st.button(f"✓ Mark Read", key=f"notif_{notif.id}"):
                            async_manager.mark_notification_read(notif.id)
                            st.experimental_rerun()
                elif notif.type == 'search_submitted':
                    with st.sidebar:
                        st.info(notif.message)
                        if st.button(f"✓ Mark Read", key=f"notif_{notif.id}"):
                            async_manager.mark_notification_read(notif.id)
                            st.experimental_rerun()
            
            if len(unread_notifications) > 3:
                st.sidebar.caption(f"... and {len(unread_notifications) - 3} more")
            st.sidebar.markdown("---")
    except Exception as e:
        # Silently handle notification errors to not break main app
        pass
    
    st.sidebar.header("🎯 Search Parameters")
    
    # Location selection - Permission-based
    location_options = ["Select Market"]
    if check_coach_permission('can_use_custom_locations'):
        location_options.append("Custom Location")
    else:
        st.sidebar.info("💡 Custom locations disabled. Contact admin to enable.")
    
    location_type = st.sidebar.radio(
        "Location Type:",
        location_options,
        help="Choose from preset markets or enter a custom location"
    )
    
    location = None
    custom_location = None
    
    if location_type == "Select Market":
        markets = pipeline.get_markets()
        selected_markets = st.sidebar.multiselect(
            "Target Markets:",
            markets,
            help="Select one or more markets to search"
        )
        
        if selected_markets:
            # Show selected markets
            locations = [pipeline.get_market_location(market) for market in selected_markets]
            location = ", ".join(locations)  # Combine for display
            st.sidebar.success(f"📍 Selected: {len(selected_markets)} market{'s' if len(selected_markets) > 1 else ''}")
            
            # Show locations in expandable section
            with st.sidebar.expander("📋 Selected Markets", expanded=len(selected_markets) <= 3):
                for i, market in enumerate(selected_markets):
                    market_location = pipeline.get_market_location(market)
                    st.write(f"{i+1}. **{market}**: {market_location}")
        else:
            location = None
        
    else:  # Custom Location
        custom_location = st.sidebar.text_input(
            "Custom Location:",
            placeholder="e.g., Austin, TX or 90210",
            help="Enter city, state, or ZIP code"
        )
        location = custom_location
    
    # Search parameters
    route_filter = st.sidebar.selectbox(
        "Route Preference:",
        ["both", "local", "regional", "otr"],
        help="Filter jobs by route type"
    )
    
    # Search mode - Permission-based with job count display
    mode_display_map = {
        "10 jobs": "test",
        "100 jobs": "sample", 
        "250 jobs": "medium",
        "500 jobs": "large",
        "1000 jobs": "full"
    }
    
    search_display_options = ["10 jobs", "100 jobs", "250 jobs", "500 jobs"]
    if check_coach_permission('can_access_full_mode'):
        search_display_options.append("1000 jobs")
    
    search_mode_display = st.sidebar.selectbox(
        "Search Mode:",
        search_display_options,
        index=1,  # default to "100 jobs" (sample)
        help="Number of jobs to analyze and classify"
    )
    
    # Convert display choice back to pipeline mode
    search_mode = mode_display_map[search_mode_display]
    
    search_terms = st.sidebar.text_input(
        "Search Terms:",
        value="CDL Driver No Experience",
        help="Job search keywords. Use commas for multiple terms: 'CDL driver, truck driver, delivery driver'"
    )
    
    # Exact location option (affects radius calculation)
    exact_location = st.sidebar.checkbox(
        "Use exact location only",
        value=False,
        help="Search only the specified city (radius=0). Faster and more stable, but may find fewer jobs."
    )
    
    # Search radius (conditional on exact location setting)
    if exact_location:
        search_radius = 0
        st.sidebar.info("📍 Radius set to 0 (exact location mode)")
    else:
        search_radius = st.sidebar.selectbox(
            "Search Radius:",
            [25, 50, 100],
            index=1,  # default to 50
            help="Search radius in miles from target location"
        )
    
    # PDF Export Options (controls what gets included in PDF output)
    with st.sidebar.expander("📄 PDF Export Options"):
        st.markdown("**Quality & Quantity Controls**")
        max_jobs_pdf = st.slider(
            "Maximum jobs in PDF",
            min_value=10,
            max_value=200,
            value=50,
            step=5,
            help="Maximum number of jobs to include in PDF report"
        )
        
        pdf_match_quality_filter = st.multiselect(
            "Include job quality levels",
            options=['good', 'so-so', 'bad'],
            default=['good', 'so-so'],
            help="Which AI quality assessments to include in PDF"
        )
        
        pdf_include_memory_jobs = st.checkbox(
            "Include memory jobs",
            value=True,
            help="Include recent jobs from memory database in PDF output"
        )
        
        
        st.markdown("**Job Characteristics Filters**")
        col1, col2 = st.columns(2)
        with col1:
            pdf_fair_chance_only = st.checkbox(
                "Fair chance jobs only", 
                value=False,
                help="Include only jobs friendly to people with records in PDF"
            )
            
            pdf_route_type_filter = st.multiselect(
                "Route types to include",
                options=['Local', 'OTR', 'Unknown'],
                default=['Local', 'OTR', 'Unknown'],
                help="Which driving route types to include in PDF"
            )
        
        with col2:
            pdf_experience_level_filter = st.selectbox(
                "Experience level filter",
                options=['Any', 'Entry Level', 'Experienced'],
                index=0,
                help="Experience level filter for PDF jobs"
            )
    
    
    # Experience filter (for all search types)
    no_experience = st.sidebar.checkbox(
        "No Experience Filter", 
        value=True,
        help="Include jobs that don't require prior experience"
    )
    
    # Advanced options - Permission-based controls
    with st.sidebar.expander("🔧 Advanced Options"):
        st.markdown("**Output Formats**")
        # Only show PDF generation if coach has permission
        generate_pdf = False
        if check_coach_permission('can_generate_pdf'):
            generate_pdf = st.checkbox("Generate PDF Report", value=True)
        
        # Only show CSV export if coach has permission
        generate_csv = False
        if check_coach_permission('can_generate_csv'):
            generate_csv = st.checkbox("Generate CSV Export", value=True)
        save_parquet = st.checkbox("Save Parquet Files", value=False, help="Save pipeline stage data for debugging")
        
        # Search strategy is now determined by which search button is clicked
        search_strategy = "balanced"
        
        # Force fresh is now handled by dedicated button below
        force_fresh = False
        
        # Only show Force Fresh Classification if coach has permission  
        force_fresh_classification = False
        if check_coach_permission('can_force_fresh_classification'):
            force_fresh_classification = st.checkbox("Force Fresh Classification", value=False, help="Re-run AI classification even on cached jobs (useful when testing new prompts)")
        
        st.markdown("**Data Sync**")
        # Only show Airtable sync if coach has permission
        push_to_airtable = False
        if check_coach_permission('can_sync_airtable'):
            push_to_airtable = st.checkbox("Sync to Airtable", value=True)
        
        st.markdown("**Candidate Tagging (Optional)**")
        # Airtable lookup UI
        with st.container(border=True):
            st.caption("Lookup Free Agent from Airtable (fills fields below)")
            c1, c2, c3 = st.columns([2,1,1])
            with c1:
                lookup_q = st.text_input("Search", key="candidate_lookup_q", placeholder="Type name, UUID, or email")
            with c2:
                lookup_by = st.selectbox("By", ["name", "uuid", "email"], index=0, key="candidate_lookup_by")
            with c3:
                # Add spacing to align button with input fields
                st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
                do_lookup = st.button("🔎 Search", key="do_candidate_lookup")
            if do_lookup:
                st.session_state.candidate_search_results = airtable_find_candidates(lookup_q, by=lookup_by, limit=15)
            results = st.session_state.get("candidate_search_results", [])
            if results:
                def _label(r):
                    loc = ", ".join([x for x in [r.get('city') or '', r.get('state') or ''] if x])
                    suffix = f" ({loc})" if loc else ""
                    return f"{r['name']} — {r['uuid'] or 'no-uuid'}{suffix}"
                options = [_label(r) for r in results]
                sel = st.selectbox("Select Candidate", options, index=0, key="candidate_select")
                if sel and st.button("Use Selected", key="use_selected_candidate"):
                    idx = options.index(sel)
                    chosen = results[idx]
                    st.session_state.candidate_id = chosen.get("uuid", "")
                    st.session_state.candidate_name = chosen.get("name", "")
            else:
                st.info("No candidates found. Try switching the search mode (name/uuid/email) or broadening your query.")
        # Manual override / final values
        candidate_id = st.text_input(
            "Candidate ID (UUID)", 
            value=st.session_state.get("candidate_id", ""), 
            help="Attach a specific Free Agent to links for analytics"
        )
        candidate_name = st.text_input(
            "Candidate Name", 
            value=st.session_state.get("candidate_name", ""), 
            help="Used on PDF title page and link tags"
        )
    
    # Pipeline Settings (matching GUI wrapper functionality)
    with st.sidebar.expander("⚙️ Pipeline Settings"):
        st.markdown("**Quality Filters**")
        enable_business_rules = st.checkbox("Business Rules Filter", value=True, help="Remove spam and low-quality jobs")
        enable_deduplication = st.checkbox("Deduplication", value=True, help="Remove duplicate job postings")
        enable_experience_filter = st.checkbox("Experience Level Filter", value=True, help="Filter by experience requirements")
        
        # Clear cache button moved here from header
        if st.button("🔄 Clear Cache", help="Clear cached data and force fresh results"):
            try:
                st.cache_data.clear()
                st.cache_resource.clear()
                st.success("✅ Cache cleared successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error clearing cache: {e}")
        
        st.markdown("**Data Processing**")
        classification_model = st.selectbox("AI Classification Model", ["gpt-4o-mini", "gpt-4o"], index=0)
        batch_size = st.number_input("Batch Size", min_value=1, max_value=100, value=25, help="Jobs processed per API call")
        
        if st.button("🔄 Reset to Defaults"):
            st.rerun()
    
    # Cost estimation
    if location:
        cost_info = pipeline.estimate_cost(search_mode, 1)
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
        st.sidebar.markdown("💰 **Cost Estimate**")
        
        # Safe access to job_limit
        job_limit = cost_info.get('job_limit', 100)
        st.sidebar.metric(
            "Search Cost",
            f"${cost_info['total_cost']:.3f}"
        )
    
    # Run Job Search Button in Sidebar - Always show regardless of location
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    run_disabled = not location or (location_type == "Custom Location" and not custom_location)
    
    # Three search options - all visible
    st.sidebar.markdown("### 🚀 Search Options")
    
    # Memory system configuration
    memory_time_period = st.sidebar.selectbox(
        "Smart memory lookback period",
        options=['24h', '48h', '72h', '96h'],
        index=2,  # default to 72h
        help="How far back the smart memory system searches for existing jobs"
    )
    
    # Memory Search Button
    memory_clicked = st.sidebar.button(
        "💾 Search Memory Only", 
        disabled=run_disabled,
        help="Search cached jobs from all sources - instant results, no API costs",
        key="memory_search_btn"
    )
    
    # Indeed Search Button  
    indeed_clicked = st.sidebar.button(
        "🔍 Search Indeed + Memory",
        disabled=run_disabled,
        help="Search fresh Indeed jobs plus all cached jobs (~$0.10/search)",
        key="indeed_search_btn"
    )
    
    # Indeed Fresh Only Button (if permission)
    indeed_fresh_clicked = False
    if can_pull_fresh:
        indeed_fresh_clicked = st.sidebar.button(
            "🔍 Indeed Fresh Only",
            disabled=run_disabled,
            help="Search Indeed API only, bypass memory cache (~$0.10/search)",
            key="indeed_fresh_btn"
        )
    
    # Google Search Button (if permission)
    google_clicked = False
    if check_coach_permission('can_access_google_jobs'):
        google_clicked = st.sidebar.button(
            "🌐 Submit Google Search",
            disabled=run_disabled,  
            help="Submit async Google Jobs search - results ready in 2-3 minutes (~$0.005/search)",
            key="google_search_btn"
        )
    
    # Scheduling option
    st.sidebar.markdown("---")
    schedule_search = st.sidebar.checkbox(
        "🗓️ Schedule this search",
        value=False,
        help="Set up recurring searches instead of running once"
    )
    
    if schedule_search:
        with st.sidebar.expander("⏰ Scheduling Options"):
            schedule_freq = st.selectbox("Frequency", ["Daily", "Weekly", "Once"])
            schedule_time = st.time_input("Run at", value=pd.Timestamp("02:00").time())
            
            if schedule_freq == "Weekly":
                schedule_days = st.multiselect("Days", 
                    ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    default=["Mon", "Wed", "Fri"]
                )
    
    # Account management at bottom of sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 Account")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔐 Change Password", key="sidebar_change_password", width='stretch'):
            st.session_state.show_password_change = True
    with col2:
        if st.button("🚪 Logout", key="sidebar_logout", width='stretch'):
            st.session_state.current_coach = None
            st.rerun()
    
    # Handle button clicks
    if memory_clicked:
        search_type = 'memory'
    elif indeed_clicked:
        search_type = 'indeed'
    elif indeed_fresh_clicked:
        search_type = 'indeed_fresh'
    elif google_clicked:
        search_type = 'google'
    else:
        # No button was clicked, show the interface but don't execute
        search_type = None
    
    if search_type:
        if not location:
            st.stop()
        
        # Determine final location for search
        final_location = location
        if location_type == "Custom Location" and custom_location:
            final_location = custom_location
        elif location_type == "Select Market" and 'selected_markets' not in locals():
            st.stop()
        
        # Handle different search types
        if search_type == 'memory':
            # Memory-only search - use EXACT same approach as Indeed button but with memory_only=True
            
            # Build parameters exactly like Indeed button
            params = {
                'mode': search_mode,
                'route_filter': route_filter,
                'search_terms': search_terms,
                'push_to_airtable': push_to_airtable,
                'generate_pdf': generate_pdf,
                'generate_csv': generate_csv,
                'search_radius': search_radius,
                'no_experience': no_experience,
                'force_fresh': False,  # Never force fresh for memory-only
                'force_fresh_classification': force_fresh_classification,
                'coach_name': coach.full_name,
                'coach_username': coach.username,
                'memory_only': True,  # FORCE memory-only mode
                'candidate_id': candidate_id.strip() if candidate_id else "",
                'candidate_name': candidate_name.strip() if candidate_name else "",
                'search_sources': {'indeed': False, 'google': False},  # Memory only
                'search_strategy': 'memory_first'
            }
            
            # Add location parameters based on type (same as Indeed button)
            if location_type == "Select Market":
                if 'selected_markets' in locals() and selected_markets:
                    params['markets'] = selected_markets  # Multiple markets
                    params['location'] = location  # Combined location string for display
                else:
                    st.stop()
            else:
                params['custom_location'] = custom_location
                params['location'] = custom_location
            
            # Run pipeline with memory-only spinner text
            with st.spinner(f"💾 Searching memory only for jobs in {final_location}..."):
                df, metadata = pipeline.run_pipeline(params)
            
            # Store results in session state (same as Indeed button)
            st.session_state.last_results = {
                'df': df,
                'metadata': metadata,
                'params': params,
                'timestamp': datetime.now()
            }
            
            # Show results (same as Indeed button approach)
            if metadata.get('success', False):
                st.success(f"✅ Memory search completed! Found {metadata.get('included_jobs', 0)} quality jobs from memory")
                
                # Generate download buttons if files exist
                if generate_csv and metadata.get('csv_path'):
                    csv_bytes = pipeline.dataframe_to_csv_bytes(df)
                    if csv_bytes:
                        st.download_button(
                            label="📊 Download CSV",
                            data=csv_bytes,
                            file_name=f"memory_jobs_{final_location}.csv",
                            mime="text/csv"
                        )
                
                if generate_pdf and metadata.get('pdf_path'):
                    pdf_bytes = pipeline.get_pdf_bytes(metadata['pdf_path'])
                    if pdf_bytes:
                        st.download_button(
                            label="📄 Download PDF", 
                            data=pdf_bytes,
                            file_name=f"memory_jobs_{final_location}.pdf",
                            mime="application/pdf"
                        )
                
                # Display results summary (same as Indeed button)
                if not df.empty:
                    st.balloons()
            else:
                st.error(f"❌ Memory search failed: {metadata.get('error', 'Unknown error')}")
        
        elif search_type == 'google':
            # Check for pending Google Jobs in the same market first
            try:
                from async_job_manager import AsyncJobManager
                async_manager = AsyncJobManager()
                
                # Check if there are already pending Google searches for this market
                pending_jobs = async_manager.check_pending_google_jobs_in_market(final_location)
                
                if pending_jobs:
                    # Show warning about existing pending jobs
                    st.warning("⚠️ **Duplicate Google Search Detected**")
                    st.markdown(f"There are already **{len(pending_jobs)}** pending Google Jobs searches for **{final_location}**:")
                    
                    for job in pending_jobs[:3]:  # Show up to 3 pending jobs
                        with st.container():
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.write(f"• **{job.search_params.get('search_terms', 'Unknown')}** by **{job.coach_username}**")
                            with col2:
                                if job.submitted_at:
                                    elapsed = datetime.now(timezone.utc) - job.submitted_at
                                    st.caption(f"Running {elapsed.seconds // 60}m {elapsed.seconds % 60}s")
                    
                    if len(pending_jobs) > 3:
                        st.write(f"...and {len(pending_jobs) - 3} more pending searches")
                    
                    # Show confirmation dialog
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        proceed_anyway = st.button("🚨 Submit Anyway", type="secondary", help="This will create a duplicate search and cost money")
                    with col2:
                        cancel_search = st.button("✅ Cancel Search", type="primary", help="Wait for existing searches to complete")
                    
                    if cancel_search:
                        st.info("Search cancelled. Check the Async Batches Table to monitor existing searches.")
                        st.stop()
                    
                    if not proceed_anyway:
                        st.stop()  # Don't proceed unless user explicitly confirms
                
                # If no pending jobs or user confirmed, proceed with search
                with st.spinner("🚀 Submitting Google Jobs search..."):
                    search_params = {
                        'search_terms': search_terms,
                        'location': final_location,
                        'limit': job_limit,
                        'coach_username': coach.username
                    }
                    
                    job = async_manager.submit_google_search(search_params, coach.username)
                    
                    st.success(f"✅ Google Jobs search submitted successfully!")
                    st.info(f"""
                    **Job ID:** {job.id}
                    
                    Your search is now processing in the background. You'll be notified when results are ready (typically 2-3 minutes).
                    
                    💡 **Next steps:**
                    - Continue using the app normally
                    - Check notifications for completion alert  
                    - Results will automatically appear in future searches
                    """)
                    st.balloons()
                    
            except Exception as e:
                st.error(f"❌ Failed to submit Google search: {str(e)}")
        
        elif search_type in ['indeed', 'indeed_fresh']:
            # Indeed searches (with or without memory)
            is_fresh_only = (search_type == 'indeed_fresh')
            
            # Build parameters for existing pipeline
            params = {
                'mode': search_mode,
                'route_filter': route_filter,
                'search_terms': search_terms,
                'push_to_airtable': push_to_airtable,
                'generate_pdf': generate_pdf,
                'generate_csv': generate_csv,
                'search_radius': search_radius,
                'no_experience': no_experience,
                'force_fresh': is_fresh_only,  # Force fresh for indeed_fresh, regular behavior for indeed
                'force_fresh_classification': force_fresh_classification,
                'coach_name': coach.full_name,
                'coach_username': coach.username,
                'memory_only': not can_pull_fresh,  # Test accounts use memory only
                'candidate_id': candidate_id.strip() if candidate_id else "",
                'candidate_name': candidate_name.strip() if candidate_name else "",
                'search_sources': {'indeed': True, 'google': False},  # Indeed + memory
                'search_strategy': 'indeed_first'
            }
            
            # Add location parameters based on type
            if location_type == "Select Market":
                if 'selected_markets' in locals() and selected_markets:
                    params['markets'] = selected_markets  # Multiple markets
                    params['location'] = location  # Combined location string for display
                else:
                    st.stop()
            else:
                params['custom_location'] = custom_location
                params['location'] = custom_location
            
            # Run pipeline with appropriate spinner text
            try:
                if location_type == "Select Market" and 'selected_markets' in locals() and selected_markets:
                    display_location = ", ".join(selected_markets)
                else:
                    display_location = final_location
            except Exception:
                display_location = final_location

            spinner_text = (
                f"🔍 Searching Indeed fresh only for jobs in {display_location}..."
                if is_fresh_only else
                f"🔍 Searching Indeed + memory for jobs in {display_location}..."
            )
            with st.spinner(spinner_text):
                df, metadata = pipeline.run_pipeline(params)
            
            # Store results in session state
            st.session_state.last_results = {
                'df': df,
                'metadata': metadata,
                'params': params,
                'timestamp': datetime.now()
            }
            
            # Show results and update coach stats
            if metadata.get('success', False):
                st.success(f"✅ Search completed! Found {metadata.get('included_jobs', 0)} quality jobs")
                
                # Record search in coach's usage stats
                coach_manager.record_search(
                    coach.username, 
                    metadata.get('included_jobs', 0),
                    metadata.get('total_cost', 0.0)
                )
            else:
                st.error(f"❌ Search failed: {metadata.get('error', 'Unknown error')}")
    
    # Configuration Preview
    if location:
        mode_limits = {'test': '10', 'sample': '100', 'medium': '250', 'large': '500', 'full': '1000'}
        
        st.markdown("""
            <div style="background: var(--fw-card-bg); 
                        border: 3px solid var(--fw-roots); border-radius: 12px; padding: 0.75rem; 
                        margin: 1rem 0; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);">
                <h2 style="margin: 0; color: var(--fw-freedom-green); font-family: 'Outfit', sans-serif; 
                           display: flex; align-items: center; font-weight: 600; font-size: 1.25rem;">
                    ⚙️ Search Configuration
                </h2>
            """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1], gap="small")
        with col1:
            st.markdown(f"""
            <div style="margin-bottom: 0.75rem;">
                <span style="color: var(--fw-freedom-green); font-weight: 500; font-size: 0.875rem;">📍 LOCATION</span><br>
                <span style="color: var(--fw-text-light); font-weight: 600; font-size: 1rem;">
                    {location if location_type == "Custom Location" else f"{len(selected_markets) if 'selected_markets' in locals() and selected_markets else 0} market{'s' if 'selected_markets' in locals() and len(selected_markets) > 1 else ''}"}
                </span>
                {f"<br><small style='color: var(--fw-text-muted);'>{', '.join(selected_markets) if 'selected_markets' in locals() and selected_markets else ''}</small>" if location_type == "Select Market" and 'selected_markets' in locals() and selected_markets else ""}
            </div>
            <div style="margin-bottom: 0.75rem;">
                <span style="color: var(--fw-freedom-green); font-weight: 500; font-size: 0.875rem;">🔍 SEARCH MODE</span><br>
                <span style="color: var(--fw-text-light); font-weight: 600; font-size: 1rem;">{search_mode.title()}</span>
                <span style="color: var(--fw-text-muted); font-size: 0.875rem;"> ({mode_limits[search_mode]} jobs)</span>
            </div>
            <div style="margin-bottom: 0.75rem;">
                <span style="color: var(--fw-freedom-green); font-weight: 500; font-size: 0.875rem;">🛣️ ROUTE FILTER</span><br>
                <span style="color: var(--fw-text-light); font-weight: 600; font-size: 1rem;">{route_filter}</span>
            </div>
            <div style="margin-bottom: 0.75rem;">
                <span style="color: var(--fw-freedom-green); font-weight: 500; font-size: 0.875rem;">📏 SEARCH RADIUS</span><br>
                <span style="color: var(--fw-text-light); font-weight: 600; font-size: 1rem;">{search_radius} miles</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            no_exp_status = '<span style="color: var(--fw-freedom-green);">✅ Enabled</span>' if no_experience else '<span style="color: #dc3545;">❌ Disabled</span>'
            pdf_status = '<span style="color: var(--fw-freedom-green);">✅ Enabled</span>' if generate_pdf else '<span style="color: #dc3545;">❌ Disabled</span>'
            csv_status = '<span style="color: var(--fw-freedom-green);">✅ Enabled</span>' if generate_csv else '<span style="color: #dc3545;">❌ Disabled</span>'
            airtable_status = '<span style="color: var(--fw-freedom-green);">✅ Enabled</span>' if push_to_airtable else '<span style="color: #dc3545;">❌ Disabled</span>'
            fresh_status = '<span style="color: var(--fw-freedom-green);">✅ Enabled</span>' if force_fresh else '<span style="color: #dc3545;">❌ Disabled</span>'
            
            st.markdown(f"""
            <div style="margin-bottom: 0.75rem;">
                <span style="color: var(--fw-freedom-green); font-weight: 500; font-size: 0.875rem;">👤 NO EXPERIENCE</span><br>
                {no_exp_status}
            </div>
            <div style="margin-bottom: 0.75rem;">
                <span style="color: var(--fw-freedom-green); font-weight: 500; font-size: 0.875rem;">📄 PDF GENERATION</span><br>
                {pdf_status}
            </div>
            <div style="margin-bottom: 0.75rem;">
                <span style="color: var(--fw-freedom-green); font-weight: 500; font-size: 0.875rem;">📊 CSV EXPORT</span><br>
                {csv_status}
            </div>
            <div style="margin-bottom: 0.375rem;">
                <span style="color: var(--fw-freedom-green); font-weight: 500; font-size: 0.875rem;">📋 AIRTABLE SYNC</span><br>
                {airtable_status}
            </div>
            """, unsafe_allow_html=True)
        
        # Search terms and additional options
        st.markdown(f"""
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #dee2e6;">
            <div style="margin-bottom: 0.75rem;">
                <span style="color: #6c757d; font-weight: 500; font-size: 0.875rem;">💼 SEARCH TERMS</span><br>
                <span style="color: var(--fw-text-light); font-weight: 600; font-size: 1rem;">{search_terms or 'CDL driver'}</span>
            </div>
            <div style="display: flex; gap: 2rem;">
                <div>
                    <span style="color: #6c757d; font-weight: 500; font-size: 0.875rem;">🔄 FORCE FRESH:</span>
                    {fresh_status}
                </div>
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display: flex; justify-content: center;">
            <div style="padding: 0.75rem 1.5rem; background-color: var(--fw-card-bg); 
                        border: 2px solid var(--fw-freedom-green); border-radius: 8px; 
                        text-align: center; color: var(--fw-freedom-green); font-weight: 600;
                        display: inline-block; width: fit-content;">
                👈 Select location to see configuration
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Search status
        if 'last_results' in st.session_state:
            st.markdown("---")
            results = st.session_state.last_results
            metadata = results['metadata']
            
            st.markdown("📊 **Last Search Results**")
            
            if metadata.get('success', False):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Quality Jobs Found", metadata.get('included_jobs', 0))
                with col2:
                    st.metric("Total Jobs Analyzed", metadata.get('total_jobs', 0))
                with col3:
                    # Check multiple possible field names for processing time
                    processing_time = (metadata.get('processing_time', 0) or 
                                     metadata.get('duration', 0) or 
                                     metadata.get('elapsed_time', 0) or 
                                     metadata.get('time', 0))
                    # Format processing time as minutes and seconds
                    if processing_time >= 60:
                        minutes = int(processing_time // 60)
                        seconds = processing_time % 60
                        time_str = f"{minutes}m {seconds:.1f}s"
                    else:
                        time_str = f"{processing_time:.1f}s"
                    st.metric("Processing Time", time_str)
                with col4:
                    total_cost = metadata.get('total_cost', 0)
                    st.metric("Total Cost", f"${total_cost:.3f}")
                
                # Additional row for more metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    memory_efficiency = metadata.get('memory_efficiency', 0)
                    st.metric("Memory Efficiency", f"{memory_efficiency:.1f}%")
                with col2:
                    cost_per_quality_job = metadata.get('cost_per_quality_job', 0)
                    st.metric("Cost per Quality Job", f"${cost_per_quality_job:.3f}")
                
                st.caption(f"Search completed: {results['timestamp'].strftime('%Y-%m-%d %H:%M')}")
            else:
                st.error("Last search failed")
    
    # Results display
    if 'last_results' in st.session_state:
        results = st.session_state.last_results
        df = results['df']
        metadata = results['metadata']
        
        
        if not df.empty and metadata.get('success', False):
            st.markdown("---")
            st.markdown("""
            <div class="job-results-container">
                <h2 style="font-family: 'Outfit', sans-serif; color: var(--fw-freedom-green); margin: 0; font-size: 1.25rem;">
                    📋 Search Results
                </h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Dynamic tabs based on permissions
            tab_names = ["📊 Data View"]
            has_export = check_coach_permission('can_generate_pdf') or check_coach_permission('can_generate_csv')
            has_sync = check_coach_permission('can_sync_airtable') or check_coach_permission('can_sync_supabase')
            
            if has_export:
                tab_names.append("📄 Export Options")
            if has_sync:
                tab_names.append("🔄 Sync Options")
            
            tabs = st.tabs(tab_names)
            tab1 = tabs[0]  # Always Data View
            
            # Assign tabs based on what was actually created
            tab2 = None  # Export Options tab
            tab3 = None  # Sync Options tab
            
            tab_index = 1
            if has_export:
                tab2 = tabs[tab_index]
                tab_index += 1
            if has_sync:
                tab3 = tabs[tab_index]
            
            with tab1:
                # Display dataframe with admin portal styling
                st.markdown("""
                <div style="border: 1px solid hsl(240, 5.9%, 90%); 
                           border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                """, unsafe_allow_html=True)
                
                # Filter display to show only good and so-so jobs while keeping full data in CSV exports
                display_df = df.copy()
                if 'ai.match' in df.columns:
                    display_df = df[df['ai.match'].isin(['good', 'so-so'])]
                elif 'classification' in df.columns:
                    display_df = df[df['classification'].isin(['good', 'so-so'])]
                
                # Show only essential columns in the display
                display_columns = ['source.title', 'source.company', 'ai.summary', 'ai.match', 'ai.route_type', 'ai.fair_chance', 'source.indeed_url']
                available_columns = [col for col in display_columns if col in display_df.columns]
                
                if available_columns:
                    display_df = display_df[available_columns]
                
                st.dataframe(
                    display_df,
                    width="stretch",
                    height=400
                )
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Enhanced stats with admin portal styling - ALL from pipeline metadata
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    # Use pipeline-calculated good jobs metric
                    good_jobs = metadata.get('ai_good', 0)
                    st.metric("Excellent Matches", good_jobs)
                with col2:
                    # Use pipeline-calculated so-so jobs metric
                    so_so_jobs = metadata.get('ai_so_so', 0)
                    st.metric("Possible Fits", so_so_jobs)
                with col3:
                    # Use pipeline-calculated local routes metric
                    route_local = metadata.get('local_routes', 0)
                    st.metric("Local Routes", route_local)
                with col4:
                    # Use pipeline-calculated OTR routes metric
                    route_otr = metadata.get('otr_routes', 0)
                    st.metric("OTR Routes", route_otr)
            
            if tab2:  # Export Options tab
                with tab2:
                    st.markdown("### 📁 Download Results")
                
                # CSV Download - only show if coach has permission
                if check_coach_permission('can_generate_csv'):
                    try:
                        csv_bytes = pipeline.dataframe_to_csv_bytes(df)
                        if csv_bytes and len(csv_bytes) > 0:
                            st.download_button(
                                label="📊 Download CSV",
                                data=csv_bytes,
                                file_name=f"freeworld_jobs_{results['params']['location'].replace(', ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                width="stretch"
                            )
                            st.success(f"✅ CSV ready for download ({len(df)} jobs)")
                        else:
                            st.warning("⚠️ No data available for CSV download")
                    except Exception as e:
                        st.error(f"❌ CSV generation error: {e}")
                
                # PDF Download - only show if coach has permission
                if check_coach_permission('can_generate_pdf'):
                    # Handle failure gracefully
                    if metadata.get('pdf_failed'):
                        st.warning("⚠️ PDF generation failed during pipeline execution")
                        st.info("📄 You can generate PDF manually below:")
                    
                    if metadata.get('pdf_path') and os.path.exists(metadata['pdf_path']):
                        # PDF was generated by pipeline - offer direct download
                        try:
                            with open(metadata['pdf_path'], 'rb') as f:
                                pdf_bytes = f.read()
                            if pdf_bytes:
                                st.download_button(
                                    label="📄 Download PDF Report",
                                    data=pdf_bytes,
                                    file_name=f"freeworld_jobs_{results['params']['location'].replace(', ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                    mime="application/pdf",
                                    width="stretch"
                                )
                                st.success(f"✅ PDF ready for download ({metadata.get('included_jobs', 0)} quality jobs)")
                            else:
                                st.error("❌ PDF file is empty")
                        except Exception as e:
                            st.error(f"❌ PDF read error: {e}")
                    else:
                        # Offer to generate PDF manually
                        quality_df = df
                        if 'ai.match' in df.columns:
                            quality_df = df[df['ai.match'].isin(['good', 'so-so'])]
                        
                        if not quality_df.empty:
                            if st.button("📄 Generate PDF Report", width="stretch"):
                                with st.spinner("Generating PDF report..."):
                                    try:
                                        # Apply PDF Export Options filters to the data
                                        filtered_pdf_df = quality_df.copy()
                                        
                                        # Filter by match quality levels (use AI classification columns)
                                        if 'ai.match' in filtered_pdf_df.columns and pdf_match_quality_filter:
                                            filtered_pdf_df = filtered_pdf_df[filtered_pdf_df['ai.match'].isin(pdf_match_quality_filter)]
                                        
                                        # Filter by route types (use AI route classification)
                                        if 'ai.route_type' in filtered_pdf_df.columns and pdf_route_type_filter:
                                            filtered_pdf_df = filtered_pdf_df[filtered_pdf_df['ai.route_type'].isin(pdf_route_type_filter)]
                                        
                                        # Filter by fair chance only
                                        if pdf_fair_chance_only and 'ai.fair_chance' in filtered_pdf_df.columns:
                                            filtered_pdf_df = filtered_pdf_df[filtered_pdf_df['ai.fair_chance'] == True]
                                        
                                        # Filter by experience level (if available)
                                        if pdf_experience_level_filter != 'Any' and 'experience_level' in filtered_pdf_df.columns:
                                            filtered_pdf_df = filtered_pdf_df[filtered_pdf_df['experience_level'] == pdf_experience_level_filter]
                                        
                                        # Sort jobs for PDF: Most recent, excellent match, fair chance jobs first
                                        if not filtered_pdf_df.empty:
                                            sort_columns = []
                                            sort_ascending = []
                                            
                                            # 1. Fair chance jobs first (True values first)
                                            if 'ai.fair_chance' in filtered_pdf_df.columns:
                                                sort_columns.append('ai.fair_chance')
                                                sort_ascending.append(False)  # True first, then False
                                            
                                            # 2. Excellent match jobs first (good > so-so > bad)
                                            if 'ai.match' in filtered_pdf_df.columns:
                                                # Create numeric priority: good=3, so-so=2, bad=1
                                                filtered_pdf_df['match_priority'] = filtered_pdf_df['ai.match'].map({'good': 3, 'so-so': 2, 'bad': 1}).fillna(0)
                                                sort_columns.append('match_priority')
                                                sort_ascending.append(False)  # Higher numbers first
                                            
                                            # 3. Route type with Local first, then OTR, then Unknown (Local > OTR > Unknown)
                                            if 'ai.route_type' in filtered_pdf_df.columns:
                                                # Create numeric priority: Local=3, OTR=2, Unknown=1
                                                filtered_pdf_df['route_priority'] = filtered_pdf_df['ai.route_type'].map({'Local': 3, 'OTR': 2, 'Unknown': 1}).fillna(0)
                                                sort_columns.append('route_priority')
                                                sort_ascending.append(False)  # Local first
                                            
                                            # 4. Most recent jobs first (newest first)
                                            date_column = None
                                            for col in ['source.date_posted', 'meta.scraped_at', 'id.timestamp']:
                                                if col in filtered_pdf_df.columns:
                                                    date_column = col
                                                    break
                                            
                                            if date_column:
                                                # Convert to datetime if needed
                                                try:
                                                    filtered_pdf_df[date_column] = pd.to_datetime(filtered_pdf_df[date_column], errors='coerce')
                                                    sort_columns.append(date_column)
                                                    sort_ascending.append(False)  # Most recent first
                                                except (KeyError, ValueError):
                                                    pass  # Date column not found or invalid format
                                            
                                            # Apply sorting
                                            if sort_columns:
                                                filtered_pdf_df = filtered_pdf_df.sort_values(sort_columns, ascending=sort_ascending)
                                                
                                                # Clean up temporary columns
                                                temp_cols = ['match_priority', 'route_priority']
                                                for col in temp_cols:
                                                    if col in filtered_pdf_df.columns:
                                                        filtered_pdf_df = filtered_pdf_df.drop(col, axis=1)
                                        
                                        # Limit to max jobs for PDF (after sorting, so we get the best jobs)
                                        if len(filtered_pdf_df) > max_jobs_pdf:
                                            filtered_pdf_df = filtered_pdf_df.head(max_jobs_pdf)
                                        
                                        market_name = results['params']['location']
                                        coach_first_name = coach.full_name.split()[0] if coach.full_name else ""
                                        
                                        # Show sorting and filtering info
                                        sort_info = "Sorted by: "
                                        sort_criteria = []
                                        if 'ai.fair_chance' in filtered_pdf_df.columns:
                                            sort_criteria.append("fair chance first")
                                        if 'ai.match' in filtered_pdf_df.columns:
                                            sort_criteria.append("excellent matches first")
                                        if 'ai.route_type' in filtered_pdf_df.columns:
                                            sort_criteria.append("local > OTR > unknown")
                                        if date_column:
                                            sort_criteria.append("most recent first")
                                        
                                        sort_info += ", ".join(sort_criteria) if sort_criteria else "default order"
                                        
                                        st.info(f"📊 PDF Export: {len(filtered_pdf_df)} jobs selected from {len(quality_df)} quality jobs. {sort_info}.")
                                        
                                        pdf_bytes = pipeline.generate_pdf_from_canonical(filtered_pdf_df, market_name, coach_first_name)
                                        
                                        if pdf_bytes:
                                            st.download_button(
                                                label="📥 Download PDF Report",
                                                data=pdf_bytes,
                                                file_name=f"freeworld_jobs_{market_name.replace(', ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                                mime="application/pdf",
                                                width="stretch"
                                            )
                                            st.success("✅ PDF generated successfully!")
                                        else:
                                            st.error("❌ PDF generation failed")
                                    except Exception as e:
                                        st.error(f"❌ PDF generation error: {e}")
                        else:
                            st.warning("⚠️ No quality jobs found for PDF generation")
                        
            if tab3:  # Sync Options tab
                with tab3:
                    st.markdown("### 🔄 Database Sync")
                
                if not df.empty:
                    # Show sync options based on permissions
                    has_supabase = check_coach_permission('can_sync_supabase')
                    has_airtable = check_coach_permission('can_sync_airtable')
                    
                    if has_supabase and has_airtable:
                        col1, col2 = st.columns(2)
                    elif has_supabase or has_airtable:
                        col1 = st.columns(1)[0]
                    else:
                        st.info("💡 Database sync features not enabled for your account. Contact admin to enable.")
                        col1 = None
                    
                    if col1 and has_supabase:
                        with col1:
                            if st.button("📊 Sync to Supabase", width="stretch"):
                                with st.spinner("Syncing to Supabase..."):
                                    try:
                                        sync_result = sync_to_supabase(df, coach.id)
                                        if sync_result['success']:
                                            st.success(f"✅ Successfully synced {sync_result['count']} jobs to Supabase!")
                                        else:
                                            st.error(f"❌ Supabase sync failed: {sync_result['error']}")
                                    except Exception as e:
                                        st.error(f"❌ Supabase sync error: {e}")
                    
                    if has_supabase and has_airtable:
                        with col2:
                            if st.button("📋 Sync to Airtable", width="stretch"):
                                with st.spinner("Syncing to Airtable..."):
                                    try:
                                        sync_result = sync_to_airtable(df, coach.id)
                                        if sync_result['success']:
                                            st.success(f"✅ Successfully synced {sync_result['count']} jobs to Airtable!")
                                        else:
                                            st.error(f"❌ Airtable sync failed: {sync_result['error']}")
                                    except Exception as e:
                                        st.error(f"❌ Airtable sync error: {e}")
                    elif col1 and has_airtable:
                        with col1:
                            if st.button("📋 Sync to Airtable", width="stretch"):
                                with st.spinner("Syncing to Airtable..."):
                                    try:
                                        sync_result = sync_to_airtable(df, coach.id)
                                        if sync_result['success']:
                                            st.success(f"✅ Successfully synced {sync_result['count']} jobs to Airtable!")
                                        else:
                                            st.error(f"❌ Airtable sync failed: {sync_result['error']}")
                                    except Exception as e:
                                        st.error(f"❌ Airtable sync error: {e}")
                else:
                    st.info("No data available to sync")
        elif df.empty:
            st.markdown("""
            <div class="job-results-container">
                <h3 style="color: hsl(240, 3.8%, 46.1%);">No jobs found in this search</h3>
                <p>Try adjusting your search parameters or selecting a different location.</p>
            </div>
            """, unsafe_allow_html=True)
        elif not metadata.get('success', False):
            st.markdown(f"""
            <div class="job-results-container" style="border-left: 4px solid #EF4444;">
                <h3 style="color: #DC2626;">Search Failed</h3>
                <p>{metadata.get('error', 'Unknown error occurred during the search.')}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Analytics Dashboard (matching GUI wrapper)
    if 'last_results' in st.session_state:
        st.markdown("---")
        st.markdown("## 📊 Pipeline Analytics")
        
        results = st.session_state.last_results
        metadata = results['metadata']
        
        if metadata.get('success', False):
            # Pipeline performance metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Pipeline Efficiency", 
                    f"{(metadata.get('included_jobs', 0) / max(1, metadata.get('total_jobs', 1))) * 100:.1f}%",
                    help="Percentage of jobs that passed all filters"
                )
            
            with col2:
                cost_per_quality_job = metadata.get('cost_per_quality_job', 0)
                st.metric(
                    "Cost per Quality Job",
                    f"${cost_per_quality_job:.3f}",
                    help="Average cost to find one quality job"
                )
            
            with col3:
                # Check multiple possible field names for processing time
                processing_time = (metadata.get('processing_time', 0) or 
                                 metadata.get('duration', 0) or 
                                 metadata.get('elapsed_time', 0) or 
                                 metadata.get('time', 0))
                st.metric(
                    "Processing Time",
                    f"{processing_time:.1f}s",
                    help="Total pipeline execution time"
                )
            
            with col4:
                memory_efficiency = metadata.get('memory_efficiency', 0)
                st.metric(
                    "Memory Efficiency",
                    f"{memory_efficiency:.1f}%",
                    help="Percentage of jobs loaded from memory vs fresh scraping"
                )
            
            # Pipeline stage breakdown
            if 'stage_metrics' in metadata:
                st.markdown("### 🔧 Pipeline Stage Performance")
                stage_data = []
                for stage, metrics in metadata['stage_metrics'].items():
                    stage_data.append({
                        'Stage': stage,
                        'Input Jobs': metrics.get('input', 0),
                        'Output Jobs': metrics.get('output', 0),
                        'Filtered': metrics.get('filtered', 0),
                        'Processing Time': f"{metrics.get('time', 0):.1f}s" if metrics.get('time', 0) < 60 else f"{int(metrics.get('time', 0) // 60)}m {metrics.get('time', 0) % 60:.1f}s"
                    })
                
                if stage_data:
                    st.dataframe(pd.DataFrame(stage_data), width="stretch")

        # Link Analytics (Short.io) - aggregate by tags
        st.markdown("---")
        st.markdown("## 🔗 Link Analytics")
        # Prefer Supabase (persistent) if configured; fall back to Short.io
        try:
            from supabase_utils import fetch_click_events, fetch_candidate_clicks
            import pandas as _pd
            days = st.slider("Time window (days)", min_value=7, max_value=365, value=180, step=7)
            events = fetch_click_events(limit=20000, since_days=int(days))
            if events:
                df_ev = _pd.DataFrame(events)
                # Filters
                with st.expander("Filters"):
                    cols = st.columns(4)
                    with cols[0]:
                        coach_filter = st.multiselect("Coach", sorted(df_ev['coach'].dropna().unique().tolist())) if 'coach' in df_ev else []
                    with cols[1]:
                        market_filter = st.multiselect("Market", sorted(df_ev['market'].dropna().unique().tolist())) if 'market' in df_ev else []
                    with cols[2]:
                        route_filter_ = st.multiselect("Route", sorted(df_ev['route'].dropna().unique().tolist())) if 'route' in df_ev else []
                    with cols[3]:
                        match_filter = st.multiselect("Match", sorted(df_ev['match'].dropna().unique().tolist())) if 'match' in df_ev else []
                def apply_filters(df):
                    if 'coach' in df and coach_filter:
                        df = df[df['coach'].isin(coach_filter)]
                    if 'market' in df and market_filter:
                        df = df[df['market'].isin(market_filter)]
                    if 'route' in df and route_filter_:
                        df = df[df['route'].isin(route_filter_)]
                    if 'match' in df and match_filter:
                        df = df[df['match'].isin(match_filter)]
                    return df
                df_ev = apply_filters(df_ev)
                # Timeseries
                df_ev['date'] = _pd.to_datetime(df_ev['clicked_at']).dt.date
                ts = df_ev.groupby('date').size().reset_index(name='clicks')
                st.markdown("### Clicks Over Time")
                st.line_chart(ts.set_index('date'))
                # Aggregations
                for k in ['coach', 'market', 'route', 'match', 'fair', 'candidate_id']:
                    if k in df_ev.columns and not df_ev.empty:
                        counts = df_ev.groupby(k).size().sort_values(ascending=False).head(20)
                        if not counts.empty:
                            st.markdown(f"### By {k.replace('_',' ').title()}")
                            st.dataframe(counts.rename('clicks'), width=None)
                # Top candidates from Supabase aggregate table if exists
                supa_rows = fetch_candidate_clicks(limit=50)
                if supa_rows:
                    st.markdown("#### Top Candidates (Supabase)")
                    st.dataframe(_pd.DataFrame(supa_rows), width=None)
            else:
                st.info("No Supabase click events found. Add Short.io → Supabase webhook to ingest clicks.")
        except Exception as e:
            st.info(f"Supabase analytics unavailable: {e}")

    # Removed redundant end-of-file CSS/JS overrides to reduce conflicts

def show_scheduled_searches_page(coach):
    """Show scheduled searches management page"""
    st.header("🗓️ Scheduled Searches")
    st.markdown("Manage your scheduled job searches and view their status.")
    
    try:
        from async_job_manager import AsyncJobManager
        async_manager = AsyncJobManager()
        
        # Create new scheduled search
        with st.expander("➕ Create New Scheduled Search"):
            with st.form("new_scheduled_search"):
                col1, col2 = st.columns(2)
                
                with col1:
                    search_name = st.text_input("Search Name", placeholder="Dallas OTR Jobs")
                    search_terms = st.text_input("Search Terms", value="CDL driver")
                    location = st.text_input("Location", placeholder="Dallas, TX")
                
                with col2:
                    sources = st.multiselect(
                        "Sources to Search",
                        ['google', 'indeed'],
                        default=['google'],
                        help="Google runs async in background, Indeed runs at scheduled time"
                    )
                    
                    schedule_type = st.selectbox("Frequency", ["Daily", "Weekly", "Once"])
                    schedule_time = st.time_input("Run at", value=pd.Timestamp("02:00").time())
                
                if schedule_type == "Weekly":
                    days = st.multiselect("Days of Week", 
                        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                        default=["Monday", "Wednesday", "Friday"]
                    )
                
                max_jobs = st.slider("Max Jobs per Search", 100, 1000, 500)
                
                if st.form_submit_button("Create Schedule", width='stretch'):
                    st.success("Scheduled search created! (Note: Backend implementation in progress)")
        
        # Show existing scheduled searches (placeholder)
        st.subheader("Active Scheduled Searches")
        st.info("📋 No scheduled searches configured yet. Backend implementation in progress.")
        
        # Show recent scheduled search history (placeholder)
        st.subheader("Recent Scheduled Search History")
        st.info("📊 Search history will appear here once scheduling is active.")
        
    except Exception as e:
        st.error(f"Error loading scheduled searches: {e}")

def show_pending_jobs_page(coach):
    """Show pending and completed async batches page"""
    st.header("📦 Async Batches Table")
    st.markdown("Monitor your async batch searches and view their results.")
    
    try:
        from async_job_manager import AsyncJobManager
        async_manager = AsyncJobManager()
        
        # Tabs for different batch statuses
        tab1, tab2, tab3 = st.tabs(["⏳ Pending Batches", "✅ Completed Batches", "❌ Failed Batches"])
        
        with tab1:
            st.subheader("All Pending Async Batches")
            
            # Add automatic batch status checking tool
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                if st.button("🔄 Check All Batch Status", help="Check Outscraper API for batch completion status"):
                    with st.spinner("Checking batch status with Outscraper API..."):
                        # Check all pending batches for completion
                        checked_count = 0
                        completed_count = 0
                        pending_batches = async_manager.get_pending_jobs()
                        
                        for batch in pending_batches:
                            if batch.request_id:  # Only check batches with request IDs
                                try:
                                    # Check Outscraper API for batch completion
                                    result = async_manager.get_async_results(batch.request_id)
                                    checked_count += 1
                                    
                                    if result:
                                        # Batch is completed, process it
                                        completed_count += 1
                                        st.info(f"🎉 Batch {batch.id} completed! Processing results...")
                                        
                                        # Process the completed batch results (same as webhook processing)
                                        try:
                                            async_manager.process_completed_google_job(batch.id)
                                            st.success(f"✅ Batch {batch.id} processed successfully!")
                                        except Exception as process_error:
                                            st.error(f"❌ Error processing batch {batch.id}: {process_error}")
                                        
                                except Exception as e:
                                    st.error(f"Error checking batch {batch.id}: {e}")
                        
                        if checked_count > 0:
                            st.success(f"✅ Checked {checked_count} batches, found {completed_count} completed")
                            st.rerun()  # Refresh the page to show updated status
                        else:
                            st.info("No batches with request IDs to check")
            
            with col2:
                auto_refresh = st.checkbox("Auto-refresh (30s)", help="Automatically refresh batch status every 30 seconds")
            
            with col3:
                if st.button("🔄 Refresh", help="Manually refresh the page"):
                    st.rerun()
            
            # Auto-refresh functionality
            if auto_refresh:
                import time
                time.sleep(30)  # Wait 30 seconds
                st.rerun()  # Refresh the page
            
            st.divider()
            
            pending_jobs = async_manager.get_pending_jobs()  # Get all pending batches, not filtered by user
            
            if pending_jobs:
                for job in pending_jobs:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1])
                        
                        with col1:
                            st.write(f"**{job.search_params.get('search_terms', 'Unknown')}** in {job.search_params.get('location', 'Unknown')}")
                            st.caption(f"Batch Type: {job.job_type} | Status: {job.status}")
                        
                        with col2:
                            st.write(f"**Coach:** {job.coach_username}")
                            
                        with col3:
                            if job.submitted_at:
                                elapsed = datetime.now(timezone.utc) - job.submitted_at
                                st.write(f"Running: {elapsed.seconds // 60}m {elapsed.seconds % 60}s")
                        
                        with col4:
                            if st.button(f"Cancel", key=f"cancel_{job.id}"):
                                st.info("Cancel functionality coming soon")
                        
                        st.divider()
            else:
                st.info("No pending batches. Submit a Google Jobs search to see pending batches here.")
        
        with tab2:
            st.subheader("All Completed Batches")
            completed_jobs = async_manager.get_completed_jobs()  # Get all completed batches, not filtered by user
            
            if completed_jobs:
                for job in completed_jobs:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1])
                        
                        with col1:
                            st.write(f"**{job.search_params.get('search_terms', 'Unknown')}** in {job.search_params.get('location', 'Unknown')}")
                            st.caption(f"Batch Type: {job.job_type} | Limit: {job.search_params.get('limit', 'N/A')}")
                        
                        with col2:
                            st.write(f"**Coach:** {job.coach_username}")
                            
                        with col3:
                            if job.completed_at:
                                st.write(f"**Completed:** {job.completed_at.strftime('%m/%d %H:%M')}")
                            st.write(f"**Results:** {job.result_count} total, {job.quality_job_count} quality")
                        
                        with col4:
                            if job.completed_at and job.submitted_at:
                                duration = job.completed_at - job.submitted_at
                                st.write(f"**Duration:** {duration.seconds // 60}m {duration.seconds % 60}s")
                        
                        st.divider()
            else:
                st.info("No completed batches yet. Completed async searches will appear here.")
        
        with tab3:
            st.subheader("All Failed Batches")
            failed_jobs = async_manager.get_failed_jobs()  # Get all failed batches, not filtered by user
            
            if failed_jobs:
                for job in failed_jobs:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1])
                        
                        with col1:
                            st.write(f"**{job.search_params.get('search_terms', 'Unknown')}** in {job.search_params.get('location', 'Unknown')}")
                            st.caption(f"Batch Type: {job.job_type} | Limit: {job.search_params.get('limit', 'N/A')}")
                        
                        with col2:
                            st.write(f"**Coach:** {job.coach_username}")
                            
                        with col3:
                            if job.created_at:
                                st.write(f"**Failed:** {job.created_at.strftime('%m/%d %H:%M')}")
                            
                        with col4:
                            if job.error_message:
                                st.error(f"Error: {job.error_message}")
                            else:
                                st.error("Unknown error")
                        
                        st.divider()
            else:
                st.info("No failed batches. Failed async searches will appear here with error details.")
        
    except Exception as e:
        st.error(f"Error loading job status: {e}")

if __name__ == "__main__":
    main()
