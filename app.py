
"""
FreeWorld Success Coach Portal - QA/STAGING ENVIRONMENT  
Complete fresh start to bypass Streamlit Cloud import caching
DEPLOYMENT VERSION: September 5, 2025 - Tab navigation complete fix - CACHE BUST
CACHE_BUSTER_ID: tab_complete_fix_force_rebuild_c9f3d06
"""

# === IMPORTS ===
# AGGRESSIVE CACHE BUST - Import cache buster to force rebuild
from CACHE_BUSTER import CACHE_BUST_VERSION, FORCE_REBUILD_TOKEN
print(f"🔥 FORCE REBUILD ACTIVE: {CACHE_BUST_VERSION}")

import streamlit as st

# === AGGRESSIVE CACHE CLEARING (copied from main app) ===
# Prevent infinite rerun loops by clearing only once per session
if not st.session_state.get("_cleared_startup_cache_once"):
    try:
        st.cache_data.clear()
        print("🧹 Cleared st.cache_data on startup")
    except Exception:
        pass
    try:
        st.cache_resource.clear()
        print("🧹 Cleared st.cache_resource on startup")
    except Exception:
        pass
    st.session_state["_cleared_startup_cache_once"] = True
    print("🚀 Cache clearing completed - fresh session")

# === CACHE BUSTER ===
# Clear all Streamlit caches on app startup to ensure fresh deployment
CACHE_VERSION = "supabase_filter_fix_v2_262d9f9_sept5_AGGRESSIVE_CLEAR"

@st.cache_data
def get_cache_version():
    """Returns cache version to force cache invalidation on deployment"""
    return CACHE_VERSION

# Force cache clearing on version change
current_version = get_cache_version()
if 'cache_version' not in st.session_state or st.session_state.cache_version != current_version:
    st.cache_data.clear()
    st.cache_resource.clear() 
    st.session_state.cache_version = current_version
    print(f"🔄 Cache cleared for version: {current_version}")

# Add QA environment banner at the very top
st.markdown("""
<div style="background-color: #FF6B6B; color: white; padding: 10px; text-align: center; font-weight: bold; margin-bottom: 20px;">
    🧪 QA/STAGING ENVIRONMENT - This is a test version for safely testing changes before production
</div>
""", unsafe_allow_html=True)

# === IMPORTS CONTINUED ===
from app_utils import (
    filter_quality_jobs, 
    calculate_search_metrics, 
    generate_pdf_from_dataframe,
    display_market_section,
    process_search_results,
    get_ordered_markets,
    debug_dataframe_info
)

# === SHARED CONSTANTS (prevent duplication) ===
# Mode display mappings - used throughout the app
MODE_DISPLAY_MAP = {
    "10 jobs": "test",
    "50 jobs": "mini", 
    "100 jobs": "sample",
    "250 jobs": "medium",
    "500 jobs": "large",
    "1000 jobs": "full"
}

MODE_DISPLAY_OPTIONS = ["10 jobs", "50 jobs", "100 jobs", "250 jobs", "500 jobs"]

MODE_LIMITS = {
    'test': '10', 
    'mini': '50', 
    'sample': '100', 
    'medium': '250', 
    'large': '500', 
    'full': '1000'
}

# --- IMPORTANT: Configure page FIRST to avoid Streamlit API errors ---
import os
from pathlib import Path
import re
import streamlit as st
try:
    # Call set_page_config as the first Streamlit command with proper favicon
    page_icon = "🚛"  # fallback
    try:
        from PIL import Image
        import os
        # Try to load FW logo for favicon
        logo_paths = [
            "data/fw_logo.png",
            "data/FW-Logo-Roots@2x.png", 
            "assets/FW-Logo-Roots.svg"
        ]
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    page_icon = Image.open(logo_path)
                    break
                except Exception:
                    continue
    except Exception:
        pass
    
    # Set QA-specific favicon
    try:
        from PIL import Image
        qa_favicon = Image.open("fw_logo.png")
    except:
        qa_favicon = "🧪"  # Fallback emoji for QA
    
    st.set_page_config(
        page_title="FreeWorld QA Portal - Test Environment", 
        page_icon=qa_favicon, 
        layout="wide", 
        initial_sidebar_state="expanded"
    )
    # Mark configured to prevent later duplicate calls
    st.session_state["_page_configured"] = True
except Exception:
    # If Streamlit isn't fully initialized (e.g., when imported by tests), ignore
    pass

# --- CACHE KILL-SWITCH (moved below set_page_config to prevent rerun loop issues) ---
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Bootstrap: mirror Streamlit secrets into os.environ so modules using os.getenv can work locally
def _bootstrap_secrets_to_env():
    try:
        for k, v in st.secrets.items():
            # Top-level simple values
            if isinstance(v, (str, int, float, bool)) or v is None:
                os.environ.setdefault(str(k), "" if v is None else str(v))
            elif isinstance(v, dict):
                # Flatten nested tables with upper-case child keys
                for kk, vv in v.items():
                    if vv is None:
                        continue
                    os.environ.setdefault(f"{k}_{str(kk).upper()}", str(vv))
                    os.environ.setdefault(str(kk).upper(), str(vv))
    except Exception:
        # st.secrets may not be available in certain contexts (tests)
        pass

_bootstrap_secrets_to_env()

# Kill-switch via env var or URL query param
force_clear = os.getenv("CLEAR_CACHE") == "1"


try:
    # Streamlit 1.30+ query params API
    params = st.query_params
    qp_clear = params.get("clear") == "1"
except Exception:
    # Fallback - no query params
    qp_clear = False

if force_clear or qp_clear:
    # Prevent infinite rerun loops by clearing only once per session
    if not st.session_state.get("_cleared_startup_cache_once"):
        try:
            st.cache_data.clear()
        except Exception:
            pass
        try:
            st.cache_resource.clear()
        except Exception:
            pass
        st.session_state["_cleared_startup_cache_once"] = True
        st.rerun()

# --- end kill-switch ---

import pandas as pd
from datetime import datetime, timezone, timedelta
import base64
import time

# Import cache utilities
try:
    from cache_utils import clear_all_caches_and_refresh, safe_cache_data
except ImportError:
    # Fallback if cache_utils doesn't exist yet
    def clear_all_caches_and_refresh():
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
    safe_cache_data = st.cache_data
from pathlib import Path
from unittest.mock import MagicMock
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
        except:
            pass
except Exception as e:
    # Fallback to .env loading for local development
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass

# Force cache refresh - increment this to clear caches on deployment
APP_VERSION = "2.3.8-security-token-sync"
DEPLOYMENT_TIMESTAMP = "2025-09-01-14-15"
BUILD_COMMIT = "429a7f2"  # Security + Sync implementation

# Auto cache-bust detection
import hashlib
BUILD_HASH = hashlib.md5(f"{APP_VERSION}-{DEPLOYMENT_TIMESTAMP}-{BUILD_COMMIT}".encode()).hexdigest()[:8]

# Global pipeline wrapper import
_PIPELINE_WRAPPER_CLASS = None
try:
    from pipeline_wrapper import StreamlitPipelineWrapper
    _PIPELINE_WRAPPER_CLASS = StreamlitPipelineWrapper
except ImportError as e:
    import streamlit as st
    st.error(f"❌ Failed to import pipeline_wrapper: {e}")
    st.info("🔧 This appears to be a deployment issue. Try refreshing the page or contact support.")
    st.stop()
from user_management import get_coach_manager, check_coach_permission, require_permission, get_current_coach_name

# Import new analytics modules
from src.coach_analytics import get_coach_performance_metrics, generate_weekly_performance_report, get_coach_comparison_data

# HTML PDF preview functionality
try:
    from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html
except ImportError:
    jobs_dataframe_to_dicts = None
    render_jobs_html = None

def wrap_html_in_phone_screen(html_content: str) -> str:
    """Wrap HTML content in a phone screen container for preview only."""
    return f"""
    <div style="
        display: flex;
        justify-content: center;
        align-items: flex-start;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    ">
        <div style="
            width: 375px;
            max-width: 100%;
            background: #000;
            border-radius: 25px;
            padding: 8px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            position: relative;
        ">
            <!-- Phone notch -->
            <div style="
                position: absolute;
                top: 8px;
                left: 50%;
                transform: translateX(-50%);
                width: 120px;
                height: 25px;
                background: #000;
                border-radius: 15px;
                z-index: 10;
            "></div>
            
            <!-- Phone screen -->
            <div style="
                background: #fff;
                border-radius: 20px;
                overflow: hidden;
                height: 812px;
                overflow-y: auto;
                position: relative;
                -webkit-overflow-scrolling: touch;
            ">
                <!-- Status bar -->
                <div style="
                    height: 44px;
                    background: #fff;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0 20px;
                    font-size: 14px;
                    font-weight: 600;
                    color: #000;
                    border-bottom: 1px solid #e5e7eb;
                ">
                    <span>9:41</span>
                    <div style="display: flex; gap: 4px; align-items: center;">
                        <div style="width: 18px; height: 10px; border: 1px solid #000; border-radius: 2px; position: relative;">
                            <div style="width: 14px; height: 6px; background: #000; border-radius: 1px; position: absolute; top: 1px; left: 1px;"></div>
                        </div>
                        <span style="font-size: 12px;">100%</span>
                    </div>
                </div>
                
                <!-- Content -->
                <div style="
                    padding: 0;
                    height: calc(812px - 44px);
                    overflow-y: auto;
                ">
                    {html_content}
                </div>
            </div>
        </div>
    </div>
    """

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
    except:
        return None

def generate_secure_portal_token(agent_uuid: str) -> str:
    """Generate secure token for agent portal access"""
    import hashlib
    return hashlib.md5(f"{agent_uuid}:FreeWorld2025".encode()).hexdigest()[:12]

def create_secure_portal_link(base_url: str, agent_uuid: str, agent_data: dict = None) -> str:
    """Create secure portal link with token validation and search parameters"""
    token = generate_secure_portal_token(agent_uuid)
    url = f"{base_url}?agent={agent_uuid}&token={token}"
    
    # Add search parameters if agent data is provided
    if agent_data:
        # Add market/location
        if agent_data.get('location'):
            url += f"&location={agent_data['location']}"
        
        # Add route preference (handle both parameter names)
        route_filter = agent_data.get('route_filter') or agent_data.get('route_type_filter')
        if route_filter:
            url += f"&route={route_filter}"
            
        # Add experience level
        if agent_data.get('experience_level'):
            url += f"&experience={agent_data['experience_level']}"
            
        # Add job limit if specified
        if agent_data.get('max_jobs'):
            url += f"&limit={agent_data['max_jobs']}"
            
        # Add fair chance preference
        if agent_data.get('fair_chance_only'):
            url += f"&fair_chance=true"
    
    return url

def generate_dynamic_portal_link(agent_data: dict) -> str:
    """Generate a dynamic portal link based on current agent search preferences"""
    from free_agent_system import generate_agent_url
    agent_uuid = agent_data.get('agent_uuid', '')
    if not agent_uuid:
        return "Missing UUID - Cannot generate secure link"
    return generate_agent_url(agent_uuid, agent_data)

# Page config (already set at file top). Compute an icon for later use if needed.
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

# Ensure sidebar toggle is always visible - safety override
st.markdown("""
<style>
/* Hide sidebar permanently */
header { visibility: visible !important; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
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
        background: var(--fw-freedom-green);
        color: hsl(240, 10%, 3.9%);
        border-color: var(--fw-freedom-green);
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
/* Target multiselect tag text content */
span[data-baseweb="tag"],
span[data-baseweb="tag"] span {
    color: var(--fw-midnight) !important;
}

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
    # pandas already imported globally
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
        coach_options = [getattr(c, 'full_name', c.username) for c in coach_manager.coaches.values() if hasattr(c, 'username') and c.username != 'admin']
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

    # Fetch click events based on filters
    st.markdown("### 📈 Overall Click Metrics")
    
    # Determine start and end dates for fetching
    end_date = datetime.now(timezone.utc)
    if date_range == "Custom range":
        start_date = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_date = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
    else:
        start_date = end_date - timedelta(days=since_days)

    # Fetch all click events within the date range
    all_clicks_df = fetch_click_events(start_date, end_date)

    if all_clicks_df.empty:
        st.info("No click data available for the selected period and filters.")
        return

    # Apply coach filter
    if coach_filter == "My Free Agents":
        all_clicks_df = all_clicks_df[all_clicks_df['coach_username'] == coach.username]
    elif coach_filter == "Specific Coach" and selected_coach:
        # Need to map selected_coach name back to username
        target_coach_username = next(
            (
                c.username
                for c in coach_manager.coaches.values()
                if hasattr(c, 'username')
                and getattr(c, 'full_name', getattr(c, 'username', None)) == selected_coach
            ),
            None,
        )
        if target_coach_username:
            all_clicks_df = all_clicks_df[all_clicks_df['coach_username'] == target_coach_username]
        else:
            st.warning(f"Could not find username for selected coach: {selected_coach}")
            all_clicks_df = pd.DataFrame() # Empty dataframe if coach not found
    # Admin View (All) means no filter needed

    # Apply Free Agent search filter
    if airtable_matches:
        matched_uuids = [m['uuid'] for m in airtable_matches if m['uuid']]
        if matched_uuids:
            all_clicks_df = all_clicks_df[all_clicks_df['candidate_id'].isin(matched_uuids)]
        else:
            all_clicks_df = pd.DataFrame() # No UUIDs from search, so no clicks

    if all_clicks_df.empty:
        st.info("No click data available after applying Free Agent filters.")
        return

    total_clicks = len(all_clicks_df)
    unique_clicks = all_clicks_df['click_id'].nunique()
    unique_agents = all_clicks_df['candidate_id'].nunique()
    unique_jobs = all_clicks_df['target_url'].nunique()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Clicks", total_clicks)
    with col2:
        st.metric("Unique Clicks", unique_clicks)
    with col3:
        st.metric("Unique Free Agents", unique_agents)
    with col4:
        st.metric("Unique Jobs Clicked", unique_jobs)

    st.markdown("### 📊 Click Activity Over Time")
    # Group by date and count clicks
    clicks_over_time = all_clicks_df.groupby(all_clicks_df['timestamp'].dt.date).size().reset_index(name='clicks')
    clicks_over_time.columns = ['Date', 'Clicks']
    st.line_chart(clicks_over_time, x='Date', y='Clicks')

    st.markdown("### 🔝 Top Clicked Jobs")
    top_jobs = all_clicks_df['target_url'].value_counts().reset_index(name='clicks')
    top_jobs.columns = ['Job URL', 'Clicks']
    st.dataframe(top_jobs.head(10), width="stretch")

    st.markdown("### 👥 Free Agent Engagement")
    # Aggregate clicks by candidate
    agent_engagement = all_clicks_df.groupby('candidate_id').agg(
        total_clicks=('click_id', 'count'),
        unique_jobs_clicked=('target_url', 'nunique')
    ).reset_index()

    # Try to get agent names from Airtable matches if available, otherwise use UUID
    if airtable_matches:
        uuid_to_name = {m['uuid']: m['name'] for m in airtable_matches if m['uuid']}
        agent_engagement['Agent Name'] = agent_engagement['candidate_id'].map(uuid_to_name).fillna(agent_engagement['candidate_id'])
    else:
        agent_engagement['Agent Name'] = agent_engagement['candidate_id']
    
    agent_engagement = agent_engagement.sort_values(by='total_clicks', ascending=False)
    st.dataframe(agent_engagement, width="stretch")

    st.markdown("### 📋 Raw Click Data")
    st.dataframe(all_clicks_df, width="stretch")

    # --- New: Coach Performance Analytics ---
    st.markdown("### 📊 Coach Performance Analytics")
    st.markdown("Track your performance and compare with other coaches.")

    # Date range selector for coach analytics
    coach_analytics_end_date = st.date_input("Coach Analytics End Date", value=datetime.now(), key="coach_analytics_end_date")
    coach_analytics_start_date = st.date_input("Coach Analytics Start Date", value=coach_analytics_end_date - timedelta(days=30), key="coach_analytics_start_date")

    # Convert to datetime objects with timezone info
    start_dt_coach = datetime.combine(coach_analytics_start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt_coach = datetime.combine(coach_analytics_end_date, datetime.max.time(), tzinfo=timezone.utc)

    # Get current coach's performance metrics
    st.subheader(f"Your Performance ({coach.full_name})")
    my_metrics = get_coach_performance_metrics(coach.username, start_dt_coach, end_dt_coach)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Clicks", my_metrics.get("total_clicks", 0))
    with col2:
        st.metric("Unique Agents Engaged", my_metrics.get("unique_agents_engaged", 0))
    with col3:
        st.metric("Avg Clicks/Agent", f"{my_metrics.get('avg_clicks_per_agent', 0.0):.1f}")
    with col4:
        st.metric("Job Quality Breakdown", f"Good: {my_metrics.get('job_quality_breakdown', {}).get('good', 0)}")

    st.subheader("Coach Comparison")
    all_coach_usernames = [c.username for c in coach_manager.coaches.values() if c.username != 'admin']
    selected_coaches_for_comparison = st.multiselect(
        "Select Coaches to Compare",
        options=all_coach_usernames,
        default=[coach.username] if coach.username in all_coach_usernames else [],
        key="coach_comparison_select"
    )

    if selected_coaches_for_comparison:
        comparison_data = get_coach_comparison_data(selected_coaches_for_comparison, start_dt_coach, end_dt_coach)
        comparison_df = pd.DataFrame([
            {
                "Coach": coach_manager.coaches.get(u, MagicMock(full_name=u)).full_name,
                "Total Clicks": data.get("total_clicks", 0),
                "Unique Agents": data.get("unique_agents_engaged", 0),
                "Avg Clicks/Agent": f"{data.get('avg_clicks_per_agent', 0.0):.1f}",
                "Good Jobs Clicked": data.get("job_quality_breakdown", {}).get('good', 0)
            }
            for u, data in comparison_data["coaches"].items()
        ])
        st.dataframe(comparison_df, width="stretch")

    st.subheader("Weekly Performance Report (Example)")
    if st.button("Generate Weekly Report for Me", key="generate_my_weekly_report"):
        weekly_report = generate_weekly_performance_report(coach.username)
        st.json(weekly_report)

    # --- New: Free Agent Engagement Insights ---
    st.markdown("### 👥 Free Agent Engagement Insights")
    st.markdown("Analyze engagement patterns and preferences of your Free Agents.")

    # Date range selector for engagement insights
    engagement_end_date = st.date_input("Engagement End Date", value=datetime.now(), key="engagement_end_date")
    engagement_start_date = st.date_input("Engagement Start Date", value=engagement_end_date - timedelta(days=30), key="engagement_start_date")

    start_dt_engagement = datetime.combine(engagement_start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt_engagement = datetime.combine(engagement_end_date, datetime.max.time(), tzinfo=timezone.utc)

    # Filter by coach if needed
    engagement_coach_filter = st.selectbox(
        "Filter Engagement by Coach",
        ["All Coaches", coach.full_name] + [getattr(c, 'full_name', c.username) for c in coach_manager.coaches.values() if hasattr(c, 'username') and c.username != 'admin' and c.username != coach.username],
        key="engagement_coach_filter"
    )
    selected_engagement_coach_username = None
    if engagement_coach_filter != "All Coaches":
        selected_engagement_coach_username = next((c.username for c in coach_manager.coaches.values() if hasattr(c, 'full_name') and getattr(c, 'full_name', c.username) == engagement_coach_filter), coach.username)

    engagement_insights = get_free_agent_engagement_insights(start_dt_engagement, end_dt_engagement, coach_username=selected_engagement_coach_username)

    col_eng1, col_eng2, col_eng3 = st.columns(3)
    with col_eng1:
        st.metric("Total Engagement Clicks", engagement_insights.get("total_clicks", 0))
    with col_eng2:
        st.metric("Unique Engaged Agents", engagement_insights.get("unique_agents", 0))
    with col_eng3:
        st.metric("Avg Clicks/Agent", f"{engagement_insights.get('avg_clicks_per_agent', 0.0):.1f}")

    st.subheader("Engagement Clicks Over Time")
    clicks_over_time = engagement_insights.get("clicks_over_time")
    if clicks_over_time:
        clicks_df = None
        if isinstance(clicks_over_time, dict):
            clicks_df = pd.DataFrame({
                'Date': list(clicks_over_time.keys()),
                'clicks': list(clicks_over_time.values())
            })
        else:
            tmp_df = pd.DataFrame(clicks_over_time)
            # Find plausible date and clicks columns regardless of casing/naming
            date_col = next((c for c in tmp_df.columns if str(c).lower() in ('date', 'day', 'timestamp')), None)
            clicks_col = next((c for c in tmp_df.columns if str(c).lower() in ('clicks', 'count', 'value')), None)
            if date_col and clicks_col:
                clicks_df = tmp_df.rename(columns={date_col: 'Date', clicks_col: 'clicks'})[['Date', 'clicks']]
        if clicks_df is not None and not clicks_df.empty:
            clicks_df['Date'] = pd.to_datetime(clicks_df['Date'], errors='coerce')
            clicks_df = clicks_df.dropna(subset=['Date'])
            if not clicks_df.empty:
                st.line_chart(clicks_df, x='Date', y='clicks')
            else:
                st.info("No dated engagement data to plot.")
        else:
            st.info("No engagement time series available.")

    st.subheader("Top Engaged Agents")
    if engagement_insights.get("top_agents_by_clicks"):
        top_agents_df = pd.DataFrame(engagement_insights["top_agents_by_clicks"])
        st.dataframe(top_agents_df, width="stretch")

    st.subheader("Geographic Engagement (by Market)")
    if engagement_insights.get("geographic_engagement"):
        geo_df = pd.DataFrame(list(engagement_insights["geographic_engagement"].items()), columns=['Market', 'Clicks'])
        st.dataframe(geo_df, width="stretch")

    st.subheader("Job Category Preference")
    if engagement_insights.get("top_job_categories"):
        cat_df = pd.DataFrame(list(engagement_insights["top_job_categories"].items()), columns=['Category', 'Clicks'])
        st.dataframe(cat_df, width="stretch")

    st.subheader("Engagement Patterns (Hourly/Daily)")
    col_pat1, col_pat2 = st.columns(2)
    with col_pat1:
        st.write("Clicks by Hour of Day")
        if engagement_insights.get("engagement_patterns", {}).get("clicks_by_hour"):
            hour_df = pd.DataFrame(list(engagement_insights["engagement_patterns"]["clicks_by_hour"].items()), columns=['Hour', 'Clicks'])
            st.bar_chart(hour_df, x='Hour', y='Clicks')
    with col_pat2:
        st.write("Clicks by Day of Week")
        if engagement_insights.get("engagement_patterns", {}).get("clicks_by_day_of_week"):
            day_df = pd.DataFrame(list(engagement_insights["engagement_patterns"]["clicks_by_day_of_week"].items()), columns=['Day', 'Clicks'])
            # Map day numbers to names for better readability
            day_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
            day_df['Day'] = day_df['Day'].map(day_map)
            st.bar_chart(day_df, x='Day', y='Clicks')

    # --- New: Business Intelligence Reports ---
    st.markdown("### 📈 Business Intelligence Reports")
    st.markdown("Generate comprehensive reports on program effectiveness.")


def show_free_agent_management_page(coach):
    """Show Free Agent Management page with inline editable agent table"""
    # Ensure we have access to the latest coach manager data
    from user_management import get_coach_manager
    coach_manager = get_coach_manager()
    from free_agent_system import (
        save_agent_profile, load_agent_profiles, load_agent_profiles_with_stats, delete_agent_profile, 
        get_agent_click_stats, get_all_agents_click_stats, encode_agent_params, get_market_options
    )
    
    st.header("👥 Free Agent Management")
    st.markdown("*Configure job searches for your Free Agents and manage their custom job feeds*")
    
    # Analytics settings section
    with st.expander("📊 Analytics Settings", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            lookback_days = st.number_input(
                "Click data lookback period (days)", 
                min_value=1, 
                max_value=365, 
                value=st.session_state.get('analytics_lookback_days', 14),
                help="How many days back to look for click activity"
            )
        with col2:
            st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Update Analytics", key="update_analytics_btn"):
                st.session_state['analytics_lookback_days'] = lookback_days
                st.success(f"Analytics updated to {lookback_days} days lookback")
                st.rerun()
    
    # Get current lookback setting
    current_lookback = st.session_state.get('analytics_lookback_days', 14)
    
    # Add New Agent Section
    with st.expander("➕ Add New Free Agent", expanded=False):
        st.markdown("### Airtable Lookup")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            lookup_query = st.text_input("Search Airtable", placeholder="Name, UUID, or email", key="agent_lookup")
        with col2:
            lookup_by = st.selectbox("Search by", ["name", "uuid", "email"], key="agent_lookup_by")
        with col3:
            st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
            search_button = st.button("🔎 Search", key="agent_search_btn")
        
        # Store search results in session state to persist across reruns
        if search_button and lookup_query:
            try:
                results = airtable_find_candidates(lookup_query, by=lookup_by, limit=10)
                st.session_state['search_results'] = results
                if results:
                    st.success(f"Found {len(results)} candidate(s)")
                else:
                    st.warning("No candidates found. Try a different search term or method.")
            except Exception as e:
                st.error(f"Airtable search error: {e}")
                st.session_state['search_results'] = []
        
        # Display results if we have them
        if st.session_state.get('search_results'):
            results = st.session_state['search_results']
            
            # Display results for selection
            agent_options = []
            for r in results:
                loc_str = f"{r.get('city', '')} {r.get('state', '')}".strip()
                location_part = f" ({loc_str})" if loc_str else ""
                agent_options.append(f"{r['name']} — {r['uuid'][:8] if r['uuid'] else 'no-uuid'}{location_part}")
            
            selected_agent = st.selectbox("Select Agent", agent_options, key="agent_select")
            
            # Add agent button with debugging
            if st.button("Add Selected Agent", key="add_agent_btn", type="primary"):
                if selected_agent:
                    try:
                        idx = agent_options.index(selected_agent)
                        chosen = results[idx]
                        
                        # Create agent profile with default settings
                        agent_data = {
                            'agent_uuid': chosen.get('uuid', ''),
                            'agent_name': chosen.get('name', ''),
                            'agent_email': chosen.get('email', ''),
                            'agent_city': chosen.get('city', ''),
                            'agent_state': chosen.get('state', ''),
                            'location': 'Houston',  # Default market
                            'route_filter': 'both',
                            'fair_chance_only': False,
                            'max_jobs': 25,
                            'experience_level': 'both',
                            'coach_username': coach.username,
                            'created_at': datetime.now(timezone.utc).isoformat()
                        }
                        
                        # Show loading spinner while generating portal link and saving to database
                        with st.spinner("🔗 Generating portal link and saving agent..."):
                            # Generate secure portal URL with token validation and search parameters
                            full_portal_url = generate_dynamic_portal_link(agent_data)
                            
                            # Create Short.io link with proper tags
                            try:
                                from link_tracker import LinkTracker
                                link_tracker = LinkTracker()
                                
                                portal_tags = [
                                    f"coach:{coach.username}",
                                    f"candidate:{agent_data['agent_uuid']}",
                                    f"market:{agent_data['location'].lower().replace(' ', '_')}",
                                    "type:portal_access"
                                ]
                                
                                shortened_url = link_tracker.create_short_link(full_portal_url, title=f"Portal - {agent_data['agent_name']}", tags=portal_tags, candidate_id=agent_data['agent_uuid'])
                                agent_data['portal_url'] = shortened_url
                                st.write(f"🔗 Generated portal link: {shortened_url}")
                                
                            except Exception as e:
                                st.warning(f"⚠️ Could not generate short link: {e}")
                                agent_data['portal_url'] = full_portal_url  # Fallback to full URL
                            
                            success, message = save_agent_profile(coach.username, agent_data)
                        
                        if success:
                            st.success(f"✅ {chosen['name']} successfully saved to database!")
                            if agent_data.get('portal_url'):
                                st.info(f"🔗 Portal link: {agent_data['portal_url']}")
                                # Show copy button for the portal link
                                if st.button("📋 Copy Portal Link", key="copy_new_portal"):
                                    st.success("Portal link copied to clipboard!")
                            st.balloons()
                            # Clear search results after successful add
                            st.session_state['search_results'] = []
                            st.rerun()
                        else:
                            st.error(f"❌ Database save failed: {message}")
                            st.warning("💡 Ensure Supabase is connected and environment variables are set")
                            
                    except Exception as e:
                        st.error(f"❌ Error adding agent: {str(e)}")
                else:
                    st.warning("⚠️ Please select an agent first")

    # CSV Import Section
    with st.expander("📥 Import Free Agents (CSV)", expanded=False):
        st.markdown("""
        Upload a CSV to bulk add Free Agents. Expected columns (case-insensitive):
        - **agent_name** (required) - Full name of Free Agent
        - **agent_email** (optional) - Email address  
        - **agent_uuid** (optional; auto-generated if missing) - Unique identifier
        - **agent_city** (optional) - City location
        - **agent_state** (optional) - State location  
        - **location** or **market** (defaults to 'Houston') - Search location
        - **route_filter** (both/local/otr; defaults to 'both') - Route preference
        - **fair_chance_only** (true/false; defaults to false) - Fair chance filter
        - **max_jobs** (15/25/50/100; defaults to 25) - Job limit per search
        - **experience_level** (both/entry/experienced; defaults to 'both') - Experience filter
        
        ✅ **Security**: Portal links are automatically generated with secure token authentication
        ✅ **Compatibility**: Full alignment with Airtable sync and Supabase schema
        """)

        csv_file = st.file_uploader("Upload CSV", type=["csv"], key="agent_csv_upload")
        if csv_file is not None:
            try:
                # pandas already imported globally
                import uuid as _uuid
                df_csv = pd.read_csv(csv_file)
                st.write("Preview:")
                st.dataframe(df_csv.head(10), width="stretch")

                # Normalize columns
                cols = {c.lower().strip(): c for c in df_csv.columns}
                def _get(row, keys, default=""):
                    for k in keys:
                        if k in cols:
                            return row.get(cols[k], default)
                    return default

                if st.button("🚀 Import Free Agents", type="primary", key="import_agents_btn"):
                    from free_agent_system import save_agent_profile
                    success_count = 0
                    fail_count = 0
                    errors = []
                    for _, row in df_csv.iterrows():
                        try:
                            name = str(_get(row, ["agent_name", "name"]).strip())
                            if not name:
                                continue
                            email = str(_get(row, ["agent_email", "email"]).strip())
                            agent_uuid = str(_get(row, ["agent_uuid", "uuid"]).strip()) or str(_uuid.uuid4())
                            city = str(_get(row, ["agent_city", "city"]).strip())
                            state = str(_get(row, ["agent_state", "state"]).strip())
                            # Market/location policy: use market/plain for standard, custom stays exact if provided as custom later
                            market = str(_get(row, ["location", "market"]).strip()) or "Houston"
                            route_filter = str(_get(row, ["route_filter", "route"]).strip().lower() or "both")
                            fair_raw = str(_get(row, ["fair_chance_only", "fair"]).strip().lower())
                            fair = True if fair_raw in ("true", "1", "yes", "y") else False
                            try:
                                max_jobs = int(_get(row, ["max_jobs"])) if str(_get(row, ["max_jobs"]).strip()) else 25
                            except Exception:
                                max_jobs = 25
                            exp = str(_get(row, ["experience_level", "experience"]).strip().lower() or "both")

                            agent_data = {
                                'agent_uuid': agent_uuid,
                                'agent_name': name,
                                'agent_email': email,
                                'agent_city': city,
                                'agent_state': state,
                                'location': market,
                                'route_filter': route_filter if route_filter in ['both', 'local', 'otr'] else 'both',
                                'fair_chance_only': fair,
                                'max_jobs': max_jobs if max_jobs in [15, 25, 50, 100] else 25,
                                'experience_level': exp if exp in ['both', 'entry', 'experienced'] else 'both',
                                'coach_username': coach.username,
                                'created_at': datetime.now(timezone.utc).isoformat()
                            }

                            ok, msg = save_agent_profile(coach.username, agent_data)
                            if ok:
                                success_count += 1
                            else:
                                fail_count += 1
                                errors.append(msg)
                        except Exception as e:
                            fail_count += 1
                            errors.append(str(e))

                    st.success(f"✅ Imported {success_count} agent(s)")
                    if fail_count:
                        st.error(f"❌ Failed to import {fail_count} row(s)")
                        with st.expander("Errors", expanded=False):
                            st.write("\n".join(errors[:50]))
                    # Refresh the page to show new agents
                    if success_count:
                        if 'agent_profiles' in st.session_state:
                            del st.session_state['agent_profiles']
                        st.rerun()
            except Exception as e:
                st.error(f"CSV parse error: {e}")
    
    # Add refresh button and status indicator
    col1, col2, col3 = st.columns([3, 1, 1])
    with col2:
        if st.button("🔄 Refresh", help="Reload agents from database"):
            # Clear any session state cache to force fresh load
            if 'agent_profiles' in st.session_state:
                del st.session_state['agent_profiles']
            st.rerun()
    
    with col3:
        # Show data source indicator
        try:
            from supabase_utils import get_client
            client = get_client()
            if client:
                st.success("🟢 Supabase")
            else:
                st.warning("🟡 Session")
        except:
            st.warning("🟡 Session")
    
    # Load existing agents with optimized batch loading (includes click stats)
    agents = load_agent_profiles_with_stats(coach.username, current_lookback)
    
    # Debug info for testing
    if agents:
        st.info(f"📊 Loaded {len(agents)} agent profile(s)")
    else:
        st.info("📝 No agents configured yet - add your first agent above")
    
    if agents:
        st.markdown("### Your Free Agents")
        
        # Convert agents to DataFrame for streamlit data_editor
        # pandas already imported globally
        
        # Prepare data for the editor
        agent_data = []
        for agent in agents:
            # Use pre-loaded click stats from optimized batch loading
            stats = {
                'total_clicks': agent.get('total_clicks', 0),
                'recent_clicks': agent.get('recent_clicks', 0),
                'lookback_days': agent.get('lookback_days', current_lookback)
            }
            
            # Use stored portal URL if available, otherwise generate dynamic URL
            agent_uuid = agent.get('agent_uuid', '')
            if agent_uuid:
                # Prefer stored portal_url (which should be a short link from agent creation)
                stored_portal_url = agent.get('portal_url', '')
                if stored_portal_url:
                    dynamic_portal_url = stored_portal_url
                else:
                    # Fallback to generating dynamic URL if no stored portal_url
                    dynamic_portal_url = generate_dynamic_portal_link(agent)
            else:
                dynamic_portal_url = "Missing UUID - Cannot generate secure link"
            
            agent_row = {
                'Free Agent Name': agent.get('agent_name', 'Unknown'),
                f'Total Clicks ({current_lookback}d)': stats['total_clicks'],
                'Recent (7d)': stats['recent_clicks'],
                'Market': agent.get('location', 'Houston'),
                'Route': agent.get('route_filter', 'both'),
                'Fair Chance': agent.get('fair_chance_only', False),
                'Max Jobs': agent.get('max_jobs', 25),
                'Match Level': agent.get('match_level', 'good and so-so'),
                'City': agent.get('agent_city', ''),
                'State': agent.get('agent_state', ''),
                'Created': agent.get('created_at', '')[:10] if agent.get('created_at') else '',
                'Portal Link': dynamic_portal_url,
                'Admin Portal': agent.get('admin_portal_url', ''),
                'Delete': False,  # Checkbox for bulk deletion
                # Hidden fields for updates
                '_agent_uuid': agent.get('agent_uuid', ''),
                '_created_at': agent.get('created_at', ''),
                '_original_data': agent  # Store original for comparison
            }
            agent_data.append(agent_row)
        
        df = pd.DataFrame(agent_data)
        # Reorder columns to prioritize metrics next to name 
        desired_order = [
            'Free Agent Name', f'Total Clicks ({current_lookback}d)', 'Recent (7d)',
            'Market', 'Route', 'Fair Chance', 'Max Jobs', 'Match Level', 'City', 'State', 'Created',
            'Portal Link', 'Admin Portal', 'Delete', '_agent_uuid', '_created_at', '_original_data'
        ]
        df = df[[c for c in desired_order if c in df.columns]]
        
        # Configure column editor types
        column_config = {
            'Free Agent Name': st.column_config.TextColumn(
                "Free Agent Name",
                help="Free Agent's full name",
                disabled=True,
                width="medium"
            ),
            'City': st.column_config.TextColumn(
                "City",
                disabled=True,
                width="small"
            ),
            'State': st.column_config.TextColumn(
                "State", 
                disabled=True,
                width="small"
            ),
            'Market': st.column_config.SelectboxColumn(
                "Market",
                help="Job search market/location",
                width="small",
                options=get_market_options(),
                required=True
            ),
            'Route': st.column_config.SelectboxColumn(
                "Route",
                help="Route type preference", 
                width="small",
                options=["both", "local", "otr"],
                required=True
            ),
            'Fair Chance': st.column_config.CheckboxColumn(
                "Fair Chance",
                help="Only show fair chance friendly jobs",
                width="small"
            ),
            'Max Jobs': st.column_config.SelectboxColumn(
                "Max Jobs",
                help="Maximum jobs in search results",
                width="small", 
                options=[15, 25, 50, 100],
                required=True
            ),
            'Match Level': st.column_config.SelectboxColumn(
                "Match Level",
                help="AI match quality filter for jobs",
                width="small",
                options=["good", "so-so", "good and so-so", "all"],
                required=True
            ),
            f'Total Clicks ({current_lookback}d)': st.column_config.NumberColumn(
                f"Total Clicks ({current_lookback}d)",
                help=f"Total clicks in last {current_lookback} days",
                disabled=True,
                width="small"
            ),
            'Recent (7d)': st.column_config.NumberColumn(
                "Recent (7d)",
                help="Clicks in last 7 days",
                disabled=True,
                width="small"
            ),
            'Portal Link': st.column_config.LinkColumn(
                "Portal Link",
                help="Job portal link for free agent",
                disabled=True,
                width="medium"
            ),
            'Admin Portal': st.column_config.LinkColumn(
                "Admin Portal",
                help="Admin portal link from Airtable (if available)",
                disabled=True,
                width="medium"
            ),
            'Created': st.column_config.DateColumn(
                "Created",
                help="Date agent was added",
                disabled=True,
                width="small"
            ),
            'Delete': st.column_config.CheckboxColumn(
                "Delete",
                help="Check to mark for deletion",
                width="small"
            ),
            # Hide internal columns
            '_agent_uuid': None,
            '_created_at': None,
            '_original_data': None
        }
        
        # Show the editable data table
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            hide_index=True,
            width="stretch",
            num_rows="fixed",  # Don't allow adding/removing rows
            key="agent_editor"
        )

        
        # Check for changes and update database
        if not edited_df.equals(df):
            st.info("💾 Changes detected - updating database...")
            
            # Find changed rows
            changed_rows = []
            for idx in range(len(edited_df)):
                original = df.iloc[idx]
                edited = edited_df.iloc[idx]
                
                # Check if editable fields changed
                editable_fields = ['Market', 'Route', 'Fair Chance', 'Max Jobs', 'Match Level']
                if not all(original[field] == edited[field] for field in editable_fields):
                    changed_rows.append((idx, original, edited))
            
            if changed_rows:
                success_count = 0
                error_count = 0
                
                for idx, original, edited in changed_rows:
                    # Update the agent data
                    agent_uuid = original['_agent_uuid']
                    original_agent = original['_original_data']
                    
                    # Create updated agent data
                    updated_agent = original_agent.copy()
                    updated_agent.update({
                        'location': str(edited['Market']),
                        'route_filter': str(edited['Route']), 
                        'fair_chance_only': bool(edited['Fair Chance']),
                        'max_jobs': int(edited['Max Jobs']),
                        'match_level': str(edited['Match Level'])
                    })
                    
                    # Note: Portal link regeneration only happens with "Regenerate All Portal Links" button
                    st.info(f"📝 Updated parameters for {edited['Free Agent Name']} - use 'Regenerate All Portal Links' to update portal URLs")
                    
                    # Save to database
                    success, message = save_agent_profile(coach.username, updated_agent)
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        st.error(f"❌ Failed to update {edited['Free Agent Name']}: {message}")
                
                if success_count > 0:
                    st.success(f"✅ Successfully updated {success_count} agent(s)")
                if error_count > 0:
                    st.error(f"❌ Failed to update {error_count} agent(s)")
                
                # Refresh the page to show updated data
                if success_count > 0:
                    st.rerun()
        
        # Handle bulk deletions
        agents_to_delete = edited_df[edited_df['Delete'] == True]
        if not agents_to_delete.empty:
            st.warning(f"⚠️ {len(agents_to_delete)} agent(s) marked for deletion")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Confirm Delete Selected", type="secondary"):
                    delete_count = 0
                    for _, agent_row in agents_to_delete.iterrows():
                        agent_uuid = agent_row['_agent_uuid']
                        agent_name = agent_row['Free Agent Name']
                        try:
                            from free_agent_system import delete_agent_profile
                            if delete_agent_profile(coach.username, agent_uuid):
                                delete_count += 1
                                st.success(f"✅ Deleted {agent_name}")
                            else:
                                st.error(f"❌ Failed to delete {agent_name}")
                        except Exception as e:
                            st.error(f"❌ Error deleting {agent_name}: {e}")
                    
                    if delete_count > 0:
                        st.success(f"✅ Successfully deleted {delete_count} agent(s)")
                        st.rerun()
            with col2:
                if st.button("❌ Cancel", type="primary"):
                    st.rerun()
        
        # Bulk actions
        st.markdown("### 🔧 Bulk Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔗 Regenerate All Portal Links", help="Regenerate Short.io portal links for all agents using current table settings"):
                with st.spinner("Regenerating portal links for all agents..."):
                    regenerated_count = 0
                    failed_count = 0
                    
                    # Use current edited table data instead of original stored data
                    for idx, edited_row in edited_df.iterrows():
                        # Get the original agent data for UUID and other non-editable fields
                        original_agent = edited_row['_original_data']
                        agent_name = edited_row['Free Agent Name']
                        
                        # Create updated agent object with current table filter values
                        # Build fresh agent dict from table data instead of trying to convert original_agent
                        updated_agent = {
                            'agent_uuid': edited_row.get('_agent_uuid', ''),
                            'agent_name': agent_name,
                            'agent_email': getattr(original_agent, 'get', lambda x,d: d)('agent_email', ''),
                            'agent_city': getattr(original_agent, 'get', lambda x,d: d)('agent_city', ''),
                            'agent_state': getattr(original_agent, 'get', lambda x,d: d)('agent_state', ''),
                            'created_at': edited_row.get('_created_at', ''),
                            'coach_username': coach.username
                        }
                        # Normalize route filter value to ensure consistency
                        route_value = str(edited_row['Route']).lower()  # Ensure lowercase
                        
                        updated_agent.update({
                            'location': edited_row['Market'],
                            'route_filter': route_value,  # Use normalized lowercase value
                            'fair_chance_only': bool(edited_row['Fair Chance']),
                            'max_jobs': int(edited_row['Max Jobs']),
                            'match_level': edited_row['Match Level'],
                            'coach_username': coach.username  # Ensure coach username is included
                        })
                        
                        print(f"🔍 ROUTE DEBUG: Table shows '{edited_row['Route']}', normalized to '{route_value}'")
                        try:
                            # DEBUG: Show exactly what we're passing to portal link generation
                            debug_params = {
                                'agent_uuid': updated_agent.get('agent_uuid', 'MISSING'),
                                'agent_name': updated_agent.get('agent_name', 'MISSING'),
                                'location': updated_agent.get('location', 'MISSING'),
                                'route_filter': updated_agent.get('route_filter', 'MISSING'),
                                'fair_chance_only': updated_agent.get('fair_chance_only', 'MISSING'),
                                'max_jobs': updated_agent.get('max_jobs', 'MISSING'),
                                'match_level': updated_agent.get('match_level', 'MISSING'),
                                'coach_username': updated_agent.get('coach_username', 'MISSING')
                            }
                            print(f"🔍 DEBUG: Agent parameters being passed: {debug_params}")
                            
                            # Generate secure portal URL with current table filter values
                            print(f"🔗 Regenerating link for {agent_name} with filters: Market={updated_agent['location']}, Route={updated_agent['route_filter']}, Fair Chance={updated_agent['fair_chance_only']}")
                            full_portal_url = generate_dynamic_portal_link(updated_agent)
                            print(f"🔗 Generated full URL: {full_portal_url[:100]}...")
                            
                            # Create new Short.io link
                            from link_tracker import LinkTracker
                            link_tracker = LinkTracker()
                            
                            # Check if LinkTracker is properly configured
                            if not hasattr(link_tracker, 'is_available') or not link_tracker.is_available:
                                raise Exception("LinkTracker not available - check Short.io API configuration")
                            
                            portal_tags = [
                                f"coach:{coach.username}",
                                f"candidate:{updated_agent['agent_uuid']}",
                                f"market:{updated_agent['location'].lower().replace(' ', '_')}",
                                f"route:{updated_agent['route_filter'].lower().replace(' ', '_')}",
                                "type:portal_access"
                            ]
                            print(f"🔗 Creating Short.io link with tags: {portal_tags}")
                            
                            shortened_url = link_tracker.create_short_link(full_portal_url, title=f"Portal - {agent_name}", tags=portal_tags, candidate_id=updated_agent['agent_uuid'])
                            print(f"🔗 Got shortened URL: {shortened_url}")
                            
                            if not shortened_url or shortened_url == full_portal_url:
                                raise Exception("Short.io returned empty or same URL - possible API limit reached")
                            
                            # Update agent with new URL (updated_agent already has current table filter values)
                            updated_agent['portal_url'] = shortened_url
                            
                            success, message = save_agent_profile(coach.username, updated_agent)
                            if success:
                                regenerated_count += 1
                                print(f"✅ Successfully regenerated link for {agent_name}")
                            else:
                                failed_count += 1
                                st.error(f"❌ Failed to save {agent_name}: {message}")
                                
                        except Exception as e:
                            failed_count += 1
                            error_msg = str(e)
                            print(f"❌ Failed to regenerate link for {agent_name}: {error_msg}")
                            st.error(f"❌ Failed to regenerate link for {agent_name}: {error_msg}")
                    
                    if regenerated_count > 0:
                        st.success(f"✅ Regenerated {regenerated_count} portal links")
                    if failed_count > 0:
                        st.error(f"❌ Failed to regenerate {failed_count} links")
                    
                    if regenerated_count > 0:
                        st.rerun()
        
        with col2:
            if st.button("📧 Export Email List", help="Export all agent emails as CSV"):
                # Create CSV of email addresses
                email_list = [agent.get('agent_email', '') for agent in agents if agent.get('agent_email')]
                email_df = pd.DataFrame({'Email': email_list})
                csv = email_df.to_csv(index=False)
                st.download_button(
                        
                    label="📥 Download Email CSV",
                    data=csv,
                    file_name=f"free_agent_emails_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col3:
            if st.button("🗑️ Delete Selected", help="Delete multiple agents (not implemented yet)"):
                st.info("Bulk delete functionality would be implemented here")
        
        # Show summary stats using pre-loaded data (no individual API calls!)
        st.markdown("### 📊 Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Agents", len(agents))
        with col2:
            # Use pre-loaded total_clicks from optimized batch loading
            total_clicks = sum(agent.get('total_clicks', 0) for agent in agents)
            st.metric(f"Total Clicks ({current_lookback}d)", total_clicks)
        with col3:
            # Use pre-loaded recent_clicks for 7-day activity
            active_agents = len([a for a in agents if a.get('recent_clicks', 0) > 0])
            st.metric("Active Agents (7d)", active_agents)
        with col4:
            avg_clicks = total_clicks / len(agents) if agents else 0
            st.metric(f"Avg Clicks/Agent", f"{avg_clicks:.1f}")
                
    
    else:
        st.info("👆 Add your first Free Agent using the search above")

        st.subheader("Weekly Performance Report (Example)")
        if st.button("Generate Weekly Report for Me", key="generate_my_weekly_report"):
            weekly_report = generate_weekly_performance_report(coach.username)
            st.json(weekly_report)




# Mobile-friendly HTML helpers for Free Agent Portal
def _df_fingerprint(df) -> str:
    """Stable-ish hash of the jobs DF for caching."""
    import json
    import hashlib
    # Choose columns that matter to the HTML; sort to avoid row-order noise
    cols = [c for c in df.columns if not c.startswith("_")]
    safe = df[cols].copy()
    # Convert to json with stable ordering
    payload = safe.to_dict(orient="records")
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()

@safe_cache_data(ttl=300, max_entries=5)  # 5 min cache, max 5 entries  
def _render_jobs_html_cached(df_json: str, agent_params_json: str) -> str:
    """Cached HTML render with limited cache size."""
    import json
    from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html
    from free_agent_system import update_job_tracking_for_agent
    
    df = pd.DataFrame(json.loads(df_json))
    agent_params = json.loads(agent_params_json)
    
    # IMPORTANT: Use the same processing as PDF to include tracked URLs
    processed_df = update_job_tracking_for_agent(df, agent_params)
    jobs = jobs_dataframe_to_dicts(processed_df)
    
    return render_jobs_html(jobs, agent_params)


def show_free_agent_portal(agent_config_encoded):
    """
    Shows a landing page, runs the search, and then displays the
    final mobile-friendly HTML report by injecting it into the main DOM.
    """
    from free_agent_system import decode_agent_params

    # --- Page Config and Styling ---
    # Already configured at module import; guard against duplicate calls
    try:
        if not st.session_state.get("_page_configured"):
            import os
            page_icon_img = None
            logo_candidates = [
                os.path.join('assets', 'FW-Logo-Roots@2x.png'),
                os.path.join('assets', 'fw_logo.png'),
                os.path.join('data', 'FW-Logo-Roots@2x.png'),
                os.path.join('data', 'fw_logo.png'),
                os.path.join('assets', 'FW-Wordmark-Roots@3x.png'),
            ]
            for _p in logo_candidates:
                if os.path.exists(_p) and Image:
                    try:
                        page_icon_img = Image.open(_p)
                        break
                    except Exception:
                        continue
            # Use FreeWorld logo or fallback to QA emoji
            try:
                qa_favicon = Image.open("fw_logo.png") if page_icon_img is None else page_icon_img
            except:
                qa_favicon = "🧪"  # QA test tube emoji
                
            st.set_page_config(
                page_title="FreeWorld QA Portal - Test Environment",
                page_icon=qa_favicon,
                layout="wide",
            )
            st.session_state["_page_configured"] = True
    except Exception:
        pass

    # --- Decode agent parameters once ---
    try:
        agent_params = decode_agent_params(agent_config_encoded)
        agent_name = agent_params.get('agent_name', 'Free Agent')
    except Exception as e:
        st.error("❌ Invalid or expired portal link.")
        st.stop()

    # Hide Streamlit chrome and badges globally for the portal route (especially on mobile)
    st.markdown("""
    <style>
      #MainMenu, header, footer { display: none !important; }
      [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
      .viewerBadge_link__wrapper, .viewerBadge_container__2QSsR { display: none !important; }
      a[href^="https://streamlit.io"] { display: none !important; }
      /* Remove default paddings around the app view on mobile */
      [data-testid="stAppViewContainer"] { padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

    # --- Splash placeholder so we can overwrite it with the title page ---
    _portal_placeholder = st.empty()

    # --- Show Splash Screen & Run Pipeline ---
    # Prepare round logo for the splash (prefer small square/round icon)
    try:
        splash_logo_candidates = [
            os.path.join('assets', 'FW-Logo-Roots.svg'),
            os.path.join('assets', 'FW-Logo-Roots@3x.png'),
            os.path.join('assets', 'FW-Logo-Roots@2x.png'),
            os.path.join('assets', 'fw_logo.png'),
            os.path.join('data', 'FW-Logo-Roots.svg'),
            os.path.join('data', 'FW-Logo-Roots@3x.png'),
            os.path.join('data', 'FW-Logo-Roots@2x.png'),
            os.path.join('data', 'fw_logo.png'),
        ]
        _splash_logo_b64 = None
        _splash_logo_mime = 'image/png'
        for _lp in splash_logo_candidates:
            if os.path.exists(_lp):
                _b64 = get_base64_of_image(_lp)
                if _b64:
                    _splash_logo_b64 = _b64
                    _splash_logo_mime = 'image/svg+xml' if _lp.lower().endswith('.svg') else 'image/png'
                    break
    except Exception:
        _splash_logo_b64 = None
        _splash_logo_mime = 'image/png'

    _portal_placeholder.markdown(f"""
    <style>
        /* Kill Streamlit chrome for a full-bleed look on the portal route only */
        #MainMenu, header, footer {{ display: none !important; }}
        [data-testid="stAppViewContainer"] {{ padding: 0 !important; }}
        .block-container {{ padding: 0 !important; }}
        [data-testid="stToolbar"] {{ display: none !important; }}
        html, body, .block-container {{ height: 100%; margin: 0; }}

        /* Fullscreen splash */
        .fw-splash {{ 
          position: fixed; inset: 0; z-index: 9999;
          width: 100vw; height: 100svh; min-height: 100dvh;
          display: flex; flex-direction: column; 
          align-items: center; justify-content: center;
          background: #191931; color: #E5E5E5; text-align: center; padding: 24px;
          font-family: 'Outfit', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
        }}
        .fw-splash-logo {{
          /* Big, responsive logo */
          width: clamp(120px, 22vw, 220px); height: clamp(120px, 22vw, 220px);
          border-radius: 50%; object-fit: cover;
          box-shadow: 0 6px 24px rgba(0,0,0,0.35); margin-bottom: 16px;
          background: #fff;
        }}
        .fw-splash h1 {{ margin: 0 0 10px; color: #CDF95C; font-size: clamp(24px, 4.5vw, 40px); line-height: 1.1; }}
        .fw-splash p  {{ margin: 0; opacity: .9; font-size: clamp(14px, 2.8vw, 18px); }}
        .fw-spinner {{ margin-top: 20px; width: 44px; height: 44px; border-radius: 50%;
          border: 4px solid rgba(255,255,255,0.2); border-top-color: #CDF95C; animation: spin 1s linear infinite; }}
        
        /* Desktop fine-tune */
        @media (min-width: 900px) {{
          .fw-splash {{ padding: 40px; }}
          .fw-spinner {{ width: 52px; height: 52px; border-width: 5px; }}
        }}
        
        /* Account for iOS safe areas */
        @supports (padding: max(0px)) {{
          .fw-splash {{
            padding-bottom: max(24px, env(safe-area-inset-bottom));
            padding-top: max(24px, env(safe-area-inset-top));
          }}
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    </style>
    <div class="fw-splash">
      {f'<img class="fw-splash-logo" src="data:{_splash_logo_mime};base64,{_splash_logo_b64}" alt="FreeWorld" />' if _splash_logo_b64 else ''}
      <h1>FreeWorld</h1>
      <p>Building your custom job list...</p>
      <div class="fw-spinner"></div>
    </div>
    """, unsafe_allow_html=True)

    # Helper: load latest CSVs from FreeWorld_Jobs for this market/location
    def _load_latest_market_csv(location_str: str, limit: int = 25) -> 'pd.DataFrame':
        try:
            import pandas as pd
            from pathlib import Path
            import glob
            base = Path('FreeWorld_Jobs')
            if not base.exists():
                return pd.DataFrame()
            # Normalize market tokens: "Houston, TX" → "Houston" and "Houston_TX"
            city = (location_str or 'Houston').split(',')[0].strip()
            city_token = city.replace(' ', '_')
            # 1) Try market-specific quality CSVs (newer pattern)
            candidates = []
            candidates += glob.glob(str(base / f"{city_token}*_quality*.csv"))
            candidates += glob.glob(str(base / f"FreeWorld_Jobs_{city}*.csv"))
            # 2) Fallback to complete CSV and filter by meta.market
            complete = sorted(glob.glob(str(base / 'complete_jobs_*.csv')))
            df = pd.DataFrame()
            if candidates:
                latest = max(candidates, key=os.path.getmtime)
                try:
                    df = pd.read_csv(latest)
                except Exception:
                    df = pd.DataFrame()
            elif complete:
                latest = max(complete, key=os.path.getmtime)
                try:
                    tmp = pd.read_csv(latest)
                    if 'meta.market' in tmp.columns:
                        df = tmp[tmp['meta.market'].astype(str).str.lower().str.contains(city.lower())]
                    else:
                        df = tmp
                except Exception:
                    df = pd.DataFrame()
            if df.empty:
                return df
            # Prefer quality subset if available
            if 'ai.match' in df.columns:
                df = df[df['ai.match'].isin(['good', 'so-so'])]
            # Apply agent preference filters if columns exist
            try:
                # Fair chance filter
                if agent_params.get('fair_chance_only', False) and 'ai.fair_chance' in df.columns:
                    # Canonical value is a category string; accept true-like markers
                    df = df[df['ai.fair_chance'].astype(str).str.contains('fair', case=False, na=False)]
                # Route filter
                route_pref = agent_params.get('route_filter', 'both')
                if route_pref in ['local', 'otr'] and 'ai.route_type' in df.columns:
                    route_map = {'local': 'Local', 'otr': 'OTR'}
                    df = df[df['ai.route_type'] == route_map[route_pref]]
                # Experience filter (mirrors UI behavior)
                exp = agent_params.get('experience_level', 'both')
                if exp == 'entry' and 'ai.match' in df.columns:
                    df = df[df['ai.match'].isin(['good', 'so-so'])]
                elif exp == 'experienced' and 'ai.match' in df.columns:
                    df = df[df['ai.match'] == 'bad']
            except Exception:
                pass
            # Limit rows
            return df.head(limit)
        except Exception:
            return pd.DataFrame()

    # --- Use clean agent portal implementation ---
    try:
        from agent_portal_clean import generate_agent_portal
        report_fragment = generate_agent_portal(agent_params)
    except Exception as e:
        print(f"❌ CLEAN PORTAL ERROR: {e}")
        import traceback
        print(f"❌ CLEAN PORTAL TRACEBACK: {traceback.format_exc()}")
        report_fragment = f"<div class='fw-splash'><h1>Clean Portal Error</h1><p>{e}</p></div>"

    # --- Replace splash with final report directly (no iframe, no fixed height) ---
    try:
        # Clear the splash (removes its CSS) to prevent any fixed overlay artifacts
        _portal_placeholder.empty()
        
        # Apply proper edge-to-edge styling for unlimited height documents
        st.markdown("""
        <style>
        /* 1) Remove all page padding and width limits */
        [data-testid="stAppViewContainer"] { padding: 0 !important; }
        [data-testid="block-container"] { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
        
        /* 2) Remove any default gap between blocks */
        [data-testid="stVerticalBlock"] { gap: 0rem !important; }
        
        /* 3) Hide the Streamlit header/footer for clean canvas */
        header[data-testid="stHeader"] { display: none; }
        footer { visibility: hidden; }
        
        /* 4) Make blocks visually flat */
        :root {
          --border-width: 0px;
          --block-border-width: 0px;
          --block-radius: 0px;
          --secondary-background-color: transparent;
        }
        
        /* 5) Let the whole app grow with content - no height limits */
        html, body, [data-testid="stAppViewContainer"], section.main, 
        [data-testid="block-container"] {
          height: auto !important;
          min-height: 100vh !important;
          overflow: visible !important;
        }
        
        /* 6) Make sure content flows naturally */
        [data-testid="stVerticalBlock"] { overflow: visible !important; }
        .fullbleed, .hero, .hero-card, .fw-wrapper {
          overflow: visible !important;
          height: auto !important;
          max-height: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Calculate dynamic height based on content + enable scrolling as backup
        # Estimate: ~400px per job card + 2000px for headers/footers/spacing
        try:
            # Count actual job cards in the HTML for precise height calculation
            import re
            job_card_count = len(re.findall(r'<div[^>]*class="[^"]*job-card[^"]*"', report_fragment))
            
            # If no job cards found, try alternate patterns
            if job_card_count == 0:
                job_card_count = len(re.findall(r'<div[^>]*class="[^"]*job[^"]*"', report_fragment))
            
            # Fallback to content-based estimation if regex fails
            if job_card_count == 0:
                job_card_count = max(3, len(report_fragment) // 2000)  # More conservative estimate
            
            # Calculate precise height based on actual CSS measurements:
            # - Header/branding: ~400px
            # - Each job card: ~240px (16px padding + content + 16px margin)
            # - Footer/spacing: ~200px
            # - Buffer for loading states: ~160px
            base_height = 760  # Header + footer + buffer  
            job_height_per_card = 240  # Based on CSS: padding(32px) + content(~192px) + margin(16px)
            calculated_height = base_height + (job_card_count * job_height_per_card)
            
            # Debug info for testing (can be removed later)
            if st.query_params.get("debug_height"):
                st.info(f"🔧 Height Debug: Found {job_card_count} job cards → {calculated_height}px total")
            
            # Apply reasonable bounds (min 3k for small screens, max 25k for UX)
            final_height = min(25000, max(3000, calculated_height))
            
            st.components.v1.html(report_fragment, height=final_height, scrolling=True)
        except Exception:
            # Fallback: reasonable height with scrolling enabled
            st.components.v1.html(report_fragment, height=12000, scrolling=True)

        # Optional debug-frame outlines for portal rendering (use ?debug_frame=1)
        try:
            _qp = st.query_params
            _df = str(_qp.get("debug_frame", "")).lower() in ("1", "true", "yes")
        except Exception:
            _df = False
        if _df:
            st.markdown(
                    """
                    <style>
                      [data-testid='stAppViewContainer'] { outline: 2px dashed #ff4d4f; outline-offset: -2px; }
                      section.main { outline: 2px dashed #40a9ff; outline-offset: -2px; }
                      section.main .block-container { outline: 2px dashed #52c41a; outline-offset: -2px; }
                      section.main .block-container > div:first-child { outline: 2px dashed #fa8c16; outline-offset: -2px; }
                      [data-testid='stMarkdownContainer'] { outline: 2px dashed #722ed1; outline-offset: -2px; }
                      .fw-debug-banner { position: fixed; top: 8px; right: 8px; z-index: 10000; background: #000c17; color: #fff; padding: 6px 10px; border-radius: 6px; font-size: 12px; opacity: 0.85; }
                    </style>
                    <div class='fw-debug-banner'>🧪 Debug Frame: ON</div>
                    """,
                    unsafe_allow_html=True,
                )
            import uuid as _uuid
            from streamlit.components.v1 import html as _html
            _html(
                    """
                    <script>
                    (function(){
                      const sel = s => document.querySelector(s);
                      const targets = [
                        "[data-testid='stAppViewContainer']",
                        "section.main",
                        "section.main .block-container",
                        "section.main .block-container > div:first-child",
                        "[data-testid='stMarkdownContainer']"
                      ];
                      const report = targets.map(t => {
                        const el = sel(t);
                        if(!el) return { t, present:false };
                        const r = el.getBoundingClientRect();
                        const cs = getComputedStyle(el);
                        return { t, present:true, top:r.top, mt:cs.marginTop, pt:cs.paddingTop, h:r.height, w:r.width };
                      });
                      console.log("FW DEBUG FRAMES (portal)", report);
                    })();
                    </script>
                    """,
                    height=1,
                    scrolling=False,
                )
    except Exception:
        # Final fallback: reasonable height with scrolling enabled  
        st.components.v1.html(report_fragment, height=15000, scrolling=True)


def show_system_testing_page(coach):
    """Show System Testing page - placeholder for now"""
    st.header("🧪 System Testing")
    st.info("🚧 System testing interface coming soon...")
    st.markdown("This will include:")
    st.markdown("• API connection tests")
    st.markdown("• Database connectivity")
    st.markdown("• Cost calculator tests")
    st.markdown("• Debug tools")

def main():
    """Main Streamlit application"""
    
    # Check for public-facing agent portal link FIRST
    try:
        params = st.query_params
        agent_config = params.get("agent_config") or params.get("config")
        agent_uuid_param = params.get("agent")
        clear_cache_param = params.get("clear")
        debug_frame_param = params.get("debug_frame")
    except Exception: # Fallback if query params fail
        agent_config = None
        agent_uuid_param = None
        clear_cache_param = None
        debug_frame_param = None
    
    # URL-based cache clearing removed to prevent issues

    if agent_config or agent_uuid_param:
        # 🔐 SECURITY: Validate secure token for portal access
        try:
            token = params.get("token") or params.get("t")
        except AttributeError:
            token = params.get("token", [None])[0] or params.get("t", [None])[0]
        
        # For agent_uuid access, validate the token matches the UUID
        if agent_uuid_param and token:
            # Generate expected token from UUID (simple hash-based validation)
            import hashlib
            expected_token = hashlib.md5(f"{agent_uuid_param}:FreeWorld2025".encode()).hexdigest()[:12]
            if token != expected_token:
                st.error("🚫 Invalid access token")
                st.markdown("**Access denied**: This link appears to be invalid or expired.")
                st.markdown("Please contact your Career Services coach for a new portal link.")
                st.stop()
        elif agent_uuid_param and not token:
            st.error("🔒 Secure access token required")
            st.markdown("**Access denied**: This portal requires a secure access token.")
            st.markdown("Please use the complete link provided by your Career Services coach.")
            st.stop()
        
        # If only agent UUID provided, fetch configuration server-side from Supabase
        if not agent_config and agent_uuid_param:
            try:
                from supabase_utils import get_client
                client = get_client()
                if client:
                    res = client.table('agent_profiles').select('*').eq('agent_uuid', agent_uuid_param).limit(1).execute()
                    if res and res.data:
                        profile = res.data[0]
                        cfg = profile.get('search_config', {}) or {}
                        # Extract first name for friendly display (acceptable PII exposure)
                        full_name = profile.get('agent_name', '')
                        first_name = full_name.split()[0] if full_name else 'Free Agent'
                        
                        agent_config_obj = {
                            'agent_uuid': profile.get('agent_uuid', ''),
                            'agent_name': first_name,  # 🔐 SECURITY: First name only
                            'location': cfg.get('location', 'Houston'),  # Use config location only
                            'route_filter': cfg.get('route_filter', 'both'),
                            'fair_chance_only': cfg.get('fair_chance_only', False),
                            'max_jobs': cfg.get('max_jobs', 25),
                            'experience_level': cfg.get('experience_level', 'both'),
                            'coach_username': '',  # 🔐 SECURITY: Hide coach info from public
                        }
                        from free_agent_system import encode_agent_params
                        agent_config = encode_agent_params(agent_config_obj)
            except Exception:
                pass
        show_free_agent_portal(agent_config)
        st.stop()

    # If not an agent portal, proceed with coach authentication
    authenticate_coach()
    
    # Get current coach info
    coach = st.session_state.current_coach
    coach_manager = get_coach_manager()
    
    # Use getattr with default True for backwards compatibility with existing coaches
    can_pull_fresh = getattr(coach, 'can_pull_fresh_jobs', True)
    
    # Auto cache-bust on build changes
    last_build_key = f"last_build_hash_{coach.username}"
    if last_build_key not in st.session_state:
        st.session_state[last_build_key] = None
    
    if st.session_state[last_build_key] != BUILD_HASH:
        # New build detected - clear caches automatically (silent)
        try:
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state[last_build_key] = BUILD_HASH
            # Cache clearing now happens silently - no UI noise
        except Exception as e:
            st.warning(f"⚠️ Cache clear failed: {e}")
    
    # Initialize pipeline wrapper with version-based cache busting
    @st.cache_resource
    def get_pipeline(version):
        if _PIPELINE_WRAPPER_CLASS is None:
            st.error("❌ Pipeline wrapper class not available")
            st.stop()
        return _PIPELINE_WRAPPER_CLASS()
    
    pipeline = get_pipeline(BUILD_HASH)  # Use build hash for stronger cache busting
    
    # FreeWorld Logo at top left of main page - prefer round logo for QA
    logo_paths = [
        "assets/fw_logo.png",           # Round logo (preferred for QA)
        "assets/FW-Logo-Roots@2x.png",  # Round logo alternate
        "data/fw_logo.png",
        "data/FW-Logo-Roots@2x.png", 
        "assets/FW-Wordmark-Roots@3x.png"  # Wordmark (fallback)
    ]
    
    # Remove dead space at top of page
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        .stApp > header {
            background-color: transparent;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Clean header with logo and title on left, hamburger far right
    # Try to load the logo
    logo_b64 = None
    for logo_path in logo_paths:
        logo_b64 = get_base64_of_image(logo_path)
        if logo_b64:
            break
    
    # Create layout with logo/title taking most space, hamburger at far right
    coach_name = getattr(coach, 'full_name', 'Coach')
    
    # Create header using columns for proper Streamlit component positioning
    col_left, col_right = st.columns([4, 1])
    
    with col_left:
        # Logo and title side by side
        if logo_b64:
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 20px; margin-top: 0;">
                    <img src="data:image/png;base64,{logo_b64}" 
                         style="width: 150px; height: auto;">
                    <h1 style="color: #CDF95C; margin: 0; font-weight: 700;">
                        FreeWorld Success Coach Portal
                    </h1>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<h1 style="color: #CDF95C; margin: 0;">🌍 FreeWorld Success Coach Portal</h1>', unsafe_allow_html=True)
    
    with col_right:
        # Hamburger menu aligned to the right
        st.markdown('<div style="text-align: right; margin-top: 0;">', unsafe_allow_html=True)
        with st.popover("☰", help=f"Account menu for {coach_name}"):
            st.markdown(f"**{coach_name}**")
            st.caption(f"@{coach.username}")
            st.divider()
            
            if st.button("🔑 Change Password", key="hamburger_password", width="stretch"):
                st.session_state.show_password_change = True
                st.rerun()
            
            if st.button("🔄 Clear Cache", key="hamburger_cache", width="stretch", help="Clear all caches and refresh"):
                clear_all_caches_and_refresh()
            
            st.divider()
            
            if st.button("🚪 Sign Out", key="hamburger_logout", width="stretch", type="secondary"):
                # Clear session state and rerun
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle password change modal
    if st.session_state.get('show_password_change', False):
        with st.expander("🔑 Change Password", expanded=True):
            new_password = st.text_input("New Password", type="password", key="new_password_input")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password_input")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Password", key="update_password_btn"):
                    if new_password and new_password == confirm_password:
                        success = coach_manager.update_coach_password(coach.username, new_password)
                        if success:
                            st.success("✅ Password updated successfully!")
                            st.session_state.show_password_change = False
                            st.rerun()
                        else:
                            st.error("❌ Failed to update password")
                    else:
                        st.error("❌ Passwords don't match or are empty")
            
            with col2:
                if st.button("Cancel", key="cancel_password_btn"):
                    st.session_state.show_password_change = False
                    st.rerun()

    # Clean spacer between header and tabs
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    # Tab Navigation - Use radio buttons for persistent state
    tab_options = [
        "🔍 Job Search",
        "🗓️ Batches & Scheduling", 
        "👥 Free Agents",
        "📊 Coach Analytics",
        "👑 Admin Panel" if coach.role == 'admin' else "🔒 Restricted"
    ]
    
    # Initialize current tab if not set
    if 'current_tab_index' not in st.session_state:
        st.session_state.current_tab_index = 0
    
    # Navigation bar using radio buttons (persists across reruns)
    selected_tab = st.radio(
        "Navigation",
        options=tab_options,
        index=st.session_state.current_tab_index,
        key="main_tab_radio",
        horizontal=True
    )
    
    # Update session state with current selection index
    if selected_tab in tab_options:
        st.session_state.current_tab_index = tab_options.index(selected_tab)
    
    st.markdown("---")  # Separator line
    
    # Show selected tab content based on selection
    if selected_tab == "🔍 Job Search":
        # Job Search tab - cloned sidebar content (original sidebar still exists for now)
        st.header("🔍 Job Search")
        
        # COMPACT Search Parameters Section
        st.header("🎯 Search Parameters")
        
        # Single Row: Location Type, Target Markets, Job Quantity, Search Terms, and Search Radius
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 3, 1.5, 1.5, 1])
        
        with col1:
            location_options_tab = ["Select Market"]
            if check_coach_permission('can_use_custom_locations'):
                location_options_tab.append("Custom Location")
            
            location_type_tab = st.radio(
                "Location Type:",
                location_options_tab,
                help="Choose from preset markets or enter a custom location",
                key="tab_location_type"
            )
        
        with col2:
            location_tab = None
            if location_type_tab == "Select Market":
                markets = pipeline.get_markets()
                selected_market_tab = st.selectbox(
                    "Target Market:",
                    markets,
                    help="Select a market to search",
                    key="tab_selected_market"
                )
                if selected_market_tab:
                    location_tab = pipeline.get_market_location(selected_market_tab)
                else:
                    st.warning("👆 Please select a market")
                    
            elif location_type_tab == "Custom Location":
                custom_location_tab = st.text_input(
                    "Enter ZIP code, city, or state:",
                    placeholder="e.g., 90210, Austin TX, California",
                    help="Enter any US location - ZIP code, city name, or state",
                    key="tab_custom_location"
                )
                if custom_location_tab:
                    location_tab = custom_location_tab.strip()
                    st.success(f"📍 Custom Location: {location_tab}")
                else:
                    st.warning("👆 Please enter a location")
        
        with col3:
            # Use shared constants to prevent duplication
            mode_display_map_tab = MODE_DISPLAY_MAP
            search_display_options_tab = MODE_DISPLAY_OPTIONS.copy()
            if check_coach_permission('can_access_full_mode'):
                search_display_options_tab.append("1000 jobs")
            
            search_mode_display_tab = st.selectbox(
                "📊 Job Quantity:",
                search_display_options_tab,
                index=1,  # default to "100 jobs"
                help="Number of jobs to analyze and classify",
                key="tab_search_mode_display"
            )
            search_mode_tab = mode_display_map_tab[search_mode_display_tab]
        
        with col4:
            search_terms_tab = st.text_input(
                "🔍 Search Terms:",
                value="CDL Driver No Experience",
                help="Job search keywords. Use commas for multiple terms",
                key="tab_search_terms"
            )
        
        with col5:
            search_radius_tab = st.selectbox(
                "📏 Search Radius:",
                [25, 50, 100],
                index=1,  # default to 50
                help="Search radius in miles from target location",
                key="tab_search_radius"
            )
            exact_location_tab = st.checkbox(
                "📍 Use exact location only",
                value=False,
                help="Search only the specified city (radius=0)",
                key="tab_exact_location"
            )
            if exact_location_tab:
                search_radius_tab = 0
        
        # Row 3: Additional Options
        col1, col2, col3 = st.columns(3)
        with col1:
            no_experience_tab = st.checkbox(
                "📋 Indeed No Experience Filter",
                value=True,
                help="Include jobs that don't require prior experience",
                key="tab_no_experience"
            )
        
        # Set default value for removed advanced options
        push_to_airtable_tab = False
        
        
        # PDF Export Configuration
        st.markdown("### 📄 PDF Export Configuration")
        
        # Only show PDF generation if coach has permission
        if check_coach_permission('can_generate_pdf'):
            # Row 1: Max Jobs - automatically set based on search mode
            search_mode_to_pdf_limit = {
                'test': 10,    # "10 jobs" → 10 in PDF
                'mini': 50,    # "50 jobs" → 50 in PDF  
                'sample': 100, # "100 jobs" → 100 in PDF
                'medium': 100, # "250 jobs" → 100 in PDF (cap for readability)
                'large': 100,  # "500 jobs" → 100 in PDF (cap for readability)
                'full': 100    # "1000 jobs" → 100 in PDF (cap for readability)
            }
            default_pdf_limit = search_mode_to_pdf_limit.get(search_mode_tab, 50)
            default_index = 2  # default to 50
            pdf_options = [10, 25, 50, 100, "All"]
            if default_pdf_limit in pdf_options:
                default_index = pdf_options.index(default_pdf_limit)
            
            max_jobs_pdf_tab = st.selectbox(
                "📊 Maximum jobs in PDF:",
                options=pdf_options,
                index=default_index,
                help=f"Auto-set to {default_pdf_limit} based on '{search_mode_display_tab}' selection"
                # No key = always follows search mode default
            )
            
            # Row 2: Route Types and Job Quality Levels  
            col1, col2, col3 = st.columns(3)
            with col1:
                pdf_route_type_filter_tab = st.multiselect(
                    "🛣️ Route types:",
                    options=['Local', 'OTR', 'Unknown'],
                    default=['Local', 'OTR', 'Unknown'],
                    help="Which driving route types to include in PDF",
                    key="tab_pdf_route_type_filter"
                )
            with col2:
                pdf_match_quality_filter_tab = st.multiselect(
                    "⭐ Job quality levels:",
                    options=['good', 'so-so', 'bad'],
                    default=['good', 'so-so'],
                    help="Which AI quality assessments to include in PDF",
                    key="tab_pdf_match_quality_filter"
                )
            with col3:
                pdf_include_memory_jobs_tab = st.checkbox(
                    "🧠 Include memory jobs",
                    value=True,
                    help="Include recent jobs from memory database in PDF output",
                    key="tab_pdf_include_memory_jobs"
                )
            
            # Row 3: Fair Chance Only, HTML Preview, and Portal Link
            col_fair, col_preview, col_portal = st.columns(3)
            with col_fair:
                pdf_fair_chance_only_tab = st.checkbox(
                    "🤝 Fair chance jobs only", 
                    value=False,
                    help="Include only jobs friendly to people with records in PDF",
                    key="tab_pdf_fair_chance_only"
                )
            # Check if this is an Indeed search (needed for both preview and portal)
            # Default to False since search_type_tab is defined later in the button handlers
            is_indeed_search = False
            
            with col_preview:
                # Disable HTML preview for Indeed searches
                html_preview_help = "HTML preview not available for Indeed searches" if is_indeed_search else "Preview PDF layout in HTML format (same styling as PDF export)"
                
                show_html_preview_tab = st.checkbox(
                    "👁️ Show HTML preview", 
                    value=False,
                    help=html_preview_help,
                    disabled=is_indeed_search,
                    key="tab_show_html_preview"
                )
            with col_portal:
                # Disable portal links for any Indeed searches (fresh or memory) 
                portal_help = "Portal links not available for Indeed searches" if is_indeed_search else "Create a shareable job portal with current filters"
                
                generate_portal_link_tab = st.checkbox(
                    "🔗 Generate portal link", 
                    value=False,
                    help=portal_help,
                    disabled=is_indeed_search,
                    key="tab_generate_portal_link"
                )
                
            # Row 4: Additional Options
            col_prepared, col_empty1, col_empty2 = st.columns(3)
            with col_prepared:
                show_prepared_for_tab = st.checkbox(
                    "👤 Show 'prepared for' message",
                    value=True,
                    help="Include personalized 'Prepared for [Name] by Coach [Name]' message",
                    key="tab_show_prepared_for"
                )
        else:
            st.info("📄 PDF generation not available - contact admin for access")
            # Set default values for variables that would be defined in the PDF section
            max_jobs_pdf_tab = 50
            pdf_route_type_filter_tab = ['Local', 'OTR', 'Unknown']
            pdf_match_quality_filter_tab = ['good', 'so-so']
            pdf_include_memory_jobs_tab = True
            pdf_fair_chance_only_tab = False
            show_html_preview_tab = False
            generate_portal_link_tab = False
            show_prepared_for_tab = True
        
        # Free Agent Lookup Section
        st.markdown("### 👤 Free Agent Lookup")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            lookup_q_tab = st.text_input("Search", key="tab_candidate_lookup_q", placeholder="Type name, UUID, or email")
        with col2:
            lookup_by_tab = st.selectbox("By", ["name", "uuid", "email"], index=0, key="tab_candidate_lookup_by")
        with col3:
            st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
            do_lookup_tab = st.button("🔎 Search", key="tab_do_candidate_lookup")
        
        if do_lookup_tab and lookup_q_tab:
            # Use Supabase search for coach's saved agents
            current_coach = st.session_state.get('current_coach')
            coach_username = current_coach.username if current_coach else 'NOT LOGGED IN'
            try:
                from supabase_utils import supabase_find_agents
                st.session_state.candidate_search_results_tab = supabase_find_agents(
                    lookup_q_tab, 
                    coach_username=coach_username, 
                    by=lookup_by_tab, 
                    limit=15
                )
            except Exception as e:
                st.error(f"Search failed: {e}")
                st.session_state.candidate_search_results_tab = []
        
        results_tab = st.session_state.get("candidate_search_results_tab", [])
        if results_tab:
            def _label_tab(r):
                loc = ", ".join([x for x in [r.get('city') or '', r.get('state') or ''] if x])
                suffix = f" ({loc})" if loc else ""
                
                
                return f"{r['name']} — {r['uuid'] or 'no-uuid'}{suffix}"
            options_tab = [_label_tab(r) for r in results_tab]
            sel_tab = st.selectbox("Select Free Agent", options_tab, index=0, key="tab_candidate_select")
            if sel_tab and st.button("✅ Use Selected", key="tab_use_selected_candidate"):
                idx_tab = options_tab.index(sel_tab)
                chosen_tab = results_tab[idx_tab]
                st.session_state.candidate_id = chosen_tab.get("uuid", "")
                st.session_state.candidate_name = chosen_tab.get("name", "")
                st.rerun()  # Refresh to show the fields
        elif do_lookup_tab and lookup_q_tab:
            st.info("No candidates found. Try switching the search mode (name/uuid/email) or broadening your query.")
        
        # Manual Entry Option
        st.markdown("**Or manually enter free agent details:**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            manual_name_tab = st.text_input("Free Agent Name", key="tab_manual_name", placeholder="Enter full name")
        with col2:
            manual_uuid_tab = st.text_input("Agent UUID", key="tab_manual_uuid", placeholder="Enter UUID (optional)")
        with col3:
            st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
            use_manual_tab = st.button("✅ Use Manual Entry", key="tab_use_manual_entry")
        
        if use_manual_tab and manual_name_tab:
            # Generate UUID if not provided
            if not manual_uuid_tab:
                import uuid
                manual_uuid_tab = str(uuid.uuid4())
                st.info(f"Generated UUID: {manual_uuid_tab}")
            
            st.session_state.candidate_id = manual_uuid_tab
            st.session_state.candidate_name = manual_name_tab
            st.success(f"✅ Manually added: {manual_name_tab}")
            st.rerun()  # Refresh to show the fields
        
        # Show candidate fields only after successful selection
        if st.session_state.get("candidate_id") or st.session_state.get("candidate_name"):
            candidate_id_tab = st.text_input(
                "Selected Free Agent ID", 
                value=st.session_state.get("candidate_id", ""), 
                help="Selected Free Agent UUID for analytics tracking",
                key="tab_candidate_id",
                disabled=True  # Make it read-only
            )
            candidate_name_tab = st.text_input(
                "Selected Free Agent Name", 
                value=st.session_state.get("candidate_name", ""), 
                help="Used on PDF title page and link tags",
                key="tab_candidate_name",
                disabled=True  # Make it read-only
            )
        else:
            # Hidden fields for when no selection is made
            candidate_id_tab = ""
            candidate_name_tab = ""
        
        # Combined Row: Smart Memory and Search Options  
        with st.container():
            col1, col2 = st.columns([1, 1])  # Equal columns without cost
        with col1:
            st.markdown("### ⏰ Smart Memory")
            memory_time_period_tab = st.selectbox(
                "Lookback period:",
                options=['24h', '48h', '72h', '96h'],
                index=2,  # default to 72h
                help="How far back the smart memory system searches for existing jobs",
                key="tab_memory_time_period"
            )
        with col2:
            st.markdown("### 🚀 Search Options")
            # Row 1: Memory and Indeed+Memory
            col3_1, col3_2 = st.columns(2)
            with col3_1:
                memory_clicked_tab = st.button(
                    "💾 Memory Only", 
                    help="Search cached jobs - instant results, no API costs",
                    key="tab_memory_search_btn",
                    width='stretch'
                )
            with col3_2:
                # Disable fresh scraping if coach lacks permission
                _can_fresh = check_coach_permission('can_pull_fresh_jobs')
                indeed_clicked_tab = st.button(
                    "🔍 Indeed + Memory",
                    help="Fresh Indeed scrape plus memory jobs",
                    key="tab_indeed_search_btn",
                    width='stretch',
                    disabled=not _can_fresh
                )
            # Row 2: Fresh and Google
            col3_3, col3_4 = st.columns(2)
            with col3_3:
                indeed_fresh_clicked_tab = st.button(
                    "🔍 Indeed Fresh Only",
                    help="Search Indeed API only, bypass memory cache",
                    key="tab_indeed_fresh_btn",
                    width='stretch',
                    disabled=not _can_fresh
                )
            with col3_4:
                # Google ordering removed from Job Search page
                pass
        
        # Brief permission hints under buttons
        try:
            hint_cols = st.columns(2)
            with hint_cols[0]:
                if not _can_fresh:
                    st.caption("🔒 Fresh scraping disabled for this coach")
            with hint_cols[1]:
                if not _can_google:
                    st.caption("🔒 Google Jobs disabled for this coach")
        except Exception:
            pass
        
        # Advanced Options for Job Search tab
        with st.expander("🔧 Advanced Options"):
            # Only show Force Fresh Classification if coach has permission  
            force_fresh_classification_tab = False
            if check_coach_permission('can_force_fresh_classification'):
                force_fresh_classification_tab = st.checkbox(
                    "⚡ Force Fresh Classification", 
                    value=False, 
                    help="Re-run AI classification even on cached jobs (useful when testing new prompts)",
                    key="tab_force_fresh_classification"
                )
        
        # Handle button clicks in Job Search tab
        search_type_tab = None
        if memory_clicked_tab:
            search_type_tab = 'memory'
        elif indeed_clicked_tab:
            search_type_tab = 'indeed'
        elif indeed_fresh_clicked_tab:
            search_type_tab = 'indeed_fresh'
        # Google ordering removed from Job Search page
        
        # Search results section
        st.markdown("### 📊 Search Results")
        # Debug/export helpers visible regardless of results presence
        with st.expander("🧪 Debug / Export", expanded=False):
            st.caption("Use these tools to inspect pipeline outputs even if no rows display")
            col_dbg1, col_dbg2 = st.columns(2)
            with col_dbg1:
                export_combined_parquet = st.checkbox("Enable Parquet Export", value=False, key="tab_enable_parquet")
            with col_dbg2:
                show_market_counts = st.checkbox("Show per-market counts", value=False, key="tab_show_market_counts")
        
        # Initialize variables to prevent NameError
        import pandas as pd
        df = pd.DataFrame()
        metadata = {'success': False, 'message': 'No search executed'}
        
        if search_type_tab:
            if not location_tab:
                st.error("❌ Please select a location first")
            else:
                # Determine final location for search
                final_location_tab = location_tab
                if location_type_tab == "Custom Location" and custom_location_tab:
                    final_location_tab = custom_location_tab
                
                # Build parameters for pipeline (same as sidebar)
                params = {
                    'mode': search_mode_tab,
                    'search_terms': search_terms_tab,
                    'push_to_airtable': False,
                    'generate_pdf': False,
                    'search_radius': search_radius_tab,
                    'force_fresh_classification': force_fresh_classification_tab if 'force_fresh_classification_tab' in locals() else False,
                    'coach_name': coach.full_name,
                    'coach_username': coach.username,
                    'candidate_id': st.session_state.get('candidate_id', '').strip() or (candidate_id_tab.strip() if candidate_id_tab else ""),
                    'candidate_name': st.session_state.get('candidate_name', '').strip() or (candidate_name_tab.strip() if candidate_name_tab else ""),
                }
                
                # Add search-type specific parameters
                if search_type_tab == 'memory':
                    params.update({
                        'memory_only': True,
                        'memory_hours': int(memory_time_period_tab.replace('h','') or 72),
                        'search_sources': {'indeed': False, 'google': False},
                        'search_strategy': 'memory_first'
                        # DO NOT set ui_direct=True - let memory searches use dedicated memory path
                    })
                elif search_type_tab == 'indeed':
                    params.update({
                        'memory_only': False,
                        'search_sources': {'indeed': True, 'google': False},
                        'search_strategy': 'memory_first'
                    })
                elif search_type_tab == 'indeed_fresh':
                    params.update({
                        'memory_only': False,
                        'force_fresh': True,
                        'search_sources': {'indeed': True, 'google': False},
                        'search_strategy': 'fresh_only'
                    })
                # Google ordering removed from Job Search page
                
                # Add location parameters (for non-Google searches)
                if location_type_tab == "Select Market":
                    params.update({
                        'location_type': 'markets',
                        'markets': selected_market_tab,
                        'location': location_tab
                    })
                else:
                    params.update({
                        'location_type': 'custom',
                        'custom_location': custom_location_tab,
                        'location': final_location_tab
                    })
                
                # Add PDF parameters (always generate PDF) - use correct parameter names for pipeline
                params.update({
                    'generate_pdf': True,  # Enable PDF generation
                    'max_jobs': max_jobs_pdf_tab if max_jobs_pdf_tab != "All" else 999,  # Pipeline expects 'max_jobs'
                    'route_type_filter': pdf_route_type_filter_tab,  # Pipeline expects 'route_type_filter'
                    'match_quality_filter': pdf_match_quality_filter_tab,  # Pipeline expects 'match_quality_filter' 
                    'fair_chance_only': pdf_fair_chance_only_tab  # Pipeline expects 'fair_chance_only'
                })
                
                # Run pipeline with appropriate spinner message (non-Google searches only)
                if search_type_tab and search_type_tab != 'google':  # Only run pipeline for non-Google searches
                    # Display selected market names (not underlying city used for queries)
                    try:
                        if location_type_tab == "Select Market" and selected_market_tab:
                            display_location_tab = selected_market_tab
                        else:
                            display_location_tab = final_location_tab
                    except Exception:
                        display_location_tab = final_location_tab

                    search_messages = {
                        'memory': f"💾 Searching memory only for jobs in {display_location_tab}...",
                        'indeed': f"🔍 Searching Indeed + Memory for jobs in {display_location_tab}...",
                        'indeed_fresh': f"🔍 Searching fresh Indeed jobs in {display_location_tab}..."
                    }

                    # Use full pipeline for memory searches to enable URL generation and PDF creation
                    if search_type_tab == 'memory':
                        # Configure pipeline parameters for memory-heavy search with URL generation and PDF
                        params.update({
                            'memory_only': True,  # Use memory as primary source
                            'generate_pdf': True,  # Enable PDF generation with tracking URLs
                            'generate_csv': True,  # Enable CSV export
                            'force_fresh': False,  # Don't bypass memory
                            'memory_hours': int(memory_time_period_tab.replace('h','') or 72),
                            'mode': search_mode_tab,  # Use selected search mode instead of hardcoded 'sample'
                            'job_limit': max_jobs_pdf_tab if 'max_jobs_pdf_tab' in locals() and max_jobs_pdf_tab != "All" else 50  # Respect PDF quantity setting
                        })
                        
                        # Override local variables for memory search download buttons
                        generate_pdf = True  # Force PDF generation for memory searches
                        generate_csv = True  # Force CSV generation for memory searches
                        
                        # Add coach and candidate information to params for PDF generation
                        coach = st.session_state.get('current_coach')
                        if coach:
                            params['coach_name'] = coach.full_name
                            params['coach_username'] = coach.username
                        
                        # Add candidate information if available (prioritize session state)
                        candidate_id = st.session_state.get('candidate_id', '').strip()
                        candidate_name = st.session_state.get('candidate_name', '').strip()
                        # Fallback to local variables if session state is empty
                        if not candidate_id and 'candidate_id_tab' in locals() and locals()['candidate_id_tab']:
                            candidate_id = str(locals()['candidate_id_tab']).strip()
                        if not candidate_name and 'candidate_name_tab' in locals() and locals()['candidate_name_tab']:
                            candidate_name = str(locals()['candidate_name_tab']).strip()
                        
                        if candidate_id or candidate_name:
                            params['candidate_id'] = candidate_id
                            params['candidate_name'] = candidate_name
                        
                        # Run full pipeline for memory search (enables URL generation and PDF)
                        with st.spinner(search_messages.get(search_type_tab, "Searching...")):
                            df, metadata = pipeline.run_pipeline(params)
                            
                            # Add coach and candidate info to ALL jobs in DataFrame (for link tracking and PDF)
                            if not df.empty:
                                coach = st.session_state.get('current_coach')
                                if coach:
                                    df['meta.coach_name'] = coach.full_name
                                    df['meta.coach_username'] = coach.username
                                    df['meta.candidate_name'] = candidate_name_tab if 'candidate_name_tab' in locals() else st.session_state.get('candidate_name', '')
                                    df['meta.candidate_id'] = candidate_id_tab if 'candidate_id_tab' in locals() else st.session_state.get('candidate_id', '')
                        
                        # Jobs Report PDF button removed per user request
                    else:
                        # Add coach and candidate information to params for PDF generation
                        coach = st.session_state.get('current_coach')
                        if coach:
                            params['coach_name'] = coach.full_name
                            params['coach_username'] = coach.username
                        
                        # Add candidate information if available (prioritize session state)
                        candidate_id = st.session_state.get('candidate_id', '').strip()
                        candidate_name = st.session_state.get('candidate_name', '').strip()
                        # Fallback to local variables if session state is empty
                        if not candidate_id and 'candidate_id_tab' in locals() and locals()['candidate_id_tab']:
                            candidate_id = str(locals()['candidate_id_tab']).strip()
                        if not candidate_name and 'candidate_name_tab' in locals() and locals()['candidate_name_tab']:
                            candidate_name = str(locals()['candidate_name_tab']).strip()
                        
                        if candidate_id or candidate_name:
                            params['candidate_id'] = candidate_id
                            params['candidate_name'] = candidate_name
                        
                        with st.spinner(search_messages.get(search_type_tab, "Searching...")):
                            df, metadata = pipeline.run_pipeline(params)
                            
                            # Add coach and candidate info to ALL jobs in DataFrame (for link tracking and PDF)
                            if not df.empty:
                                if coach:
                                    df['meta.coach_name'] = coach.full_name
                                    df['meta.coach_username'] = coach.username
                                    df['meta.candidate_name'] = candidate_name
                                    df['meta.candidate_id'] = candidate_id
                else:
                    # For Google searches or when no search type, initialize empty results  
                    import pandas as pd
                    df, metadata = pd.DataFrame(), {'success': True, 'message': 'Google search submitted'}
                
                # Export combined Parquet from DataFrame if enabled (visible before results)
                try:
                    if export_combined_parquet and isinstance(df, pd.DataFrame) and not df.empty:
                        from datetime import datetime as _dt
                        parquet_bytes = pipeline.dataframe_to_parquet_bytes(df) if hasattr(pipeline, 'dataframe_to_parquet_bytes') else b""
                        if parquet_bytes:
                            st.download_button(
                        
                                label="📦 Download Parquet (Combined Results)",
                                data=parquet_bytes,
                                file_name=f"combined_results_{_dt.now().strftime('%Y%m%d_%H%M%S')}.parquet",
                                mime="application/octet-stream",
                                key="tab_parquet_dl"
                            )
                except Exception:
                    pass
                # Optional per-market counts for multi-market runs
                try:
                    if show_market_counts and hasattr(df, 'columns') and 'meta.market' in df.columns:
                        mc = df['meta.market'].value_counts().to_frame('rows')
                        st.markdown("#### Per-market row counts")
                        st.dataframe(mc, width='stretch', height=200)
                except Exception:
                    pass
                
                # Store results in session state
                st.session_state.last_results = {
                    'df': df,
                    'metadata': metadata,
                    'params': params,
                    'search_type': search_type_tab,
                    'timestamp': datetime.now()
                }
                
                # Display results (fallback to DataFrame presence)
                if (isinstance(df, pd.DataFrame) and not df.empty) or (metadata and metadata.get('success', False)):
                    # Compute quality jobs across all markets for the success message
                    try:
                        ai_series = df.get('ai.match')
                        if ai_series is not None:
                            _q = int((ai_series == 'good').sum() + (ai_series == 'so-so').sum())
                        elif 'route.final_status' in df.columns:
                            _q = int(df['route.final_status'].astype(str).str.startswith('included').sum())
                        else:
                            _q = len(df)
                    except Exception:
                        _q = metadata.get('quality_jobs', 0)
                    st.success(f"✅ Search completed! Found {_q} quality jobs")
                    
                    # Multi-market metrics display
                    st.markdown("### 📊 Search Results Analytics")
                    try:
                        # Global combined metrics computed from DataFrame (ALL markets)
                        ai_series = df.get('ai.match')
                        route_series = df.get('ai.route_type')
                        ai_good = int((ai_series == 'good').sum()) if ai_series is not None else 0
                        ai_soso = int((ai_series == 'so-so').sum()) if ai_series is not None else 0
                        quality_jobs = ai_good + ai_soso
                        total_jobs = int(len(df))
                        local_routes = int((route_series == 'Local').sum()) if route_series is not None else 0

                        c1, c2, c3, c4, c5 = st.columns(5)
                        with c1:
                            st.metric("Quality Jobs Found", quality_jobs)
                        with c2:
                            st.metric("Total Jobs Analyzed", total_jobs)
                        with c3:
                            st.metric("Excellent Matches", ai_good)
                        with c4:
                            st.metric("Possible Fits", ai_soso)
                        with c5:
                            st.metric("Local Routes", local_routes)

                    except Exception:
                        pass

                    # Parquet download
                    parquet_path = metadata.get('parquet_path')
                    if parquet_path:
                        try:
                            pq_bytes = pipeline.get_parquet_bytes(parquet_path) if hasattr(pipeline, 'get_parquet_bytes') else None
                            if pq_bytes:
                                st.download_button(
                                    label="📦 Download Parquet (Complete Results)",
                                    data=pq_bytes,
                                    file_name=os.path.basename(parquet_path),
                                    mime="application/octet-stream",
                                    use_container_width=True
                                )
                        except Exception:
                            pass


                    # Per-market sections with visibility fixes
                    try:
                        if 'meta.market' in df.columns:
                            unique_mkts = [m for m in df['meta.market'].dropna().unique().tolist() if str(m).strip() != '' ]
                            if len(unique_mkts) >= 1:
                                # Show market count indicator to help debug missing markets
                                st.info(f"📊 **{len(unique_mkts)} markets found**: {', '.join(unique_mkts)}")
                                
                                # Simplified market ordering - just sort them alphabetically
                                ordered = sorted(unique_mkts, key=lambda s: s.lower())
                                

                                for mk in ordered:
                                    try:  # Wrap each market section to prevent one market from breaking others
                                        # Market header with PDF generation
                                        st.markdown("---")
                                        col_h, col_btn = st.columns([8, 2])
                                        with col_h:
                                            st.markdown(f"## 📍 **{mk}**")
                                            st.caption(f"Jobs found in {mk}")
                                        with col_btn:
                                            # Download link to pipeline-generated PDF (includes all markets)
                                            if metadata.get('pdf_path'):
                                                try:
                                                    pdf_bytes = pipeline.get_pdf_bytes(metadata['pdf_path'])
                                                    if pdf_bytes:
                                                        st.download_button(
                                                            label="📄 Download PDF",
                                                            data=pdf_bytes,
                                                            file_name="freeworld_jobs_report.pdf",
                                                            mime="application/pdf",
                                                            key=f"download_pipeline_pdf_{mk}",
                                                            use_container_width=True
                                                        )
                                                except Exception:
                                                    st.caption("PDF unavailable")

                                        # Market-specific dataframe
                                        mdf = df[df['meta.market'] == mk]
                                        
                                        # Filter for quality jobs using standardized logic
                                        debug_dataframe_info(mdf, f"Market {mk} - All Jobs")
                                        mdf_inc = filter_quality_jobs(mdf)
                                        debug_dataframe_info(mdf_inc, f"Market {mk} - Quality Jobs")

                                        # Market job table with height constraint to prevent viewport overflow
                                        cols_pref = ['source.title', 'source.company', 'ai.summary', 'ai.match', 'ai.route_type', 'ai.fair_chance', 'source.indeed_url']
                                        cols_show = [c for c in cols_pref if c in mdf_inc.columns]
                                        st.dataframe(
                                            mdf_inc[cols_show] if cols_show else mdf_inc, 
                                            use_container_width=True, 
                                            height=400  # Limit height to ensure all markets are visible
                                        )

                                        # Per-market metrics using standardized calculation
                                        try:
                                            total_metrics = calculate_search_metrics(mdf)
                                            quality_metrics = calculate_search_metrics(mdf_inc)
                                            inc_count = len(mdf_inc)
                                            total_count = len(mdf)
                                            
                                            colA, colB, colC, colD = st.columns(4)
                                            with colA:
                                                st.metric("Quality Jobs Found", inc_count)
                                            with colB:
                                                st.metric("Total Jobs Analyzed", total_count)
                                            with colC:
                                                st.metric("Excellent Matches", quality_metrics['good'])
                                            with colD:
                                                st.metric("Possible Fits", quality_metrics['so_so'])
                                            colE, colF = st.columns(2)
                                            with colE:
                                                st.metric("Local Routes", quality_metrics['local'])
                                            with colF:
                                                st.metric("OTR Routes", quality_metrics['otr'])
                                        except Exception:
                                            pass

                                        # Full results for this market
                                        with st.expander(f"🔎 Full Results — {mk}", expanded=False):
                                            st.dataframe(mdf, use_container_width=True, height=480)

                                    except Exception as e:
                                        st.error(f"❌ Error displaying {mk} market: {str(e)}")
                                    
                                    st.markdown("---")
                    except Exception:
                        pass
                    
                    # CSV download removed per new UI
                    
                    # (Removed top-level PDF download; PDFs are per-market)
                    
                    # HTML Preview if enabled (but NOT for Indeed searches)
                    if show_html_preview_tab and jobs_dataframe_to_dicts and render_jobs_html and not df.empty and search_type_tab not in ['indeed_fresh', 'indeed']:
                        try:
                            st.markdown("### 👁️ HTML Preview")
                            
                            # IMPORTANT: Use the same processing as PDF to include tracked URLs
                            from free_agent_system import update_job_tracking_for_agent
                            agent_params = {
                                'location': final_location_tab,
                                'agent_name': candidate_name_tab,
                                'agent_uuid': candidate_id_tab,
                                'coach_username': get_current_coach_name(),
                                'show_prepared_for': show_prepared_for_tab
                            }
                            
                            # Supabase has already filtered by route type and quality - no need for post-processing
                            filtered_df = df
                            
                            # Filter by fair chance only
                            if pdf_fair_chance_only_tab and 'ai.fair_chance_employer' in filtered_df.columns:
                                filtered_df = filtered_df[filtered_df['ai.fair_chance_employer'] == True]
                            
                            # Apply max jobs limit
                            if max_jobs_pdf_tab != "All":
                                filtered_df = filtered_df.head(max_jobs_pdf_tab)
                            
                            # Process DataFrame the same way PDF does
                            processed_df = update_job_tracking_for_agent(filtered_df, agent_params)
                            jobs = jobs_dataframe_to_dicts(processed_df)
                            
                            html = render_jobs_html(jobs, agent_params)
                            phone_html = wrap_html_in_phone_screen(html)
                            st.components.v1.html(phone_html, height=900, scrolling=False)
                        except Exception as e:
                            st.error(f"HTML preview error: {e}")
                    
                    # Portal Link Generation if enabled (but NOT for any Indeed searches)
                    if generate_portal_link_tab and search_type_tab not in ['indeed_fresh', 'indeed']:
                        try:
                            st.markdown("### 🔗 Custom Job Portal Link")
                            
                            # Use ALL current search form parameters (exactly like the pipeline params)
                            portal_config = {
                                # Base parameters from search form
                                'mode': search_mode_tab,
                                'search_terms': search_terms_tab,
                                'search_radius': search_radius_tab,
                                'force_fresh_classification': force_fresh_classification_tab if 'force_fresh_classification_tab' in locals() else False,
                                
                                # Location parameters
                                'location': final_location_tab,
                                'location_type': location_type_tab,
                                
                                # Search type specific parameters
                                'search_type': search_type_tab,
                                'memory_hours': int(memory_time_period_tab.replace('h','') or 72) if search_type_tab == 'memory' else 72,
                                
                                # PDF/Filter parameters (use the form values directly)
                                'max_jobs': max_jobs_pdf_tab if max_jobs_pdf_tab != "All" else 50,
                                'route_type_filter': pdf_route_type_filter_tab,  # Pipeline expects route_type_filter
                                'match_quality_filter': pdf_match_quality_filter_tab,
                                'include_memory_jobs': pdf_include_memory_jobs_tab,
                                'fair_chance_only': pdf_fair_chance_only_tab,
                                'no_experience': no_experience_tab,
                                
                                # Location type specific parameters
                                'selected_market': selected_market_tab if location_type_tab == "Select Market" else None,
                                'custom_location': custom_location_tab if location_type_tab == "Custom Location" else None,
                            }

                            # Add Free Agent info if provided
                            if candidate_id_tab and candidate_name_tab:
                                portal_config.update({
                                    'agent_uuid': candidate_id_tab,
                                    'agent_name': candidate_name_tab,
                                    'coach_username': get_current_coach_name(),
                                    'show_prepared_for': show_prepared_for_tab
                                })

                            # Generate encoded configuration
                            from free_agent_system import encode_agent_params
                            
                            # Use modern parameter names (agent portal now supports both old and new)
                            agent_params = portal_config.copy()
                            
                            encoded_config = encode_agent_params(agent_params)

                            # Create portal URL - use QA environment and correct format
                            base_url = "https://fwcareertest.streamlit.app"  # QA portal URL  
                            portal_url = f"{base_url}/agent_job_feed?config={encoded_config}"  # Use same format as free_agent_system.py
                            
                            # Add candidate_id parameter if available
                            if candidate_id_tab:
                                portal_url += f"&candidate_id={candidate_id_tab}"
                            
                            # Create shortened link
                            from link_tracker import LinkTracker
                            link_tracker = LinkTracker()
                            
                            # Prepare tags for tracking (handle both parameter names)
                            route_for_tags = portal_config.get('route_filter') or portal_config.get('route_type_filter', 'both')
                            portal_tags = f"coach:{get_current_coach_name()},market:{final_location_tab},route:{route_for_tags}"
                            if pdf_fair_chance_only_tab:
                                portal_tags += ",fair_chance:true"
                            
                            # Generate shortened URL
                            title = f"Portal - {candidate_name_tab}" if candidate_name_tab else f"Portal - {final_location_tab}"
                            candidate_id = candidate_id_tab if candidate_id_tab else ""
                            
                            shortened_url = link_tracker.create_short_link(
                                portal_url,
                                title=title,
                                tags=portal_tags,
                                candidate_id=candidate_id
                            )

                            # Display the shortened link with copy functionality
                            st.success("✅ **Custom Job Portal Generated!**")
                            st.code(shortened_url, language="text")

                            # Show portal configuration summary
                            with st.expander("🔍 Portal Configuration Summary"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("📍 **Location:**", portal_config['location'])
                                    st.write("🔍 **Search Type:**", search_type_tab.title() if search_type_tab else "None")
                                    st.write("⚙️ **Mode:**", portal_config['mode'])
                                    st.write("📊 **Max Jobs:**", portal_config['max_jobs'])
                                    st.write("🔄 **Search Radius:**", f"{portal_config['search_radius']} miles")
                                with col2:
                                    st.write("🛣️ **Route Filter:**", portal_config.get('route_type_filter', ['All']))
                                    st.write("🎓 **No Experience Required:**", "Yes" if portal_config.get('no_experience', False) else "No")
                                    st.write("🤝 **Fair Chance Only:**", "Yes" if portal_config['fair_chance_only'] else "No")
                                    if candidate_name_tab:
                                        st.write("👤 **Free Agent:**", candidate_name_tab)
                                    if search_terms_tab:
                                        st.write("🔎 **Search Terms:**", search_terms_tab)

                            st.info("💡 **Tip:** This shortened link contains ALL your current search settings and will run the same search when accessed!")

                        except Exception as e:
                            st.error(f"Portal link generation error: {e}")
                        
                    # Top-level combined quality jobs display - using standardized filtering
                    quality_df = filter_quality_jobs(df)
                    debug_dataframe_info(df, "All Jobs")
                    debug_dataframe_info(quality_df, "Top-Level Quality Jobs")
                    
                    
                    # DISABLED: Duplicate per-market section (keeping only the first one)
                    if False:
                        try:
                            # Build normalized, deduplicated and safely sortable market list
                            markets_series = df['meta.market'].dropna().astype(str)
                            markets_clean = sorted({m.strip() for m in markets_series if m.strip()}, key=lambda s: s.lower())
                            if len(markets_clean) > 1:  # Only show per-market if multiple markets
                                st.markdown("---")
                                
                                for market in markets_clean:
                                    market_df = df[df['meta.market'] == market].copy()
                                    # Supabase has already filtered by route type, quality, and fair chance - no post-processing needed
                                    market_quality = market_df
                                    
                                    # Apply max jobs limit for PDF generation
                                    if 'max_jobs_pdf_tab' in locals() and max_jobs_pdf_tab != "All":
                                        market_quality = market_quality.head(max_jobs_pdf_tab)
                                    
                                    if not market_df.empty:
                                        col_header, col_pdf = st.columns([3, 1])
                                        with col_header:
                                            st.markdown(f"#### 📍 {market}")
                                            # Show if PDF limit was applied
                                            pdf_limit_text = ""
                                            if 'max_jobs_pdf_tab' in locals() and max_jobs_pdf_tab != "All":
                                                original_quality = market_df[market_df['ai.match'].isin(['good', 'so-so'])] if 'ai.match' in market_df.columns else market_df
                                                if len(original_quality) > max_jobs_pdf_tab:
                                                    pdf_limit_text = f" (PDF limited to {max_jobs_pdf_tab})"
                                            st.caption(f"Quality jobs: {len(market_quality)} | Total: {len(market_df)}{pdf_limit_text}")
                                    
                                    with col_pdf:
                                        # Market PDF generation with side-by-side buttons
                                        col_market_gen, col_market_download = st.columns([1, 1])
                                        
                                        with col_market_gen:
                                            generate_market_clicked = st.button(f"📄 Generate", key=f"market_pdf_tab_{market}_btn")
                                        
                                        # Check if we have a generated PDF for this market in session state
                                        market_pdf_key = f"market_pdf_{market}_{hash(str(market_quality.index.tolist()))}"
                                        
                                        if generate_market_clicked:
                                            with st.spinner(f"🔗 Generating PDF with fresh tracking links for {market}..."):
                                                try:
                                                    # Create fresh tracked links for market PDF
                                                    from link_tracker import LinkTracker
                                                    if LinkTracker:
                                                        link_tracker = LinkTracker()
                                                        if link_tracker.is_available:
                                                            url_mapping = {}
                                                            for _, job in market_quality.iterrows():
                                                                original_url = (
                                                                    job.get('source.indeed_url', '') or 
                                                                    job.get('source.google_url', '') or 
                                                                    job.get('source.apply_url', '')
                                                                )
                                                                job_id = job.get('id.job', '')
                                                                
                                                                if original_url and len(original_url) > 10 and job_id:
                                                                    try:
                                                                        # Get candidate info from DataFrame metadata (same source as PDF)
                                                                        coach_username = coach.username
                                                                        candidate_name = job.get('meta.candidate_name', '') if 'meta.candidate_name' in job else ''
                                                                        candidate_id = job.get('meta.candidate_id', '') if 'meta.candidate_id' in job else ''
                                                                        
                                                                        tags = [f"coach:{coach_username}", f"market:{market}", "market_pdf"]
                                                                        if candidate_id:
                                                                            tags.append(f"candidate:{candidate_id}")
                                                                        if candidate_name:
                                                                            tags.append(f"agent:{candidate_name.replace(' ', '-')}")
                                                                        
                                                                        job_title = job.get('source.title', f"Job {job_id[:8]}")
                                                                        tracked_url = link_tracker.create_short_link(
                                                                            original_url,
                                                                            title=f"{market} - {job_title}",
                                                                            tags=tags,
                                                                            candidate_id=candidate_id
                                                                        )
                                                                        
                                                                        if tracked_url and tracked_url != original_url:
                                                                            url_mapping[job_id] = tracked_url
                                                                    except Exception as e:
                                                                        print(f"Link generation failed for {job_id[:8]}: {e}")
                                                            
                                                            if url_mapping:
                                                                updated_market_df = market_quality.copy()
                                                                for job_id, tracked_url in url_mapping.items():
                                                                    mask = updated_market_df['id.job'] == job_id
                                                                    updated_market_df.loc[mask, 'meta.tracked_url'] = tracked_url
                                                                
                                                                # Generate PDF using correct method
                                                                try:
                                                                    # Initialize a fresh pipeline wrapper locally for PDF gen
                                                                    from pipeline_wrapper import StreamlitPipelineWrapper
                                                                    _pipeline = StreamlitPipelineWrapper()

                                                                    pdf_bytes = None
                                                                    if hasattr(_pipeline, 'generate_pdf_from_canonical'):
                                                                        # Add coach and candidate info to DataFrame so it travels with the data
                                                                        pdf_df = updated_market_df.copy()
                                                                        candidate_name = st.session_state.get('candidate_name', '')
                                                                        candidate_id = st.session_state.get('candidate_id', '')
                                                                        
                                                                        # Add metadata columns to first row (PDF generator will read these)
                                                                        if len(pdf_df) > 0:
                                                                            pdf_df['meta.coach_name'] = coach.full_name
                                                                            pdf_df['meta.coach_username'] = coach.username  
                                                                            pdf_df['meta.candidate_name'] = candidate_name
                                                                            pdf_df['meta.candidate_id'] = candidate_id
                                                                            
                                                                        print(f"🔍 PDF DataFrame Info Added:")
                                                                        print(f"   Coach: {coach.full_name}")
                                                                        print(f"   Candidate: {candidate_name}")
                                                                        
                                                                        pdf_bytes = _pipeline.generate_pdf_from_canonical(
                                                                            pdf_df,
                                                                            market_name=market
                                                                        )
                                                                    if pdf_bytes:
                                                                        # Store PDF in session state
                                                                        st.session_state[market_pdf_key] = {
                                                                            'pdf_bytes': pdf_bytes,
                                                                            'filename': f"FreeWorld_Jobs_{market}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                                                            'timestamp': pd.Timestamp.now()
                                                                        }
                                                                        st.success(f"✅ {market} PDF generated!")
                                                                    else:
                                                                        st.error("PDF generation returned no data")
                                                                except Exception as e:
                                                                    st.error(f"PDF generation error: {e}")
                                                except Exception as e:
                                                    st.error(f"Market PDF error: {e}")
                                        
                                        # Show download button if PDF is ready
                                        with col_market_download:
                                            if market_pdf_key in st.session_state:
                                                pdf_data = st.session_state[market_pdf_key]
                                                st.download_button(
                                                    label=f"📥 Download",
                                                    data=pdf_data['pdf_bytes'],
                                                    file_name=pdf_data['filename'],
                                                    mime="application/pdf",
                                                    key=f"download_market_pdf_tab_{market}",
                                                    use_container_width=True
                                                )
                                    
                                    # Quality jobs for this market
                                    if not market_quality.empty:
                                        market_display_cols = ['source.title', 'source.company', 'ai.summary', 'ai.match', 'ai.route_type', 'meta.tracked_url']
                                        market_available_cols = [col for col in market_display_cols if col in market_quality.columns]
                                        market_display_df = market_quality[market_available_cols].copy().reset_index(drop=True)
                                        st.dataframe(market_display_df, width="stretch", height=300, hide_index=True)
                                    
                                    # Collapsed full data for this market
                                    with st.expander(f"🔍 Full Data - {market} ({len(market_df)} total jobs)", expanded=False):
                                        full_market_df = market_df.copy().reset_index(drop=True)
                                        st.dataframe(full_market_df, width="stretch", height=400, hide_index=True)
                                    
                                    st.markdown("---")
                        except Exception as e:
                            st.warning(f"⚠️ Per-market display error: {e}")
                    
                    if not df.empty:
                        st.balloons()
                else:
                    # If metadata says failed but we have rows, still show them for debugging
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        st.warning("⚠️ Metadata reported failure, but results contain rows. Showing data.")
                        display_df = df.copy().reset_index(drop=True)
                        st.dataframe(display_df, width="stretch", height=420, hide_index=True)
                    else:
                        st.error(f"❌ Search failed: {metadata.get('error', 'Unknown error')}")
        else:
            # Only show placeholder message if no persistent results exist
            if 'last_results' not in st.session_state:
                st.info("🚧 Click a search button above to start searching for jobs...")
    
    elif selected_tab == "🗓️ Batches & Scheduling":
        show_combined_batches_and_scheduling_page(coach)
    
    elif selected_tab == "👥 Free Agents":
        show_free_agent_management_page(coach)
    
    elif selected_tab == "📊 Coach Analytics":
        st.header("📊 Coach Performance Analytics")
        st.markdown("Track your performance and compare with other coaches.")
        
        try:
            from src.coach_analytics import get_coach_performance_metrics, get_coach_comparison_data
            
            # Date range selector for coach analytics
            col1, col2 = st.columns(2)
            with col1:
                coach_analytics_start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30), key="coach_analytics_start_date")
            with col2:
                coach_analytics_end_date = st.date_input("End Date", value=datetime.now(), key="coach_analytics_end_date")

            # Convert to datetime objects with timezone info
            start_dt = datetime.combine(coach_analytics_start_date, datetime.min.time(), tzinfo=timezone.utc)
            end_dt = datetime.combine(coach_analytics_end_date, datetime.max.time(), tzinfo=timezone.utc)

            # Get current coach's performance metrics
            st.subheader(f"Your Performance ({coach.full_name})")
            my_metrics = get_coach_performance_metrics(coach.username, start_dt, end_dt)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Clicks", my_metrics.get("total_clicks", 0))
            with col2:
                st.metric("Unique Agents Engaged", my_metrics.get("unique_agents_engaged", 0))
            with col3:
                st.metric("Avg Clicks/Agent", f"{my_metrics.get('avg_clicks_per_agent', 0.0):.1f}")
            with col4:
                quality_breakdown = my_metrics.get("job_quality_breakdown", {})
                good_jobs = quality_breakdown.get('good', 0)
                st.metric("Good Jobs Clicked", good_jobs)

            st.subheader("Coach Comparison")
            all_coach_usernames = [c.username for c in coach_manager.coaches.values() if c.username != 'admin']
            selected_coaches_for_comparison = st.multiselect(
                "Select Coaches to Compare",
                options=all_coach_usernames,
                default=[coach.username] if coach.username in all_coach_usernames else [],
                key="coach_comparison_select"
            )

            if selected_coaches_for_comparison:
                comparison_data = get_coach_comparison_data(selected_coaches_for_comparison, start_dt, end_dt)
                import pandas as pd
                comparison_df = pd.DataFrame([
                    {
                        "Coach": coach_manager.coaches.get(u, type('obj', (object,), {'full_name': u})).full_name,
                        "Total Clicks": data.get("total_clicks", 0),
                        "Unique Agents": data.get("unique_agents_engaged", 0),
                        "Avg Clicks/Agent": f"{data.get('avg_clicks_per_agent', 0.0):.1f}",
                        "Good Jobs Clicked": data.get("job_quality_breakdown", {}).get('good', 0)
                    }
                    for u, data in comparison_data["coaches"].items()
                ])
                st.dataframe(comparison_df, width="stretch")
                
        except ImportError as e:
            st.error(f"Coach analytics not available: {e}")
            st.info("Coach analytics require the analytics modules to be properly set up.")
    
    elif selected_tab.startswith("👑 Admin Panel") or selected_tab == "🔒 Restricted":
        if coach.role == 'admin':
            st.header("👑 Admin Panel")
            
            # Initialize session state for admin function selection
            admin_function_options = ["Manage Coaches", "View Analytics", "System Settings"]
            if 'admin_function_index' not in st.session_state:
                st.session_state.admin_function_index = 0
            
            # Use radio buttons for admin function selection
            admin_tab_select = st.radio(
                "Admin Function",
                options=admin_function_options,
                index=st.session_state.admin_function_index,
                key="admin_function_radio",
                horizontal=True
            )
            
            # Update session state
            if admin_tab_select in admin_function_options:
                st.session_state.admin_function_index = admin_function_options.index(admin_tab_select)
            
            if admin_tab_select == "Manage Coaches":
                st.markdown("### ➕ Add New Coach")
                with st.form("tab_add_coach"):
                    new_username = st.text_input("Username", placeholder="new.coach", key="tab_new_username")
                    new_fullname = st.text_input("Full Name", placeholder="New Coach", key="tab_new_fullname") 
                    new_email = st.text_input("Email", placeholder="new@freeworld.com", key="tab_new_email")
                    new_password = st.text_input("Password", placeholder="coach123", key="tab_new_password")
                    new_is_test = st.checkbox("Test Account (Memory-only, no API calls)", value=False, help="Test accounts can only use cached jobs, no outscraper/openai calls", key="tab_new_is_test")
                    new_is_admin = st.checkbox("🔑 Create as Admin", value=False, help="Admin accounts have full system access and can manage other coaches", key="tab_new_is_admin")
                    
                    if st.form_submit_button("➕ Add Coach", width='stretch'):
                        role = "admin" if new_is_admin else "coach"
                        if coach_manager.create_coach(new_username, new_fullname, new_email, new_password, role=role, can_pull_fresh_jobs=not new_is_test):
                            st.success(f"✅ Created coach: {new_fullname}")
                            st.rerun()  # Refresh to show new coach in list
                        else:
                            st.error("❌ Username already exists")
                
                st.markdown("### 👥 Existing Coaches")
                for username, existing_coach in coach_manager.coaches.items():
                    if username != 'admin':  # Don't show admin in list
                        with st.expander(f"{existing_coach.full_name} ({username})"):
                            # Coach info display
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Role:** {existing_coach.role}")
                                st.write(f"**Budget:** ${existing_coach.monthly_budget}")
                                st.write(f"**Spent:** ${existing_coach.current_month_spending}")
                            with col2:
                                st.write(f"**Searches:** {existing_coach.total_searches}")
                                st.write(f"**Jobs Found:** {existing_coach.total_jobs_processed}")
                                st.write(f"**Last Login:** {existing_coach.last_login or 'Never'}")
                            
                            # Permissions Management - single column with checkboxes
                            st.markdown("**Edit Permissions**")
                            with st.form(f"tab_edit_permissions_{username}"):
                                new_pdf = st.checkbox("PDF Generation", value=existing_coach.can_generate_pdf, key=f"tab_pdf_{username}")
                                new_csv = st.checkbox("CSV Export", value=existing_coach.can_generate_csv, key=f"tab_csv_{username}")
                                new_airtable = st.checkbox("Airtable Sync", value=existing_coach.can_sync_airtable, key=f"tab_airtable_{username}")
                                new_supabase = st.checkbox("Supabase Sync", value=existing_coach.can_sync_supabase, key=f"tab_supabase_{username}")
                                new_custom_locations = st.checkbox("Custom Locations", value=existing_coach.can_use_custom_locations, key=f"tab_custom_{username}")
                                new_google_jobs = st.checkbox("Google Jobs Access (99% savings)", value=getattr(existing_coach, 'can_access_google_jobs', True), key=f"tab_google_{username}")
                                new_full_mode = st.checkbox("Full Mode Access", value=existing_coach.can_access_full_mode, key=f"tab_full_{username}")
                                new_edit_filters = st.checkbox("Edit Filters", value=existing_coach.can_edit_filters, key=f"tab_filters_{username}")
                                new_pull_fresh = st.checkbox("Pull Fresh Jobs (API calls)", value=getattr(existing_coach, 'can_pull_fresh_jobs', True), key=f"tab_fresh_{username}")
                                new_force_fresh_classification = st.checkbox("Force Fresh Classification", value=getattr(existing_coach, 'can_force_fresh_classification', existing_coach.role == 'admin'), key=f"tab_force_class_{username}")
                                
                                st.markdown("**Role & Budget**")
                                new_admin_role = st.checkbox("🔑 Admin Role (Full System Access)", value=existing_coach.role == "admin", key=f"tab_admin_{username}", help="Grants all permissions and access to admin panel")
                                new_budget = st.number_input("Monthly Budget ($)", min_value=0.0, value=float(existing_coach.monthly_budget), key=f"tab_budget_{username}")
                                
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
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to update permissions")

                            # Admin password reset (tab admin panel)
                            with st.expander("🔐 Reset Password", expanded=False):
                                st.info("As an admin, you can reset this coach's password without their current password.")
                                with st.form(f"tab_reset_password_{username}"):
                                    new_password = st.text_input(
                                        "New Password",
                                        type="password",
                                        key=f"tab_new_pass_{username}",
                                        help="Minimum 6 characters"
                                    )
                                    confirm_password = st.text_input(
                                        "Confirm New Password",
                                        type="password",
                                        key=f"tab_confirm_pass_{username}"
                                    )
                                    
                                    if st.form_submit_button(f"🔐 Reset Password for {existing_coach.full_name}", type="secondary", width='stretch'):
                                        if not new_password or not confirm_password:
                                            st.error("❌ Both password fields are required")
                                        elif new_password != confirm_password:
                                            st.error("❌ Passwords do not match")
                                        else:
                                            success, message = coach_manager.admin_reset_password(
                                                coach.username,
                                                username,
                                                new_password
                                            )
                                            if success:
                                                st.success(f"✅ {message}")
                                            else:
                                                st.error(f"❌ {message}")
                            
                            # Delete coach option
                            if st.button(f"🗑️ Delete {existing_coach.full_name}", key=f"tab_delete_{username}", width='stretch'):
                                if coach_manager.delete_coach(username):
                                    st.success(f"✅ Deleted coach: {existing_coach.full_name}")
                                    st.rerun()
                                else:
                                    st.error("❌ Could not delete coach")
            
            elif admin_tab_select == "View Analytics":
                from admin_market_dashboard import show_admin_market_dashboard
                show_admin_market_dashboard()
                
            elif admin_tab_select == "System Settings":
                st.markdown("### 🔧 System Settings")
                
                # API Tests
                st.markdown("#### 🔌 API Connection Tests")
                if st.button("🧪 Test All APIs", key="tab_test_apis"):
                    # Test Supabase
                    try:
                        from supabase_utils import get_supabase
                        supabase = get_supabase()
                        if supabase:
                            st.success("✅ Supabase connection successful")
                        else:
                            st.warning("⚠️ Supabase connection failed")
                    except Exception as e:
                        st.error(f"❌ Supabase test failed: {e}")
                    
                    # Test Airtable
                    try:
                        from pyairtable import Api
                        import os
                        api_key = os.getenv('AIRTABLE_API_KEY')
                        if api_key and api_key.startswith('key'):
                            st.success("✅ Airtable API key found")
                        else:
                            st.warning("⚠️ Airtable API key not found")
                    except Exception as e:
                        st.error(f"❌ Airtable test failed: {e}")
                    
                    # Test OpenAI
                    try:
                        import os
                        openai_key = os.getenv('OPENAI_API_KEY')
                        if openai_key and openai_key.startswith('sk-'):
                            st.success("✅ OpenAI API key found")
                        else:
                            st.warning("⚠️ OpenAI API key not found")
                    except Exception as e:
                        st.error(f"❌ OpenAI test failed: {e}")
                
                # Environment Info
                with st.expander("🔧 Environment Info", expanded=False):
                    import os
                    import sys
                    st.code(f"""
Python Version: {sys.version}
Working Directory: {os.getcwd()}
Streamlit Version: {st.__version__}
App Version: {APP_VERSION}
Deployment: {DEPLOYMENT_TIMESTAMP}
                    """)
        else:
            st.header("🔒 Restricted Access")
            st.warning("Admin access required for this section.")
            st.info("Contact an administrator to get admin privileges if needed.")
    
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
    
    # Sidebar controls with FreeWorld logo - prefer round logo for QA
    # Add FreeWorld logo to sidebar with light green border
    logo_paths = [
        "assets/fw_logo.png",           # Round logo (preferred for QA)
        "assets/FW-Logo-Roots@2x.png",  # Round logo alternate
        "data/fw_logo.png",
        "data/FW-Logo-Roots@2x.png", 
        "assets/FW-Wordmark-Roots@3x.png"  # Wordmark (fallback)
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
    
    # OLD PAGE NAVIGATION - COMMENTED OUT (replaced with tabs above)
    # st.sidebar.markdown("---")
    # page = st.sidebar.selectbox(
    #     "📱 Navigation", 
    #     ["🔍 Job Search", "📊 Analytics Dashboard", "🗓️ Scheduled Searches", "📦 Async Batches Table", "👥 Free Agent Management", "🧪 System Testing"],
    #     key="page_selector"
    # )
    # 
    # if page == "📊 Analytics Dashboard":
    #     show_analytics_dashboard(coach, coach_manager)
    #     return
    # elif page == "🗓️ Scheduled Searches":
    #     show_scheduled_searches_page(coach)
    #     return
    # elif page == "📦 Async Batches Table":
    #     show_pending_jobs_page(coach)
    #     return
    # elif page == "👥 Free Agent Management":
    #     show_free_agent_management_page(coach)
    #     return
    # elif page == "🧪 System Testing":
    #     show_system_testing_page(coach)
    #     return
    
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
                            st.rerun()
                elif notif.type == 'error':
                    with st.sidebar:
                        st.error(notif.message)
                        if st.button(f"✓ Mark Read", key=f"notif_{notif.id}"):
                            async_manager.mark_notification_read(notif.id)
                            st.rerun()
                elif notif.type == 'search_submitted':
                    with st.sidebar:
                        st.info(notif.message)
                        if st.button(f"✓ Mark Read", key=f"notif_{notif.id}"):
                            async_manager.mark_notification_read(notif.id)
                            st.rerun()
            
            if len(unread_notifications) > 3:
                st.sidebar.caption(f"... and {len(unread_notifications) - 3} more")
            st.sidebar.markdown("---")
    except Exception as e:
        # Silently handle notification errors to not break main app
        pass
    
    # Removed obsolete sidebar code - all functionality moved to main tab interface
    # Set default values for removed sidebar variables  
    search_type = None
    location = None
    custom_location = None
    route_filter = "both"
    search_mode = "sample"
    search_terms = "CDL Driver No Experience"
    exact_location = False
    search_radius = 50
    no_experience = True
    generate_pdf = False
    generate_csv = False
    save_parquet = False
    search_strategy = "balanced"
    force_fresh = False
    force_fresh_classification = False
    push_to_airtable = False
    candidate_id = ""
    candidate_name = ""
    enable_business_rules = True
    enable_deduplication = True
    enable_experience_filter = True
    classification_model = "gpt-4o-mini"
    batch_size = 25
    
    # Safe preview location for any HTML preview blocks (avoid UnboundLocalError)
    preview_location = location

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
        if search_type == 'memory_display':
            # Display previous memory search results from session state
            df = st.session_state.memory_search_df
            metadata = st.session_state.memory_search_metadata
            params = st.session_state.memory_search_params
            
            # Set display location from previous search
            final_location = params.get('location', 'Unknown')
            
            st.info("📋 Displaying previous search results. Click a search button to run a new search.")
            
        elif search_type == 'memory':
            # Memory-only search - use EXACT same approach as Indeed button but with memory_only=True
            # Clear any previous results first since we're running a new search
            for key in ['memory_search_df', 'memory_search_metadata', 'memory_search_params', 'last_results']:
                if hasattr(st.session_state, key):
                    delattr(st.session_state, key)
            
            # Build parameters exactly like Indeed button
            # Map UI lookback (e.g., '72h') to hours integer
            try:
                _mem_hours = int(str(memory_time_period).replace('h','').strip())
            except Exception:
                _mem_hours = 72

            params = {
                'mode': search_mode,
                'route_filter': route_filter,
                'search_terms': search_terms,
                'push_to_airtable': push_to_airtable,
                'generate_pdf': False,  # UI memory-only: no PDF during search
                'generate_csv': False,  # UI memory-only: no CSV during search
                'search_radius': search_radius,
                'no_experience': no_experience,
                'force_fresh': False,  # Never force fresh for memory-only
                'force_fresh_classification': force_fresh_classification,
                'coach_name': coach.full_name,
                'coach_username': coach.username,
                'memory_only': True,  # FORCE memory-only mode
                'memory_hours': _mem_hours,
                'candidate_id': candidate_id.strip() if candidate_id else "",
                'candidate_name': candidate_name.strip() if candidate_name else "",
                'search_sources': {'indeed': False, 'google': False},  # Memory only
                'search_strategy': 'memory_first'
            }
            
            
            # Add location parameters based on type (support single or multi market without stopping)
            if location_type == "Select Market":
                if 'selected_markets' in locals() and selected_markets:
                    params['markets'] = selected_markets  # Multiple markets
                    params['location'] = location
                else:
                    params['location'] = location
            else:
                params['custom_location'] = custom_location
                params['location'] = custom_location
            
            # Determine display-friendly location string (markets without state abbrev)
            try:
                if location_type == "Select Market" and 'selected_markets' in locals() and selected_markets:
                    display_location = ", ".join(selected_markets)
                else:
                    display_location = final_location
            except Exception:
                display_location = final_location

            # Add coach information to params for PDF generation
            coach = st.session_state.get('current_coach')
            if coach:
                params['coach_name'] = coach.full_name
                params['coach_username'] = coach.username
            
            # Add candidate information from session state (from "Use Selected" button)
            candidate_name = st.session_state.get('candidate_name', '')
            candidate_id = st.session_state.get('candidate_id', '')
            if candidate_name:
                params['candidate_name'] = candidate_name
                print(f"🔍 Memory Search: Added candidate_name: '{candidate_name}'")
            if candidate_id:
                params['candidate_id'] = candidate_id
                print(f"🔍 Memory Search: Added candidate_id: '{candidate_id}'")

            # Run pipeline with memory-only spinner text and capture logs to show in UI
            import io, contextlib
            log_buffer = io.StringIO()
            with st.spinner(f"💾 Searching memory only for jobs in {display_location}..."):
                try:
                    with contextlib.redirect_stdout(log_buffer), contextlib.redirect_stderr(log_buffer):
                        # DO NOT set ui_direct=True for memory searches - let it use dedicated memory path
                        df, metadata = pipeline.run_pipeline(params)
                        
                        # Add coach and candidate info to ALL jobs in DataFrame (for link tracking and PDF)
                        if not df.empty:
                            df['meta.coach_name'] = coach.full_name
                            df['meta.coach_username'] = coach.username
                            # NUCLEAR FIX: Only set meta fields if we have actual data, don't wipe out agent.* fields
                            candidate_name_session = st.session_state.get('candidate_name', '')
                            candidate_id_session = st.session_state.get('candidate_id', '')
                            # Only override if we have actual non-empty values, otherwise keep pipeline data
                            if candidate_name_session and candidate_name_session.strip():
                                df['meta.candidate_name'] = candidate_name_session
                            if candidate_id_session and candidate_id_session.strip():
                                df['meta.candidate_id'] = candidate_id_session
                        
                        # CRITICAL FIX: Apply market sanitization to Memory Only results 
                        # to ensure "Berkeley" -> "Bay Area" mapping for proper display
                        if not df.empty and 'meta.market' in df.columns:
                            from shared_search import MARKET_TO_LOCATION
                            def _sanitize_market_memory(val: str) -> str:
                                """Sanitize market values for Memory Only results"""
                                s = str(val or '').strip()
                                if not s:
                                    return s
                                # Map representative cities back to markets
                                city_to_market = {
                                    'berkeley': 'Bay Area',
                                    'ontario': 'Inland Empire', 
                                    'fort worth': 'Dallas'
                                }
                                if s.lower() in city_to_market:
                                    return city_to_market[s.lower()]
                                # Remove state abbreviations (e.g., "Berkeley, CA" -> "Berkeley")
                                if ', ' in s:
                                    s = s.split(', ')[0].strip()
                                    if s.lower() in city_to_market:
                                        return city_to_market[s.lower()]
                                return s
                            
                            df['meta.market'] = df['meta.market'].apply(_sanitize_market_memory)
                            print(f"🔧 Applied market sanitization to Memory Only results")
                        
                        # Store results in session state so they persist until next search
                        # Add protection flag to prevent accidental clearing
                        st.session_state.memory_search_df = df
                        st.session_state.memory_search_metadata = metadata
                        st.session_state.memory_search_params = params.copy()  # Store search params too
                        st.session_state.search_results_protected = True  # Protection flag
                except Exception as e:
                    # Ensure we always define df/metadata on error and surface logs
                    # pandas already imported globally
                    df = pd.DataFrame()
                    metadata = {'success': False, 'error': str(e)}
                    
                    # Store error results in session state too
                    st.session_state.memory_search_df = df
                    st.session_state.memory_search_metadata = metadata
                    st.session_state.memory_search_params = params.copy()
                    st.session_state.search_results_protected = True  # Protection flag even for errors
            mem_logs = log_buffer.getvalue()

            # Build concise debug summary for memory search
            try:
                dbg = []
                dbg.append("=== Memory Search Debug Summary ===")
                dbg.append(f"success={metadata.get('success', False)} error={metadata.get('error', '')}")
                dbg.append(f"df.shape={getattr(df, 'shape', None)} cols={len(getattr(df, 'columns', []))}")
                if not df.empty:
                    cols = list(df.columns)[:12]
                    dbg.append(f"columns(sample)={cols}")
                    # Field presence
                    for key in ['ai.match', 'route.final_status', 'meta.market', 'source.title']:
                        dbg.append(f"has[{key}]={key in df.columns}")
                    # Sample titles
                    try:
                        sample_titles = df.get('source.title').dropna().astype(str).head(5).tolist()
                        if sample_titles:
                            dbg.append(f"titles(sample)={sample_titles}")
                    except Exception:
                        pass
                    # Quality counts
                    try:
                        if 'ai.match' in df.columns:
                            vc = df['ai.match'].value_counts().to_dict()
                            dbg.append(f"ai.match={vc}")
                    except Exception:
                        pass
                mem_debug_summary = "\n".join(dbg) + "\n\n"
            except Exception:
                mem_debug_summary = "(debug summary unavailable)\n\n"

            # No CSV fallback here — rely on pipeline behavior only

            # If no jobs, surface helpful diagnostics inline
            if (df is None or df.empty) and (not metadata.get('success', False)):
                try:
                    import os
                    from job_memory_db import JobMemoryDB
                    st.warning("No jobs returned. Running quick diagnostics…")
                    st.caption(f"Location used: {display_location} | Lookback: {params.get('memory_hours', 'n/a')}h | Terms: '{params.get('search_terms','')}'")
                    # Env check
                    su = os.getenv('SUPABASE_URL'); sk = os.getenv('SUPABASE_ANON_KEY')
                    st.write(f"SUPABASE_URL set: {'✅' if su else '❌'}  |  SUPABASE_ANON_KEY set: {'✅' if sk else '❌'}")
                    # Connection test
                    try:
                        conn = JobMemoryDB().test_connection()
                        ok = conn.get('success', False)
                        st.write(f"Supabase connection: {'✅ OK' if ok else '❌ Failed'} — {conn.get('message','')}" )
                    except Exception as _e:
                        st.write(f"Supabase connection test error: {_e}")
                except Exception:
                    pass
            
            # Store results in session state (same as Indeed button)
            st.session_state.last_results = {
                'df': df,
                'metadata': metadata,
                'params': params,
                'timestamp': datetime.now()
            }
            
            # Show results (fallback to DataFrame presence)
            if (isinstance(df, pd.DataFrame) and not df.empty) or metadata.get('success', False):
                st.success(f"✅ Memory search completed! Found {metadata.get('quality_jobs', 0)} quality jobs from memory")
                
                # CSV download removed per new UI
                
                if generate_pdf and metadata.get('pdf_path'):
                    pdf_bytes = pipeline.get_pdf_bytes(metadata['pdf_path'])
                    if pdf_bytes:
                        pretty = f"{final_location} Jobs Report"
                        st.download_button(
                            label="📄 Download PDF", 
                            data=pdf_bytes,
                            file_name=f"{pretty.lower().replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                
                # HTML Preview if enabled (but NOT for Indeed searches)  
                if show_html_preview_tab and jobs_dataframe_to_dicts and render_jobs_html and not df.empty and search_type not in ['indeed_fresh', 'indeed']:
                    try:
                        st.markdown("### 👁️ HTML Preview")
                        # IMPORTANT: Use the same processing as PDF to include tracked URLs
                        from free_agent_system import update_job_tracking_for_agent
                        agent_params = {
                            'location': preview_location,
                            'agent_name': candidate_name_tab,
                            'agent_uuid': candidate_id_tab,
                            'coach_username': get_current_coach_name(),
                            'show_prepared_for': show_prepared_for_tab
                        }
                        
                        # Supabase has already filtered by route type, quality, and fair chance - no post-processing needed
                        filtered_df = df
                        
                        # Apply max jobs limit only (Supabase already handled filtering)
                        if max_jobs_pdf_tab != "All":
                            filtered_df = filtered_df.head(max_jobs_pdf_tab)
                        
                        # Process DataFrame the same way PDF does
                        processed_df = update_job_tracking_for_agent(filtered_df, agent_params)
                        jobs = jobs_dataframe_to_dicts(processed_df)
                        
                        html = render_jobs_html(jobs, agent_params)
                        phone_html = wrap_html_in_phone_screen(html)
                        st.components.v1.html(phone_html, height=900, scrolling=False)
                    except Exception as e:
                        st.error(f"HTML preview error: {e}")
                
                # Display results table inline (quality-first ordering) + on-demand PDF  
                # Using standardized quality filtering
                quality_df = filter_quality_jobs(df)
                debug_dataframe_info(df, "Memory Only - All Jobs")
                debug_dataframe_info(quality_df, "Memory Only - Quality Jobs")
                show_all_rows = st.checkbox("Show all rows (no filters)", value=False, key="mem_show_all_rows")
                display_df = (df if show_all_rows else quality_df).copy().reset_index(drop=True)
                st.dataframe(display_df, width="stretch", height=420, hide_index=True)

                # Generate PDF button (pulls market/coach/candidate from DF + context)
                col_pdf, _ = st.columns([1, 3])
                with col_pdf:
                    if st.button("📄 Generate PDF", key="mem_generate_pdf_btn"):
                        # Determine market name for title; prefer single meta.market
                        market_name = 'Multiple Markets'
                        try:
                            if 'meta.market' in quality_df.columns:
                                mkts = [m for m in quality_df['meta.market'].dropna().unique().tolist() if str(m).strip()]
                                if len(mkts) == 1:
                                    market_name = mkts[0]
                                elif len(mkts) == 0:
                                    market_name = params.get('location') or 'Market'
                            else:
                                market_name = params.get('location') or 'Market'
                        except Exception:
                            market_name = params.get('location') or 'Market'

                        # Apply reasonable default limit since sidebar PDF options are disabled
                        limited_quality_df = quality_df.head(50)  # Default to 50 jobs for PDF

                        # Add coach and candidate info to DataFrame so it travels with the data
                        pdf_df = limited_quality_df.copy()
                        if len(pdf_df) > 0:
                            pdf_df['meta.coach_name'] = coach.full_name
                            pdf_df['meta.coach_username'] = coach.username
                            # Use same source as HTML (text input values, not just session state)
                            pdf_df['meta.candidate_name'] = candidate_name_tab if 'candidate_name_tab' in locals() else st.session_state.get('candidate_name', '')
                            pdf_df['meta.candidate_id'] = candidate_id_tab if 'candidate_id_tab' in locals() else st.session_state.get('candidate_id', '')
                        
                        pdf_bytes = pipeline.generate_pdf_from_canonical(
                            pdf_df,
                            market_name=market_name
                        )
                        if pdf_bytes:
                            st.download_button(

                                label="📥 Download PDF",
                                data=pdf_bytes,
                                file_name=f"freeworld_jobs_{str(market_name).replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        else:
                            st.error("PDF generation failed")

                if not df.empty:
                    st.balloons()
            else:
                st.error(f"❌ Memory search failed: {metadata.get('error', 'Unknown error')}")

            # Always show debug logs for memory search (collapsed)
            if mem_logs.strip() or mem_debug_summary:
                with st.expander("🧪 Debug logs (memory search)", expanded=False):
                    # Prepend summary to the captured logs
                    text = mem_debug_summary + (mem_logs[-5000:] if mem_logs else '')
                    st.code(text, language="text")
        
        # Google ordering removed from Job Search sidebar
        
        elif search_type in ['indeed', 'indeed_fresh']:
            # Indeed searches (with or without memory) 
            # Clear any previous results first since we're running a new search
            for key in ['memory_search_df', 'memory_search_metadata', 'memory_search_params', 'last_results']:
                if hasattr(st.session_state, key):
                    delattr(st.session_state, key)
            
            is_fresh_only = (search_type == 'indeed_fresh')
            
            # Build parameters for existing pipeline
            params = {
                'mode': search_mode,
                'route_filter': route_filter,
                'search_terms': search_terms,
                'push_to_airtable': push_to_airtable,
                'generate_pdf': False,  # UI: no PDF during search; on-demand only
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
            
            
            # Add location parameters based on type (support single or multi market without stopping)
            if location_type == "Select Market":
                if 'selected_markets' in locals() and selected_markets:
                    params['markets'] = selected_markets
                    params['location'] = location
                else:
                    params['location'] = location
            else:
                params['custom_location'] = custom_location
                params['location'] = custom_location
            
            # Determine display-friendly location
            try:
                if location_type == "Select Market" and 'selected_markets' in locals() and selected_markets:
                    display_location = ", ".join(selected_markets)
                else:
                    display_location = final_location
            except Exception:
                display_location = final_location

            # Run pipeline with appropriate spinner text and capture logs
            spinner_text = (
                f"🔍 Searching Indeed fresh only for jobs in {display_location}..."
                if is_fresh_only else
                f"🔍 Searching Indeed + memory for jobs in {display_location}..."
            )
            
            # Add coach information to params for PDF generation
            coach = st.session_state.get('current_coach')
            if coach:
                params['coach_name'] = coach.full_name
                params['coach_username'] = coach.username

            import io, contextlib
            indeed_log_buffer = io.StringIO()
            with st.spinner(spinner_text):
                try:
                    with contextlib.redirect_stdout(indeed_log_buffer), contextlib.redirect_stderr(indeed_log_buffer):
                        params['ui_direct'] = True
                        df, metadata = pipeline.run_pipeline(params)
                        
                        # Add coach and candidate info to ALL jobs in DataFrame (for link tracking and PDF)
                        if not df.empty:
                            df['meta.coach_name'] = coach.full_name
                            df['meta.coach_username'] = coach.username
                            # NUCLEAR FIX: Only set meta fields if we have actual data, don't wipe out agent.* fields
                            candidate_name_session = st.session_state.get('candidate_name', '')
                            candidate_id_session = st.session_state.get('candidate_id', '')
                            # Only override if we have actual non-empty values, otherwise keep pipeline data
                            if candidate_name_session and candidate_name_session.strip():
                                df['meta.candidate_name'] = candidate_name_session
                            if candidate_id_session and candidate_id_session.strip():
                                df['meta.candidate_id'] = candidate_id_session
                        
                except Exception as e:
                    # pandas already imported globally
                    df = pd.DataFrame()
                    metadata = {'success': False, 'error': str(e)}
            indeed_logs = indeed_log_buffer.getvalue()

            # Build concise debug summary for Indeed searches
            try:
                idbg = []
                idbg.append("=== Indeed Search Debug Summary ===")
                idbg.append(f"success={metadata.get('success', False)} error={metadata.get('error', '')}")
                idbg.append(f"df.shape={getattr(df, 'shape', None)} cols={len(getattr(df, 'columns', []))}")
                if not df.empty:
                    cols = list(df.columns)[:12]
                    idbg.append(f"columns(sample)={cols}")
                    for key in ['ai.match', 'route.final_status', 'meta.market', 'source.title']:
                        idbg.append(f"has[{key}]={key in df.columns}")
                    try:
                        sample_titles = df.get('source.title').dropna().astype(str).head(5).tolist()
                        if sample_titles:
                            idbg.append(f"titles(sample)={sample_titles}")
                    except Exception:
                        pass
                    try:
                        if 'ai.match' in df.columns:
                            vc = df['ai.match'].value_counts().to_dict()
                            idbg.append(f"ai.match={vc}")
                    except Exception:
                        pass
                # Metadata hints
                for k in ['csv_path','parquet_path','included_jobs','total_jobs','run_id']:
                    if k in metadata:
                        idbg.append(f"meta[{k}]={metadata.get(k)}")
                indeed_debug_summary = "\n".join(idbg) + "\n\n"
            except Exception:
                indeed_debug_summary = "(debug summary unavailable)\n\n"
            
            # Store results in session state
            st.session_state.last_results = {
                'df': df,
                'metadata': metadata,
                'params': params,
                'timestamp': datetime.now()
            }
            
            # Show results and update coach stats
            if metadata.get('success', False):
                try:
                    ai_series = df.get('ai.match')
                    if ai_series is not None:
                        _q = int((ai_series == 'good').sum() + (ai_series == 'so-so').sum())
                    elif 'route.final_status' in df.columns:
                        _q = int(df['route.final_status'].astype(str).str.startswith('included').sum())
                    else:
                        _q = len(df)
                except Exception:
                    _q = metadata.get('quality_jobs', 0)
                st.success(f"✅ Search completed! Found {_q} quality jobs")
                
                # HTML Preview if enabled (but NOT for Indeed searches)  
                if show_html_preview_tab and jobs_dataframe_to_dicts and render_jobs_html and not df.empty and search_type not in ['indeed_fresh', 'indeed']:
                    try:
                        st.markdown("### 👁️ HTML Preview")
                        # IMPORTANT: Use the same processing as PDF to include tracked URLs
                        from free_agent_system import update_job_tracking_for_agent
                        agent_params = {
                            'location': preview_location,
                            'agent_name': candidate_name_tab,
                            'agent_uuid': candidate_id_tab,
                            'coach_username': get_current_coach_name(),
                            'show_prepared_for': show_prepared_for_tab
                        }
                        
                        # Supabase has already filtered by route type, quality, and fair chance - no post-processing needed
                        filtered_df = df
                        
                        # Apply max jobs limit only (Supabase already handled filtering)
                        if max_jobs_pdf_tab != "All":
                            filtered_df = filtered_df.head(max_jobs_pdf_tab)
                        
                        # Process DataFrame the same way PDF does
                        processed_df = update_job_tracking_for_agent(filtered_df, agent_params)
                        jobs = jobs_dataframe_to_dicts(processed_df)
                        
                        html = render_jobs_html(jobs, agent_params)
                        phone_html = wrap_html_in_phone_screen(html)
                        st.components.v1.html(phone_html, height=900, scrolling=False)
                    except Exception as e:
                        st.error(f"HTML preview error: {e}")
                
                # Inline results table + on-demand PDF - using standardized filtering
                quality_df = filter_quality_jobs(df)
                debug_dataframe_info(df, "Indeed Fresh Only - All Jobs")
                debug_dataframe_info(quality_df, "Indeed Fresh Only - Quality Jobs")
                show_all_rows_indeed = st.checkbox("Show all rows (no filters)", value=False, key="indeed_show_all_rows_main")
                display_df = (df if show_all_rows_indeed or quality_df.empty else quality_df).copy().reset_index(drop=True)
                st.dataframe(display_df, width="stretch", height=420, hide_index=True)

                col_pdf2, _ = st.columns([1, 3])
                with col_pdf2:
                    if st.button("📄 Generate PDF", key="indeed_generate_pdf_btn"):
                        market_name = 'Multiple Markets'
                        try:
                            if 'meta.market' in quality_df.columns:
                                mkts = [m for m in quality_df['meta.market'].dropna().unique().tolist() if str(m).strip()]
                                if len(mkts) == 1:
                                    market_name = mkts[0]
                                elif len(mkts) == 0:
                                    market_name = params.get('location') or 'Market'
                            else:
                                market_name = params.get('location') or 'Market'
                        except Exception:
                            market_name = params.get('location') or 'Market'

                        # Apply reasonable default limit since sidebar PDF options are disabled
                        limited_quality_df = quality_df.head(50)  # Default to 50 jobs for PDF

                        # Add coach and candidate info to DataFrame so it travels with the data
                        pdf_df = limited_quality_df.copy()
                        if len(pdf_df) > 0:
                            pdf_df['meta.coach_name'] = coach.full_name
                            pdf_df['meta.coach_username'] = coach.username
                            # Use same source as HTML (text input values, not just session state)
                            pdf_df['meta.candidate_name'] = candidate_name_tab if 'candidate_name_tab' in locals() else st.session_state.get('candidate_name', '')
                            pdf_df['meta.candidate_id'] = candidate_id_tab if 'candidate_id_tab' in locals() else st.session_state.get('candidate_id', '')
                        
                        pdf_bytes = pipeline.generate_pdf_from_canonical(
                            pdf_df,
                            market_name=market_name
                        )
                        if pdf_bytes:
                            st.download_button(

                                label="📥 Download PDF",
                                data=pdf_bytes,
                                file_name=f"freeworld_jobs_{str(market_name).replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        else:
                            st.error("PDF generation failed")

                # Record search in coach's usage stats
                coach_manager.record_search(
                    coach.username, 
                    metadata.get('included_jobs', 0),
                    metadata.get('total_cost', 0.0)
                )
            # Always show debug logs for Indeed searches (collapsed)
            if indeed_logs.strip() or indeed_debug_summary:
                with st.expander("🧪 Debug logs (Indeed)", expanded=False):
                    text = indeed_debug_summary + (indeed_logs[-8000:] if indeed_logs else '')
                    st.code(text, language="text")
            else:
                if isinstance(df, pd.DataFrame) and not df.empty:
                    st.warning("⚠️ Metadata reported failure, but results contain rows. Showing data.")
                    display_df = df.copy().reset_index(drop=True)
                    st.dataframe(display_df, width="stretch", height=420, hide_index=True)
                else:
                    st.error(f"❌ Search failed: {metadata.get('error', 'Unknown error')}")
    
    # Configuration Preview
    if location:
        mode_limits = MODE_LIMITS
        
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
            airtable_status = '<span style="color: #dc3545;">❌ Disabled</span>'
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
        
        # (Removed legacy 'Last Search Results' status block)
    
    # Results display - Show persistent results from last search
    if 'last_results' in st.session_state:
        results = st.session_state.last_results
        df = results['df']
        metadata = results['metadata']
        
        
        if not df.empty and metadata.get('success', False):
            st.markdown("---")
            
            # Add timestamp info for the persistent results
            result_timestamp = results.get('timestamp', 'Unknown time')
            search_type = results.get('search_type', 'Unknown')
            st.info(f"📊 **Last Search Results** (from {search_type} search at {result_timestamp.strftime('%I:%M %p') if hasattr(result_timestamp, 'strftime') else result_timestamp})")
            st.markdown("*These results will persist until you run a new search*")

            # Included Jobs view (filtered to PDF-exportable)
            filtered_df = df
            try:
                if 'route.final_status' in df.columns:
                    _mask = df['route.final_status'].astype(str).str.startswith('included')
                    if _mask.any():
                        filtered_df = df[_mask]
                elif 'ai.match' in df.columns:
                    filtered_df = df[df['ai.match'].isin(['good', 'so-so'])]
            except Exception:
                pass

            # (No global/top PDF button per new design)

            # Top-level global metrics + quality DF
            try:
                # Global combined metrics computed from DataFrame (ALL markets)
                ai_series = df.get('ai.match')
                route_series = df.get('ai.route_type')
                ai_good = int((ai_series == 'good').sum()) if ai_series is not None else 0
                ai_soso = int((ai_series == 'so-so').sum()) if ai_series is not None else 0
                quality_jobs = ai_good + ai_soso
                total_jobs = int(len(df))
                local_routes = int((route_series == 'Local').sum()) if route_series is not None else 0
                otr_routes = int((route_series == 'OTR').sum()) if route_series is not None else 0

                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Quality Jobs Found", quality_jobs)
                with c2:
                    st.metric("Total Jobs Analyzed", total_jobs)
                with c3:
                    st.metric("Excellent Matches", ai_good)
                with c4:
                    st.metric("Possible Fits", ai_soso)
                with c5:
                    st.metric("Local Routes", local_routes)

                d1, d2, d3, d4, d5 = st.columns(5)
                with d1:
                    st.metric("OTR Routes", otr_routes)
                with d2:
                    st.metric("Pipeline Efficiency", f"{metadata.get('memory_efficiency', 0):.1f}%")
                with d3:
                    st.metric("Cost per Quality Job", f"${metadata.get('cost_per_quality_job', 0):.3f}")
                with d4:
                    processing_time = (metadata.get('processing_time', 0) or metadata.get('duration', 0) or metadata.get('elapsed_time', 0) or metadata.get('time', 0))
                    time_str = f"{int(processing_time // 60)}m {processing_time % 60:.1f}s" if processing_time >= 60 else f"{processing_time:.1f}s"
                    st.metric("Processing Time", time_str)
                with d5:
                    st.metric("Memory Efficiency", f"{metadata.get('memory_efficiency', 0):.1f}%")

                # Terminal Parquet (99_complete)
                parquet_path = metadata.get('parquet_path')
                run_id = metadata.get('run_id', 'unknown')
                pdebug = metadata.get('parquet_debug', {}) or {}
                try:
                    if parquet_path:
                        pq_bytes2 = pipeline.get_parquet_bytes(parquet_path) if hasattr(pipeline, 'get_parquet_bytes') else None
                        if pq_bytes2:
                            st.download_button(
                        
                                label="📦 Download Parquet (Terminal Output)",
                                data=pq_bytes2,
                                file_name=os.path.basename(parquet_path),
                                mime="application/octet-stream",
                                width='stretch'
                            )
                            # Debug caption removed
                        else:
                            # Fallback: build combined parquet from DataFrame in-memory
                            fallback_bytes = pipeline.dataframe_to_parquet_bytes(df) if hasattr(pipeline, 'dataframe_to_parquet_bytes') else b""
                            if fallback_bytes:
                                st.download_button(
                        
                                    label="📦 Download Parquet (Combined Results)",
                                    data=fallback_bytes,
                                    file_name=f"multi_market_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet",
                                    mime="application/octet-stream",
                                    width='stretch'
                                )
                                # Debug caption removed
                            else:
                                pass
                    else:
                        # Fallback when no path: attempt in-memory parquet from results
                        fallback_bytes = pipeline.dataframe_to_parquet_bytes(df) if hasattr(pipeline, 'dataframe_to_parquet_bytes') else b""
                        if fallback_bytes:
                            st.download_button(
                        
                                label="📦 Download Parquet (Combined Results)",
                                data=fallback_bytes,
                                file_name=f"multi_market_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet",
                                mime="application/octet-stream",
                                width='stretch'
                            )
                            # Debug caption removed
                        else:
                            pass
                except Exception:
                    # Last-ditch fallback
                    try:
                        fallback_bytes = pipeline.dataframe_to_parquet_bytes(df) if hasattr(pipeline, 'dataframe_to_parquet_bytes') else b""
                        if fallback_bytes:
                            st.download_button(
                        
                                label="📦 Download Parquet (Combined Results)",
                                data=fallback_bytes,
                                file_name=f"multi_market_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet",
                                mime="application/octet-stream",
                                width='stretch'
                            )
                            # Debug caption removed
                        else:
                            pass
                    except Exception:
                        pass

                # Optional: show recent parquet files in the directory to aid debugging
                try:
                    import glob, os, time
                    pq_dir = pdebug.get('dir')
                    if pq_dir and os.path.isdir(pq_dir):
                        files = glob.glob(os.path.join(pq_dir, '*_99_complete.parquet'))
                        files = sorted(files, key=os.path.getmtime, reverse=True)[:8]
                        if files:
                            rows = []
                            for f in files:
                                try:
                                    rows.append({
                                        'file': os.path.basename(f),
                                        'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(f))),
                                        'size_kb': int(os.path.getsize(f)/1024)
                                    })
                                except Exception:
                                    pass
                            if rows:
                                with st.expander('Parquet files (debug)', expanded=False):
                                    st.dataframe(pd.DataFrame(rows), width='stretch', height=180)
                except Exception:
                    pass

                # (Removed selected/detected markets debug readout and table)

                # Global quality DataFrame (all markets) - using standardized filtering
                quality_df = filter_quality_jobs(df)
                show_all_rows_global = st.checkbox("Show all rows (no filters)", value=False, key="global_show_all_rows")
                display_df = (df if show_all_rows_global or quality_df.empty else quality_df).copy().reset_index(drop=True)
                st.dataframe(display_df, width="stretch", height=420, hide_index=True)
            except Exception:
                pass

            

            

            # (Removed bottom terminal parquet button and duplicate analytics)

            # Collapsible full DataFrame
            with st.expander("🔎 Full Results (all columns)", expanded=False):
                # Show full canonical DataFrame, no filtering or reordering
                st.dataframe(df, width='stretch')

            # Per-market sections (clone results UI for each market)
            try:
                if 'meta.market' in df.columns:
                    unique_mkts = [m for m in df['meta.market'].dropna().unique().tolist() if str(m).strip() != '' ]
                    # DEBUG: Show actual market values in DataFrame
                    market_counts = df['meta.market'].value_counts()
                    st.info(f"🐛 DEBUG - Actual market values in DataFrame: {dict(market_counts)}")
                    if len(unique_mkts) >= 1:
                        order_hint = results.get('params', {}).get('markets') or []
                        ordered = []
                        seen = set()
                        for m in order_hint:
                            if m in unique_mkts and m not in seen:
                                ordered.append(m); seen.add(m)
                        for m in sorted(unique_mkts):
                            if m not in seen:
                                ordered.append(m)

                        for mk in ordered:
                            # Header with inline PDF download if available
                            try:
                                import glob
                                col_h, col_btn = st.columns([8, 2])
                                with col_h:
                                    st.markdown(f"### 📍 {mk}")
                                with col_btn:
                                    # Generate PDF button for this market with fresh tracked links
                                    if st.button(f"📄 Generate PDF", key=f"market_pdf_{mk}_btn"):
                                        with st.spinner(f"🔗 Generating PDF with fresh tracking links for {mk}..."):
                                            try:
                                                # Filter jobs for this market
                                                market_df = df[df['meta.market'] == mk].copy()
                                                
                                                if not market_df.empty:
                                                    # Create fresh tracked links for PDF
                                                    from link_tracker import LinkTracker
                                                    if LinkTracker:
                                                        link_tracker = LinkTracker()
                                                        if link_tracker.is_available:
                                                            # Generate new tracked URLs for PDF
                                                            url_mapping = {}
                                                            for _, job in market_df.iterrows():
                                                                original_url = (
                                                                    job.get('source.indeed_url', '') or 
                                                                    job.get('source.google_url', '') or 
                                                                    job.get('source.apply_url', '')
                                                                )
                                                                job_id = job.get('id.job', '')
                                                                
                                                                if original_url and len(original_url) > 10 and job_id:
                                                                    try:
                                                                        # Get environment variables for tracking
                                                                        # Get candidate info from DataFrame metadata (same source as PDF)
                                                                        coach_username = coach.username
                                                                        candidate_name = job.get('meta.candidate_name', '') if 'meta.candidate_name' in job else ''
                                                                        candidate_id = job.get('meta.candidate_id', '') if 'meta.candidate_id' in job else ''
                                                                        
                                                                        # Prepare tags for Short.io
                                                                        tags = [f"coach:{coach_username}", f"market:{mk}", "pdf_generation"]
                                                                        if candidate_id:
                                                                            tags.append(f"candidate:{candidate_id}")
                                                                        if candidate_name:
                                                                            tags.append(f"agent:{candidate_name.replace(' ', '-')}")
                                                                        
                                                                        job_title = job.get('source.title', f"Job {job_id[:8]}")
                                                                        tracked_url = link_tracker.create_short_link(
                                                                            original_url,
                                                                            title=f"{mk} - {job_title}",
                                                                            tags=tags
                                                                        )
                                                                        
                                                                        if tracked_url and tracked_url != original_url:
                                                                            url_mapping[job_id] = tracked_url
                                                                    except Exception as e:
                                                                        print(f"Link generation failed for {job_id[:8]}: {e}")
                                                            
                                                            # Apply new tracked URLs to market DataFrame
                                                            if url_mapping:
                                                                for job_id, tracked_url in url_mapping.items():
                                                                    mask = market_df['id.job'] == job_id
                                                                    market_df.loc[mask, 'meta.tracked_url'] = tracked_url
                                                                st.success(f"✅ Generated {len(url_mapping)} fresh tracking links")
                                                    
                                                    # Generate PDF for this market
                                                    if hasattr(pipeline, '_generate_pdf'):
                                                        pdf_path = pipeline._generate_pdf(market_df, mk, None)
                                                        if pdf_path and hasattr(pipeline, 'get_pdf_bytes'):
                                                            pdf_bytes = pipeline.get_pdf_bytes(pdf_path)
                                                            if pdf_bytes:
                                                                st.download_button(
                                                                    label=f"📄 Download {mk} PDF",
                                                                    data=pdf_bytes,
                                                                    file_name=f"FreeWorld_Jobs_{mk}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                                                    mime="application/pdf",
                                                                    key=f"download_{mk}_pdf",
                                                                    use_container_width=True
                                                                )
                                                                st.success(f"✅ PDF generated for {mk} with fresh tracking links!")
                                                            else:
                                                                st.error("Failed to read PDF bytes")
                                                        else:
                                                            st.error("PDF generation failed")
                                                    else:
                                                        st.error("PDF generation not available")
                                                else:
                                                    st.warning(f"No jobs found for {mk}")
                                            except Exception as e:
                                                st.error(f"PDF generation error: {e}")
                            except Exception:
                                st.markdown(f"### 📍 {mk}")
                            mdf = df[df['meta.market'] == mk]
                            # Filter for quality jobs using standardized logic
                            mdf_inc = filter_quality_jobs(mdf)

                            # (Per-market PDF generation flow removed; using inline download link if file exists)

                            # Included table
                            cols_pref = ['source.title', 'source.company', 'ai.summary', 'ai.match', 'ai.route_type', 'ai.fair_chance', 'source.indeed_url']
                            cols_show = [c for c in cols_pref if c in mdf_inc.columns]
                            st.dataframe(mdf_inc[cols_show] if cols_show else mdf_inc, width='stretch')

                            # Per-market metrics using standardized calculation
                            try:
                                quality_metrics = calculate_search_metrics(mdf_inc)
                                inc_count = len(mdf_inc)
                                total_count = len(mdf)
                                
                                colA, colB, colC, colD = st.columns(4)
                                with colA:
                                    st.metric("Quality Jobs Found", inc_count)
                                with colB:
                                    st.metric("Total Jobs Analyzed", total_count)
                                with colC:
                                    st.metric("Excellent Matches", quality_metrics['good'])
                                with colD:
                                    st.metric("Possible Fits", quality_metrics['so_so'])
                                colE, colF = st.columns(2)
                                with colE:
                                    st.metric("Local Routes", quality_metrics['local'])
                                with colF:
                                    st.metric("OTR Routes", quality_metrics['otr'])
                            except Exception:
                                pass

                            # Full results for market
                            with st.expander(f"🔎 Full Results — {mk}", expanded=False):
                                st.dataframe(mdf, width='stretch', height=480)
                            st.markdown("---")
            except Exception:
                pass
            
                        
            # Removed legacy Sync Options UI (pipeline handles syncing)
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
    
    # (Removed bottom Pipeline Analytics — consolidated at top of Search Results)

        # Link Analytics removed (will be rebuilt in Free Agent Management)

    # Removed redundant end-of-file CSS/JS overrides to reduce conflicts

def show_combined_batches_and_scheduling_page(coach):
    """Combined page for async batches and scheduled searches"""
    # Ensure pandas is available in this function scope before any usage
    import pandas as pd
    st.header("🗓️ Batches & Scheduling")
    st.markdown("Manage scheduled searches and monitor async batch processing.")
    # Supabase health check
    with st.expander("🩺 Supabase Health", expanded=False):
        try:
            supabase_url = os.getenv('SUPABASE_URL', '')
            st.write({"SUPABASE_URL": supabase_url})
            from supabase_utils import get_client
            client = get_client()
            if client:
                st.success("✅ Supabase client initialized")
                try:
                    res = client.table('jobs').select('*', count='exact').limit(0).execute()
                    st.write({"jobs_count": getattr(res, 'count', None)})
                except Exception as e:
                    st.info(f"jobs count not available: {e}")
                try:
                    resp = client.table('agent_profiles').select('*', count='exact').limit(0).execute()
                    st.write({"agent_profiles_count": getattr(resp, 'count', None)})
                except Exception as e:
                    st.info(f"agent_profiles count not available: {e}")
                try:
                    one = client.table('jobs').select('job_title,company,market').order('created_at', desc=True).limit(1).execute()
                    if getattr(one, 'data', None):
                        st.caption("Latest job (sample):")
                        st.write(one.data[0])
                except Exception:
                    pass
            else:
                st.error("❌ Supabase client not available. Check SUPABASE_URL and SUPABASE_ANON_KEY.")
        except Exception as e:
            st.error(f"Health check failed: {e}")

    
    try:
        from async_job_manager import AsyncJobManager
        async_manager = AsyncJobManager()
        
        # Create radio buttons for inner tabs (persistent navigation)
        inner_tab_options = ["📦 Async Batches", "🗓️ Scheduled Searches", "📄 CSV Classification"]
        
        # Initialize session state for inner tab if not exists
        if 'inner_tab_index' not in st.session_state:
            st.session_state.inner_tab_index = 0
        
        selected_inner_tab = st.radio(
            "Select Section",
            options=inner_tab_options,
            index=st.session_state.inner_tab_index,
            key="inner_tab_radio",
            horizontal=True
        )
        
        # Update session state based on selection
        st.session_state.inner_tab_index = inner_tab_options.index(selected_inner_tab)
        
        if selected_inner_tab == "📦 Async Batches":
            st.markdown("### 🚀 Batch Job Scheduler")
            st.markdown("Create async Google/Indeed jobs with the same search parameters as main search")
            
            # Simple batch creation form
            with st.expander("➕ Create New Batch Job", expanded=True):
                with st.form("batch_scheduler"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        batch_search_terms = st.text_input("🔍 Search Terms", 
                                                         value="CDL Driver No Experience",
                                                         help="Job search keywords")
                        
                        batch_location_type = st.selectbox("📍 Location Type", 
                                                         ["Select Market", "Custom Location"])
                        
                        if batch_location_type == "Select Market":
                            batch_markets = st.multiselect("Markets", 
                                                          ["Houston", "Dallas", "Bay Area", "Stockton", "Denver", "Vegas", "Newark", "Phoenix", "Trenton", "Inland Empire"],
                                                          default=["Houston"])
                        else:
                            batch_custom_location = st.text_input("Custom Location", 
                                                                placeholder="e.g., Austin TX, 90210")
                    
                    with col2:
                        batch_source = st.selectbox("Source", ["Google Jobs", "Indeed"])
                        batch_job_limit = st.selectbox("Job Limit", [100, 250, 500, 1000], index=1)
                        batch_route_filter = st.selectbox("Route Filter", ["All Routes", "Local Only", "OTR Only"])
                    
                    with col3:
                        batch_frequency = st.selectbox("Frequency", ["Once", "Daily", "Weekly"])
                        if batch_frequency == "Weekly":
                            batch_days = st.multiselect("Days", 
                                                       ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                                                       default=["Mon", "Wed", "Fri"])
                        batch_time = st.time_input("Run Time", value=pd.Timestamp("02:00").time())
                    
                    # Submit buttons
                    col_save, col_run = st.columns(2)
                    with col_save:
                        submitted = st.form_submit_button("💾 Save for Later", use_container_width=True)
                    with col_run:
                        run_now = st.form_submit_button("🚀 Run Now", use_container_width=True, type="primary")
                    
                    if submitted or run_now:
                        try:
                            from async_job_manager import AsyncJobManager
                            manager = AsyncJobManager()
                            
                            # Determine location
                            if batch_location_type == "Select Market":
                                location = ", ".join(batch_markets) if batch_markets else "Houston"
                            else:
                                location = batch_custom_location or "Houston, TX"
                            
                            # Create job parameters
                            search_params = {
                                'search_terms': batch_search_terms,
                                'location': location,
                                'limit': batch_job_limit,
                                'route_filter': batch_route_filter,
                                'frequency': batch_frequency,
                                'coach_username': coach.username,
                                'run_immediately': run_now  # Flag for immediate execution
                            }
                            
                            # Submit the job
                            if batch_source == "Google Jobs":
                                job = manager.submit_google_search(search_params, coach.username)
                                if run_now:
                                    st.success(f"🚀 Google Jobs batch submitted and running! Job ID: {job.id}")
                                else:
                                    st.success(f"💾 Google Jobs batch saved for later! Job ID: {job.id}")
                            else:
                                job = manager.submit_indeed_search(search_params, coach.username)
                                if run_now:
                                    st.success(f"🚀 Indeed batch submitted and running! Job ID: {job.id}")
                                else:
                                    st.success(f"💾 Indeed batch saved for later! Job ID: {job.id}")
                            
                            st.rerun()  # Refresh to show the job in table
                            
                        except Exception as e:
                            st.error(f"❌ Failed to create batch: {e}")
            
            # Simple batch jobs table
            st.markdown("### 📊 Batch Jobs")
            show_simple_batch_table(coach)
        
        elif selected_inner_tab == "🗓️ Scheduled Searches":
            # Scheduled Searches content 
            st.markdown("Manage your scheduled job searches and view their status.")
            st.caption("Times below are Central Time (America/Chicago)")
            
            # Create new scheduled search - enhanced with Indeed async support
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
                            help="Both Google & Indeed run async batches in background"
                        )
                        
                        schedule_type = st.selectbox("Frequency", ["Daily", "Weekly", "Once"])
                        schedule_time = st.time_input("Run at (Central Time)", value=pd.Timestamp("02:00").time())
                    
                    if schedule_type == "Weekly":
                        days = st.multiselect("Days of Week", 
                            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                            default=["Monday", "Wednesday", "Friday"]
                        )
                    
                    max_jobs = st.slider("Max Jobs per Search", 100, 1000, 500)
                    
                    # Advanced search options
                    st.markdown("**Advanced Search Options**")
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        search_radius = st.selectbox(
                            "Search Radius (miles)", 
                            [0, 25, 50, 100], 
                            index=2,  # default to 50
                            help="0 = Exact location only (faster), >0 = Include nearby cities"
                        )
                    
                    with col4:
                        exact_location_only = st.checkbox(
                            "Use exact location only", 
                            value=(search_radius == 0),
                            help="Faster and more stable searches, but may return fewer jobs"
                        )
                    
                    # Override radius if exact location is checked
                    if exact_location_only:
                        search_radius = 0
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        create_clicked = st.form_submit_button("Create Schedule", use_container_width=True)
                    with col_btn2:
                        execute_now = st.form_submit_button("🌙 Execute at Midnight", use_container_width=True, type="secondary")

                    if create_clicked:
                        st.success("Scheduled search created! (Note: Backend implementation in progress)")

                    if execute_now:
                        try:
                            from async_job_manager import AsyncJobManager
                            mgr = AsyncJobManager()
                            submitted = []
                            if 'google' in sources:
                                params = {
                                    'search_terms': search_terms,
                                    'location': location,
                                    'limit': max_jobs,
                                    'radius': search_radius,
                                    'exact_location': exact_location_only,
                                    'coach_username': coach.username
                                }
                                job = mgr.submit_google_search(params, coach.username)
                                submitted.append(('Google', job.id))
                            if 'indeed' in sources:
                                params = {
                                    'search_terms': search_terms,
                                    'location': location,
                                    'limit': max_jobs,
                                }
                                job = mgr.submit_indeed_search(params, coach.username)
                                submitted.append(('Indeed', job.id))
                            if submitted:
                                lines = "\n".join([f"• {src}: Batch #{jid}" for src, jid in submitted])
                                st.success(f"Search submitted:\n{lines}")
                                st.info("Track progress in the Async Batches tab.")
                                st.rerun()
                            else:
                                st.info("No sources selected to execute.")
                        except Exception as e:
                            st.error(f"Execute error: {e}")
            
            # Show existing scheduled searches (placeholder)
            st.subheader("Active Scheduled Searches")
            st.info("📋 No scheduled searches configured yet. Backend implementation in progress.")
            
            # Show recent scheduled search history (placeholder)
            st.subheader("Recent Scheduled Search History") 
            st.info("📊 Search history will appear here once scheduling is active.")

        elif selected_inner_tab == "📄 CSV Classification":
            st.markdown("### 📄 Classify CSV (Outscraper → Pipeline)")
            st.caption("Drop an Outscraper CSV (Google or Indeed). We will map fields, classify with AI, and generate outputs. Markets are tracked as plain names (e.g., Dallas, Bay Area, Inland Empire). City,ST is used only for scraping — not here.")

            # Upload control
            uploaded = st.file_uploader("Upload Outscraper CSV", type=["csv"], accept_multiple_files=False)
            csv_preview_cols = []
            csv_preview = None
            if uploaded is not None:
                try:
                    from io import StringIO
                    _raw = uploaded.getvalue()
                    csv_preview = pd.read_csv(StringIO(_raw.decode('utf-8', errors='ignore')), nrows=50)
                    csv_preview_cols = list(csv_preview.columns)
                except Exception:
                    pass
            colL, colR = st.columns([2, 1])
            with colL:
                source_type = st.radio("Source Type", ["Outscraper (Indeed)", "Outscraper (Google)"], horizontal=True)
                market_source = st.radio("Market Assignment", [
                    "Choose one market for all rows",
                    "Map from CSV column"
                ], index=0)
                standard_markets = [
                    "Houston", "Dallas", "Bay Area", "Stockton", "Denver",
                    "Las Vegas", "Newark", "Phoenix", "Trenton", "Inland Empire", "San Antonio", "Austin"
                ]
                chosen_market = st.selectbox("Target Market (stored in meta.market)", standard_markets, index=1,
                                             help="Used when 'Choose one market' is selected, and as fallback for unmapped values.")
                route_filter = st.selectbox("Route Filter", ["both", "local", "otr"], index=0)
            with colR:
                st.caption("This path classifies CSV jobs and stores them to Supabase memory database with tracking URLs. No PDFs generated.")
                if uploaded is not None and market_source == "Map from CSV column":
                    # Let the user pick the market column before running
                    default_idx = 0
                    for i, c in enumerate(csv_preview_cols):
                        if str(c).strip().lower() in ("market", "meta.market", "markets"):
                            default_idx = i
                            break
                    st.markdown("Pick the CSV column that contains market names (e.g., Dallas, Bay Area):")
                    market_col_preview = st.selectbox("CSV column for market", csv_preview_cols or [""], index=min(default_idx, max(len(csv_preview_cols)-1, 0)))
                    if csv_preview is not None and market_col_preview:
                        try:
                            vc = csv_preview[market_col_preview].astype(str).str.strip().value_counts().head(10)
                            st.caption("Sample market values (top 10):")
                            st.write(vc)
                        except Exception:
                            pass

            run_csv = st.button("🚀 Classify CSV", type="primary", disabled=(uploaded is None))
            if uploaded and run_csv:
                try:
                    from io import StringIO
                    csv_bytes = uploaded.getvalue()
                    df_src = pd.read_csv(StringIO(csv_bytes.decode('utf-8', errors='ignore')))
                    st.success(f"✅ Loaded CSV with {len(df_src)} rows and {len(df_src.columns)} columns")

                    # Quick check: do any description-like columns end with ellipses?
                    try:
                        text_cols = [c for c in df_src.columns if df_src[c].dtype == object]
                        def _ends_with_ellipsis(series):
                            try:
                                s = series.astype(str).str.strip()
                                return s.str.endswith('...') | s.str.endswith('…')
                            except Exception:
                                return series.astype(str).str.strip().str.endswith('...')
                        ellipsis_counts = {}
                        for c in text_cols:
                            cnt = int(_ends_with_ellipsis(df_src[c]).sum())
                            if cnt:
                                ellipsis_counts[c] = cnt
                        total_any = 0
                        if ellipsis_counts:
                            any_mask = None
                            for c in ellipsis_counts.keys():
                                m = _ends_with_ellipsis(df_src[c])
                                any_mask = m if any_mask is None else (any_mask | m)
                            total_any = int(any_mask.sum()) if any_mask is not None else 0
                        if total_any:
                            st.warning(f"ℹ️ {total_any} rows end with ellipses (…) in at least one text column.")
                            top = sorted(ellipsis_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
                            st.caption("Top columns with trailing ellipses:")
                            for name, cnt in top:
                                st.write(f"• {name}: {cnt}")
                        else:
                            st.info("No trailing ellipses detected in text columns.")
                    except Exception:
                        pass

                    # Map CSV to raw Outscraper-like rows
                    raw_rows = []
                    cols = {c.lower(): c for c in df_src.columns}

                    def first(row, names, default=''):
                        for n in names:
                            k = cols.get(n.lower())
                            if k is not None:
                                v = row.get(k)
                                if pd.notna(v) and str(v).strip():
                                    return str(v).strip()
                        return default

                    for _, row in df_src.iterrows():
                        title = first(row, ["title", "job_title", "job"], "")
                        company = first(row, ["company", "company_name", "employer"], "")
                        location_raw = first(row, ["formattedLocation", "location", "city", "job_location"], "")
                        # Prefer concrete apply URL
                        apply_url = first(row, ["viewJobLink", "apply_url", "applyUrl", "url", "link"], "")
                        # Extract description/snippet - CRITICAL for AI classification
                        description = first(row, ["snippet", "description", "job_description", "jobDescription", "details"], "")
                        # Build minimal Outscraper-like object
                        raw = {
                            "title": title,
                            "company": company,
                            "formattedLocation": location_raw,
                            "viewJobLink": apply_url,
                            "snippet": description,  # Use 'snippet' key to match canonical transform expectations
                        }
                        raw_rows.append(raw)

                    # Run through pipeline stages
                    from pipeline_v3 import FreeWorldPipelineV3
                    from canonical_transforms import transform_ingest_outscraper, transform_business_rules
                    from shared_search import MARKET_TO_LOCATION
                    from jobs_schema import ensure_schema

                    pipe = FreeWorldPipelineV3()
                    # Ingest
                    st.info("📥 Ingesting…")
                    df_ing = transform_ingest_outscraper(raw_rows, pipe.run_id) if raw_rows else ensure_schema(pd.DataFrame())
                    st.success(f"✅ Ingested: {len(df_ing)} rows")
                    # Apply stages 2-6 using pipeline helpers
                    st.info("🧹 Normalizing…")
                    df_norm = pipe._stage2_normalization(df_ing)
                    st.success("✅ Normalized")
                    # Assign markets
                    if market_source == "Choose one market for all rows":
                        df_rules = pipe._stage3_business_rules(df_norm, chosen_market)
                    else:
                        # Build normalized meta.market from a CSV column
                        cols_list = list(df_src.columns)
                        market_col = market_col_preview if 'market_col_preview' in locals() and market_col_preview else st.selectbox("CSV column for market", cols_list)
                        st.info(f"🏷️ Mapping markets from CSV column: {market_col}")
                        # Prepare mappings
                        inverse_map = {v: k for k, v in MARKET_TO_LOCATION.items()}  # "City, ST" -> "Market"
                        cities_map = {v.split(',')[0].strip(): k for k, v in MARKET_TO_LOCATION.items()}  # City -> Market

                        def _normalize_market(v: str) -> str:
                            try:
                                s = str(v or '').strip()
                                if not s:
                                    return chosen_market
                                # Exact market name (case-insensitive)
                                for m in standard_markets:
                                    if s.lower() == m.lower():
                                        return m
                                # Map from "City, ST"
                                if s in inverse_map:
                                    return inverse_map[s]
                                # Map from City only
                                city = s.split(',')[0].strip()
                                if city in cities_map:
                                    return cities_map[city]
                                # Special handling
                                if city.lower() == 'berkeley':
                                    return 'Bay Area'
                                if city.lower() == 'ontario':
                                    return 'Inland Empire'
                                # Strip state if present (ensure no comma state suffix)
                                if ',' in s:
                                    return s.split(',')[0].strip()
                                return s
                            except Exception:
                                return chosen_market

                        # Support multiple markets per row by splitting on common delimiters
                        import re as _re
                        def _extract_markets(val: str):
                            try:
                                s = str(val or '').strip()
                                if not s:
                                    return [chosen_market]
                                # Split on ; | / & and the word 'and' (but NOT comma, which is used for City, ST)
                                parts = _re.split(r"[;\\/|]|\\s*&\\s*|\\s+and\\s+", s, flags=_re.IGNORECASE)
                                parts = [p.strip() for p in parts if p and p.strip()]
                                if not parts:
                                    return [_normalize_market(s)]
                                # Normalize each token and de-dup while preserving order
                                seen = set()
                                out = []
                                for p in parts:
                                    mk = _normalize_market(p)
                                    key = mk.lower()
                                    if key not in seen and mk:
                                        seen.add(key)
                                        out.append(mk)
                                return out or [chosen_market]
                            except Exception:
                                return [chosen_market]

                        try:
                            mk_lists = df_src[market_col].apply(_extract_markets)
                            df_exp = df_norm.copy()
                            df_exp['meta.market'] = mk_lists
                            df_exp = df_exp.explode('meta.market')
                            # Guard: drop empties and fill with chosen_market
                            df_exp['meta.market'] = df_exp['meta.market'].fillna(chosen_market).astype(str)
                            st.write("🔎 Market distribution:", df_exp['meta.market'].value_counts().to_dict())
                            df_rules = transform_business_rules(df_exp, filter_settings={})
                        except Exception:
                            # Fallback: assign chosen market to all rows
                            df_norm['meta.market'] = chosen_market
                            df_rules = transform_business_rules(df_norm, filter_settings={})
                    st.info("🧼 Deduplicating…")
                    df_dedup = pipe._stage4_deduplication(df_rules)
                    st.success(f"✅ Deduped to {len(df_dedup)} rows")
                    st.info("🤖 Classifying with AI…")
                    df_ai = pipe._stage5_ai_classification(df_dedup, force_fresh_classification=True)
                    try:
                        st.write("🔎 Match breakdown:", df_ai['ai.match'].value_counts().to_dict())
                    except Exception:
                        pass
                    st.info("🧭 Deriving route types and routing…")
                    
                    # Debug: Check AI classification before routing
                    print(f"🔍 DEBUG: Before routing - AI match counts: {df_ai['ai.match'].value_counts().to_dict() if 'ai.match' in df_ai.columns else 'No ai.match column'}")
                    
                    df_route = pipe._stage5_5_route_rules(df_ai)
                    df_final = pipe._stage6_routing(df_route, 'both')
                    
                    # Debug: Check final status after routing
                    if 'route.final_status' in df_final.columns:
                        final_status_counts = df_final['route.final_status'].value_counts().to_dict()
                        print(f"🔍 DEBUG: After routing - Final status counts: {final_status_counts}")
                        included_count = sum(1 for status in final_status_counts.keys() if status.startswith('included'))
                        print(f"🔍 DEBUG: Jobs with 'included' status: {included_count}")
                    else:
                        print(f"🔍 DEBUG: No route.final_status column found after routing!")

                    # Classification summary
                    try:
                        total_jobs = int(len(df_final))
                        included = int((df_final['route.final_status'].astype(str).str.startswith('included')).sum()) if 'route.final_status' in df_final.columns else 0
                        ai_good = int((df_final['ai.match'].astype(str).str.lower() == 'good').sum()) if 'ai.match' in df_final.columns else 0
                        ai_soso = int((df_final['ai.match'].astype(str).str.lower() == 'so-so').sum()) if 'ai.match' in df_final.columns else 0
                        local_routes = int((df_final['ai.route_type'].astype(str) == 'Local').sum()) if 'ai.route_type' in df_final.columns else 0
                        otr_routes = int((df_final['ai.route_type'].astype(str) == 'OTR').sum()) if 'ai.route_type' in df_final.columns else 0

                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            st.metric("Total Classified", total_jobs)
                        with m2:
                            st.metric("Included (quality)", included)
                        with m3:
                            st.metric("Excellent Matches", ai_good)
                        with m4:
                            st.metric("Possible Fits", ai_soso)

                        r1, r2 = st.columns(2)
                        with r1:
                            st.metric("Local Routes", local_routes)
                        with r2:
                            st.metric("OTR Routes", otr_routes)
                    except Exception:
                        pass

                    # Ensure meta.market stores plain market names (no state abbreviations)
                    try:
                        standard_markets_set = {m.lower(): m for m in standard_markets}
                        from shared_search import MARKET_TO_LOCATION
                        inv_map = {v: k for k, v in MARKET_TO_LOCATION.items()}  # "City, ST" -> Market
                        city_map = {v.split(',')[0].strip().lower(): k for k, v in MARKET_TO_LOCATION.items()}  # city -> Market

                        def _sanit_market(val: str) -> str:
                            s = str(val or '').strip()
                            if not s:
                                return chosen_market
                            # exact market name
                            if s.lower() in standard_markets_set:
                                return standard_markets_set[s.lower()]
                            # map from City, ST
                            if s in inv_map:
                                return inv_map[s]
                            # if includes comma, strip state
                            if ',' in s:
                                s = s.split(',')[0].strip()
                            # map from city only
                            mk = city_map.get(s.lower())
                            if mk:
                                return mk
                            # special cases
                            if s.lower() == 'berkeley':
                                return 'Bay Area'
                            if s.lower() == 'ontario':
                                return 'Inland Empire'
                            return s

                        if 'meta.market' in df_final.columns:
                            df_final['meta.market'] = df_final['meta.market'].apply(_sanit_market)
                    except Exception:
                        pass

                    # Generate tracking URLs for CSV jobs (previously missing)
                    try:
                        from link_tracker import LinkTracker
                        link_tracker = LinkTracker()
                        if link_tracker.is_available:
                            jobs_without_tracking = df_final[df_final.get('meta.tracked_url', '').fillna('') == '']
                            if len(jobs_without_tracking) > 0:
                                st.info(f"🔗 Generating tracking URLs for {len(jobs_without_tracking)} CSV jobs...")
                                
                                for idx, job in jobs_without_tracking.iterrows():
                                    original_url = job.get('source.url', '')
                                    if original_url:
                                        job_title = job.get('source.title', 'CSV Job')[:50]  # Truncate for clean tracking
                                        
                                        # Create tracking tags for CSV jobs
                                        tags = ['source:csv']
                                        if job.get('meta.market'):
                                            tags.append(f"market:{job.get('meta.market')}")
                                        if job.get('ai.match'):
                                            tags.append(f"match:{job.get('ai.match')}")
                                        if job.get('ai.route_type'):
                                            tags.append(f"route:{job.get('ai.route_type')}")
                                        
                                        tracked_url = link_tracker.create_short_link(
                                            original_url,
                                            title=f"CSV Import: {job_title}",
                                            tags=tags
                                        )
                                        
                                        if tracked_url and tracked_url != original_url:
                                            df_final.at[idx, 'meta.tracked_url'] = tracked_url
                                        else:
                                            df_final.at[idx, 'meta.tracked_url'] = original_url
                                
                                st.success(f"✅ Generated tracking URLs for {len(jobs_without_tracking)} CSV jobs")
                            else:
                                st.info("ℹ️ All CSV jobs already have tracking URLs")
                        else:
                            st.warning("⚠️ LinkTracker not available - using original URLs")
                            # Ensure all jobs have meta.tracked_url field populated
                            missing_urls = df_final['meta.tracked_url'].fillna('') == ''
                            df_final.loc[missing_urls, 'meta.tracked_url'] = df_final.loc[missing_urls, 'source.url']
                    except Exception as link_e:
                        st.warning(f"⚠️ Link generation failed: {link_e} - using original URLs")
                        missing_urls = df_final.get('meta.tracked_url', pd.Series(dtype=str)).fillna('') == ''
                        df_final.loc[missing_urls, 'meta.tracked_url'] = df_final.loc[missing_urls, 'source.url']

                    # Store to memory (Supabase) WITH tracking URLs - using same logic as classify_csv.py
                    st.info("🔍 Running Data Quality Control before Supabase upload...")
                    try:
                        # Quality Control: Validate data before upload (same as classify_csv.py)
                        from data_quality_control import validate_jobs_for_upload
                        
                        # Mark all jobs as fresh for storage (CSV jobs are always considered fresh)
                        df_final = df_final.copy()
                        df_final['sys.is_fresh_job'] = True
                        
                        # Filter jobs that should go to Supabase: passed_all_filters or included*
                        final_status_col = 'route.final_status'
                        if final_status_col in df_final.columns:
                            supabase_jobs = df_final[
                                (df_final[final_status_col] == 'passed_all_filters') |
                                (df_final[final_status_col].str.startswith('included', na=False))
                            ].copy()
                        else:
                            # Fallback if no routing status column
                            supabase_jobs = df_final.copy()
                        
                        if len(supabase_jobs) == 0:
                            st.info("ℹ️ No jobs qualified for Supabase storage (must have status 'passed_all_filters' or 'included')")
                        else:
                            # Run QC validation (non-strict mode for CSV - we want to store data but show warnings)
                            df_validated, qc_report = validate_jobs_for_upload(supabase_jobs, strict_mode=False)
                            
                            st.text(qc_report)
                            
                            # QC is now REPORT-ONLY mode - always proceed to upload all jobs
                            # Store validated jobs to Supabase directly (same as classify_csv.py)
                            st.info(f"💾 Storing {len(df_validated)} QC-validated jobs to Supabase...")
                            from job_memory_db import JobMemoryDB
                            memory_db = JobMemoryDB()
                            
                            success = memory_db.store_classifications(df_validated)
                            error_count = (df_validated.get('ai.match', '') == 'error').sum() if 'ai.match' in df_validated.columns else 0
                            
                            if success:
                                if error_count > 0:
                                    st.success(f"✅ Stored {len(df_validated)} QC-validated jobs to Supabase ({error_count} had classification errors)")
                                else:
                                    st.success(f"✅ Stored {len(df_validated)} QC-validated jobs to Supabase with tracking URLs")
                                    
                                # Show data quality summary
                                rejected_count = len(supabase_jobs) - len(df_validated)
                                filtered_count = len(df_final) - len(supabase_jobs)
                                if rejected_count > 0:
                                    st.info(f"📊 QC Summary: {rejected_count} jobs had quality issues but were stored with warnings")
                                if filtered_count > 0:
                                    st.info(f"📊 Routing Summary: {filtered_count} jobs filtered out (not 'passed_all_filters' or 'included')")
                            else:
                                st.warning("⚠️ Failed to store some jobs to Supabase")
                    except Exception as store_e:
                        st.warning(f"⚠️ Classification complete, but Supabase storage failed: {store_e}")
                    
                    # CSV Download Section - Always show after processing
                    st.markdown("---")
                    st.markdown("### 📄 **Export Options**")
                    col_download, col_stats = st.columns([1, 1])
                    
                    with col_download:
                        # Generate CSV for download
                        try:
                            # Check if df_final exists and has data
                            if 'df_final' in locals() and len(df_final) > 0:
                                # Use the final DataFrame with all markets and statuses
                                csv_buffer = df_final.to_csv(index=False)
                                
                                # Create filename with timestamp
                                from datetime import datetime
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"classified_jobs_multi_market_{timestamp}.csv"
                                
                                st.download_button(
                                    label="📥 Download Full Classified Data (All Markets)",
                                    data=csv_buffer,
                                    file_name=filename,
                                    mime="text/csv",
                                    help="Download complete classified DataFrame with all jobs from all markets (includes filtered jobs for analysis)"
                                )
                                
                                # Show CSV stats
                                total_csv_jobs = len(df_final)
                                included_csv_jobs = int((df_final['route.final_status'].str.startswith('included')).sum()) if 'route.final_status' in df_final.columns else 0
                                filtered_csv_jobs = total_csv_jobs - included_csv_jobs
                                
                                st.caption(f"CSV contains: {total_csv_jobs} jobs total • {included_csv_jobs} included • {filtered_csv_jobs} filtered/bad")
                            else:
                                st.info("📤 CSV download will be available after successful classification")
                                st.caption("Upload a CSV file and run classification to enable download")
                        except Exception as csv_e:
                            st.error(f"❌ CSV generation failed: {csv_e}")
                            import traceback
                            st.code(traceback.format_exc())
                    
                    with col_stats:
                        # Enhanced classification summary
                        try:
                            if 'df_final' in locals() and len(df_final) > 0:
                                # Calculate comprehensive stats
                                total_jobs = len(df_final)
                                
                                # AI match breakdown
                                ai_good = int((df_final.get('ai.match', '') == 'good').sum())
                                ai_soso = int((df_final.get('ai.match', '') == 'so-so').sum()) 
                                ai_bad = int((df_final.get('ai.match', '') == 'bad').sum())
                                ai_error = int((df_final.get('ai.match', '') == 'error').sum())
                                
                                # Route type breakdown
                                local_routes = int((df_final.get('ai.route_type', '') == 'Local').sum())
                                otr_routes = int((df_final.get('ai.route_type', '') == 'OTR').sum())
                                regional_routes = int((df_final.get('ai.route_type', '') == 'Regional').sum())
                                
                                # Final status breakdown
                                if 'route.final_status' in df_final.columns:
                                    included_jobs = int(df_final['route.final_status'].str.startswith('included').sum())
                                    filtered_jobs = int(df_final['route.final_status'].str.startswith('filtered').sum())
                                    passed_filters = int((df_final['route.final_status'] == 'passed_all_filters').sum())
                                else:
                                    included_jobs = ai_good + ai_soso
                                    filtered_jobs = ai_bad
                                    passed_filters = 0
                                
                                st.markdown("**📊 Classification Summary**")
                                st.write(f"**Total Jobs Processed:** {total_jobs}")
                                st.write(f"**✅ Included for Export:** {included_jobs}")
                                st.write(f"**🎯 Excellent Matches:** {ai_good}")  
                                st.write(f"**👍 Good Fits:** {ai_soso}")
                                st.write(f"**❌ Filtered Out:** {filtered_jobs}")
                                if ai_error > 0:
                                    st.write(f"**⚠️ Classification Errors:** {ai_error}")
                                
                                st.markdown("**🚛 Route Types**")
                                st.write(f"**🏠 Local:** {local_routes}")
                                st.write(f"**🛣️ OTR:** {otr_routes}")
                                if regional_routes > 0:
                                    st.write(f"**🗺️ Regional:** {regional_routes}")
                            else:
                                st.info("📊 Classification stats will appear after successful processing")
                        except Exception:
                            st.write("📊 Classification stats unavailable")

                    # Show results table (outside column structure)
                    if 'df_final' in locals() and len(df_final) > 0:
                        st.markdown("### 📋 **Classified Jobs Data**")
                        st.dataframe(df_final, use_container_width=True, height=420)

                        # Multi-market display (similar to job search page)
                        try:
                            if 'meta.market' in df_final.columns:
                                unique_mkts = [m for m in df_final['meta.market'].dropna().unique().tolist() if str(m).strip()]
                                if unique_mkts:
                                    st.info(f"📊 Markets detected: {', '.join(sorted(unique_mkts))}")
                                    ordered = sorted(unique_mkts, key=lambda s: s.lower())
                                    for mk in ordered:
                                        try:
                                            st.markdown("---")
                                            col_h, _ = st.columns([8, 2])
                                            with col_h:
                                                st.markdown(f"## 📍 **{mk}**")
                                                st.caption(f"Jobs classified for {mk}")

                                            mdf = df_final[df_final['meta.market'] == mk]

                                            # Included subset for this market
                                            try:
                                                if 'route.final_status' in mdf.columns:
                                                    mask_m = mdf['route.final_status'].astype(str).str.startswith('included')
                                                    mdf_inc = mdf[mask_m] if mask_m.any() else mdf
                                                elif 'ai.match' in mdf.columns:
                                                    mdf_inc = mdf[mdf['ai.match'].isin(['good', 'so-so'])]
                                                else:
                                                    mdf_inc = mdf
                                            except Exception:
                                                mdf_inc = mdf

                                            # Preferred columns similar to job search
                                            cols_pref = ['source.title', 'source.company', 'ai.summary', 'ai.match', 'ai.route_type', 'ai.fair_chance', 'source.indeed_url']
                                            cols_show = [c for c in cols_pref if c in mdf_inc.columns]
                                            st.dataframe(mdf_inc[cols_show] if cols_show else mdf_inc, use_container_width=True, height=360)

                                            # Per-market metrics
                                            try:
                                                inc_count = len(mdf_inc)
                                                total_count = len(mdf)
                                                ai_good_m = int((mdf['ai.match'] == 'good').sum()) if 'ai.match' in mdf.columns else 0
                                                ai_soso_m = int((mdf['ai.match'] == 'so-so').sum()) if 'ai.match' in mdf.columns else 0
                                                local_routes_m = int((mdf['ai.route_type'] == 'Local').sum()) if 'ai.route_type' in mdf.columns else 0
                                                otr_routes_m = int((mdf['ai.route_type'] == 'OTR').sum()) if 'ai.route_type' in mdf.columns else 0
                                                colA, colB, colC, colD = st.columns(4)
                                                with colA:
                                                    st.metric("Quality Jobs Found", inc_count)
                                                with colB:
                                                    st.metric("Total Jobs Analyzed", total_count)
                                                with colC:
                                                    st.metric("Excellent Matches", ai_good_m)
                                                with colD:
                                                    st.metric("Possible Fits", ai_soso_m)
                                                colE, colF = st.columns(2)
                                                with colE:
                                                    st.metric("Local Routes", local_routes_m)
                                                with colF:
                                                    st.metric("OTR Routes", otr_routes_m)
                                            except Exception:
                                                pass

                                            # Full results for this market
                                            with st.expander(f"🔎 Full Results — {mk}", expanded=False):
                                                st.dataframe(mdf, use_container_width=True, height=480)
                                        except Exception as e:
                                            st.warning(f"⚠️ Display error for {mk}: {e}")
                        except Exception:
                            pass

                except Exception as e:
                    st.error(f"❌ CSV classification failed: {e}")
        
    except Exception as e:
        st.error(f"Error loading batches and scheduling: {e}")

def show_scheduled_searches_page(coach):
    """Show scheduled searches management page - DEPRECATED: Use show_combined_batches_and_scheduling_page"""
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
    """Show all async batches in compact spreadsheet view"""
    st.markdown("Monitor async batches and download results")
    
    try:
        from async_job_manager import AsyncJobManager
        # pandas already imported globally
        import os
        async_manager = AsyncJobManager()
        
        # Cache management
        if st.button("🔄 Clear Cache", help="Clear all caches and refresh"):
            clear_all_caches_and_refresh()
        
        # Debug: Check if AsyncJobManager is properly initialized
        cache_info = f"Cache cleared: {st.session_state.get('cache_cleared_at', 'never')}"
        st.write(f"🔍 AsyncJobManager initialized: {async_manager is not None}")
        st.write(f"🔍 Supabase client available: {async_manager.supabase_client is not None}")
        st.write(f"🔍 {cache_info}")
        
        # Batch status checking tool at the top
        col1, col2 = st.columns([2, 1])
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
                                # Update last checked timestamp
                                try:
                                    async_manager.update_job(batch.id, {'last_checked_at': datetime.now(timezone.utc).isoformat()})
                                except Exception:
                                    pass
                                
                                if result:
                                    # Batch is completed, process it
                                    completed_count += 1
                                    st.info(f"🎉 Batch {batch.id} completed! Processing results...")
                                    
                                    # Process the completed batch results
                                    try:
                                        async_manager.process_completed_async_job(batch.id)
                                        st.success(f"✅ Batch {batch.id} processed successfully!")
                                    except Exception as process_error:
                                        st.error(f"❌ Error processing batch {batch.id}: {process_error}")
                                        
                            except Exception as check_error:
                                st.warning(f"⚠️ Error checking batch {batch.id}: {check_error}")
                                continue
                                
                    st.success(f"✅ Checked {checked_count} batches, {completed_count} completed and processed")
                    if completed_count > 0:
                        st.rerun()  # Refresh to show updated status
        
        # Debug section - show raw database counts
        with st.expander("🔍 Debug Info", expanded=False):
            try:
                # Query database directly for debug info
                result = async_manager.supabase_client.table('async_job_queue').select('id,status,job_type,coach_username,created_at').execute()
                if result.data:
                    st.write(f"Total jobs in database: {len(result.data)}")
                    status_counts = {}
                    type_counts = {}
                    for job in result.data:
                        status_counts[job['status']] = status_counts.get(job['status'], 0) + 1
                        type_counts[job['job_type']] = type_counts.get(job['job_type'], 0) + 1
                    st.write("Status distribution:", status_counts)
                    st.write("Job type distribution:", type_counts)
                    
                    # Show recent 5 jobs
                    st.write("Recent 5 jobs:")
                    recent_jobs = sorted(result.data, key=lambda x: x['created_at'], reverse=True)[:5]
                    for job in recent_jobs:
                        st.write(f"- ID {job['id']}: {job['job_type']} | {job['status']} | {job['coach_username']} | {job['created_at']}")
                else:
                    st.write("No jobs found in database")
            except Exception as e:
                st.error(f"Debug query failed: {e}")
        
        # Get all jobs and prepare DataFrame
        pending_jobs = async_manager.get_pending_jobs()
        completed_jobs = async_manager.get_completed_jobs()
        failed_jobs = async_manager.get_failed_jobs()
        
        st.write(f"🔍 Jobs found: {len(pending_jobs)} pending, {len(completed_jobs)} completed, {len(failed_jobs)} failed")
        
        all_jobs = pending_jobs + completed_jobs + failed_jobs
        
        if not all_jobs:
            st.info("No async batches found. Submit a Google or Indeed Jobs search to see batches here.")
            return
        
        # Prepare data for spreadsheet view with integrated actions
        batch_data = []
        for job in all_jobs:
            # Calculate duration or elapsed time
            duration_text = "—"
            if job.status == 'completed' and job.submitted_at and job.completed_at:
                duration = job.completed_at - job.submitted_at  
                duration_text = f"{duration.seconds // 60}m {duration.seconds % 60}s"
            elif job.status in ['pending', 'submitted'] and job.submitted_at:
                elapsed = datetime.now(timezone.utc) - job.submitted_at
                duration_text = f"{elapsed.seconds // 60}m {elapsed.seconds % 60}s"
            
            # Status text (no emojis)
            status_display = job.status.title()
            
            # Ordered (requested) job count — default 500 for Google Jobs if not present
            ordered_limit = job.search_params.get('limit') if isinstance(job.search_params, dict) else None
            if not ordered_limit:
                ordered_limit = 500 if job.job_type == 'google_jobs' else job.search_params.get('max_jobs', 100)

            batch_data.append({
                'ID': job.id,
                'Search Terms': job.search_params.get('search_terms', 'Unknown'),
                'Location': job.search_params.get('location', 'Unknown'),
                'Type': job.job_type.replace('_jobs', '').title(),
                'Coach': job.coach_username,
                'Status': status_display,
                'Ordered': ordered_limit,
                'Quality': job.quality_job_count if job.status == 'completed' else '—',
                'Total': job.result_count if job.status == 'completed' else '—',
                'Duration': duration_text,
                'Submitted': job.submitted_at.strftime('%m/%d %H:%M') if job.submitted_at else '—',
                'Error': job.error_message[:50] + '...' if job.error_message and len(job.error_message) > 50 else job.error_message or '',
                '_csv_filename': job.csv_filename or '',
                '_job_object': job
            })
        
        # Create DataFrame and display with integrated actions
        df = pd.DataFrame(batch_data)
        
        # Display as a table with action buttons integrated
        st.markdown("### 📦 Async Batches")
        
        if df.empty:
            st.info("No batches found.")
        else:
            # Create header row
            header_cols = st.columns([1, 2, 2, 1, 1.5, 1.5, 1, 1, 1, 1.3, 1.3, 1.5, 1.5, 1])
            headers = ['ID', 'Search Terms', 'Location', 'Type', 'Coach', 'Status', 'Ordered', 'Quality', 'Total', 'Duration', 'Submitted', 'Actions', 'Downloads', 'Debug']
            for i, header in enumerate(headers):
                with header_cols[i]:
                    st.markdown(f"**{header}**")
            
            st.markdown("---")
            
            # Display each row with integrated action buttons
            for idx, row in df.iterrows():
                cols = st.columns([1, 2, 2, 1, 1.5, 1.5, 1, 1, 1, 1.3, 1.3, 1.5, 1.5, 1])
                job = row['_job_object']
                
                # Basic info columns
                with cols[0]:
                    st.write(str(row['ID']))
                with cols[1]:
                    st.write(row['Search Terms'][:30] + '...' if len(row['Search Terms']) > 30 else row['Search Terms'])
                with cols[2]:
                    st.write(row['Location'])
                with cols[3]:
                    st.write(row['Type'])
                with cols[4]:
                    st.write(row['Coach'])
                with cols[5]:
                    st.write(row['Status'])
                with cols[6]:
                    st.write(row['Ordered'])
                with cols[7]:
                    st.write(row['Quality'])
                with cols[8]:
                    st.write(row['Total'])
                with cols[9]:
                    st.write(row['Duration'])
                with cols[10]:
                    # Display submission time in Central Time if available
                    try:
                        from zoneinfo import ZoneInfo
                        central = ZoneInfo("America/Chicago")
                        _submitted_at = job.submitted_at.astimezone(central) if job.submitted_at else None
                        st.write(_submitted_at.strftime('%m/%d %H:%M CT') if _submitted_at else '—')
                    except Exception:
                        st.write(row['Submitted'])
                
                # Action buttons column
                with cols[11]:
                    if job.status in ['pending', 'submitted']:
                        if st.button(f"🚫 Cancel", key=f"cancel_{job.id}", help=f"Cancel batch {job.id}"):
                            try:
                                async_manager.update_job(job.id, {
                                    'status': 'failed',
                                    'error_message': 'Cancelled by admin',
                                    'completed_at': datetime.now(timezone.utc).isoformat()
                                })
                                st.success(f"Batch {job.id} cancelled")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                        # Force process now (helpful if webhook/polling missed)
                        if st.button(f"⚙️ Process Now", key=f"process_{job.id}", help=f"Attempt to finalize batch {job.id} now"):
                            try:
                                async_manager.process_completed_async_job(job.id)
                                st.success(f"Batch {job.id} processed")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Process error: {e}")
                    elif job.status == 'failed':
                        st.write("❌ Failed")
                    else:
                        st.write("—")
                
                # Download buttons column  
                with cols[12]:
                    if job.status == 'completed':
                        # Prefer filename from DB, otherwise glob by job id
                        csv_filename = row.get('_csv_filename') or ''
                        csv_path = f"data/async_batches/{csv_filename}" if csv_filename else ''
                        if not csv_filename or not os.path.exists(csv_path):
                            try:
                                import glob
                                matches = glob.glob(f"data/async_batches/*_job{job.id}.csv")
                                if matches:
                                    # Pick latest by mtime
                                    matches.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                                    csv_path = matches[0]
                                    csv_filename = os.path.basename(csv_path)
                            except Exception:
                                pass
                        if csv_path and os.path.exists(csv_path):
                            with open(csv_path, 'rb') as f:
                                csv_data = f.read()
                            st.download_button(
                        
                                label="📥 CSV",
                                data=csv_data,
                                file_name=csv_filename,
                                mime='text/csv',
                                key=f"csv_{job.id}",
                                help=f"Download CSV for batch {job.id}"
                            )
                        else:
                            st.write("No CSV")
                    else:
                        st.write("—")
                
                # Debug/Parquet column
                with cols[13]:
                    if job.status == 'completed':
                        # Try to find parquet file
                        parquet_path = f"data/async_batches/{job.id}_results.parquet"
                        if os.path.exists(parquet_path):
                            with open(parquet_path, 'rb') as f:
                                parquet_data = f.read()
                            st.download_button(
                        
                                label="📦 PQ",
                                data=parquet_data,
                                file_name=f"batch_{job.id}_results.parquet",
                                mime='application/octet-stream',
                                key=f"parquet_{job.id}",
                                help=f"Download Parquet for batch {job.id}"
                            )
                        else:
                            st.write("No PQ")
                    else:
                        if row['Error']:
                            # Show error icon with truncated error in title attribute via HTML
                            error_text = row['Error'][:30] + '...' if len(row['Error']) > 30 else row['Error']
                            st.markdown(f'<span title="{row["Error"]}" style="cursor: help;">⚠️ {error_text}</span>', unsafe_allow_html=True)
                        else:
                            # Inspect button removed for cleaner UI
                            st.write("—")
                
                # Add separator
                st.markdown("---")
    
    except Exception as e:
        st.error(f"❌ Error loading async batches: {e}")
        import traceback
        st.code(traceback.format_exc())

def show_simple_batch_table(coach):
    """Simple, clear batch table with 4-status workflow"""
    try:
        from async_job_manager import AsyncJobManager
        from datetime import datetime, timedelta
        import pandas as pd
        
        manager = AsyncJobManager()
        
        # Get all jobs for this coach using the available methods
        pending_jobs = manager.get_pending_jobs(None if coach.role == 'admin' else coach.username)
        completed_jobs = manager.get_completed_jobs(None if coach.role == 'admin' else coach.username)
        failed_jobs = manager.get_failed_jobs(None if coach.role == 'admin' else coach.username)
        retrieved_jobs = manager.get_retrieved_jobs(None if coach.role == 'admin' else coach.username)
        
        # Combine all job types
        all_jobs = pending_jobs + completed_jobs + failed_jobs + retrieved_jobs
        
        if not all_jobs:
            st.info("📝 No batch jobs found. Create your first batch above!")
            return
        
        # Prepare table data with your 4-status workflow
        table_data = []
        for job in all_jobs:
            # Calculate time since creation for fetch button logic
            created_time = pd.to_datetime(job.created_at)
            time_since_creation = datetime.now() - created_time.replace(tzinfo=None)
            
            # Map database status to your 4-status workflow
            if job.status == 'submitted':
                if time_since_creation < timedelta(minutes=5):
                    display_status = "⏳ Scheduled"
                else:
                    display_status = "🔄 Pending Response"
            elif job.status == 'processing':
                display_status = "📥 Awaiting Classification"
            elif job.status == 'completed':
                display_status = "✅ Complete"
            elif job.status == 'failed':
                display_status = "❌ Failed"
            else:
                display_status = f"❓ {job.status}"
            
            # Get search parameters
            params = job.search_params if isinstance(job.search_params, dict) else {}
            location = params.get('location', 'Unknown')
            search_terms = params.get('search_terms', 'Unknown')
            limit = params.get('limit', 'Unknown')
            
            table_data.append({
                'ID': job.id,
                'Coach': job.coach_username,
                'Source': 'Google Jobs' if job.job_type == 'google_jobs' else 'Indeed',
                'Location': location,
                'Terms': search_terms,
                'Limit': limit,
                'Status': display_status,
                'Total Jobs': job.result_count or 0,
                'Quality Jobs': job.quality_job_count or 0,
                'Created': created_time.strftime('%m/%d %H:%M'),
                'Actions': time_since_creation.total_seconds() // 60  # Minutes since creation
            })
        
        # Display table
        if table_data:
            df = pd.DataFrame(table_data)
            
            # Display as interactive table with action buttons
            for i, row in df.iterrows():
                job_id = row['ID']
                status = row['Status']
                minutes_old = row['Actions']
                
                with st.container():
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 2, 1, 1, 1, 2])
                    
                    with col1:
                        st.write(f"**{job_id}**")
                    with col2:
                        st.write(row['Coach'])
                    with col3:
                        st.write(f"{row['Source']} | {row['Location']} | {row['Terms'][:20]}...")
                    with col4:
                        st.write(status)
                    with col5:
                        st.write(f"{row['Total Jobs']}")
                    with col6:
                        st.write(f"{row['Quality Jobs']}")
                    with col7:
                        # Action buttons based on status and time
                        if "Pending Response" in status and minutes_old >= 5:
                            if st.button("📥 Fetch Jobs", key=f"fetch_{job_id}"):
                                st.info(f"Checking if batch {job_id} is ready...")
                                # TODO: Implement fetch logic
                        elif "Awaiting Classification" in status:
                            if st.button("⚙️ Process Jobs", key=f"process_{job_id}"):
                                st.info(f"Starting classification for batch {job_id}...")
                                # TODO: Implement process logic
                        elif "Complete" in status:
                            col_action1, col_action2 = st.columns(2)
                            with col_action1:
                                if st.button("📊 Download CSV", key=f"download_{job_id}"):
                                    st.info(f"Preparing download for batch {job_id}...")
                                    # TODO: Implement download logic
                            with col_action2:
                                if st.button("🗑️ Delete", key=f"delete_{job_id}", type="secondary"):
                                    if manager.delete_job(job_id):
                                        st.success(f"✅ Deleted batch {job_id}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to delete batch {job_id}")
                        else:
                            # For other statuses, just show delete button
                            if st.button("🗑️ Delete", key=f"delete_{job_id}", type="secondary"):
                                if manager.delete_job(job_id):
                                    st.success(f"✅ Deleted batch {job_id}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to delete batch {job_id}")
                    
                    st.divider()
                    
        else:
            st.info("📝 No batch jobs found. Create your first batch above!")
            
    except Exception as e:
        st.error(f"❌ Error displaying batch table: {e}")
        import traceback
        st.code(traceback.format_exc())

# Check for Free Agent Portal Access (after function definitions)
try:
    # Newer API (1.30+)
    portal_params = st.query_params
    agent_config = portal_params.get("agent_config")
except Exception:
    # Fallback for older Streamlit
    portal_params = st.query_params
    agent_config = portal_params.get("agent_config", [None])[0]

if agent_config:
    # Debug: Confirm portal detection
    
    # Show free agent portal instead of normal coach interface
    show_free_agent_portal(agent_config)
    st.stop()

if __name__ == "__main__":
    main()
