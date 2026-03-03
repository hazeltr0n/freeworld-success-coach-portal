
"""
FreeWorld Success Coach Portal - Production Environment
DEPLOYMENT VERSION: September 18, 2025 - Full feature deployment from QA
"""

# === IMPORTS ===
import streamlit as st

if not st.session_state.get("_startup_initialized"):
    st.session_state["_startup_initialized"] = True
    print("🚀 App startup completed")

# Production environment - all QA features deployed

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

# Import new display utilities to eliminate code duplication
from display_utils import (
    render_search_summary_header,
    calculate_quality_metrics,
    render_quality_metrics,
    render_supabase_upload_info,
    calculate_route_distribution,
    render_route_distribution,
    render_html_preview,
    render_download_button,
    wrap_html_in_phone_screen,
    render_portal_link_section,
    get_quality_display_dataframe,
    get_full_display_dataframe,
    run_progressive_pipeline,
    run_search_with_location_handling
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
    
    # Set production favicon
    try:
        from PIL import Image
        production_favicon = Image.open("fw_logo.png")
    except (ImportError, FileNotFoundError):
        production_favicon = "🚀"  # Production rocket emoji

    st.set_page_config(
        page_title="FreeWorld Success Coach Portal",
        page_icon=production_favicon,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    # Mark configured to prevent later duplicate calls
    st.session_state["_page_configured"] = True
except Exception:
    # If Streamlit isn't fully initialized (e.g., when imported by tests), ignore
    pass

# Add responsive CSS that keeps login page properly sized
st.markdown("""
<style>
    /* Make dataframes responsive */
    .stDataFrame > div {
        width: 100% !important;
    }

    /* Ensure login page and all content fits in viewport */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
        min-height: fit-content;
    }

    /* Reduce excessive padding that pushes content down */
    .main .block-container {
        padding-top: 0.5rem;
    }

    /* Fix metric box colors - use freedom green brand color */
    .stMetric > div > div > div > div {
        color: #10B981 !important; /* Freedom green */
    }

    .stMetric > div > div > div {
        color: #10B981 !important; /* Freedom green */
    }

    /* Metric label and value styling */
    .stMetric label {
        color: #10B981 !important; /* Freedom green */
    }

    .stMetric > div[data-testid="metric-container"] > div {
        color: #10B981 !important; /* Freedom green */
    }

    /* Responsive form controls - prevent cramping */
    .stSelectbox > div > div {
        min-width: 120px !important;
    }

    .stTextInput > div > div > input {
        min-width: 100px !important;
    }

    /* Main navigation tabs - force horizontal layout */
    div[data-testid="stRadio"] > div > div {
        flex-direction: row !important;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
    }

    /* Form radio buttons can stay vertical for better UX */
    .stForm .stRadio > div {
        flex-direction: column !important;
    }

    /* Better column spacing on mobile */
    @media (max-width: 768px) {
        .stColumn {
            margin-bottom: 1rem !important;
        }

        .stSelectbox > div > div {
            min-width: auto !important;
            width: 100% !important;
        }

        .stTextInput > div > div > input {
            min-width: auto !important;
            width: 100% !important;
        }
    }

    /* Prevent text overflow in columns */
    .stColumn > div {
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }

    /* Allow zoom functionality */
    html {
        zoom: 1;
    }
</style>
""", unsafe_allow_html=True)

# Bootstrap secrets to environment variables
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

import pandas as pd
from datetime import datetime, timezone, timedelta
import base64
import time
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
        except ImportError:
            pass  # dotenv not available in this environment
except Exception as e:
    # Fallback to .env loading for local development
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not available in this environment

APP_VERSION = "2.3.8-security-token-sync"
DEPLOYMENT_TIMESTAMP = "2025-09-01-14-15"
BUILD_COMMIT = "429a7f2"  # Security + Sync implementation

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


def convert_max_jobs(value):
    """Robust conversion for max_jobs field handling 'All', NaN, and numeric values"""
    try:
        if pd.isna(value) or str(value).strip() == "" or str(value) == "All":
            return 250  # Default for "All" or empty values
        return int(float(value))  # Handle float-like strings
    except (ValueError, TypeError):
        return 25  # Safe default if conversion fails

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
    table_id_or_name = _os.getenv("AIRTABLE_CANDIDATES_TABLE_ID")
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

def airtable_find_candidates(query: str, by: str = "name", limit: int = 10, skip_view: bool = False):
    """Lookup candidates in Airtable by name, uuid, or email.

    Environment variables required:
    - AIRTABLE_API_KEY
    - AIRTABLE_BASE_ID
    - AIRTABLE_CANDIDATES_TABLE_ID
    - Optional: AIRTABLE_CANDIDATES_VIEW_ID

    Args:
        skip_view: If True, bypass view filtering (useful for sync operations)
    """
    if not Api:
        return []
    import os as _os
    import time as _time

    api_key = _os.getenv("AIRTABLE_API_KEY")
    base_id = _os.getenv("AIRTABLE_BASE_ID")
    table_id_or_name = _os.getenv("AIRTABLE_CANDIDATES_TABLE_ID")
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
        if view_id and not skip_view:
            kwargs["view"] = view_id
            print(f"🔍 Airtable exact search (view: {view_id}): {primary_formula}")
        elif skip_view:
            print(f"🔍 Airtable exact search (NO VIEW - unrestricted): {primary_formula}")
        else:
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
                "zip_code": f.get("zipcode") or f.get("Zipcode") or f.get("ZIP") or "",
                "cbsa": f.get("CBSA") or f.get("cbsa") or "",  # Core Based Statistical Area for market mapping
                "admin_portal_url": f.get("Admin Portal Record") or f.get("admin_portal_url") or "",
                "placement_status": f.get("placementStatus") or f.get("Placement Status") or "",
                "employment_status": f.get("employmentStatus") or f.get("Employment Status") or "",
            })

        return results[:limit]
    except Exception:
        # Avoid crashing caller
        return []

def sync_agent_airtable_status(agent_uuid: str) -> dict:
    """Sync placement and employment status from Airtable for a specific agent

    Returns updated status dict with placement_status, employment_status, and sync timestamp
    """
    if not agent_uuid:
        print(f"❌ SYNC: No agent_uuid provided")
        return {}

    try:
        # Look up agent in Airtable by UUID (skip view filtering for sync operations)
        print(f"🔍 SYNC: Looking up agent {agent_uuid} in Airtable (unrestricted search)")
        airtable_results = airtable_find_candidates(agent_uuid, by="uuid", limit=1, skip_view=True)

        if not airtable_results:
            print(f"⚠️ SYNC: Agent {agent_uuid} not found in Airtable")
            return {}

        agent_data = airtable_results[0]
        placement_status = agent_data.get('placement_status', '')
        employment_status = agent_data.get('employment_status', '')

        print(f"📊 SYNC: Found agent in Airtable - placement={placement_status}, employment={employment_status}")

        # Update agent_profiles in Supabase with latest Airtable data
        from supabase_utils import get_client
        from datetime import datetime, timezone

        client = get_client()
        if client:
            update_data = {
                'placement_status': placement_status,
                'employment_status': employment_status,
                'airtable_synced_at': datetime.now(timezone.utc).isoformat()
            }

            client.table('agent_profiles').update(update_data).eq('agent_uuid', agent_uuid).execute()
            print(f"✅ Synced Airtable status for {agent_uuid}: placement={placement_status}, employment={employment_status}")

            return update_data

        return {}

    except Exception as e:
        print(f"❌ Error syncing Airtable status for {agent_uuid}: {e}")
        return {}

def sync_all_agents_airtable_status(coach_username: str = None) -> int:
    """Sync placement and employment status from Airtable for all agents (or specific coach's agents)

    OPTIMIZED: Makes ONE bulk Airtable query instead of N individual queries.
    This is 10-50x faster when syncing many agents from a large Airtable (23k+ records).

    Returns count of successfully synced agents
    """
    try:
        from supabase_utils import get_client
        from datetime import datetime, timezone

        client = get_client()
        if not client:
            return 0

        # Get all active agents (optionally filtered by coach)
        query = client.table('agent_profiles').select('agent_uuid').eq('is_active', True)
        if coach_username:
            # MULTI-COACH SUPPORT: Use array contains operator
            query = query.contains('coach_usernames', [coach_username])

        result = query.execute()
        agents = result.data

        if not agents:
            return 0

        # Extract all UUIDs for bulk Airtable lookup
        agent_uuids = [a.get('agent_uuid') for a in agents if a.get('agent_uuid')]
        if not agent_uuids:
            return 0

        print(f"🔍 BULK SYNC: Looking up {len(agent_uuids)} agents in Airtable...")

        # Build OR formula for bulk Airtable query
        # Example: OR({uuid}="uuid1", {uuid}="uuid2", {uuid}="uuid3")
        if not Api:
            print("⚠️ Airtable API not available - skipping sync")
            return 0

        import os
        api_key = os.getenv('AIRTABLE_API_KEY')
        base_id = os.getenv('AIRTABLE_BASE_ID')
        table_id = os.getenv('AIRTABLE_CANDIDATES_TABLE_ID')

        if not api_key or not base_id or not table_id:
            print("⚠️ Airtable credentials not configured")
            return 0

        api = Api(api_key)
        table = api.table(base_id, table_id)

        # Airtable has a formula length limit (~16k chars), so batch if needed
        batch_size = 100  # Conservative batch size to avoid formula length limits
        airtable_data_map = {}

        for i in range(0, len(agent_uuids), batch_size):
            batch_uuids = agent_uuids[i:i+batch_size]

            # Build OR formula for this batch using LOWER() for case-insensitive matching
            # This matches the pattern from airtable_find_candidates function
            or_conditions = []
            for uuid_val in batch_uuids:
                # Escape quotes in UUID values
                escaped_uuid = uuid_val.replace('"', '\\"')
                # Use LOWER() comparison like airtable_find_candidates does
                or_conditions.append(f'LOWER({{uuid}}&"")=LOWER("{escaped_uuid}")')
            formula = f"OR({', '.join(or_conditions)})"  # Note: space after comma!

            try:
                # Single Airtable query for entire batch
                records = table.all(formula=formula, max_records=len(batch_uuids))

                # Map results by UUID for fast lookup
                for record in records:
                    fields = record.get('fields', {})
                    uuid = fields.get('uuid') or fields.get('UUID')
                    if uuid:
                        # Match the field name patterns from airtable_find_candidates
                        placement = fields.get('placementStatus') or fields.get('Placement Status') or ''
                        employment = fields.get('employmentStatus') or fields.get('Employment Status') or ''

                        airtable_data_map[uuid] = {
                            'placement_status': placement,
                            'employment_status': employment
                        }

                        # Debug: Print what we found
                        print(f"📋 AIRTABLE DATA: {uuid[:8]}... placement='{placement}', employment='{employment}'")

                print(f"✅ Retrieved {len(records)} agents from Airtable (batch {i//batch_size + 1})")

            except Exception as e:
                print(f"⚠️ Airtable batch query failed: {e}")
                continue

        # Now update Supabase with all the data we found
        sync_count = 0
        sync_timestamp = datetime.now(timezone.utc).isoformat()

        for agent_uuid in agent_uuids:
            airtable_data = airtable_data_map.get(agent_uuid)
            if airtable_data:
                try:
                    update_data = {
                        'placement_status': airtable_data['placement_status'],
                        'employment_status': airtable_data['employment_status'],
                        'airtable_synced_at': sync_timestamp
                    }

                    client.table('agent_profiles').update(update_data).eq('agent_uuid', agent_uuid).execute()
                    sync_count += 1

                except Exception as e:
                    print(f"⚠️ Failed to update {agent_uuid} in Supabase: {e}")

        print(f"✅ BULK SYNC COMPLETE: Synced {sync_count}/{len(agents)} agents from Airtable")
        return sync_count

    except Exception as e:
        print(f"❌ Error in bulk Airtable sync: {e}")
        import traceback
        traceback.print_exc()
        return 0

# Function to encode image as base64
def get_base64_of_image(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except (FileNotFoundError, OSError):
        return None

def generate_secure_portal_token(agent_uuid: str) -> str:
    """Generate secure token for agent portal access"""
    import hashlib
    return hashlib.md5(f"{agent_uuid}:FreeWorld2025".encode()).hexdigest()[:12]

def map_cbsa_to_market(cbsa: str) -> str:
    """Map a CBSA (Core Based Statistical Area) to a FreeWorld market

    Args:
        cbsa: CBSA string from Airtable (e.g., "Dallas-Fort Worth-Arlington, TX")

    Returns:
        Market name from our 10 FreeWorld markets or "Houston" as fallback
    """
    if not cbsa or pd.isna(cbsa):
        return "Houston"  # Default fallback

    # Direct CBSA → Market mapping for our 10 markets
    CBSA_TO_MARKET = {
        # Dallas
        "Dallas-Fort Worth-Arlington, TX": "Dallas",

        # Houston
        "Houston-The Woodlands-Sugar Land, TX": "Houston",

        # Trenton
        "Trenton-Princeton, NJ": "Trenton",

        # Newark
        "New York-Newark-Jersey City, NY-NJ-PA": "Newark",

        # Las Vegas
        "Las Vegas-Henderson-Paradise, NV": "Las Vegas",

        # Bay Area (multiple CBSAs)
        "San Francisco-Oakland-Berkeley, CA": "Bay Area",
        "San Jose-Sunnyvale-Santa Clara, CA": "Bay Area",
        "Santa Rosa-Petaluma, CA": "Bay Area",
        "Napa, CA": "Bay Area",
        "Vallejo, CA": "Bay Area",

        # Stockton
        "Stockton, CA": "Stockton",
        "Stockton-Lodi, CA": "Stockton",

        # Inland Empire
        "Riverside-San Bernardino-Ontario, CA": "Inland Empire",
        "Los Angeles-Long Beach-Anaheim, CA": "Inland Empire",  # LA metro often overlaps

        # Phoenix
        "Phoenix-Mesa-Chandler, AZ": "Phoenix",
        "Phoenix-Mesa-Scottsdale, AZ": "Phoenix",

        # Denver
        "Denver-Aurora-Lakewood, CO": "Denver",
    }

    cbsa_normalized = str(cbsa).strip()

    # Direct lookup
    if cbsa_normalized in CBSA_TO_MARKET:
        market = CBSA_TO_MARKET[cbsa_normalized]
        print(f"✅ Mapped CBSA '{cbsa}' → {market}")
        return market

    # Fallback to Houston
    print(f"⚠️ CBSA '{cbsa}' not in our 10 markets, defaulting to Houston")
    return "Houston"

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
    """Get the agent's existing static Short.io link from the database"""
    agent_uuid = agent_data.get('agent_uuid', '')
    if not agent_uuid:
        return "Missing UUID - Cannot generate secure link"

    # First try to get the existing custom_url from the agent_data
    existing_custom_url = agent_data.get('custom_url', '')
    if existing_custom_url:
        return existing_custom_url

    # If not in agent_data, fetch from database
    try:
        from supabase_utils import get_client
        client = get_client()
        if client:
            result = client.table('agent_profiles').select('custom_url').eq('agent_uuid', agent_uuid).limit(1).execute()
            if result.data and len(result.data) > 0 and result.data[0].get('custom_url'):
                return result.data[0]['custom_url']
    except Exception as e:
        print(f"⚠️ Could not fetch custom_url from database: {e}")

    # Fallback: generate predictable short link format if no custom_url exists
    short_id = agent_uuid[:8]
    return f"https://freeworldjobs.short.gy/{short_id}"

def generate_tracked_portal_link(agent_data: dict) -> str:
    """Generate Short.io link that points to edge function for portal click tracking"""
    from free_agent_system import generate_agent_url
    from link_tracker import LinkTracker

    agent_uuid = agent_data.get('agent_uuid', '')
    if not agent_uuid:
        return "Missing UUID"

    try:
        # Generate the actual portal URL to redirect to
        actual_portal_url = generate_agent_url(agent_uuid, agent_data)

        # Create edge function URL that will track the click and redirect
        tracker = LinkTracker()
        agent_name = agent_data.get('agent_name', 'Unknown')
        coach_username = agent_data.get('coach_username', '')

        tags = [
            f"coach:{coach_username}",
            f"candidate:{agent_uuid}",
            f"agent:{agent_name.replace(' ', '-')}",
            f"market:{agent_data.get('location', 'Unknown')}",
            "type:portal_access"
        ]

        # Generate edge function URL that will receive the click and redirect to portal
        edge_function_url = tracker.generate_edge_function_url(
            target_url=actual_portal_url,
            candidate_id=agent_uuid,
            tags=tags
        )

        # Create Short.io link that points to the edge function (not directly to portal)
        tracked_shortio_link = tracker.create_short_link(
            edge_function_url,  # Short.io points to edge function
            title=f"Portal - {agent_name}",
            tags=tags,
            candidate_id=agent_uuid
        )

        return tracked_shortio_link or edge_function_url

    except Exception as e:
        print(f"⚠️ Error creating tracked portal link: {e}")
        # Fallback to static Short.io link
        return generate_dynamic_portal_link(agent_data)

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

    # Default analytics settings - no user controls needed
    since_days = 14  # Default to last 2 weeks
    coach_filter = "My Free Agents"  # Default to current coach's agents
    selected_coach = None
    
    # Free Agent search functionality removed (sidebar eliminated)
    agent_search = ""
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

    # Create tabs for different management functions
    agent_tab_options = ["📋 Manage Agents", "🎯 Track Applications"]

    # Initialize session state for tab selection
    if 'agent_management_tab' not in st.session_state:
        st.session_state.agent_management_tab = 0

    # Tab selection using radio buttons
    selected_agent_tab = st.radio(
        "Management Function",
        options=agent_tab_options,
        index=st.session_state.agent_management_tab,
        key="agent_management_tab_radio",
        horizontal=True
    )

    # Update session state
    if selected_agent_tab in agent_tab_options:
        st.session_state.agent_management_tab = agent_tab_options.index(selected_agent_tab)

    st.markdown("---")

    # Show content based on selected tab
    if selected_agent_tab == "📋 Manage Agents":
        show_manage_agents_tab(coach, coach_manager)
    elif selected_agent_tab == "🎯 Track Applications":
        show_track_applications_tab(coach, coach_manager)


def refresh_agent_caches_only(coach_username: str):
    """
    Lightweight refresh: Update analytics table and clear caches to show newly added agents.
    Faster than full sync - skips Airtable sync and click_events refresh.
    """
    try:
        # Step 1: Update analytics table so new agent appears
        # This is critical because the table loads from free_agents_analytics
        from free_agents_rollup import update_free_agents_analytics_table
        try:
            update_free_agents_analytics_table()
            print(f"✅ Updated analytics table with new agent")
        except Exception as e:
            print(f"⚠️ Failed to update analytics: {e}")

        # Step 2: Clear agent caches to force fresh data load
        for show_del in [True, False]:
            agents_cache_key = f'agents_{coach_username}_{show_del}'
            if agents_cache_key in st.session_state:
                del st.session_state[agents_cache_key]

        analytics_cache_key = f'analytics_{coach_username}'
        if analytics_cache_key in st.session_state:
            del st.session_state[analytics_cache_key]

        # Clear hash tracking to reset change detection
        if 'agent_table_last_saved' in st.session_state:
            st.session_state.agent_table_last_saved = {}

        # Clear Streamlit caches
        st.cache_data.clear()

        print(f"✅ Cleared caches for {coach_username}")
        return True
    except Exception as e:
        print(f"❌ Cache clear error: {e}")
        return False


def refresh_all_agent_data(coach_username: str):
    """
    Comprehensive refresh flow: Sync Airtable, update analytics, and clear all caches.
    This is SLOW - only use for the manual "Refresh All" button.
    For adding single agents, use refresh_agent_caches_only() instead.
    """
    try:
        # Step 1: Sync Airtable placement/employment status (OPTIMIZED - bulk query)
        synced_count = sync_all_agents_airtable_status(coach_username)
        if synced_count > 0:
            print(f"✅ Synced {synced_count} agents from Airtable")

        # Step 2: Update analytics table
        from free_agents_rollup import update_free_agents_analytics_table
        try:
            update_free_agents_analytics_table()
            print(f"✅ Updated analytics table")
        except Exception as e:
            print(f"⚠️ Failed to update analytics: {e}")

        # Step 3: Refresh analytics from click_events
        try:
            from supabase_utils import get_client
            client = get_client()
            if client:
                result = client.rpc('scheduled_agents_refresh').execute()
                print(f"✅ Refreshed analytics from click_events and job_feedback")
        except Exception as e:
            if "JSON could not be generated" not in str(e):
                print(f"⚠️ Analytics refresh warning: {e}")

        # Step 4: Clear ALL caches to force fresh data load
        for show_del in [True, False]:
            agents_cache_key = f'agents_{coach_username}_{show_del}'
            if agents_cache_key in st.session_state:
                del st.session_state[agents_cache_key]

        analytics_cache_key = f'analytics_{coach_username}'
        if analytics_cache_key in st.session_state:
            del st.session_state[analytics_cache_key]

        # Clear hash tracking to reset change detection
        if 'agent_table_last_saved' in st.session_state:
            st.session_state.agent_table_last_saved = {}

        # Clear all Streamlit caches
        st.cache_data.clear()

        return True
    except Exception as e:
        print(f"❌ Refresh flow error: {e}")
        return False


def show_manage_agents_tab(coach, coach_manager):
    """Show the Manage Agents tab (original Free Agent management interface)"""
    from free_agent_system import (
        save_agent_profile, load_agent_profiles, load_agent_profiles_with_stats, delete_agent_profile,
        get_agent_click_stats, get_all_agents_click_stats, encode_agent_params, get_market_options
    )

    st.markdown("*Configure job searches for your Free Agents and manage their custom job feeds*")

    # Note about analytics periods
    st.info("📊 **Analytics**: Free Agent metrics show All-Time data and 14-day periods (for bi-weekly coach check-ins).")
    
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
                        # Map CBSA to market if available
                        cbsa = chosen.get('cbsa', '')
                        market = map_cbsa_to_market(cbsa) if cbsa else 'Houston'

                        agent_data = {
                            'agent_uuid': chosen.get('uuid', ''),
                            'agent_name': chosen.get('name', ''),
                            'agent_email': chosen.get('email', ''),
                            'agent_city': chosen.get('city', ''),
                            'agent_state': chosen.get('state', ''),
                            'zip_code': chosen.get('zip_code', ''),
                            'admin_portal_url': chosen.get('admin_portal_url', ''),
                            'placement_status': chosen.get('placement_status', ''),
                            'employment_status': chosen.get('employment_status', ''),
                            'airtable_synced_at': datetime.now(timezone.utc).isoformat(),
                            'cbsa': cbsa,  # Store CBSA from Airtable
                            'location': market,  # Map CBSA to FreeWorld market
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

                                # Generate edge function URL for tracking
                                edge_function_url = link_tracker.generate_edge_function_url(
                                    target_url=full_portal_url,
                                    candidate_id=agent_data['agent_uuid'],
                                    tags=portal_tags
                                )

                                # Create Short.io link that points to edge function
                                shortened_url = link_tracker.create_short_link(edge_function_url, title=f"Portal - {agent_data['agent_name']}", tags=portal_tags, candidate_id=agent_data['agent_uuid'])
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

                            # Lightweight refresh - just clear caches (fast!)
                            refresh_agent_caches_only(coach.username)

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
        
        # Manual Entry Section
        st.markdown("---")
        st.markdown("### Manual Entry")
        st.markdown("Add a Free Agent manually without Airtable lookup")
        
        col1, col2 = st.columns(2)
        with col1:
            manual_agent_name = st.text_input(
                "Agent Name *", 
                placeholder="Enter full name",
                key="manual_agent_name",
                help="Required: Full name of the Free Agent"
            )
            manual_agent_email = st.text_input(
                "Email", 
                placeholder="agent@example.com",
                key="manual_agent_email",
                help="Optional: Agent's email address"
            )
            manual_agent_city = st.text_input(
                "City", 
                placeholder="Houston",
                key="manual_agent_city", 
                help="Optional: Agent's city"
            )
        
        with col2:
            manual_agent_uuid = st.text_input(
                "Agent UUID", 
                placeholder="Auto-generated if empty",
                key="manual_agent_uuid",
                help="Optional: Will generate UUID if not provided"
            )
            manual_agent_state = st.text_input(
                "State", 
                placeholder="TX",
                key="manual_agent_state",
                help="Optional: Agent's state (2-letter code)"
            )
            # Cache market options to avoid duplicate function calls
            market_options = get_market_options()
            manual_location = st.selectbox(
                "Market *",
                options=market_options,
                index=market_options.index("Houston") if "Houston" in market_options else 0,
                key="manual_location",
                help="Required: Market/location for job search"
            )
        
        # Advanced Settings
        with st.expander("⚙️ Advanced Settings", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                manual_route_filter = st.selectbox(
                    "Route Filter",
                    ["both", "local", "otr"],
                    index=0,
                    key="manual_route_filter",
                    help="Filter jobs by route type"
                )
                manual_fair_chance = st.checkbox(
                    "Fair Chance Only",
                    value=False,
                    key="manual_fair_chance",
                    help="Show only fair chance employers"
                )
            with col2:
                manual_max_jobs = st.number_input(
                    "Max Jobs",
                    min_value=1,
                    max_value=100,
                    value=25,
                    key="manual_max_jobs",
                    help="Maximum jobs to show in portal"
                )
                manual_experience = st.selectbox(
                    "Experience Level",
                    ["both", "entry_level", "experienced"],
                    index=0,
                    key="manual_experience",
                    help="Experience level filter"
                )

            # Unified Career Pathway Preferences
            manual_classifier_type = st.selectbox(
                "Job Classification Type",
                ["CDL Traditional", "Career Pathways"],
                index=0,
                key="manual_classifier_type",
                help="CDL Traditional: Focus on experienced CDL driving jobs\nCareer Pathways: Include warehouse-to-driver, dock-to-driver, and training opportunities"
            )

            pathway_options = [
                ("cdl_pathway", "CDL Pathway"),
                ("dock_to_driver", "Dock to Driver"),
                ("internal_cdl_training", "CDL Training Programs"),
                ("warehouse_to_driver", "Warehouse to Driver"),
                ("logistics_progression", "Logistics Career Progression"),
                ("non_cdl_driving", "Non-CDL Driving"),
                ("general_warehouse", "General Warehouse"),
                ("construction_apprentice", "Construction Apprentice"),
                ("stepping_stone", "Career Stepping Stone")
            ]

            manual_pathway_preferences = st.multiselect(
                "Career Pathway Preferences",
                options=[opt[0] for opt in pathway_options],
                format_func=lambda x: next(opt[1] for opt in pathway_options if opt[0] == x),
                default=["cdl_pathway"] if manual_classifier_type == "CDL Traditional" else [],
                key="manual_pathway_preferences",
                help="Select preferred career pathways - CDL Pathway for traditional CDL jobs, others for Career Pathways jobs"
            )
        
        # Add Manual Agent Button
        if st.button("➕ Add Manual Agent", key="add_manual_agent_btn", type="primary"):
            if manual_agent_name and manual_location:
                try:
                    # Generate UUID if not provided
                    if not manual_agent_uuid:
                        import uuid
                        generated_uuid = str(uuid.uuid4())
                    else:
                        generated_uuid = manual_agent_uuid.strip()
                    
                    # Create agent profile
                    classifier_type_value = "cdl" if manual_classifier_type == "CDL Traditional" else "pathway"

                    agent_data = {
                        'agent_uuid': generated_uuid,
                        'agent_name': manual_agent_name.strip(),
                        'agent_email': manual_agent_email.strip() if manual_agent_email else '',
                        'agent_city': manual_agent_city.strip() if manual_agent_city else '',
                        'agent_state': manual_agent_state.strip().upper() if manual_agent_state else '',
                        'location': manual_location,
                        'route_filter': manual_route_filter,
                        'fair_chance_only': manual_fair_chance,
                        'max_jobs': manual_max_jobs,
                        'experience_level': manual_experience,
                        'classifier_type': classifier_type_value,
                        'pathway_preferences': manual_pathway_preferences,  # Include all selected pathways
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
                            
                            shortened_url = link_tracker.create_short_link(
                                full_portal_url, 
                                title=f"Portal - {agent_data['agent_name']}", 
                                tags=portal_tags, 
                                candidate_id=agent_data['agent_uuid']
                            )
                            agent_data['portal_url'] = shortened_url
                            st.write(f"🔗 Generated portal link: {shortened_url}")
                            
                        except Exception as e:
                            st.warning(f"⚠️ Could not generate short link: {e}")
                            agent_data['portal_url'] = full_portal_url  # Fallback to full URL
                        
                        success, message = save_agent_profile(coach.username, agent_data)
                    
                    if success:
                        st.success(f"✅ {manual_agent_name} successfully added to database!")
                        if agent_data.get('portal_url'):
                            st.info(f"🔗 Portal link: {agent_data['portal_url']}")
                        st.balloons()

                        # Lightweight refresh - just clear caches (fast!)
                        refresh_agent_caches_only(coach.username)

                        st.rerun()
                    else:
                        st.error(f"❌ Database save failed: {message}")
                        st.warning("💡 Ensure Supabase is connected and environment variables are set")
                        
                except Exception as e:
                    st.error(f"❌ Error adding manual agent: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
            else:
                st.warning("⚠️ Please enter at least Agent Name and select a Market")

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
        - **classifier_type** (cdl/pathway; defaults to 'cdl') - Job classification type
        - **pathway_preferences** (comma-separated list; optional) - Career pathway filters for pathway classifier

        **Pathway Options**: cdl_pathway, dock_to_driver, internal_cdl_training, warehouse_to_driver, logistics_progression, non_cdl_driving, general_warehouse, construction_apprentice, stepping_stone

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
                            admin_portal_url = str(_get(row, ["admin_portal_url", "Admin Portal Record", "admin_portal"]).strip())
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

                            # Classifier type and pathway preferences
                            classifier_type = str(_get(row, ["classifier_type", "job_type"]).strip().lower() or "cdl")
                            classifier_type = classifier_type if classifier_type in ['cdl', 'pathway'] else 'cdl'

                            # Parse pathway preferences (comma-separated list)
                            pathway_prefs_raw = str(_get(row, ["pathway_preferences", "pathways"]).strip())
                            pathway_prefs = []
                            if pathway_prefs_raw and classifier_type == 'pathway':
                                # Valid pathway options
                                valid_pathways = {
                                    'cdl_pathway', 'dock_to_driver', 'internal_cdl_training', 'warehouse_to_driver',
                                    'logistics_progression', 'non_cdl_driving', 'general_warehouse',
                                    'construction_apprentice', 'stepping_stone'
                                }
                                # Split by comma and validate each pathway
                                for p in pathway_prefs_raw.split(','):
                                    p_clean = p.strip().lower()
                                    if p_clean in valid_pathways:
                                        pathway_prefs.append(p_clean)

                            agent_data = {
                                'agent_uuid': agent_uuid,
                                'agent_name': name,
                                'agent_email': email,
                                'agent_city': city,
                                'agent_state': state,
                                'admin_portal_url': admin_portal_url,
                                'location': market,
                                'route_filter': route_filter if route_filter in ['both', 'local', 'otr'] else 'both',
                                'fair_chance_only': fair,
                                'max_jobs': max_jobs if max_jobs in [15, 25, 50, 100] else 25,
                                'experience_level': exp if exp in ['both', 'entry', 'experienced'] else 'both',
                                'classifier_type': classifier_type,
                                'pathway_preferences': pathway_prefs,
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
                        # Clear ALL relevant caches to force fresh data load (same pattern as Refresh button)
                        for show_del in [True, False]:
                            agents_cache_key = f'agents_{coach.username}_{show_del}'
                            if agents_cache_key in st.session_state:
                                del st.session_state[agents_cache_key]
                        # Clear analytics cache too
                        analytics_cache_key = f'analytics_{coach.username}'
                        if analytics_cache_key in st.session_state:
                            del st.session_state[analytics_cache_key]
                        # Clear legacy cache key if it exists
                        if 'agent_profiles' in st.session_state:
                            del st.session_state['agent_profiles']
                        st.rerun()
            except Exception as e:
                st.error(f"CSV parse error: {e}")
    
    # Add refresh button, deleted agents, and status indicator
    col1, col2, col3 = st.columns([1, 1, 1])

    # Define show_deleted FIRST before using it in cache keys
    with col2:
        show_deleted = st.checkbox("👻 Show Deleted", help="Show soft-deleted (inactive) agents")

    with col1:
        if st.button("🔄 Refresh All", help="Refresh agents, sync Airtable status, and update analytics"):
            with st.spinner("🔄 Refreshing all data..."):
                refresh_all_agent_data(coach.username)
                st.success("✅ All data refreshed successfully!")
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
        except Exception:
            st.warning("🟡 Session")  # Any error connecting to Supabase

    # CACHE AGENTS TO STOP SUPABASE QUERIES ON EDIT
    # Use the show_deleted value from the checkbox defined above
    agents_cache_key = f'agents_{coach.username}_{show_deleted}'

    # AUTO-SYNC AIRTABLE STATUS ON PAGE LOAD (only placement_status and employment_status)
    # Track if we've synced this session
    airtable_sync_key = f'airtable_synced_{coach.username}'
    if airtable_sync_key not in st.session_state:
        print(f"🔄 AUTO-SYNC: Syncing Airtable placement/employment status on page load")
        sync_all_agents_airtable_status(coach.username)
        st.session_state[airtable_sync_key] = True
        print(f"✅ AUTO-SYNC: Airtable sync complete")

    if agents_cache_key not in st.session_state:
        # Only load from Supabase ONCE per session
        try:
            if show_deleted:
                print(f"🔍 LOADING PATH: Using basic loading for deleted agents")
                # For deleted agents, use basic loading since stats don't matter much
                agents = load_agent_profiles(coach.username, include_inactive=True)
                # Add empty stats for compatibility AND fix portal URLs
                for agent in agents:
                    if 'click_count' not in agent:
                        agent['click_count'] = 0
                    if 'total_portal_visits' not in agent:
                        agent['total_portal_visits'] = 0
                    # FIX: Map portal URL for basic loading path
                    agent['portal_url'] = agent.get('portal_url', agent.get('custom_url', ''))
            else:
                print(f"🔍 LOADING PATH: Using analytics rollup for active agents")
                # Use analytics rollup table for better performance and no 1000 click limit
                try:
                    from free_agents_rollup import get_free_agents_analytics
                    agents_df = get_free_agents_analytics(coach_username=coach.username, limit=None)

                    if not agents_df.empty:
                        # Convert DataFrame to list of dicts for compatibility
                        agents = agents_df.to_dict('records')
                        # Map analytics fields to expected format
                        for agent in agents:
                            # Map click data
                            agent['total_clicks'] = agent.get('total_job_clicks', 0)
                            agent['recent_clicks'] = agent.get('total_job_clicks', 0)  # Analytics table may not have 7-day split
                            agent['lookback_days'] = 14  # Fixed 14-day period
                            agent['total_applications'] = agent.get('total_applications', 0)
                            agent['last_application_at'] = agent.get('last_application_at', '')

                            # Map location and preferences - check both field names for compatibility
                            agent['location'] = agent.get('location', agent.get('market', 'Houston'))
                            # Map search config - check both nested structure and direct fields
                            search_config = agent.get('search_config', {}) if isinstance(agent.get('search_config'), dict) else {}
                            agent['route_filter'] = agent.get('route_filter', search_config.get('route_filter', 'both'))
                            agent['fair_chance_only'] = agent.get('fair_chance_only', search_config.get('fair_chance_only', False))
                            agent['max_jobs'] = agent.get('max_jobs', search_config.get('max_jobs', 25))
                            agent['match_level'] = agent.get('match_level', search_config.get('match_level', search_config.get('quality_level', 'good and so-so')))
                            agent['classifier_type'] = agent.get('search_config', {}).get('classifier_type', 'cdl') if isinstance(agent.get('search_config'), dict) else 'cdl'
                            agent['pathway_preferences'] = agent.get('pathway_preferences', [])

                            # Map portal info - check both field names for compatibility
                            custom_url = agent.get('custom_url', '')
                            portal_url = agent.get('portal_url', '')
                            final_portal_url = portal_url or custom_url
                            agent['portal_url'] = final_portal_url
                            print(f"🔗 PORTAL DEBUG: Agent {agent.get('agent_name', 'Unknown')} - custom_url='{custom_url}', portal_url='{portal_url}', final='{final_portal_url}'")
                            agent['admin_portal_url'] = agent.get('admin_portal_url', '')

                            # Map creation info
                            agent['created_at'] = agent.get('created_at', '')

                            # Map Airtable status fields (these should already be in the DataFrame from free_agents_rollup)
                            # Handle NaN values from pandas DataFrame
                            placement_val = agent.get('placement_status', '')
                            employment_val = agent.get('employment_status', '')
                            agent['placement_status'] = '' if pd.isna(placement_val) else str(placement_val)
                            agent['employment_status'] = '' if pd.isna(employment_val) else str(employment_val)

                            # Ensure required fields exist with defaults
                            for field in ['agent_name', 'agent_email', 'agent_city', 'agent_state']:
                                if field not in agent:
                                    agent[field] = ''
                    else:
                        # Fallback to original method if analytics table is empty
                        agents = load_agent_profiles_with_stats(coach.username, 14)
                        # FIX: Map portal URLs for fallback path
                        for agent in agents:
                            agent['portal_url'] = agent.get('portal_url', agent.get('custom_url', ''))
                except Exception as analytics_error:
                    print(f"⚠️ Analytics rollup failed: {analytics_error}, falling back to original method")
                    agents = load_agent_profiles_with_stats(coach.username, 14)
                    # FIX: Map portal URLs for fallback path
                    for agent in agents:
                        agent['portal_url'] = agent.get('portal_url', agent.get('custom_url', ''))

            # CACHE THE AGENTS
            st.session_state[agents_cache_key] = agents
        except Exception as e:
            st.error(f"⚠️ Failed to load agent profiles: {str(e)}")
            st.info("💡 Using fallback mode - some features may be limited")
            agents = []  # Fallback to empty list to prevent crashes
            st.session_state[agents_cache_key] = agents
    else:
        # USE CACHED AGENTS - NO MORE SUPABASE QUERIES ON EDIT!
        agents = st.session_state[agents_cache_key]
    
    # Debug info for testing
    if agents:
        st.info(f"📊 Loaded {len(agents)} agent profile(s)")
    else:
        st.info("📝 No agents configured yet - add your first agent above")
    
    if agents:
        st.markdown("### Your Free Agents")

        # STOP SUPABASE QUERIES ON EDIT - cache the analytics data completely
        analytics_cache_key = f'analytics_{coach.username}'

        if analytics_cache_key not in st.session_state:
            from supabase_utils import get_free_agents_analytics_data
            analytics_df = get_free_agents_analytics_data(coach.username)
            st.session_state[analytics_cache_key] = analytics_df
        else:
            analytics_df = st.session_state[analytics_cache_key]

        # Create lookup for analytics data (always process, just don't query DB)
        analytics_lookup = {}
        if not analytics_df.empty:
            for _, row in analytics_df.iterrows():
                analytics_lookup[row['agent_uuid']] = {
                    'total_clicks': row.get('total_job_clicks', 0),
                    'clicks_14d': row.get('job_clicks_14d', 0),
                    'total_applications': row.get('total_applications', 0),
                    'applications_14d': row.get('applications_14d', 0),
                    'engagement_score': row.get('engagement_score', 0),
                    'activity_level': row.get('activity_level', 'new')
                }

        # Prepare ALL data for the editor - keep EVERY column
        agent_data = []
        for agent in agents:
            # Use analytics data if available, fallback to agent profile data
            agent_uuid = agent.get('agent_uuid', '')
            analytics = analytics_lookup.get(agent_uuid, {})

            stats = {
                    'total_clicks': analytics.get('total_clicks', agent.get('total_clicks', 0)),
                    'clicks_14d': analytics.get('clicks_14d', 0),
                    'total_applications': analytics.get('total_applications', agent.get('total_applications', 0)),
                    'applications_14d': analytics.get('applications_14d', 0),
                    'engagement_score': analytics.get('engagement_score', 0),
                    'activity_level': analytics.get('activity_level', 'new')
            }

            # Determine status
            is_active = agent.get('is_active', True)
            status = "🟢 Active" if is_active else "👻 Deleted"

            # OPTIMIZED PATHWAY LOGIC: Convert to individual checkboxes
            pathway_prefs = agent.get('pathway_preferences', [])
            classifier_type = agent.get('classifier_type', 'cdl')

            # For CDL agents, always include CDL Pathway in the list
            if classifier_type == 'cdl' and 'cdl_pathway' not in pathway_prefs:
                pathway_prefs = ['cdl_pathway'] + pathway_prefs

            # Get all coaches assigned to this agent (multi-coach support)
            assigned_coaches = agent.get('all_coaches', coach.username)  # Fallback to current coach

            agent_row = {
                'Status': status,
                    'Name': agent.get('agent_name', 'Unknown'),
                    'Placement': agent.get('placement_status', ''),
                    'Employment': agent.get('employment_status', ''),
                    'Coaches': assigned_coaches,
                    'Clicks (All)': stats['total_clicks'],
                    'Clicks (14d)': stats['clicks_14d'],
                    'Apps (All)': stats['total_applications'],
                    'Apps (14d)': stats['applications_14d'],
                    'Score': int(stats['engagement_score']) if stats['engagement_score'] else 0,
                    'Activity': stats['activity_level'].title() if stats['activity_level'] else 'New',
                    'Last Applied': agent.get('last_application_at', '')[:10] if agent.get('last_application_at') else '',
                    'Market': agent.get('location', 'Houston'),
                    'Route': agent.get('route_filter', 'both'),
                    'Fair Chance': agent.get('fair_chance_only', False),
                    'Max Jobs': agent.get('max_jobs', 25),
                    # Convert stored "good and so-so and bad" back to "all jobs" for display
                    'Quality': 'all jobs' if agent.get('match_level') == 'good and so-so and bad' else agent.get('match_level', 'good and so-so'),
                    'Lookback': f"{agent.get('lookback_hours', 72)}h",
                    'Show Prepared For': agent.get('show_prepared_for', True),
                    # INDIVIDUAL PATHWAY CHECKBOXES (instead of ListColumn)
                    'CDL Jobs': 'cdl_pathway' in pathway_prefs,
                    'Dock→Driver': 'dock_to_driver' in pathway_prefs,
                    'CDL Training': 'internal_cdl_training' in pathway_prefs,
                    'Warehouse→Driver': 'warehouse_to_driver' in pathway_prefs,
                    'Logistics': 'logistics_progression' in pathway_prefs,
                    'Non-CDL': 'non_cdl_driving' in pathway_prefs,
                    'Warehouse': 'general_warehouse' in pathway_prefs,
                    'City': agent.get('agent_city', ''),
                    'State': agent.get('agent_state', ''),
                    'ZIP': agent.get('zip_code', ''),
                    'Radius (mi)': agent.get('zip_radius_miles', 50),
                    'Created': agent.get('created_at', '')[:10] if agent.get('created_at') else '',
                    'Portal Link': agent.get('portal_url', 'No link generated'),
                    'Admin Portal': agent.get('admin_portal_url', ''),
                    'Active': is_active,  # Editable checkbox for active status
                    # Hidden fields for updates
                    '_agent_uuid': agent.get('agent_uuid', ''),
                    '_created_at': agent.get('created_at', ''),
                    '_original_data': agent,  # Store original for comparison
                    '_is_active': is_active  # Store original active status
            }
            agent_data.append(agent_row)

        df = pd.DataFrame(agent_data)
        # Reorder columns with new placement/employment/coaches columns at the front
        desired_order = [
            'Name', 'Active', 'Placement', 'Employment',
            'Clicks (All)', 'Clicks (14d)', 'Apps (All)', 'Apps (14d)',
            'Score', 'Activity', 'Last Applied', 'Market', 'Route', 'Fair Chance', 'Max Jobs', 'Quality', 'Lookback', 'Show Prepared For',
            'CDL Jobs', 'Dock→Driver', 'CDL Training', 'Warehouse→Driver', 'Logistics', 'Non-CDL', 'Warehouse',
            'City', 'State', 'ZIP', 'Radius (mi)', 'Created', 'Portal Link', 'Admin Portal',
            '_agent_uuid', '_created_at', '_original_data', '_is_active'
        ]
        df = df[[c for c in desired_order if c in df.columns]]
        
        # Configure column editor types
        column_config = {
            'Name': st.column_config.TextColumn(
                "Name",
                help="Free Agent's full name",
                disabled=True,
                width="medium"
            ),
            'Active': st.column_config.CheckboxColumn(
                "Active",
                help="Uncheck to soft-delete agent (will hide from main view)",
                width="small"
            ),
            'Status': None,  # Hidden - not needed in main view
            'Placement': st.column_config.TextColumn(
                "Placement",
                help="Airtable placement status (synced)",
                disabled=True,
                width="medium"  # Increased from small to medium for full text visibility
            ),
            'Employment': st.column_config.TextColumn(
                "Employment",
                help="Airtable employment status (synced)",
                disabled=True,
                width="medium"  # Increased from small to medium for full text visibility
            ),
            'Coaches': None,  # Hidden - not needed in main view
            'City': st.column_config.TextColumn(
                "City",
                help="Agent's city - editable",
                width="small"
            ),
            'State': st.column_config.TextColumn(
                "State",
                help="Agent's state - editable",
                width="small"
            ),
            'ZIP': st.column_config.TextColumn(
                "ZIP",
                help="Agent's ZIP code for radius filtering - editable",
                width="small"
            ),
            'Radius (mi)': st.column_config.SelectboxColumn(
                "Radius (mi)",
                help="Job search radius in miles from ZIP code (default 50)",
                width="small",
                options=[10, 25, 50, 75, 100],
                required=True
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
                "Maximum Jobs",
                help="Maximum jobs in search results - includes All option",
                width="small", 
                options=[15, 25, 50, 100, 250],
                required=True
            ),
            'Quality': st.column_config.SelectboxColumn(
                "Quality",
                help="AI match quality filter for jobs",
                width="small",
                options=["good", "so-so", "good and so-so", "all jobs"],
                required=True
            ),
            'Lookback': st.column_config.SelectboxColumn(
                "Lookback",
                help="Memory search lookback period",
                width="small",
                options=["24h", "48h", "72h", "96h"],
                required=True
            ),
            'Show Prepared For': st.column_config.CheckboxColumn(
                "Show Prepared For",
                help="Include 'Prepared for [Agent] by Coach [Coach]' message in portal",
                width="small"
            ),
            # Hide all pathway columns - not needed in main view
            'CDL Jobs': None,
            'Dock→Driver': None,
            'CDL Training': None,
            'Warehouse→Driver': None,
            'Logistics': None,
            'Non-CDL': None,
            'Warehouse': None,
            'Clicks (All)': st.column_config.NumberColumn(
                "Clicks (All)",
                help="Total clicks since agent was created",
                disabled=True,
                width="small"
            ),
            'Clicks (14d)': st.column_config.NumberColumn(
                "Clicks (14d)",
                help="Clicks in last 14 days",
                disabled=True,
                width="small"
            ),
            'Apps (All)': st.column_config.NumberColumn(
                "Apps (All)",
                help="Total applications all-time",
                disabled=True,
                width="small"
            ),
            'Apps (14d)': st.column_config.NumberColumn(
                "Apps (14d)",
                help="Applications in last 14 days",
                disabled=True,
                width="small"
            ),
            'Score': st.column_config.NumberColumn(
                "Score",
                help="Engagement score",
                disabled=True,
                width="small"
            ),
            'Activity': st.column_config.TextColumn(
                "Activity",
                help="Activity level",
                disabled=True,
                width="small"
            ),
            'Last Applied': st.column_config.DateColumn(
                "Last Applied",
                help="Date of most recent job application",
                disabled=True,
                width="small"
            ),
            'Portal Link': st.column_config.TextColumn(
                "Portal Link",
                help="Job portal link for free agent (clickable)",
                disabled=True,
                width="medium"
            ),
            'Admin Portal': st.column_config.LinkColumn(
                "Admin Portal",
                help="Admin portal link - editable and clickable",
                width="medium"
            ),
            'Created': st.column_config.DateColumn(
                "Created",
                help="Date agent was added",
                disabled=True,
                width="small"
            ),
            # Hide internal columns
            '_agent_uuid': None,
            '_created_at': None,
            '_original_data': None,
            '_is_active': None
        }
        
        # Show the editable data table
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            hide_index=True,
            height=600,  # Enable scrolling for large tables
            width="stretch",  # Auto-expand to container width
            num_rows="fixed",  # Don't allow adding/removing rows
            key="agent_editor"
        )

        
        # Use session state to track when we need to save changes
        # Initialize session state for tracking edits
        if 'agent_table_last_saved' not in st.session_state:
            st.session_state.agent_table_last_saved = {}

        # Create a stable hash of the current dataframe state for comparison
        def get_editable_data_hash(df_row):
            """Get hash of just the editable fields for comparison"""
            editable_fields = [
                'Market', 'Route', 'Fair Chance', 'Max Jobs', 'Quality', 'Lookback', 'Show Prepared For', 'Active', 'City', 'State', 'ZIP', 'Radius (mi)', 'Admin Portal',
                'CDL Jobs', 'Dock→Driver', 'CDL Training', 'Warehouse→Driver', 'Logistics', 'Non-CDL', 'Warehouse'
            ]
            # Only include fields that actually exist in the DataFrame (safety check for column name changes)
            available_fields = [field for field in editable_fields if field in df_row.index]
            return hash(tuple(str(df_row[field]) for field in available_fields))

        # Initialize with current state on first load to avoid false positives
        # Use edited_df instead of df to match the comparison logic
        if len(edited_df) > 0:
            for idx in range(len(edited_df)):
                agent_uuid = edited_df.iloc[idx]['_agent_uuid']
                if agent_uuid not in st.session_state.agent_table_last_saved:
                    # Initialize with current state to prevent false detection on first load
                    st.session_state.agent_table_last_saved[agent_uuid] = get_editable_data_hash(edited_df.iloc[idx])

        # Check for changes and update database (but don't automatically rerun)
        current_state = {}
        changes_detected = False

        for idx in range(len(edited_df)):
            agent_uuid = edited_df.iloc[idx]['_agent_uuid']
            current_hash = get_editable_data_hash(edited_df.iloc[idx])
            current_state[agent_uuid] = current_hash

            # Check if this agent's data has changed since last save
            if agent_uuid not in st.session_state.agent_table_last_saved or \
               st.session_state.agent_table_last_saved[agent_uuid] != current_hash:
                changes_detected = True

            # Also explicitly check for Active field changes (checkbox may not trigger hash change properly)
            original_active = df.iloc[idx]['Active']
            edited_active = edited_df.iloc[idx]['Active']
            if original_active != edited_active:
                changes_detected = True

        # Save changes button (instead of auto-save on every edit)
        if changes_detected:
            st.warning("⚠️ You have unsaved changes")
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("💾 Save Changes", type="primary"):
                    # Find changed rows
                    changed_rows = []
                    for idx in range(len(edited_df)):
                        original = df.iloc[idx]
                        edited = edited_df.iloc[idx]
                        agent_uuid = edited['_agent_uuid']

                        # Check if this specific agent changed
                        current_hash = get_editable_data_hash(edited)
                        if agent_uuid not in st.session_state.agent_table_last_saved or \
                           st.session_state.agent_table_last_saved[agent_uuid] != current_hash:
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

                            # SIMPLIFIED PATHWAY LOGIC: Convert individual checkboxes to unified array
                            pathway_preferences = []
                            if edited['CDL Jobs']: pathway_preferences.append('cdl_pathway')
                            if edited['Dock→Driver']: pathway_preferences.append('dock_to_driver')
                            if edited['CDL Training']: pathway_preferences.append('internal_cdl_training')
                            if edited['Warehouse→Driver']: pathway_preferences.append('warehouse_to_driver')
                            if edited['Logistics']: pathway_preferences.append('logistics_progression')
                            if edited['Non-CDL']: pathway_preferences.append('non_cdl_driving')
                            if edited['Warehouse']: pathway_preferences.append('general_warehouse')

                            # Just save the pathway preferences - portal will filter based on pathways
                            updated_agent['pathway_preferences'] = pathway_preferences

                            # Convert lookback period from string format ("72h") to integer
                            lookback_str = str(edited['Lookback'])
                            lookback_hours = int(lookback_str.replace('h', '').strip()) if lookback_str.endswith('h') else 72

                            # Convert "all jobs" UI option to the actual match levels
                            quality_value = str(edited['Quality'])
                            if quality_value == 'all jobs':
                                quality_value = 'good and so-so and bad'

                            updated_agent.update({
                                'location': str(edited['Market']),  # Save as 'location' for legacy compatibility
                                'route_filter': str(edited['Route']),
                                'fair_chance_only': bool(edited['Fair Chance']),
                                'max_jobs': convert_max_jobs(edited['Max Jobs']),
                                'match_level': quality_value,
                                'lookback_hours': lookback_hours,  # Save as integer for database
                                'show_prepared_for': bool(edited['Show Prepared For']),
                                'is_active': bool(edited['Active']),  # Handle active/inactive status
                                'coach_username': coach.username,  # Add coach username for portal link generation
                                'agent_city': str(edited.get('City', '')),
                                'agent_state': str(edited.get('State', '')),
                                'zip_code': str(edited.get('ZIP', '')),
                                'zip_radius_miles': int(edited.get('Radius (mi)', 50)),
                                'admin_portal_url': str(edited.get('Admin Portal', ''))
                            })

                            # DEBUG: Print what we're about to save
                            print(f"🔍 TABLE SAVE DEBUG: About to save agent {edited['Name']}")
                            print(f"🔍 TABLE SAVE DEBUG: updated_agent data = {updated_agent}")

                            # Save to database
                            success, message = save_agent_profile(coach.username, updated_agent)
                            if success:
                                success_count += 1
                                # Update the saved state hash
                                st.session_state.agent_table_last_saved[agent_uuid] = get_editable_data_hash(edited)

                                # AUTOMATICALLY GENERATE/UPDATE PORTAL LINKS ON SAVE
                                try:
                                    from free_agent_system import generate_agent_url
                                    from link_tracker import LinkTracker

                                    print(f"🔗 AUTO-GENERATING portal link for {edited['Name']}")

                                    # Generate new encoded Supabase portal URL with current settings
                                    new_encoded_url = generate_agent_url(updated_agent['agent_uuid'], updated_agent)
                                    print(f"🔗 Generated encoded portal URL: {new_encoded_url}")

                                    # Get existing Short.io link
                                    existing_custom_url = original_agent.get('custom_url', '') if isinstance(original_agent, dict) else ''

                                    # Use working create_short_link method (same as jobs)
                                    tracker = LinkTracker()

                                    # Generate tags like we do for jobs
                                    tags = [
                                        f"agent:{updated_agent['agent_uuid']}",
                                        f"coach:{updated_agent.get('coach_username', '')}",
                                        f"market:{updated_agent.get('location', 'Unknown')}",
                                        "source:auto_save",
                                        "type:agent_portal"
                                    ]

                                    # Use create_short_link (SAME as jobs) for reliable portal link generation
                                    working_short_url = tracker.create_short_link(
                                        original_url=new_encoded_url,  # Pass the final portal URL directly
                                        title=f"Portal - {edited['Name']}",
                                        tags=tags,
                                        candidate_id=updated_agent['agent_uuid']
                                    )

                                    portal_link_updated = False
                                    if working_short_url and working_short_url != new_encoded_url:
                                        print(f"✅ SUCCESS! Working portal link created: {working_short_url}")
                                        updated_agent['custom_url'] = working_short_url
                                        updated_agent['original_long_url'] = new_encoded_url
                                        portal_link_updated = True
                                    else:
                                        print(f"⚠️ create_short_link failed or returned same URL: {working_short_url}")

                                    if not portal_link_updated:
                                        # Fallback: Still store the encoded URL even if Short.io fails
                                        print(f"⚠️ Portal link generation failed, storing encoded URL only")
                                        updated_agent['original_long_url'] = new_encoded_url

                                    # Save the updated portal URL info back to database
                                    if portal_link_updated:
                                        save_success, save_msg = save_agent_profile(coach.username, updated_agent)
                                        if save_success:
                                            print(f"✅ Portal link saved to database for {edited['Name']}")
                                        else:
                                            print(f"⚠️ Failed to save portal link to database: {save_msg}")

                                except Exception as e:
                                    print(f"❌ Portal link generation failed for {edited['Name']}: {e}")
                                    # Don't fail the whole save process if portal link generation fails
                                # Show detailed success message for debugging
                                st.info(f"✅ Saved changes for {edited['Name']}: Market={edited['Market']}, Route={edited['Route']}, Fair Chance={edited['Fair Chance']}, Max Jobs={edited['Max Jobs']}, Quality={edited['Quality']}, Pathways={pathway_preferences}, City={edited['City']}, State={edited['State']}, Admin Portal={edited['Admin Portal']}")
                                print(f"✅ TABLE SAVE SUCCESS: Agent {edited['Name']} saved with Market={edited['Market']}")
                            else:
                                error_count += 1
                                st.error(f"❌ Failed to update {edited['Name']}: {message}")
                                print(f"❌ TABLE SAVE FAILED: Agent {edited['Name']}: {message}")
                                # Show original values for comparison in case of failure
                                st.error(f"🔍 Original values - Market: {original_agent.get('location')}, Route: {original_agent.get('route_filter')}, Fair Chance: {original_agent.get('fair_chance_only')}, Max Jobs: {original_agent.get('max_jobs')}, Quality: {original_agent.get('match_level')}")

                        if success_count > 0:
                            st.success(f"✅ Successfully updated {success_count} agent(s)")

                            # Verify changes were actually saved by re-reading from database
                            with st.expander("🔍 Verify Database Changes", expanded=False):
                                try:
                                    verification_agents = load_agent_profiles(coach.username)
                                    for idx, original, edited in changed_rows:
                                        agent_uuid = original['_agent_uuid']
                                        agent_name = edited['Name']

                                        # Find the agent in the verification data
                                        saved_agent = None
                                        for agent in verification_agents:
                                            if agent.get('agent_uuid') == agent_uuid:
                                                saved_agent = agent
                                                break

                                        if saved_agent:
                                            saved_config = saved_agent.get('search_config', {})
                                            st.write(f"**{agent_name}**:")
                                            st.write(f"  - Market: {saved_config.get('location', 'N/A')} (expected: {edited['Market']})")
                                            st.write(f"  - Route: {saved_config.get('route_filter', 'N/A')} (expected: {edited['Route']})")
                                            st.write(f"  - Fair Chance: {saved_config.get('fair_chance_only', 'N/A')} (expected: {edited['Fair Chance']})")
                                            st.write(f"  - Max Jobs: {saved_config.get('max_jobs', 'N/A')} (expected: {edited['Max Jobs']})")
                                            st.write(f"  - Quality: {saved_config.get('match_level', 'N/A')} (expected: {edited['Quality']})")
                                        else:
                                            st.error(f"⚠️ Could not find {agent_name} in database verification")
                                except Exception as e:
                                    st.error(f"❌ Verification failed: {e}")

                            st.info("✅ Portal links will be automatically updated when you save changes")

                        if error_count > 0:
                            st.error(f"❌ Failed to update {error_count} agent(s)")

                        # ALWAYS clear cache and rerun after ANY saves (success or failure)
                        # This ensures the table reflects the current database state
                        if success_count > 0:
                            agents_cache_key = f'agents_{coach.username}_{show_deleted}'
                            analytics_cache_key = f'analytics_{coach.username}'
                            if agents_cache_key in st.session_state:
                                del st.session_state[agents_cache_key]
                            if analytics_cache_key in st.session_state:
                                del st.session_state[analytics_cache_key]
                            # Clear hash tracking to reset change detection
                            st.session_state.agent_table_last_saved = {}
                            st.rerun()
            with col2:
                if st.button("↩️ Discard Changes"):
                    # Reset by clearing session state and rerunning
                    st.session_state.agent_table_last_saved = {}
                    st.rerun()
        
        # Bulk actions
        st.markdown("### 🔧 Bulk Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("")  # Placeholder for now
        
        with col2:
            if st.button("📧 Export Email List", help="Export all agent emails as CSV"):
                # Create CSV of email addresses
                email_list = [agent.get('agent_email', '') for agent in agents if agent.get('agent_email')]
                email_df = pd.DataFrame({'Email': email_list})
                csv = email_df.to_csv(index=False)
                render_download_button(
                    data=csv,
                    label="📥 Download Email CSV",
                    filename=f"free_agent_emails_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime_type="text/csv"
                )
        
        with col3:
            if st.button("🗑️ Delete Selected", help="Delete multiple agents (not implemented yet)"):
                st.info("Bulk delete functionality would be implemented here")
        
        # Show system-wide summary stats first
        st.markdown("### 🌍 System-Wide Summary (All Free Agents)")

        # Add refresh button for system-wide stats
        col_refresh, col_spacer = st.columns([1, 6])
        with col_refresh:
            if st.button("🔄 Refresh System Stats", help="Refresh system-wide statistics"):
                # Clear cache and reload
                if 'system_wide_stats' in st.session_state:
                    del st.session_state['system_wide_stats']
                st.rerun()

        # Cache system-wide stats to avoid repeated API calls
        system_stats_cache_key = 'system_wide_stats'
        if system_stats_cache_key not in st.session_state:
            from supabase_utils import get_system_wide_agent_stats
            st.session_state[system_stats_cache_key] = get_system_wide_agent_stats()

        system_stats = st.session_state[system_stats_cache_key]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Agents (All Coaches)", system_stats['total_agents'])
        with col2:
            st.metric("Total Clicks (All-Time)", system_stats['total_clicks_all_time'])
        with col3:
            st.metric("Active Agents (14d)", system_stats['active_agents_14d'])
        with col4:
            avg_clicks_system = system_stats['avg_clicks_per_agent']
            st.metric("Avg Clicks/Agent (All-Time)", f"{avg_clicks_system:.1f}")

        # Show coach-specific summary stats
        st.markdown(f"### 📊 Your Summary ({coach.username})")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Your Agents", len(agents))
        with col2:
            # Use analytics data for accurate all-time clicks
            total_clicks_all_time = sum(analytics_lookup.get(a.get('agent_uuid', ''), {}).get('total_clicks', 0) for a in agents)
            st.metric("Your Clicks (All-Time)", total_clicks_all_time)
        with col3:
            # Use analytics data for 14-day active agents
            active_agents_14d = len([uuid for uuid, stats in analytics_lookup.items() if stats.get('clicks_14d', 0) > 0])
            st.metric("Your Active Agents (14d)", active_agents_14d)
        with col4:
            avg_clicks = total_clicks_all_time / len(agents) if agents else 0
            st.metric("Your Avg Clicks/Agent", f"{avg_clicks:.1f}")
                
    
    else:
        st.info("👆 Add your first Free Agent using the search above")

        st.subheader("Weekly Performance Report (Example)")
        if st.button("Generate Weekly Report for Me", key="generate_my_weekly_report"):
            weekly_report = generate_weekly_performance_report(coach.username)
            st.json(weekly_report)


def show_track_applications_tab(coach, coach_manager):
    """Show the Track Applications tab for viewing agent job click history and success tracking"""
    st.markdown("*Track which jobs your Free Agents have applied to and measure platform success*")
    st.info("📊 **Success Metric**: When an agent gets hired by a company from their application list, that's our platform success signal!")

    # Agent selection section
    st.markdown("### 🔍 Select Free Agent")

    # Load all agents for this coach
    from free_agent_system import load_agent_profiles_with_stats

    with st.spinner("Loading Free Agents..."):
        agents = load_agent_profiles_with_stats(coach.username, lookback_days=90)  # 90 days for comprehensive tracking

    if not agents:
        st.warning("No Free Agents found for your account. Add agents in the 'Manage Agents' tab first.")
        return

    # Create agent selection dropdown
    agent_options = {f"{agent['agent_name']} ({agent['agent_uuid'][:8]})": agent for agent in agents}

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_agent_display = st.selectbox(
            "Select Agent to Track",
            options=list(agent_options.keys()),
            key="track_applications_agent_select"
        )

    with col2:
        st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
        refresh_button = st.button("🔄 Refresh Data", key="refresh_agent_data")

    if not selected_agent_display:
        return

    selected_agent = agent_options[selected_agent_display]
    agent_uuid = selected_agent['agent_uuid']
    agent_name = selected_agent['agent_name']

    st.markdown("---")

    # Agent Summary Section
    st.markdown(f"### 📊 {agent_name}'s Activity Summary")

    # Get click stats - use exact same field names as manage agents table
    total_clicks = selected_agent.get('total_clicks', 0)
    recent_clicks = selected_agent.get('recent_clicks', 0)
    total_applications = selected_agent.get('total_applications', 0)
    portal_clicks = selected_agent.get('portal_clicks', 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Job Clicks", total_clicks)
    with col2:
        st.metric("Last 14 Days", recent_clicks)
    with col3:
        st.metric("Applications", total_applications)
    with col4:
        st.metric("Portal Visits", portal_clicks)

    # Portal Link Management Section
    with st.expander("🔗 Portal Link & Search Parameters", expanded=False):
        st.markdown("### Edit Agent's Job Search Settings")

        from free_agent_system import save_agent_profile, get_market_options
        # Note: generate_dynamic_portal_link is defined in app.py, already available

        # Get current settings
        current_location = selected_agent.get('location', 'Houston')
        current_route = selected_agent.get('route_filter', 'both')
        current_fair_chance = selected_agent.get('fair_chance_only', False)
        current_max_jobs = selected_agent.get('max_jobs', 25)
        current_experience = selected_agent.get('experience_level', 'both')

        col1, col2 = st.columns(2)
        with col1:
            markets = get_market_options()
            new_location = st.selectbox("Market/Location", markets, index=markets.index(current_location) if current_location in markets else 0, key="edit_location")
            new_route = st.selectbox("Route Type", ["both", "local", "regional"], index=["both", "local", "regional"].index(current_route), key="edit_route")
            new_fair_chance = st.checkbox("Fair Chance Only", value=current_fair_chance, key="edit_fair_chance")

        with col2:
            max_jobs_options = [15, 25, 50, 100, 250]
            current_max_jobs_index = max_jobs_options.index(current_max_jobs) if current_max_jobs in max_jobs_options else 1  # Default to 25
            new_max_jobs = st.selectbox("Maximum Jobs", max_jobs_options, index=current_max_jobs_index, key="edit_max_jobs")
            new_experience = st.selectbox("Experience Level", ["both", "no_experience", "experienced"], index=["both", "no_experience", "experienced"].index(current_experience), key="edit_experience")

        # Show current portal link
        current_portal_url = selected_agent.get('portal_url', 'Not generated')
        st.markdown("**Current Portal Link:**")
        st.code(current_portal_url, language=None)

        # Save changes button
        if st.button("💾 Save Changes & Regenerate Portal Link", key="save_agent_settings", type="primary"):
            with st.spinner("Saving changes and regenerating portal link..."):
                # Update agent data
                updated_agent = selected_agent.copy()
                updated_agent.update({
                    'location': new_location,
                    'route_filter': new_route,
                    'fair_chance_only': new_fair_chance,
                    'max_jobs': new_max_jobs,
                    'experience_level': new_experience
                })

                # Regenerate portal link
                full_portal_url = generate_dynamic_portal_link(updated_agent)

                # Create Short.io link
                try:
                    from link_tracker import LinkTracker
                    link_tracker = LinkTracker()

                    portal_tags = [
                        f"coach:{coach.username}",
                        f"candidate:{agent_uuid}",
                        f"market:{new_location.lower().replace(' ', '_')}",
                        "type:portal_access"
                    ]

                    edge_function_url = link_tracker.generate_edge_function_url(
                        target_url=full_portal_url,
                        candidate_id=agent_uuid,
                        tags=portal_tags
                    )

                    shortened_url = link_tracker.create_short_link(edge_function_url, title=f"Portal - {agent_name}", tags=portal_tags, candidate_id=agent_uuid)
                    updated_agent['portal_url'] = shortened_url

                except Exception as e:
                    st.warning(f"⚠️ Could not generate short link: {e}")
                    updated_agent['portal_url'] = full_portal_url

                # Save to database
                from free_agent_system import save_agent_profile
                success, message = save_agent_profile(coach.username, updated_agent)

                if success:
                    st.success("✅ Settings saved and portal link regenerated!")
                    st.info(f"🔗 New Portal Link: {updated_agent['portal_url']}")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to save: {message}")

    # Application History Section
    st.markdown("### 📋 Application History")
    st.markdown("Jobs this agent has marked as **'I applied to this job'**")

    # Date range selector for application history
    col1, col2 = st.columns([3, 1])
    with col1:
        days_back = st.selectbox("Time Period", [7, 14, 30, 60, 90, 180, 365], index=3, key="apps_days_back")
    with col2:
        st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
        export_csv = st.button("📥 Export CSV", key="export_apps_csv")

    # Fetch job feedback (applications) for this agent
    from supabase_utils import get_client
    from datetime import datetime, timedelta, timezone
    import pandas as pd

    try:
        client = get_client()
        if client is None:
            st.error("❌ Cannot connect to Supabase database")
            return

        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        # Query job_feedback table for applications (feedback_type = 'i_applied_to_this_job')
        response = client.table("job_feedback").select(
            "id, created_at, job_title, company, application_status"
        ).eq(
            "candidate_id", agent_uuid
        ).eq(
            "feedback_type", "i_applied_to_this_job"
        ).gte(
            "created_at", start_date.isoformat()
        ).lte(
            "created_at", end_date.isoformat()
        ).order("created_at", desc=True).execute()

        applications = response.data

        if not applications:
            st.info(f"No job applications found for {agent_name} in the last {days_back} days.")
            st.markdown("💡 Applications are tracked when the agent clicks **'I applied to this job'** in their portal.")
        else:
            # Convert to DataFrame
            df = pd.DataFrame(applications)

            # Format created_at for display
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d')

            # Default status to 'applied' if None
            df['application_status'] = df['application_status'].fillna('applied')

            # Show metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Applications", len(df))
            with col2:
                unique_companies = df['company'].nunique()
                st.metric("Unique Companies", unique_companies)
            with col3:
                hired_count = len(df[df['application_status'] == 'hired'])
                st.metric("Hired", hired_count)
            with col4:
                # Calculate recent applications (last 14 days)
                recent_apps = len(df[pd.to_datetime(df['created_at']) >= (datetime.now() - timedelta(days=14))])
                st.metric("Last 14 Days", recent_apps)

            # Create editable dataframe with status dropdown
            st.markdown("**💼 Application Status Tracking**")
            st.markdown("*Update application status by selecting from the dropdown in each row*")

            # Prepare data for editable table
            df_editable = df[['id', 'created_at', 'application_status', 'company', 'job_title']].copy()
            df_editable = df_editable.rename(columns={
                'id': 'ID',
                'created_at': 'Applied Date',
                'application_status': 'Status',
                'company': 'Company',
                'job_title': 'Job Title'
            })

            # Configure editable dataframe
            edited_df = st.data_editor(
                df_editable,
                column_config={
                    'ID': st.column_config.NumberColumn('ID', disabled=True, width="small"),
                    'Applied Date': st.column_config.TextColumn('Applied Date', disabled=True, width="medium"),
                    'Status': st.column_config.SelectboxColumn(
                        'Status',
                        options=['applied', 'haven\'t heard back', 'rejected', 'hired'],
                        required=True,
                        width="medium"
                    ),
                    'Company': st.column_config.TextColumn('Company', disabled=True, width="medium"),
                    'Job Title': st.column_config.TextColumn('Job Title', disabled=True, width="large")
                },
                width="stretch",
                height=400,
                hide_index=True,
                key="applications_editor"
            )

            # Save changes button
            if st.button("💾 Save Status Changes", key="save_app_status", type="primary"):
                with st.spinner("Saving status updates..."):
                    try:
                        # Find changed rows
                        changes_made = 0
                        for idx, row in edited_df.iterrows():
                            original_status = df_editable.iloc[idx]['Status']
                            new_status = row['Status']

                            if original_status != new_status:
                                # Update in Supabase
                                app_id = int(row['ID'])
                                client.table("job_feedback").update({
                                    'application_status': new_status
                                }).eq('id', app_id).execute()
                                changes_made += 1

                        if changes_made > 0:
                            st.success(f"✅ Updated {changes_made} application status(es)!")
                            st.rerun()
                        else:
                            st.info("No changes detected")

                    except Exception as e:
                        st.error(f"❌ Error saving status: {e}")

            # Export CSV functionality
            if export_csv:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Application History CSV",
                    data=csv,
                    file_name=f"{agent_name}_applications_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="download_apps_csv"
                )

            # Success Tracking Section
            st.markdown("---")
            st.markdown("### 🎯 Success Tracking")
            st.markdown("**Has this agent been hired?** If yes, select the company below to mark this as a platform success!")

            # Get unique companies from application history
            companies_applied = sorted(df['company'].unique().tolist())

            col1, col2 = st.columns([3, 1])
            with col1:
                hired_company = st.selectbox(
                    "Company that hired this agent",
                    options=["Not hired yet"] + companies_applied,
                    key="hired_company_select"
                )

            with col2:
                st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
                mark_success_button = st.button("✅ Mark as Success", key="mark_success_btn", type="primary", disabled=(hired_company == "Not hired yet"))

            if mark_success_button and hired_company != "Not hired yet":
                # Save success to database
                try:
                    success_data = {
                        'agent_uuid': agent_uuid,
                        'agent_name': agent_name,
                        'hired_company': hired_company,
                        'coach_username': coach.username,
                        'hired_date': datetime.now(timezone.utc).isoformat(),
                        'application_count': len(df),
                        'unique_companies_applied': unique_companies
                    }

                    # Insert into agent_success_tracking table
                    response = client.table("agent_success_tracking").insert(success_data).execute()

                    if response.data:
                        st.success(f"🎉 Success! {agent_name} hired by {hired_company}!")
                        st.balloons()

                        # Also update agent profile with success flag
                        client.table("agent_profiles").update({
                            'hired': True,
                            'hired_company': hired_company,
                            'hired_date': datetime.now(timezone.utc).isoformat()
                        }).eq('agent_uuid', agent_uuid).execute()

                    else:
                        st.error("❌ Failed to save success tracking data")

                except Exception as e:
                    st.error(f"❌ Error saving success data: {e}")
                    st.info("💡 The agent_success_tracking table may need to be created in Supabase")

            # Show if agent has been marked as successfully hired
            if selected_agent.get('hired'):
                st.success(f"✅ **Success Story**: {agent_name} was hired by {selected_agent.get('hired_company', 'Unknown')} on {selected_agent.get('hired_date', 'Unknown date')}")

    except Exception as e:
        st.error(f"❌ Error loading application history: {e}")
        st.exception(e)


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

@st.cache_data(ttl=300, max_entries=5)  # 5 min cache, max 5 entries  
def _render_jobs_html_cached(df_json: str, agent_params_json: str) -> str:
    """Cached HTML render with limited cache size."""
    import json
    from pdf.html_pdf_generator import jobs_dataframe_to_dicts, render_jobs_html
    from free_agent_system import update_job_tracking_for_agent
    
    df = pd.DataFrame(json.loads(df_json))
    agent_params = json.loads(agent_params_json)
    
    # IMPORTANT: Use the same processing as PDF to include tracked URLs
    processed_df = update_job_tracking_for_agent(df, agent_params)
    jobs = jobs_dataframe_to_dicts(processed_df, candidate_id=agent_params.get('agent_uuid'), agent_name=agent_params.get('agent_name'))
    
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
            # Use FreeWorld logo or fallback to production emoji
            try:
                production_favicon = Image.open("fw_logo.png") if page_icon_img is None else page_icon_img
            except (FileNotFoundError, OSError):
                production_favicon = "🚀"  # Production rocket emoji

            st.set_page_config(
                page_title="FreeWorld Success Coach Portal",
                page_icon=production_favicon,
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

            # DEBUG: Log first 500 chars to check for issues
            print(f"🔍 HTML FRAGMENT DEBUG (first 500 chars): {repr(report_fragment[:500])}")
            print(f"🔍 HTML FRAGMENT has <script>: {'<script>' in report_fragment}")

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

def show_pre_adverse_helper():
    """Show the pre-adverse response helper portal"""
    try:
        from pre_adverse_response_helper import main as run_helper

        # Apply minimal Streamlit CSS overrides for clean mobile experience
        st.markdown("""
        <style>
        /* Hide Streamlit chrome for cleaner public-facing page */
        #MainMenu, header, footer { display: none !important; }
        [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
        .viewerBadge_link__wrapper, .viewerBadge_container__2QSsR { display: none !important; }
        a[href^="https://streamlit.io"] { display: none !important; }
        </style>
        """, unsafe_allow_html=True)

        # Run the helper main function
        run_helper()

    except ImportError as e:
        st.error("❌ Pre-Adverse Response Helper not found")
        st.markdown("The helper feature is not available in this deployment.")
        st.code(str(e))
    except Exception as e:
        st.error(f"❌ Error loading helper: {str(e)}")
        st.code(str(e))
        import traceback
        st.code(traceback.format_exc())

def show_agent_portal_v2():
    """Show the agent portal v2 with interactive filters"""
    try:
        # Import and run the main function
        from agent_portal_v2 import main as run_portal_v2
        run_portal_v2()

    except ImportError as e:
        st.error("❌ Agent Portal V2 not found")
        st.markdown("The portal feature is not available in this deployment.")
        st.code(str(e))
    except Exception as e:
        st.error(f"❌ Error loading portal: {str(e)}")
        st.code(str(e))
        import traceback
        st.code(traceback.format_exc())

def show_loan_calculator():
    """Show the loan calculator portal"""
    try:
        from loan_calculator import generate_calculator_html

        # Apply Streamlit CSS overrides (same as agent portal)
        st.markdown("""
        <style>
        /* Remove Streamlit height constraints */
        html, body, [data-testid="stAppViewContainer"], section.main,
        [data-testid="block-container"] {
          height: auto !important;
          min-height: 100vh !important;
          overflow: visible !important;
        }
        /* Make sure content flows naturally */
        [data-testid="stVerticalBlock"] { overflow: visible !important; }
        /* Remove default Streamlit padding */
        [data-testid="stAppViewContainer"] { padding: 0 !important; }
        .block-container { padding-top: 0 !important; margin-top: 0 !important; }
        /* Hide Streamlit chrome */
        #MainMenu, header, footer { display: none !important; }
        [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
        .viewerBadge_link__wrapper, .viewerBadge_container__2QSsR { display: none !important; }
        a[href^="https://streamlit.io"] { display: none !important; }
        </style>
        """, unsafe_allow_html=True)

        # Use st.components.v1.html() with calculated height (same pattern as agent portal)
        calculator_html = generate_calculator_html()
        st.components.v1.html(calculator_html, height=1400, scrolling=True)

    except ImportError as e:
        st.error("❌ Loan calculator module not found")
        st.markdown("The loan calculator feature is not available in this deployment.")
        st.code(str(e))
    except Exception as e:
        st.error(f"❌ Error loading loan calculator: {str(e)}")
        st.code(str(e))

def main():
    """Main Streamlit application"""

    # Check for public-facing agent portal link FIRST
    try:
        params = st.query_params
        agent_config = params.get("agent_config") or params.get("config")
        agent_uuid_param = params.get("agent")
        agent_id_param = params.get("agent_id")  # NEW: agent_portal_v2 parameter
        debug_frame_param = params.get("debug_frame")
        loan_calculator_param = params.get("loan_calculator") or params.get("loan")
        pre_adverse_param = params.get("pre_adverse") or params.get("helper")
    except Exception: # Fallback if query params fail
        agent_config = None
        agent_uuid_param = None
        agent_id_param = None
        debug_frame_param = None
        loan_calculator_param = None
        pre_adverse_param = None

    # Route to agent portal v2 if agent_id parameter detected
    if agent_id_param:
        show_agent_portal_v2()
        st.stop()

    # Route to pre-adverse response helper if parameter detected
    if pre_adverse_param:
        show_pre_adverse_helper()
        st.stop()

    # Route to loan calculator if parameter detected
    if loan_calculator_param:
        show_loan_calculator()
        st.stop()


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
    
    # Initialize pipeline wrapper
    @st.cache_resource
    def get_pipeline():
        if _PIPELINE_WRAPPER_CLASS is None:
            st.error("❌ Pipeline wrapper class not available")
            st.stop()
        return _PIPELINE_WRAPPER_CLASS()

    pipeline = get_pipeline()
    
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
        "👥 Free Agents",
        "📊 Coach Analytics",
        "📈 Market Analytics",
        "🏢 Companies"
    ]
    
    # Add Batches & Scheduling tab only if coach has permission
    if check_coach_permission('can_access_batches'):
        tab_options.insert(1, "🗓️ Batches & Scheduling")

    # Add Inside Track Jobs tab only if coach has permission
    if check_coach_permission('can_manage_inside_track'):
        # Insert after Batches if present, otherwise after Job Search
        insert_pos = 2 if check_coach_permission('can_access_batches') else 1
        tab_options.insert(insert_pos, "🎯 Inside Track Jobs")

    # Add Admin Panel only for admins
    if coach.role == 'admin':
        tab_options.append("👑 Admin Panel")
    else:
        tab_options.append("🔒 Restricted")
    
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
        # Job Search tab - main interface controls
        st.header("🔍 Job Search")

        # Import helper functions for UI components
        from display_utils import render_free_agent_lookup, render_pdf_config

        # Initialize all variables with defaults to prevent NameError in results section
        location_tab = None
        location_type_tab = "Select Market"
        custom_location_tab = ""
        selected_market_tab = None
        selected_markets_tab = []
        search_mode_tab = 'sample'
        search_terms_tab = "CDL Driver No Experience"
        commute_time_tab = 35
        classifier_type_value_tab = 'cdl'
        no_experience_tab = True
        memory_time_period_tab = '72h'
        force_fresh_classification_tab = False
        push_to_airtable_tab = False

        # PDF config defaults
        max_jobs_pdf_tab = 50
        pdf_route_type_filter_tab = ['Local', 'OTR', 'Unknown']
        pdf_match_quality_filter_tab = ['good', 'so-so']
        pathway_preferences_tab = []
        pdf_fair_chance_only_tab = False
        show_html_preview_tab = False
        generate_portal_link_tab = False
        show_prepared_for_tab = True
        enable_pdf_generation_tab = True

        # Candidate defaults
        candidate_id_tab = ""
        candidate_name_tab = ""

        # Button state
        memory_clicked_tab = False
        indeed_fresh_clicked_tab = False

        # Get available markets
        markets = pipeline.get_markets()

        # Create sub-tabs for Memory vs Fresh Indeed
        memory_tab, fresh_tab = st.tabs(["💾 Memory Search", "🔍 Fresh Indeed Search"])

        # ==================== MEMORY SEARCH TAB ====================
        with memory_tab:
            st.markdown("Search cached jobs from Supabase memory - instant results, no API costs. Use this tab for PDF and portal generation.")

            # Location Selection (market or custom)
            st.markdown("##### 📍 Location Selection")
            col1, col2 = st.columns([1, 3])

            with col1:
                mem_location_options = ["Select Market"]
                if check_coach_permission('can_use_custom_locations'):
                    mem_location_options.append("Custom Location")

                mem_location_type = st.radio(
                    "Location Type:",
                    mem_location_options,
                    help="Choose a preset market or enter a custom location",
                    key="mem_location_type"
                )

            with col2:
                if mem_location_type == "Select Market":
                    mem_selected_market = st.selectbox(
                        "Target Market:",
                        [""] + markets,
                        help="Memory search supports single market only",
                        key="mem_selected_market"
                    )
                    if mem_selected_market:
                        st.success(f"📍 Selected Market: {mem_selected_market}")
                    else:
                        st.warning("👆 Please select a market")
                else:
                    mem_custom_location = st.text_input(
                        "Enter ZIP code, city, or state:",
                        placeholder="e.g., 90210, Austin TX, California",
                        help="Enter any US location",
                        key="mem_custom_location"
                    )
                    if mem_custom_location:
                        st.success(f"📍 Custom Location: {mem_custom_location}")
                    else:
                        st.warning("👆 Please enter a location")

            # Lookback Period and ZIP Radius in one row
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.markdown("##### ⏰ Lookback Period")
                mem_time_period = st.selectbox(
                    "Search jobs from:",
                    options=['24h', '48h', '72h', '96h'],
                    index=2,  # default to 72h
                    help="How far back to search in the memory cache",
                    key="mem_time_period"
                )
            with col2:
                st.markdown("##### 📍 ZIP Code (Optional)")
                mem_zip_code = st.text_input(
                    "Filter by ZIP:",
                    placeholder="e.g., 77001",
                    help="Optional: Filter jobs within radius of this ZIP code",
                    key="mem_zip_code"
                )
            with col3:
                st.markdown("##### 📏 Radius (mi)")
                mem_zip_radius = st.selectbox(
                    "Search radius:",
                    options=[10, 25, 50, 75, 100],
                    index=1,  # default to 25 miles
                    help="Miles from ZIP code to include jobs",
                    key="mem_zip_radius"
                )

            # Free Agent Lookup
            mem_candidate_id, mem_candidate_name = render_free_agent_lookup("mem_")

            # PDF/Portal Configuration (inline, simplified - no pathway preferences)
            st.markdown("### 📄 PDF & Portal Configuration")

            if check_coach_permission('can_generate_pdf'):
                # Max jobs for PDF
                mem_max_jobs_pdf = st.selectbox(
                    "📊 Maximum jobs in PDF:",
                    options=[10, 25, 50, 100, 250],
                    index=4,  # default to 250
                    help="Maximum jobs to include in PDF/portal",
                    key="mem_max_jobs_pdf"
                )

                # Route Types and Job Quality
                col1, col2 = st.columns(2)
                with col1:
                    mem_pdf_route_filter = st.multiselect(
                        "🛣️ Route types:",
                        options=['Local', 'OTR', 'Unknown'],
                        default=['Local', 'OTR', 'Unknown'],
                        help="Which route types to include",
                        key="mem_pdf_route_filter"
                    )
                with col2:
                    mem_pdf_quality_filter = st.multiselect(
                        "⭐ Job quality levels:",
                        options=['good', 'so-so', 'bad'],
                        default=['good', 'so-so'],
                        help="Which quality levels to include",
                        key="mem_pdf_quality_filter"
                    )

                # Checkboxes row
                col1, col2, col3 = st.columns(3)
                with col1:
                    mem_fair_chance_only = st.checkbox(
                        "🤝 Fair chance only",
                        value=False,
                        help="Only jobs friendly to people with records",
                        key="mem_fair_chance_only"
                    )
                with col2:
                    mem_show_html_preview = st.checkbox(
                        "👁️ HTML preview",
                        value=False,
                        help="Preview PDF layout in HTML format",
                        key="mem_show_html_preview"
                    )
                with col3:
                    mem_generate_portal = st.checkbox(
                        "🔗 Generate portal link",
                        value=False,
                        help="Create a shareable job portal",
                        key="mem_generate_portal"
                    )

                col1, col2, col3 = st.columns(3)
                with col1:
                    mem_show_prepared_for = st.checkbox(
                        "👤 Show 'prepared for'",
                        value=True,
                        help="Include personalized message",
                        key="mem_show_prepared_for"
                    )
                with col2:
                    mem_enable_pdf = st.checkbox(
                        "📄 Enable PDF",
                        value=True,
                        help="Generate downloadable PDF",
                        key="mem_enable_pdf"
                    )
            else:
                st.info("📄 PDF generation not available - contact admin for access")
                mem_max_jobs_pdf = 50
                mem_pdf_route_filter = ['Local', 'OTR', 'Unknown']
                mem_pdf_quality_filter = ['good', 'so-so']
                mem_fair_chance_only = False
                mem_show_html_preview = False
                mem_generate_portal = False
                mem_show_prepared_for = True
                mem_enable_pdf = False

            # Search Button
            st.markdown("---")
            memory_clicked_tab = st.button(
                "💾 Search Memory",
                help="Search cached jobs - instant results, no API costs",
                key="mem_search_btn",
                use_container_width=True
            )

            # Set variables when Memory search is triggered
            if memory_clicked_tab:
                if mem_location_type == "Select Market":
                    location_tab = mem_selected_market
                    location_type_tab = "Select Market"
                    selected_market_tab = mem_selected_market
                    selected_markets_tab = [mem_selected_market] if mem_selected_market else []
                else:
                    location_tab = mem_custom_location.strip() if mem_custom_location else None
                    location_type_tab = "Custom Location"
                    custom_location_tab = mem_custom_location
                    selected_market_tab = None
                    selected_markets_tab = []

                memory_time_period_tab = mem_time_period
                classifier_type_value_tab = "cdl"  # Always CDL
                # ZIP code radius filtering
                mem_agent_zip = mem_zip_code.strip() if mem_zip_code else None
                mem_agent_zip_radius = mem_zip_radius
                # Free Agent from session state
                candidate_id_tab = st.session_state.get('candidate_id', '')
                candidate_name_tab = st.session_state.get('candidate_name', '')
                # PDF config
                max_jobs_pdf_tab = mem_max_jobs_pdf
                pdf_route_type_filter_tab = mem_pdf_route_filter
                pdf_match_quality_filter_tab = mem_pdf_quality_filter
                pathway_preferences_tab = []  # Not used
                pdf_fair_chance_only_tab = mem_fair_chance_only
                show_html_preview_tab = mem_show_html_preview
                generate_portal_link_tab = mem_generate_portal
                show_prepared_for_tab = mem_show_prepared_for
                enable_pdf_generation_tab = mem_enable_pdf

        # ==================== FRESH INDEED SEARCH TAB ====================
        with fresh_tab:
            # Check permission first
            _can_fresh = check_coach_permission('can_pull_fresh_jobs')
            if not _can_fresh:
                st.warning("🔒 Fresh Indeed scraping is disabled for your account. Contact admin for access.")
            else:
                st.markdown("Fetch fresh jobs from Indeed API and save to database. Use the **Memory Search** tab afterward to generate PDFs and portals.")

            # Location Selection (multi-market or custom)
            st.markdown("##### 📍 Location Selection")
            col1, col2 = st.columns([1, 3])

            with col1:
                fresh_location_options = ["Select Market(s)"]
                if check_coach_permission('can_use_custom_locations'):
                    fresh_location_options.append("Custom Location")

                fresh_location_type = st.radio(
                    "Location Type:",
                    fresh_location_options,
                    help="Choose preset markets or enter a custom location",
                    key="fresh_location_type"
                )

            with col2:
                if fresh_location_type == "Select Market(s)":
                    fresh_selected_markets = st.multiselect(
                        "Target Markets:",
                        markets,
                        help="Select one or multiple markets to search",
                        key="fresh_selected_markets"
                    )
                    if fresh_selected_markets:
                        if len(fresh_selected_markets) == 1:
                            st.success(f"📍 Selected Market: {fresh_selected_markets[0]}")
                        else:
                            st.success(f"📍 Selected Markets: {', '.join(fresh_selected_markets)}")
                    else:
                        st.warning("👆 Please select at least one market")
                else:
                    fresh_custom_location = st.text_input(
                        "Enter ZIP code, city, or state:",
                        placeholder="e.g., 90210, Austin TX, California",
                        help="Enter any US location",
                        key="fresh_custom_location"
                    )
                    if fresh_custom_location:
                        st.success(f"📍 Custom Location: {fresh_custom_location}")
                    else:
                        st.warning("👆 Please enter a location")

            # Search Parameters
            st.markdown("##### 🔍 Search Parameters")
            col1, col2 = st.columns(2)

            with col1:
                fresh_search_terms = st.text_input(
                    "Search Terms:",
                    value="CDL Driver No Experience",
                    help="Job search keywords. Use commas for multiple terms",
                    key="fresh_search_terms"
                )

            with col2:
                # Job Quantity
                mode_display_map_tab = MODE_DISPLAY_MAP
                search_display_options = MODE_DISPLAY_OPTIONS.copy()
                if check_coach_permission('can_access_full_mode'):
                    search_display_options.append("1000 jobs")

                fresh_search_mode_display = st.selectbox(
                    "Job Quantity:",
                    search_display_options,
                    index=1,  # default to "100 jobs"
                    help="Number of jobs to fetch and classify",
                    key="fresh_search_mode_display"
                )
                fresh_search_mode = mode_display_map_tab[fresh_search_mode_display]

            # Additional Options Row
            col1, col2, col3 = st.columns(3)
            with col1:
                commute_time_options = {
                    "Exact Location": 0,
                    "15 min commute": 15,
                    "25 min commute": 25,
                    "35 min commute": 35,
                    "45 min commute": 45,
                    "60 min commute": 60,
                    "90 min commute": 90
                }
                fresh_commute_display = st.selectbox(
                    "📏 Commute Time:",
                    list(commute_time_options.keys()),
                    index=5,  # default to 60 min
                    help="Indeed search area by commute time",
                    key="fresh_commute_time"
                )
                fresh_commute_time = commute_time_options[fresh_commute_display]

            with col2:
                fresh_no_experience = st.checkbox(
                    "📋 No Experience Filter",
                    value=True,
                    help="Include jobs that don't require prior experience",
                    key="fresh_no_experience"
                )

            with col3:
                # Advanced: Force Fresh Classification
                fresh_force_classification = False
                if check_coach_permission('can_force_fresh_classification'):
                    fresh_force_classification = st.checkbox(
                        "⚡ Force Fresh Classification",
                        value=False,
                        help="Re-run AI classification even on cached jobs",
                        key="fresh_force_classification"
                    )

            # Search Button
            st.markdown("---")
            indeed_fresh_clicked_tab = st.button(
                "🔍 Fetch Fresh Jobs from Indeed",
                help="Search Indeed API and save jobs to database",
                key="fresh_search_btn",
                use_container_width=True,
                disabled=not _can_fresh
            )

            st.caption("💡 After fetching, switch to **Memory Search** tab to generate PDFs and portal links.")

            # Set variables when Fresh Indeed search is triggered
            if indeed_fresh_clicked_tab:
                location_type_tab = fresh_location_type
                if fresh_location_type == "Select Market(s)":
                    selected_markets_tab = fresh_selected_markets
                    selected_market_tab = fresh_selected_markets[0] if fresh_selected_markets else None
                    if len(fresh_selected_markets) == 1:
                        location_tab = fresh_selected_markets[0]
                    else:
                        location_tab = fresh_selected_markets  # List for multi-market
                else:
                    custom_location_tab = fresh_custom_location
                    location_tab = fresh_custom_location.strip() if fresh_custom_location else None

                search_terms_tab = fresh_search_terms
                search_mode_tab = fresh_search_mode
                commute_time_tab = fresh_commute_time
                no_experience_tab = fresh_no_experience
                classifier_type_value_tab = "cdl"  # Always CDL
                force_fresh_classification_tab = fresh_force_classification
                # Set PDF defaults (no PDF/portal generation for fresh search)
                max_jobs_pdf_tab = 50
                pdf_route_type_filter_tab = ['Local', 'OTR', 'Unknown']
                pdf_match_quality_filter_tab = ['good', 'so-so']
                pathway_preferences_tab = []
                pdf_fair_chance_only_tab = False
                show_html_preview_tab = False
                generate_portal_link_tab = False
                show_prepared_for_tab = False
                enable_pdf_generation_tab = False  # Disable PDF for fresh search

        # Determine which search was triggered (outside tabs)
        search_type_tab = None
        if memory_clicked_tab:
            search_type_tab = 'memory'
        elif indeed_fresh_clicked_tab:
            search_type_tab = 'indeed_fresh'

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
                    'commute_time': commute_time_tab,
                    'classifier_type': classifier_type_value_tab,
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
                    # Add ZIP radius filtering if provided
                    if 'mem_agent_zip' in locals() and mem_agent_zip:
                        params.update({
                            'agent_zip': mem_agent_zip,
                            'zip_radius_miles': mem_agent_zip_radius
                        })
                # Indeed + Memory search type removed
                elif search_type_tab == 'indeed_fresh':
                    params.update({
                        'memory_only': False,
                        'force_fresh': True,
                        'generate_pdf': True,  # Enable PDF generation for Indeed Fresh searches
                        'search_sources': {'indeed': True, 'google': False},
                        'search_strategy': 'fresh_only'
                    })
                # Google ordering removed from Job Search page
                
                # Add location parameters (for non-Google searches)
                if location_type_tab == "Select Market":
                    if isinstance(location_tab, list) and len(location_tab) > 1 and search_type_tab == 'memory':
                        # Memory search with multi-market: force single market
                        st.error("❌ Memory searches only support single market selection. Using first market only.")
                        location_tab = location_tab[0]  # Use first market only
                        params.update({
                            'location_type': 'markets',
                            'markets': location_tab,
                            'location': location_tab
                        })
                    elif isinstance(location_tab, list):
                        # Multi-market search (non-memory)
                        params.update({
                            'location_type': 'multi_markets',
                            'markets': location_tab,  # List of markets
                            'location': location_tab[0] if location_tab else ''  # First market for legacy compatibility
                        })
                    else:
                        # Single market search
                        params.update({
                            'location_type': 'markets',
                            'markets': location_tab,
                            'location': location_tab
                        })
                else:
                    params.update({
                        'location_type': 'custom',
                        'custom_location': custom_location_tab,
                        'location': final_location_tab
                    })
                
                # Add PDF parameters - use correct parameter names for pipeline
                params.update({
                    'generate_pdf': enable_pdf_generation_tab,  # Use toggle value
                    'max_jobs': max_jobs_pdf_tab if max_jobs_pdf_tab != "All" else 999,  # Pipeline expects 'max_jobs'
                    'route_type_filter': pdf_route_type_filter_tab,  # Pipeline expects 'route_type_filter'
                    'match_quality_filter': pdf_match_quality_filter_tab,  # Pipeline expects 'match_quality_filter' 
                    'fair_chance_only': pdf_fair_chance_only_tab,  # Pipeline expects 'fair_chance_only'
                    'show_prepared_for': show_prepared_for_tab  # Pipeline expects 'show_prepared_for'
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
                        # 'indeed' search mode removed
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
                        
                        # Use unified search function to eliminate duplicate multi-market handling
                        coach = st.session_state.get('current_coach')
                        df, metadata = run_search_with_location_handling(
                            pipeline=pipeline,
                            params=params,
                            search_type_tab=search_type_tab,
                            coach=coach,
                            candidate_id=candidate_id,
                            candidate_name=candidate_name
                        )
                        
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
                        
                        # Clear any previous tab-based PDF state when starting new search
                        pdf_keys_to_clear = [key for key in st.session_state.keys() if key.startswith('tab_pdf_bytes_') or key.startswith('tab_pdf_filename_')]
                        for key in pdf_keys_to_clear:
                            del st.session_state[key]
                        
                        # Use unified search function to eliminate duplicate multi-market handling
                        df, metadata = run_search_with_location_handling(
                            pipeline=pipeline,
                            params=params,
                            search_type_tab=search_type_tab,
                            coach=coach,
                            candidate_id=candidate_id,
                            candidate_name=candidate_name
                        )
                else:
                    # For Google searches or when no search type, initialize empty results  
                    import pandas as pd
                    df, metadata = pd.DataFrame(), {'success': True, 'message': 'Google search submitted'}
                
                # Export combined Parquet from DataFrame if enabled (visible before results)
                try:
                    if export_combined_parquet and isinstance(df, pd.DataFrame) and not df.empty:
                        from datetime import datetime as _dt
                        parquet_bytes = pipeline.dataframe_to_parquet_bytes(df) if hasattr(pipeline, 'dataframe_to_parquet_bytes') else b""
                        render_download_button(
                            data=parquet_bytes,
                            label="📦 Download Parquet (Combined Results)",
                            filename=f"combined_results_{_dt.now().strftime('%Y%m%d_%H%M%S')}.parquet",
                            mime_type="application/octet-stream",
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
                
                # Store results in session state (including HTML preview and portal link data for persistence)
                st.session_state.last_results = {
                    'df': df,
                    'metadata': metadata,
                    'params': params,
                    'search_type': search_type_tab,
                    'timestamp': datetime.now(),
                    'html_preview_enabled': show_html_preview_tab,
                    'portal_link_enabled': generate_portal_link_tab,
                    'html_preview_data': None,  # Will be populated if HTML preview is generated
                    'portal_link_data': None   # Will be populated if portal link is generated
                }
                
                # Unified results display for ALL search modes
                if isinstance(df, pd.DataFrame) and not df.empty:
                    # Check if this is a multi-market search
                    is_multi_market = 'meta.market' in df.columns and df['meta.market'].nunique() > 1

                    # 1. SUMMARY SECTION - Only show for multi-market searches
                    if is_multi_market:
                        render_search_summary_header()

                        # Calculate and display quality metrics using shared functions
                        metrics = calculate_quality_metrics(df)
                        route_counts = calculate_route_distribution(df)
                        render_quality_metrics(metrics)
                        render_supabase_upload_info(metadata)

                        render_route_distribution(route_counts)

                        st.markdown("---")
                    
                    # 2. PDF DOWNLOAD BUTTON - Always generate PDF with all included jobs
                    coach = st.session_state.get('current_coach')
                    if coach:
                        # Filter for included jobs (properly sorted)
                        included_df = df[df.get('route.final_status', '').astype(str).str.startswith('included')].copy()
                        if included_df.empty:
                            # If no route.final_status, use quality jobs
                            included_df = df[df.get('ai.match', '').isin(['good', 'so-so'])].copy()
                        if included_df.empty:
                            # If no ai.match, use all jobs
                            included_df = df.copy()
                        
                        # Sort by quality then date (use available date columns)
                        if 'ai.match' in included_df.columns:
                            quality_order = {'good': 0, 'so-so': 1, 'bad': 2}
                            included_df['_quality_sort'] = included_df['ai.match'].map(quality_order).fillna(3)
                            
                            # Find available date column for secondary sort
                            date_cols = ['sys.scraped_at', 'source.posted_date', 'sys.created_at', 'sys.updated_at']
                            date_col = None
                            for col in date_cols:
                                if col in included_df.columns:
                                    date_col = col
                                    break
                            
                            if date_col:
                                included_df = included_df.sort_values(['_quality_sort', date_col], ascending=[True, False])
                            else:
                                included_df = included_df.sort_values('_quality_sort', ascending=True)
                            included_df = included_df.drop('_quality_sort', axis=1)
                        
                        # Determine market name
                        market_name = 'Multiple Markets'
                        if 'meta.market' in df.columns:
                            markets = [m for m in df['meta.market'].dropna().unique() if str(m).strip()]
                            if len(markets) == 1:
                                market_name = str(markets[0])
                        
                        # Generate PDF
                        pdf_bytes = pipeline.generate_pdf_from_canonical(
                            included_df,
                            market_name=market_name,
                            coach_name=coach.full_name,
                            coach_username=coach.username,
                            candidate_name=st.session_state.get('candidate_name', ''),
                            candidate_id=st.session_state.get('candidate_id', ''),
                            show_prepared_for=st.session_state.get('tab_show_prepared_for', True)
                        )
                        
                        render_download_button(
                            data=pdf_bytes,
                            label=f"📥 Download PDF ({len(included_df)} jobs)",
                            filename=f"FreeWorld_Jobs_{market_name.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime_type="application/pdf",
                            key=f"{search_type_tab}_pdf_download"
                        )
                    else:
                        st.error("Coach information not available for PDF generation")
                    
                    st.markdown("---")
                    
                    # 3. COMPREHENSIVE RESULTS DISPLAY (CSV CLASSIFIER FORMAT)
# Import already handled at top of file

                    # Show overall results table first
                    st.markdown("### 📋 **All Search Results**")
                    full_display = get_full_display_dataframe(df)
                    st.dataframe(full_display, width="stretch", height=420, hide_index=True)

                    # Multi-market display (CSV classifier format)
                    try:
                        if 'meta.market' in df.columns:
                            unique_mkts = [m for m in df['meta.market'].dropna().unique().tolist() if str(m).strip()]
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

                                        mdf = df[df['meta.market'] == mk]

                                        # Quality subset for this market
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

                                        # Use standardized display format matching combined summary
                                        market_metrics = calculate_quality_metrics(mdf)
                                        market_route_counts = calculate_route_distribution(mdf)
                                        render_quality_metrics(market_metrics)
                                        render_route_distribution(market_route_counts)

                                        # Show quality jobs table for this market
                                        market_quality_display = get_quality_display_dataframe(mdf_inc)
                                        st.dataframe(market_quality_display, width="stretch", height=360, hide_index=True)

                                        # Full results for this market
                                        with st.expander(f"🔎 Full Results — {mk}", expanded=False):
                                            market_full_display = get_full_display_dataframe(mdf)
                                            st.dataframe(market_full_display, width="stretch", height=480, hide_index=True)
                                    except Exception as e:
                                        st.warning(f"⚠️ Display error for {mk}: {e}")
                            else:
                                # No markets detected - show single quality view
                                st.markdown("### 🎯 Quality Jobs")
                                quality_display = get_quality_display_dataframe(df)
                                st.dataframe(quality_display, width="stretch", height=400, hide_index=True)
                                # Single collapsible full dataframe
                                with st.expander(f"🔍 All Processed Jobs ({total_jobs} total)", expanded=False):
                                    st.dataframe(full_display, width="stretch", height=500, hide_index=True)
                        else:
                            # No meta.market column - show single quality view
                            st.markdown("### 🎯 Quality Jobs")
                            quality_display = get_quality_display_dataframe(df)
                            st.dataframe(quality_display, width="stretch", height=400, hide_index=True)
                            # Single collapsible full dataframe
                            with st.expander(f"🔍 All Processed Jobs ({total_jobs} total)", expanded=False):
                                st.dataframe(full_display, width="stretch", height=500, hide_index=True)
                    except Exception as e:
                        st.warning(f"⚠️ Multi-market display error: {e}")
                        # Fallback to simple display
                        st.markdown("### 🎯 Quality Jobs")
                        quality_display = get_quality_display_dataframe(df)
                        st.dataframe(quality_display, width="stretch", height=400, hide_index=True)
                        with st.expander(f"🔍 All Processed Jobs ({total_jobs} total)", expanded=False):
                            st.dataframe(full_display, width="stretch", height=500, hide_index=True)
                    
                    # HTML Preview if enabled (but NOT for Indeed searches)
                    if show_html_preview_tab and jobs_dataframe_to_dicts and render_jobs_html and not df.empty and search_type_tab not in ['indeed_fresh', 'indeed']:
                        render_html_preview(
                            df=df,
                            location=final_location_tab,
                            candidate_name=candidate_name_tab,
                            candidate_id=candidate_id_tab,
                            max_jobs=max_jobs_pdf_tab,
                            pdf_fair_chance_only=pdf_fair_chance_only_tab,
                            is_memory_search=False
                        )
                    
                    # Portal Link Generation if enabled (but NOT for any Indeed searches)
                    if generate_portal_link_tab:
                        # Build search parameters for unified portal function
                        search_params = {
                            'mode': search_mode_tab,
                            'search_terms': search_terms_tab,
                            'commute_time': commute_time_tab,
                            'route_filter': pdf_route_type_filter_tab,
                            'no_experience': no_experience_tab,
                            'fair_chance_only': pdf_fair_chance_only_tab,
                            'max_jobs': max_jobs_pdf_tab,
                            'show_prepared_for': show_prepared_for_tab,
                            'location_type': location_type_tab,
                            'memory_hours': int(memory_time_period_tab.replace('h','') or 72) if search_type_tab == 'memory' else 72,
                            'coach_username': st.session_state.get('current_coach').username if st.session_state.get('current_coach') else '',
                            'coach_name': st.session_state.get('current_coach').full_name if st.session_state.get('current_coach') else ''
                        }

                        render_portal_link_section(
                            search_params=search_params,
                            candidate_name=candidate_name_tab,
                            candidate_id=candidate_id_tab,
                            search_type=search_type_tab,
                            final_location=final_location_tab,
                            force_fresh_classification=force_fresh_classification_tab if 'force_fresh_classification_tab' in locals() else False,
                            is_memory_search=False
                        )
                    
                    if not df.empty:
                        st.balloons()
                        
                else:
                    # Check for filter-related "no results" vs actual error
                    if metadata and metadata.get('no_results_message'):
                        st.warning(f"📭 {metadata.get('no_results_message')}")
                        if metadata.get('no_results_tip'):
                            st.info(f"💡 **Tip:** {metadata.get('no_results_tip')}")
                    else:
                        st.error(f"❌ Search failed: {metadata.get('error', 'No jobs found') if metadata else 'No data returned'}")
                    if show_html_preview_tab and jobs_dataframe_to_dicts and render_jobs_html and not df.empty and search_type_tab not in ['indeed_fresh', 'indeed']:
                        render_html_preview(
                            df=df,
                            location=final_location_tab,
                            candidate_name=candidate_name_tab,
                            candidate_id=candidate_id_tab,
                            max_jobs=max_jobs_pdf_tab,
                            pdf_fair_chance_only=pdf_fair_chance_only_tab,
                            is_memory_search=False
                        )
                    
                    # Portal Link Generation if enabled (but NOT for any Indeed searches)
                    if generate_portal_link_tab:
                        # Build search parameters for unified portal function
                        search_params = {
                            'mode': search_mode_tab,
                            'search_terms': search_terms_tab,
                            'commute_time': commute_time_tab,
                            'route_filter': pdf_route_type_filter_tab,
                            'no_experience': no_experience_tab,
                            'fair_chance_only': pdf_fair_chance_only_tab,
                            'max_jobs': max_jobs_pdf_tab if max_jobs_pdf_tab != "All" else 50,
                            'show_prepared_for': st.session_state.get('tab_show_prepared_for', True),
                            'location_type': location_type_tab,
                            'memory_hours': int(memory_time_period_tab.replace('h','') or 72) if search_type_tab == 'memory' else 72,
                            'coach_username': st.session_state.get('current_coach').username if st.session_state.get('current_coach') else '',
                            'coach_name': st.session_state.get('current_coach').full_name if st.session_state.get('current_coach') else ''
                        }

                        render_portal_link_section(
                            search_params=search_params,
                            candidate_name=candidate_name_tab,
                            candidate_id=candidate_id_tab,
                            search_type=search_type_tab,
                            final_location=final_location_tab,
                            force_fresh_classification=force_fresh_classification_tab if 'force_fresh_classification_tab' in locals() else False,
                            is_memory_search=False
                        )
                        
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

                                                                        # Generate edge function URL for click tracking (no Short.io)
                                                                        tracked_url = link_tracker.generate_edge_function_url(
                                                                            original_url,
                                                                            candidate_id=candidate_id,
                                                                            tags=tags
                                                                        )

                                                                        if tracked_url:
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
                                                                            market_name=market,
                                                                            coach_name=coach.full_name,
                                                                            coach_username=coach.username,
                                                                            candidate_name=candidate_name,
                                                                            candidate_id=candidate_id,
                                                                            show_prepared_for=st.session_state.get('tab_show_prepared_for', True)
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
                                                render_download_button(
                                                    data=pdf_data['pdf_bytes'],
                                                    label=f"📥 Download",
                                                    filename=pdf_data['filename'],
                                                    mime_type="application/pdf",
                                                    key=f"download_market_pdf_tab_{market}"
                                                )
                                    
                                    # Quality jobs for this market
                                    if not market_quality.empty:
                    # Import already handled at top of file

                                        market_quality_display = get_quality_display_dataframe(market_quality)
                                        st.dataframe(market_quality_display, width="stretch", height=300, hide_index=True)

                                    # Collapsed full data for this market
                                    with st.expander(f"🔍 Full Data - {market} ({len(market_df)} total jobs)", expanded=False):
                                        market_full_display = get_full_display_dataframe(market_df)
                                        st.dataframe(market_full_display, width="stretch", height=400, hide_index=True)
                                    
                                    st.markdown("---")
                        except Exception as e:
                            st.warning(f"⚠️ Per-market display error: {e}")
                    
                    if not df.empty:
                        st.balloons()
        else:
            # Show persistent results if they exist, otherwise show placeholder
            if 'last_results' in st.session_state:
                # Display persistent results from previous search
                results = st.session_state.last_results
                df = results['df']
                metadata = results['metadata']
                result_timestamp = results.get('timestamp', 'Unknown time')
                
                if not df.empty and metadata.get('success', False):
                    st.info(f"📊 **Previous Search Results** ({result_timestamp.strftime('%I:%M %p') if hasattr(result_timestamp, 'strftime') else result_timestamp})")
                    st.markdown("*Results persist until you run a new search*")
                    
                    # Show results using the same logic as immediate results
# Import already handled at top of file
                    show_all_rows = st.checkbox("Show all rows (no filters)", value=False, key="persistent_show_all_rows")
                    if show_all_rows:
                        display_df = get_full_display_dataframe(df)
                    else:
                        display_df = get_quality_display_dataframe(df)
                    st.dataframe(display_df, width="stretch", height=420, hide_index=True)
                    
                    # Add on-demand PDF generation for persistent results
                    col_pdf_persistent, _ = st.columns([1, 3])
                    with col_pdf_persistent:
                        if st.button("📄 Generate PDF", key="persistent_generate_pdf_btn"):
                            coach = st.session_state.get('current_coach')
                            candidate_name = st.session_state.get('candidate_name', '')
                            candidate_id = st.session_state.get('candidate_id', '')
                            
                            # Apply reasonable limit for persistent results
                            limited_quality_df = quality_df.head(50)
                            
                            # Generate PDF from persistent results
                            market_name = results.get('params', {}).get('location', 'Search Results')
                            pdf_bytes = pipeline.generate_pdf_from_canonical(
                                limited_quality_df,
                                market_name=market_name,
                                coach_name=coach.full_name if coach else '',
                                coach_username=coach.username if coach else '',
                                candidate_name=candidate_name,
                                candidate_id=candidate_id,
                                show_prepared_for=st.session_state.get('tab_show_prepared_for', True)
                            )
                            render_download_button(
                                data=pdf_bytes,
                                label="📥 Download PDF",
                                filename=f"freeworld_jobs_{str(market_name).replace(' ', '_')}.pdf",
                                mime_type="application/pdf"
                            )
            else:
                st.info("🚧 Click a search button above to start searching for jobs...")
    
    elif selected_tab == "🗓️ Batches & Scheduling":
        # Double-check access permission
        if not check_coach_permission('can_access_batches'):
            st.error("❌ Access to Batches & Scheduling is not enabled for your account")
            st.info("💡 Contact your administrator to enable this feature")
        else:
            show_combined_batches_and_scheduling_page(coach)

    elif selected_tab == "🎯 Inside Track Jobs":
        # Double-check access permission
        if not check_coach_permission('can_manage_inside_track'):
            st.error("❌ Access to Inside Track Jobs is not enabled for your account")
            st.info("💡 Contact your administrator to enable this feature")
        else:
            show_inside_track_jobs_page(coach)

    elif selected_tab == "👥 Free Agents":
        # Free Agents management
        st.header("👥 Free Agents Portal")
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

    elif selected_tab == "📈 Market Analytics":
        from admin_market_dashboard import show_admin_market_dashboard
        show_admin_market_dashboard()

    elif selected_tab == "🏢 Companies":
        try:
            from companies_dashboard import show_companies_dashboard
            show_companies_dashboard()
        except ImportError as e:
            st.error(f"❌ Companies dashboard not available: {e}")
            st.info("💡 The companies analytics module is not properly configured.")
        except Exception as e:
            st.error(f"❌ Error loading companies dashboard: {e}")
    
    elif selected_tab.startswith("👑 Admin Panel") or selected_tab == "🔒 Restricted":
        # Strict admin-only access control
        if coach.role != 'admin':
            st.error("❌ Admin Panel access is restricted to administrators only")
            st.info("💡 This section requires admin privileges")
            st.warning("🔒 If you believe you should have admin access, contact your system administrator")
        else:
            st.header("👑 Admin Panel")
            
            # Initialize session state for admin function selection
            admin_function_options = ["Manage Coaches", "System Settings"]
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
                # Get fresh coach manager instance to ensure latest data
                coach_manager = get_coach_manager()
                
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
                                new_access_batches = st.checkbox("Batches & Scheduling Access", value=getattr(existing_coach, 'can_access_batches', True), key=f"tab_batches_{username}")
                                new_manage_inside_track = st.checkbox("Inside Track Jobs Access", value=getattr(existing_coach, 'can_manage_inside_track', True), key=f"tab_inside_track_{username}")

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
                                        'can_access_batches': new_access_batches,
                                        'can_manage_inside_track': new_manage_inside_track,
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
                                            'can_force_fresh_classification': True,
                                            'can_access_batches': True,
                                            'can_manage_inside_track': True
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
            
            elif admin_tab_select == "System Settings":
                st.markdown("### 🔧 System Settings")
                
                # API Tests
                st.markdown("#### 🔌 API Connection Tests")
                if st.button("🧪 Test All APIs", key="tab_test_apis"):
                    # Test Supabase
                    try:
                        from supabase_utils import get_client
                        supabase = get_client()
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
    
    # Logo functionality removed (sidebar eliminated)
    
    # Admin panel functionality removed (sidebar eliminated)
    
    # Old page navigation removed (sidebar eliminated)
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
    
    # Coach notifications removed - no longer needed
    
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
            for key in ['memory_search_df', 'memory_search_metadata', 'memory_search_params']:
                if hasattr(st.session_state, key):
                    delattr(st.session_state, key)
            # Keep last_results for persistence across tab navigation
            
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
                'generate_pdf': enable_pdf_generation_tab,  # Use PDF toggle value
                'generate_csv': False,  # UI memory-only: no CSV during search
                'search_radius': search_radius,
                'classifier_type': 'cdl',  # Default to CDL for sidebar memory search
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

            # If no jobs, show helpful message with actionable tip
            if (df is None or df.empty) and (not metadata.get('success', False)):
                # Check if this is a filter-related "no results" (vs actual error)
                no_results_msg = metadata.get('no_results_message')
                no_results_tip = metadata.get('no_results_tip')

                if no_results_msg:
                    # Filter-related empty results - show friendly message
                    st.warning(f"📭 {no_results_msg}")
                    if no_results_tip:
                        st.info(f"💡 **Tip:** {no_results_tip}")
                else:
                    # Actual technical issue - show diagnostics
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
            
            # Store results in session state (same as Indeed button, with HTML/portal data)
            st.session_state.last_results = {
                'df': df,
                'metadata': metadata,
                'params': params,
                'timestamp': datetime.now(),
                'html_preview_enabled': show_html_preview_tab,
                'portal_link_enabled': generate_portal_link_tab,
                'html_preview_data': None,  # Will be populated if HTML preview is generated
                'portal_link_data': None   # Will be populated if portal link is generated
            }
            
            # Show results (fallback to DataFrame presence)
            if (isinstance(df, pd.DataFrame) and not df.empty) or metadata.get('success', False):
                st.success(f"✅ Memory search completed! Found {metadata.get('quality_jobs', 0)} quality jobs from memory")
                
                # CSV download removed per new UI
                
                if generate_pdf and metadata.get('pdf_path'):
                    pdf_bytes = pipeline.get_pdf_bytes(metadata['pdf_path'])
                    if pdf_bytes:
                        pretty = f"{final_location} Jobs Report"
                        render_download_button(
                            data=pdf_bytes,
                            label="📄 Download PDF",
                            filename=f"{pretty.lower().replace(' ', '_')}.pdf",
                            mime_type="application/pdf"
                        )
                
                # HTML Preview if enabled (memory searches should work)
                if show_html_preview_tab and jobs_dataframe_to_dicts and render_jobs_html and not df.empty:
                    render_html_preview(
                        df=df,
                        location=preview_location,
                        candidate_name=candidate_name,
                        candidate_id=candidate_id,
                        max_jobs=max_jobs,
                        pdf_fair_chance_only=False,  # Memory search doesn't use this filter
                        is_memory_search=True,  # Use debugged memory search logic
                        title="HTML Preview"
                    )
                
                # Portal Link Generation if enabled
                if generate_portal_link_tab and candidate_id and candidate_name:
                    # Build search parameters for unified portal function (from memory search params)
                    search_params = {
                        'mode': params.get('mode', search_mode),
                        'search_terms': params.get('search_terms', search_terms),
                        'search_radius': params.get('search_radius', search_radius),
                        'route_filter': params.get('route_filter', route_filter),
                        'no_experience': params.get('no_experience', no_experience),
                        'fair_chance_only': params.get('fair_chance_only', fair_chance_only),
                        'max_jobs': params.get('max_jobs', max_jobs),
                        'memory_hours': params.get('memory_hours', _mem_hours),
                        'coach_username': st.session_state.get('current_coach').username if st.session_state.get('current_coach') else '',
                        'coach_name': st.session_state.get('current_coach').full_name if st.session_state.get('current_coach') else ''
                    }

                    render_portal_link_section(
                        search_params=search_params,
                        candidate_name=candidate_name,
                        candidate_id=candidate_id,
                        search_type='memory',
                        final_location=preview_location,
                        force_fresh_classification=params.get('force_fresh_classification', force_fresh_classification),
                        is_memory_search=True
                    )
                
                # Unified results display for Memory Only searches
                # Check if this is a multi-market search
                is_multi_market = 'meta.market' in df.columns and df['meta.market'].nunique() > 1

                # 1. SUMMARY SECTION - Only show for multi-market searches
                if is_multi_market:
                    render_search_summary_header()

                    # Calculate and display quality metrics using shared functions
                    metrics = calculate_quality_metrics(df)
                    route_counts = calculate_route_distribution(df)
                    render_quality_metrics(metrics)
                    render_supabase_upload_info(metadata)

                    render_route_distribution(route_counts)

                    st.markdown("---")
                
                # 2. PDF DOWNLOAD BUTTON - Always generate PDF with all included jobs
                if coach:
                    # Filter for included jobs (properly sorted)
                    included_df = df[df.get('route.final_status', '').astype(str).str.startswith('included')].copy()
                    if included_df.empty:
                        # If no route.final_status, use quality jobs
                        included_df = df[df.get('ai.match', '').isin(['good', 'so-so'])].copy()
                    if included_df.empty:
                        # If no ai.match, use all jobs
                        included_df = df.copy()
                    
                    # Sort by quality then date (use available date columns)
                    if 'ai.match' in included_df.columns:
                        quality_order = {'good': 0, 'so-so': 1, 'bad': 2}
                        included_df['_quality_sort'] = included_df['ai.match'].map(quality_order).fillna(3)
                        
                        # Find available date column for secondary sort
                        date_cols = ['sys.scraped_at', 'source.posted_date', 'sys.created_at', 'sys.updated_at']
                        date_col = None
                        for col in date_cols:
                            if col in included_df.columns:
                                date_col = col
                                break
                        
                        if date_col:
                            included_df = included_df.sort_values(['_quality_sort', date_col], ascending=[True, False])
                        else:
                            included_df = included_df.sort_values('_quality_sort', ascending=True)
                        included_df = included_df.drop('_quality_sort', axis=1)
                    
                    # Determine market name
                    market_name = 'Multiple Markets'
                    if 'meta.market' in df.columns:
                        markets = [m for m in df['meta.market'].dropna().unique() if str(m).strip()]
                        if len(markets) == 1:
                            market_name = str(markets[0])
                    
                    # Generate PDF
                    pdf_bytes = pipeline.generate_pdf_from_canonical(
                        included_df,
                        market_name=market_name,
                        coach_name=coach.full_name,
                        coach_username=coach.username,
                        candidate_name=st.session_state.get('candidate_name', ''),
                        candidate_id=st.session_state.get('candidate_id', ''),
                        show_prepared_for=st.session_state.get('tab_show_prepared_for', True)
                    )
                    
                    render_download_button(
                        data=pdf_bytes,
                        label=f"📥 Download PDF ({len(included_df)} jobs)",
                        filename=f"FreeWorld_Jobs_{market_name.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime_type="application/pdf",
                        key="memory_pdf_download"
                    )
                else:
                    st.error("Coach information not available for PDF generation")
                
                st.markdown("---")
                
                # 3. COMPREHENSIVE RESULTS DISPLAY (CSV CLASSIFIER FORMAT)
# Import already handled at top of file

                # Show overall results table first
                st.markdown("### 📋 **All Search Results**")
                full_display = get_full_display_dataframe(df)
                st.dataframe(full_display, width="stretch", height=420, hide_index=True)

                # Multi-market display (CSV classifier format)
                try:
                    if 'meta.market' in df.columns:
                        unique_mkts = [m for m in df['meta.market'].dropna().unique().tolist() if str(m).strip()]
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

                                    mdf = df[df['meta.market'] == mk]

                                    # Quality subset for this market
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

                                    # Use standardized display format matching combined summary
                                    market_metrics = calculate_quality_metrics(mdf)
                                    market_route_counts = calculate_route_distribution(mdf)
                                    render_quality_metrics(market_metrics)
                                    render_route_distribution(market_route_counts)

                                    # Show quality jobs table for this market
                                    market_quality_display = get_quality_display_dataframe(mdf_inc)
                                    st.dataframe(market_quality_display, width="stretch", height=360, hide_index=True)

                                    # Full results for this market
                                    with st.expander(f"🔎 Full Results — {mk}", expanded=False):
                                        market_full_display = get_full_display_dataframe(mdf)
                                        st.dataframe(market_full_display, width="stretch", height=480, hide_index=True)
                                except Exception as e:
                                    st.warning(f"⚠️ Display error for {mk}: {e}")
                        else:
                            # No markets detected - show single quality view
                            st.markdown("### 🎯 Quality Jobs")
                            quality_display = get_quality_display_dataframe(df)
                            st.dataframe(quality_display, width="stretch", height=400, hide_index=True)
                            # Single collapsible full dataframe
                            with st.expander(f"🔍 All Processed Jobs ({total_jobs} total)", expanded=False):
                                st.dataframe(full_display, width="stretch", height=500, hide_index=True)
                    else:
                        # No meta.market column - show single quality view
                        st.markdown("### 🎯 Quality Jobs")
                        quality_display = get_quality_display_dataframe(df)
                        st.dataframe(quality_display, width="stretch", height=400, hide_index=True)
                        # Single collapsible full dataframe
                        with st.expander(f"🔍 All Processed Jobs ({total_jobs} total)", expanded=False):
                            st.dataframe(full_display, width="stretch", height=500, hide_index=True)
                except Exception as e:
                    st.warning(f"⚠️ Multi-market display error: {e}")
                    # Fallback to simple display
                    st.markdown("### 🎯 Quality Jobs")
                    quality_display = get_quality_display_dataframe(df)
                    st.dataframe(quality_display, width="stretch", height=400, hide_index=True)
                    with st.expander(f"🔍 All Processed Jobs ({total_jobs} total)", expanded=False):
                        st.dataframe(full_display, width="stretch", height=500, hide_index=True)
                
                if not df.empty:
                    st.balloons()
            else:
                # Check for filter-related "no results" vs actual error
                if metadata and metadata.get('no_results_message'):
                    st.warning(f"📭 {metadata.get('no_results_message')}")
                    if metadata.get('no_results_tip'):
                        st.info(f"💡 **Tip:** {metadata.get('no_results_tip')}")
                else:
                    st.error(f"❌ Memory search failed: {metadata.get('error', 'No jobs found')}")

            # Always show debug logs for memory search (collapsed)
            if mem_logs.strip() or mem_debug_summary:
                with st.expander("🧪 Debug logs (memory search)", expanded=False):
                    # Prepend summary to the captured logs
                    text = mem_debug_summary + (mem_logs[-5000:] if mem_logs else '')
                    st.code(text, language="text")
        
        # Google ordering removed from Job Search sidebar


def show_inside_track_jobs_page(coach):
    """Inside Track Jobs page - manage partner opportunities that appear at top of feeds"""
    import pandas as pd
    from datetime import datetime, timedelta
    from inside_track_manager import (
        load_inside_track_jobs, save_inside_track_job, toggle_job_visibility,
        repost_job, delete_inside_track_job, get_inside_track_metadata,
        update_inside_track_job, load_inside_track_interests, update_interest_status
    )
    from market_config import get_all_markets

    st.header("🎯 Inside Track Jobs")
    st.caption("Partner opportunities that appear first in Free Agent feeds with a special badge")

    # Sub-tabs
    sub_tab_options = ["📋 All Jobs", "➕ Add New Job", "🙋 Interested Agents"]

    if 'inside_track_tab' not in st.session_state:
        st.session_state.inside_track_tab = 0

    selected_sub_tab = st.radio(
        "View",
        options=sub_tab_options,
        index=st.session_state.inside_track_tab,
        key="inside_track_sub_tab_radio",
        horizontal=True
    )

    if selected_sub_tab in sub_tab_options:
        st.session_state.inside_track_tab = sub_tab_options.index(selected_sub_tab)

    st.markdown("---")

    if selected_sub_tab == "📋 All Jobs":
        # Load all inside track jobs (all coaches can see/edit all)
        jobs = load_inside_track_jobs(visible_only=False)

        if not jobs:
            st.info("📭 No inside track jobs yet. Add your first partner opportunity!")
        else:
            st.markdown(f"**{len(jobs)} inside track jobs**")

            # Convert to DataFrame for display
            df_data = []
            for job in jobs:
                metadata = get_inside_track_metadata(job)
                is_visible = job.get('filter_reason', '') == 'included: inside_track'

                # Check if expired
                expires_at = job.get('expires_at', '')
                is_expired = False
                if expires_at:
                    try:
                        exp_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        is_expired = exp_date < datetime.now(exp_date.tzinfo)
                    except:
                        pass

                df_data.append({
                    'job_id': job.get('job_id', ''),
                    'Job Title': job.get('job_title', ''),
                    'Company': job.get('company', ''),
                    'Market': job.get('market', ''),
                    'Route': job.get('route_type', 'Local'),
                    'Quality': job.get('match_level', 'good'),
                    'Visible': is_visible,
                    'Expired': is_expired,
                    'Partner': job.get('partner_name', ''),
                    'Coach': job.get('success_coach', ''),
                    'Created': job.get('created_at', '')[:10] if job.get('created_at') else '',
                })

            df = pd.DataFrame(df_data)

            # Display with actions
            for idx, row in df.iterrows():
                job_id = row['job_id']

                with st.expander(f"**{row['Job Title']}** at {row['Company']} ({row['Market']})", expanded=False):
                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        st.write(f"**Route:** {row['Route']}")
                        st.write(f"**Quality:** {row['Quality']}")
                        st.write(f"**Partner:** {row['Partner'] or 'N/A'}")

                    with col2:
                        st.write(f"**Created by:** {row['Coach']}")
                        st.write(f"**Created:** {row['Created']}")

                    with col3:
                        # Visibility status
                        if row['Visible']:
                            st.success("✅ Visible")
                        else:
                            st.warning("🔒 Hidden")

                        if row['Expired']:
                            st.error("⏰ Expired")

                    # Action buttons
                    btn_col1, btn_col2, btn_col3 = st.columns(3)

                    with btn_col1:
                        if row['Visible']:
                            if st.button("🔒 Hide", key=f"hide_{job_id}"):
                                success, msg = toggle_job_visibility(job_id, False)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        else:
                            if st.button("👁️ Show", key=f"show_{job_id}"):
                                success, msg = toggle_job_visibility(job_id, True)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

                    with btn_col2:
                        if st.button("🔄 Repost", key=f"repost_{job_id}"):
                            success, msg = repost_job(job_id)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

                    with btn_col3:
                        if st.button("🗑️ Delete", key=f"delete_{job_id}"):
                            success, msg = delete_inside_track_job(job_id)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

    elif selected_sub_tab == "➕ Add New Job":
        st.markdown("### Add Inside Track Job")

        with st.form("add_inside_track_job"):
            # Job type selection - clean segmented control style
            inside_track_type = st.radio(
                "Job Type",
                options=["partner_opportunity", "inside_track"],
                format_func=lambda x: "🤝 Partner Opportunity" if x == "partner_opportunity" else "📋 Inside Track",
                horizontal=True,
            )
            # Show explanation based on selection
            if inside_track_type == "partner_opportunity":
                st.caption("Company hidden · Free Agent clicks 'I'm Interested' · You get notified")
            else:
                st.caption("Shows real company · Free Agent applies directly · Top of feed priority")

            st.markdown("---")

            # Required fields
            job_title = st.text_input("Job Title *", placeholder="CDL-A Driver - Local Routes")
            company = st.text_input(
                "Company *",
                placeholder="ABC Trucking",
                help="For Partner Opportunities, this is hidden from Free Agents but shown to you."
            )

            col1, col2, col3 = st.columns([2, 1, 2])
            with col1:
                location = st.text_input("Location *", placeholder="Houston, TX")
            with col2:
                zip_code = st.text_input("ZIP Code", placeholder="77001")
            with col3:
                market = st.selectbox("Market *", options=get_all_markets())

            job_description = st.text_area(
                "Job Description *",
                placeholder="Describe the position, requirements, benefits...",
                height=150
            )

            apply_url = st.text_input(
                "Apply URL",
                placeholder="https://company.com/apply",
                help="Required for Inside Track jobs. Optional for Partner Opportunities.",
                key="inside_track_apply_url"
            )

            st.markdown("---")
            st.markdown("### Optional Details")

            col1, col2 = st.columns(2)
            with col1:
                salary = st.text_input("Salary", placeholder="$25-30/hr or $65k/year")
                route_type = st.selectbox("Route Type", options=['Local', 'Regional', 'OTR', 'Unknown'])
                fair_chance = st.checkbox("Fair Chance Employer", value=True)

            with col2:
                match_level = st.selectbox("Quality Level", options=['good', 'so-so'])
                expires_at = st.date_input("Expires On (optional)", value=None)

            st.markdown("---")
            st.markdown("### Partner Information (Internal)")

            col1, col2 = st.columns(2)
            with col1:
                partner_name = st.text_input("Partner/Contact Name", placeholder="John Smith")
            with col2:
                partner_notes = st.text_area("Internal Notes", placeholder="How we got this opportunity...")

            submitted = st.form_submit_button("➕ Add Inside Track Job", type="primary")

            if submitted:
                # Validate required fields
                required_ok = all([job_title, company, location, market, job_description])
                # Apply URL required for inside_track type only
                if inside_track_type == "inside_track" and not apply_url:
                    st.error("❌ Apply URL is required for Inside Track jobs")
                elif not required_ok:
                    st.error("❌ Please fill in all required fields (marked with *)")
                else:
                    job_data = {
                        'job_title': job_title,
                        'company': company,
                        'location': location,
                        'zip_code': zip_code,
                        'market': market,
                        'job_description': job_description,
                        'apply_url': apply_url,
                        'inside_track_type': inside_track_type,
                        'salary': salary,
                        'route_type': route_type,
                        'fair_chance': 'fair_chance_employer' if fair_chance else 'background_check_required',
                        'match_level': match_level,
                        'partner_name': partner_name,
                        'partner_notes': partner_notes,
                        'expires_at': expires_at.isoformat() if expires_at else '',
                    }

                    success, msg = save_inside_track_job(job_data, coach.username)
                    if success:
                        st.success(f"✅ {msg}")
                        st.balloons()
                        # Switch to All Jobs tab (must set the radio key value, not just index)
                        st.session_state.inside_track_sub_tab_radio = "📋 All Jobs"
                        st.session_state.inside_track_tab = 0
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    elif selected_sub_tab == "🙋 Interested Agents":
        st.markdown("### Free Agents Interested in Partner Jobs")
        st.caption("When Free Agents click 'I'm Interested' on partner jobs, they appear here")

        # Load all interests
        interests = load_inside_track_interests()

        if not interests:
            st.info("📭 No interest yet. When Free Agents express interest in partner jobs, they'll appear here.")
        else:
            # Status filter
            status_filter = st.selectbox(
                "Filter by Status",
                options=["All", "new", "contacted", "applied", "hired", "declined"],
                index=0
            )

            filtered = interests if status_filter == "All" else [i for i in interests if i.get('status') == status_filter]

            st.markdown(f"**{len(filtered)} interested agents** (out of {len(interests)} total)")

            for interest in filtered:
                status = interest.get('status', 'new')
                status_emoji = {'new': '🆕', 'contacted': '📞', 'applied': '📝', 'hired': '🎉', 'declined': '❌'}.get(status, '❓')

                with st.expander(f"{status_emoji} **{interest.get('agent_name', 'Unknown')}** → {interest.get('job_title', 'Unknown Job')}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Agent:** {interest.get('agent_name', 'Unknown')}")
                        st.write(f"**Email:** {interest.get('agent_email', 'N/A')}")
                        st.write(f"**Phone:** {interest.get('agent_phone', 'N/A')}")

                    with col2:
                        st.write(f"**Job:** {interest.get('job_title', 'Unknown')}")
                        st.write(f"**Company:** {interest.get('company', 'Unknown')}")
                        st.write(f"**Market:** {interest.get('market', 'Unknown')}")

                    st.write(f"**Expressed Interest:** {interest.get('created_at', '')[:16] if interest.get('created_at') else 'Unknown'}")

                    if interest.get('coach_notes'):
                        st.info(f"**Notes:** {interest.get('coach_notes')}")

                    # Status update
                    st.markdown("---")
                    new_status = st.selectbox(
                        "Update Status",
                        options=["new", "contacted", "applied", "hired", "declined"],
                        index=["new", "contacted", "applied", "hired", "declined"].index(status) if status in ["new", "contacted", "applied", "hired", "declined"] else 0,
                        key=f"status_{interest['id']}"
                    )

                    new_notes = st.text_area(
                        "Coach Notes",
                        value=interest.get('coach_notes', ''),
                        key=f"notes_{interest['id']}",
                        placeholder="Add notes about this candidate..."
                    )

                    if st.button("💾 Save", key=f"save_{interest['id']}"):
                        success, msg = update_interest_status(interest['id'], new_status, new_notes)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)


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
        inner_tab_options = ["📦 Async Batches", "📄 CSV Classification"]
        
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
            
            # Enhanced batch creation form matching main search page
            with st.expander("➕ Create New Indeed Batch Schedule", expanded=True):
                st.caption("Schedule Indeed searches to run automatically on selected days. Uses the same parameters as the main search page.")

                with st.form("batch_scheduler"):
                    # Row 1: Location and Search Parameters (matches main search layout)
                    col1, col2, col3, col4 = st.columns([1.5, 1.5, 1, 1])

                    with col1:
                        batch_location_type = st.selectbox(
                            "📍 Location Type:",
                            ["Select Market", "Custom Location"],
                            help="Choose how to specify the search location"
                        )

                    with col2:
                        # Get markets from pipeline (same as main search)
                        try:
                            from pipeline_wrapper import StreamlitPipelineWrapper
                            pipeline = StreamlitPipelineWrapper()
                            markets = pipeline.get_markets()
                            batch_selected_markets = st.multiselect(
                                "Target Markets:",
                                markets,
                                help="Select one or multiple markets to search",
                                disabled=(batch_location_type == "Custom Location")
                            )
                            if batch_selected_markets:
                                if len(batch_selected_markets) == 1:
                                    batch_location = pipeline.get_market_location(batch_selected_markets[0])
                                else:
                                    # Multi-market: use first market for legacy location field
                                    batch_location = pipeline.get_market_location(batch_selected_markets[0])
                            else:
                                batch_location = "Houston, TX"
                        except Exception as e:
                            st.error(f"Could not load markets: {e}")
                            batch_selected_markets = ["Houston"]
                            batch_location = "Houston, TX"

                    with col3:
                        batch_custom_location = st.text_input(
                            "Custom Location:",
                            placeholder="e.g., 90210, Austin TX",
                            help="Enter ZIP code, city, or state (only used if Custom Location is selected)",
                            disabled=(batch_location_type == "Select Market")
                        )
                        if batch_location_type == "Custom Location" and batch_custom_location:
                            batch_location = batch_custom_location.strip()

                    with col4:
                        # Use same job limits as main search
                        job_limit_options = ["10 jobs", "50 jobs", "100 jobs", "250 jobs", "500 jobs"]
                        if check_coach_permission('can_access_full_mode'):
                            job_limit_options.append("1000 jobs")

                        batch_job_quantity = st.selectbox(
                            "📊 Job Quantity:",
                            job_limit_options,
                            index=2,  # default to 100 jobs
                            help="Number of jobs to analyze and classify"
                        )
                        # Map display to actual numbers
                        job_quantity_map = {"10 jobs": 10, "50 jobs": 50, "100 jobs": 100, "250 jobs": 250, "500 jobs": 500, "1000 jobs": 1000}
                        batch_job_limit = job_quantity_map[batch_job_quantity]

                    with col4:
                        batch_search_terms = st.text_input(
                            "🔍 Search Terms:",
                            value="CDL Driver No Experience",
                            help="Job search keywords. Use commas for multiple terms"
                        )

                    # Row 2: Search Filters (matches main search)
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        batch_search_radius = st.selectbox(
                            "📏 Search Radius:",
                            [25, 50, 100],
                            index=1,  # default to 50
                            help="Search radius in miles from target location"
                        )

                    with col2:
                        batch_exact_location = st.checkbox(
                            "📍 Use exact location only",
                            value=False,
                            help="Search only the specified city (radius=0)"
                        )
                        if batch_exact_location:
                            batch_search_radius = 0

                    with col3:
                        batch_no_experience = st.checkbox(
                            "📋 Indeed No Experience Filter",
                            value=True,
                            help="Filter for entry-level jobs on Indeed"
                        )

                    with col4:
                        batch_classifier_type = st.selectbox(
                            "🎯 Job Type:",
                            ["CDL Traditional", "Career Pathways"],
                            index=0,
                            help="Choose the job classification approach"
                        )

                    # Row 2.5: Additional Options
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        batch_force_fresh = st.checkbox(
                            "🔄 Force fresh classification",
                            value=False,
                            help="Bypass AI classification cache"
                        )

                    # Career Pathways specific options
                    if batch_classifier_type == "Career Pathways":
                        with col2:
                            batch_pathway_preferences = st.multiselect(
                                "🛤️ Career Pathways:",
                                ["cdl_pathway", "dock_to_driver", "internal_cdl_training",
                                 "warehouse_to_driver", "logistics_progression", "non_cdl_driving",
                                 "general_warehouse", "construction_apprentice"],
                                default=["cdl_pathway"],
                                help="Select preferred career pathways"
                            )
                    else:
                        batch_pathway_preferences = []

                    # Row 3: Scheduling Options
                    st.markdown("### 🗓️ Schedule Settings")
                    col1, col2, col3 = st.columns([1, 1, 2])

                    with col1:
                        batch_frequency = st.selectbox(
                            "Frequency:",
                            ["Once", "Daily", "Weekly"],
                            index=2,  # default to Weekly
                            help="How often to run this search"
                        )

                    with col2:
                        batch_time_str = st.text_input(
                            "Run Time (Central):",
                            value="02:00",
                            help="Time in Central Time Zone (CT/CST) - Format: HH:MM"
                        )
                        # Convert string to time object for compatibility
                        try:
                            batch_time = pd.Timestamp(batch_time_str).time()
                        except:
                            batch_time = pd.Timestamp("02:00").time()

                    with col3:
                        if batch_frequency == "Weekly":
                            st.write("**Days of Week to Run:**")
                            # Better UI for day selection with columns
                            day_cols = st.columns(7)
                            batch_days = []
                            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                            default_days = ["Mon", "Wed", "Fri"]

                            for i, day in enumerate(days):
                                with day_cols[i]:
                                    if st.checkbox(day, value=day in default_days, key=f"batch_day_{day}"):
                                        batch_days.append(day)
                        else:
                            batch_days = []
                    
                    # Submit buttons
                    col_save, col_run = st.columns(2)
                    with col_save:
                        submitted = st.form_submit_button("📅 Schedule Recurring Batch", width='stretch')
                    with col_run:
                        run_now = st.form_submit_button("🚀 Run Now", width='stretch', type="secondary")
                    
                    if submitted or run_now:
                        # Validate inputs first
                        if not batch_search_terms.strip():
                            st.error("❌ Please enter search terms")
                            st.stop()

                        if batch_location_type == "Custom Location" and not batch_custom_location.strip():
                            st.error("❌ Please enter a custom location")
                            st.stop()

                        # Only validate scheduling parameters for "Schedule Recurring Batch"
                        if submitted and batch_frequency == "Weekly" and not batch_days:
                            st.error("❌ Please select at least one day for weekly schedule")
                            st.stop()

                        # Create comprehensive job parameters matching main search page
                        search_params = {
                            # Core search parameters
                            'search_terms': batch_search_terms.strip(),
                            'location': batch_location,
                            'limit': batch_job_limit,

                            # Search filters (same as main search)
                            'search_radius': batch_search_radius,
                            'no_experience': batch_no_experience,
                            'force_fresh_classification': batch_force_fresh,

                            # Classification parameters
                            'classifier_type': batch_classifier_type,
                            'pathway_preferences': batch_pathway_preferences if batch_classifier_type == "Career Pathways" else [],

                            # Pipeline parameters
                            'coach_username': coach.username,
                            'coach_name': coach.full_name,
                            'mode': {10: 'test', 50: 'mini', 100: 'sample', 250: 'medium', 500: 'large', 1000: 'full'}.get(batch_job_limit, 'sample'),

                            # Location metadata for tracking
                            'location_type': batch_location_type,
                            'selected_markets': batch_selected_markets if batch_location_type == "Select Market" else None,
                            'custom_location': batch_custom_location if batch_location_type == "Custom Location" else None,
                            'multi_market': len(batch_selected_markets) > 1 if batch_location_type == "Select Market" and batch_selected_markets else False,

                            # Additional flags
                            'exact_location': batch_exact_location,
                            'source_type': 'Indeed'  # Focus on Indeed only
                        }

                        # Only add scheduling metadata for "Schedule Recurring Batch" (not Run Now)
                        if submitted:  # Schedule Recurring Batch
                            search_params.update({
                                'frequency': batch_frequency,
                                'time': batch_time.strftime('%H:%M'),  # Changed from 'scheduled_time' to 'time'
                                'days': batch_days if batch_frequency == "Weekly" else None,  # Changed from 'scheduled_days' to 'days'
                            })
                        else:  # Run Now - ignore scheduling
                            search_params.update({
                                'frequency': 'Once',  # Force to one-time execution
                                'time': None,
                                'days': None,
                            })

                        try:
                            from async_job_manager import AsyncJobManager
                            manager = AsyncJobManager()

                            if run_now:
                                # Create ONE batch for all markets (no per-market splitting)
                                search_params['run_immediately'] = True
                                job = manager.submit_indeed_search(search_params, coach.username)

                                markets = search_params.get('selected_markets', [])
                                market_count = len(markets) if markets else 1

                                st.success(f"🚀 Indeed batch running NOW!")
                                st.info(f"📋 Job ID: {job.id}")
                                if search_params.get('multi_market'):
                                    st.info(f"📍 Markets: {market_count} selected")
                                else:
                                    st.info(f"📍 Location: {batch_location}")
                                st.info(f"🔍 Terms: {batch_search_terms}")
                                st.info(f"🎯 Classifier: {batch_classifier_type}")
                                st.info(f"📊 Job Limit: {batch_job_limit}")
                                st.info("⚡ One-time execution (ignoring schedule settings)")

                            else:
                                # Schedule recurring batch - create scheduled job entry without immediate execution
                                search_params['run_immediately'] = False
                                search_params['status'] = 'scheduled'  # Mark as scheduled, not running

                                # Create ONE scheduled job for all markets (no per-market splitting)
                                try:
                                    # Create scheduled job with all selected markets
                                    job = manager.create_scheduled_job(search_params, coach.username)

                                    markets = search_params.get('selected_markets', [])
                                    market_count = len(markets) if markets else 1

                                    st.success(f"📅 Indeed recurring batch scheduled successfully!")
                                    st.info(f"📋 Schedule ID: {job.id}")
                                    if search_params.get('multi_market'):
                                        st.info(f"📍 Markets: {market_count} selected")
                                    else:
                                        st.info(f"📍 Location: {batch_location}")
                                    st.info(f"🔍 Terms: {batch_search_terms}")
                                    st.info(f"🎯 Classifier: {batch_classifier_type}")
                                    st.info(f"📅 Schedule: {batch_frequency}")
                                    if batch_frequency == "Weekly":
                                        st.info(f"🗓️ Days: {', '.join(batch_days)}")
                                    st.info(f"⏰ Time: {batch_time.strftime('%H:%M')} Central")
                                    st.info("🔮 Job will run at scheduled time - it has NOT been executed yet")

                                except Exception as e:
                                    # If create_scheduled_job fails, show error message
                                    st.error(f"❌ Scheduling failed: {str(e)}")

                            st.rerun()  # Refresh to show the job in table

                        except Exception as e:
                            st.error(f"❌ Failed to create batch: {e}")
                            st.error(f"Error details: {str(e)}")

            # Google Batch Schedule Section
            with st.expander("➕ Create New Google Batch Schedule", expanded=False):
                st.caption("Schedule Google Jobs searches to run automatically on selected days. Uses the same parameters as the main search page.")

                # Check Google Jobs permission
                if not check_coach_permission('can_access_google_jobs'):
                    st.error("❌ You don't have permission to access Google Jobs batches")
                else:
                    with st.form("google_batch_scheduler"):
                        st.markdown("**Google Jobs Batch Configuration**")

                        # Row 1: Location
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            google_location_type = st.selectbox(
                                "📍 Location Type:",
                                ["Select Market", "Custom Location"],
                                help="Choose from predefined markets or enter custom location",
                                key="google_location_type"
                            )

                        with col2:
                            from market_mapper import MarketMapper
                            mapper = MarketMapper()
                            markets = mapper.get_all_markets()
                            google_selected_market = st.selectbox(
                                "🎯 Select Market:",
                                markets,
                                index=markets.index('Dallas') if 'Dallas' in markets else 0,
                                key="google_selected_market",
                                disabled=(google_location_type == "Custom Location")
                            )
                            if google_location_type == "Select Market":
                                google_location = google_selected_market
                                google_custom_location = None

                        with col3:
                            google_custom_location = st.text_input(
                                "🌍 Custom Location:",
                                value="Dallas, TX",
                                help="Enter city, state (e.g., 'Phoenix, AZ')",
                                key="google_custom_location",
                                disabled=(google_location_type == "Select Market")
                            )
                            if google_location_type == "Custom Location":
                                google_location = google_custom_location
                                google_selected_market = None

                        # Row 1b: Search parameters
                        col1, col2 = st.columns(2)

                        with col1:
                            google_search_terms = st.text_input(
                                "🔍 Search Terms:",
                                value="CDL Driver No Experience",
                                help="Job search keywords. Use commas for multiple terms",
                                key="google_search_terms"
                            )

                        with col2:
                            google_job_quantity = st.selectbox(
                                "📊 Job Limit:",
                                ["100 jobs", "250 jobs", "500 jobs", "1000 jobs"],
                                index=2,  # default to 500
                                help="Number of jobs to fetch per search",
                                key="google_job_quantity"
                            )
                            job_quantity_map = {"100 jobs": 100, "250 jobs": 250, "500 jobs": 500, "1000 jobs": 1000}
                            google_job_limit = job_quantity_map[google_job_quantity]

                        # Row 2: Search Filters
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            google_search_radius = st.selectbox(
                                "📏 Search Radius:",
                                [25, 50, 100],
                                index=1,  # default to 50
                                help="Search radius in miles from target location",
                                key="google_search_radius"
                            )

                        with col2:
                            google_exact_location = st.checkbox(
                                "📍 Use exact location only",
                                value=False,
                                help="Search only the specified city (radius=0)",
                                key="google_exact_location"
                            )
                            if google_exact_location:
                                google_search_radius = 0

                        with col3:
                            google_no_experience = st.checkbox(
                                "📋 Google No Experience Filter",
                                value=True,
                                help="Add 'No Experience' to search terms for Google",
                                key="google_no_experience"
                            )

                        with col4:
                            google_force_fresh = False
                            if check_coach_permission('can_force_fresh_classification'):
                                google_force_fresh = st.checkbox(
                                    "⚡ Force Fresh Classification",
                                    value=False,
                                    help="Re-run AI classification (admin only)",
                                    key="google_force_fresh"
                                )

                        # Row 3: Classification Settings
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            google_classifier_type = st.selectbox(
                                "🎯 Classifier Type:",
                                ["CDL Traditional", "Career Pathways"],
                                index=0,
                                help="Choose classification system",
                                key="google_classifier_type"
                            )

                        with col2:
                            google_pathway_preferences = []
                            if google_classifier_type == "Career Pathways":
                                google_pathway_preferences = st.multiselect(
                                    "🛤️ Pathway Preferences:",
                                    ["dock_to_driver", "internal_cdl_training", "warehouse_to_driver", "logistics_progression", "non_cdl_driving"],
                                    default=[],
                                    help="Filter for specific career pathways",
                                    key="google_pathway_preferences"
                                )

                        # Row 4: Schedule Settings
                        st.markdown("**Schedule Configuration**")
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            google_frequency = st.selectbox(
                                "Frequency:",
                                ["Once", "Daily", "Weekly"],
                                index=2,  # default to Weekly
                                help="How often to run this search",
                                key="google_frequency"
                            )

                        with col2:
                            google_time_str = st.text_input(
                                "Run Time (Central):",
                                value="02:30",
                                help="Time in Central Time Zone (CT/CST) - Format: HH:MM",
                                key="google_time"
                            )
                            # Convert string to time object for compatibility
                            try:
                                google_time = pd.Timestamp(google_time_str).time()
                            except:
                                google_time = pd.Timestamp("02:30").time()

                        with col3:
                            if google_frequency == "Weekly":
                                st.write("**Days of Week to Run:**")
                                day_cols = st.columns(7)
                                google_days = []
                                days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                                default_days = ["Tue", "Thu", "Sat"]  # Different from Indeed

                                for i, day in enumerate(days):
                                    with day_cols[i]:
                                        if st.checkbox(day, value=day in default_days, key=f"google_batch_day_{day}"):
                                            google_days.append(day)
                            else:
                                google_days = None

                        # Submit buttons
                        col_save, col_run = st.columns(2)
                        with col_save:
                            google_submitted = st.form_submit_button("📅 Schedule Recurring Batch", width='stretch')
                        with col_run:
                            google_run_now = st.form_submit_button("⚡ Schedule One-Off Batch", width='stretch', type="secondary")

                        if google_submitted or google_run_now:
                            # Validation
                            if not google_search_terms.strip():
                                st.error("❌ Please enter search terms")
                                st.stop()

                            if not google_location:
                                st.error("❌ Please specify a location")
                                st.stop()

                            # Only validate scheduling parameters for "Schedule Recurring Batch"
                            if google_submitted and google_frequency == "Weekly" and not google_days:
                                st.error("❌ Please select at least one day for weekly schedule")
                                st.stop()

                            # Handle "No Experience" search term modification for Google
                            final_search_terms = google_search_terms.strip()
                            if google_no_experience and "no experience" not in final_search_terms.lower():
                                final_search_terms += " No Experience"

                            # Create search parameters for Google Jobs
                            google_search_params = {
                                # Core search parameters
                                'search_terms': final_search_terms,
                                'location': google_location,
                                'limit': google_job_limit,

                                # Search filters
                                'search_radius': google_search_radius,
                                'no_experience': google_no_experience,
                                'force_fresh_classification': google_force_fresh,

                                # Classification parameters
                                'classifier_type': "pathway" if google_classifier_type == "Career Pathways" else "cdl",
                                'pathway_preferences': google_pathway_preferences if google_classifier_type == "Career Pathways" else [],

                                # Pipeline parameters
                                'coach_username': coach.username,
                                'coach_name': coach.full_name,
                                'mode': {100: 'sample', 250: 'medium', 500: 'large', 1000: 'full'}.get(google_job_limit, 'large'),

                                # Location metadata
                                'location_type': google_location_type,
                                'selected_market': google_selected_market if google_location_type == "Select Market" else None,
                                'custom_location': google_custom_location if google_location_type == "Custom Location" else None,

                                # Source type
                                'exact_location': google_exact_location,
                                'source_type': 'Google Jobs'
                            }

                            # Only add scheduling metadata for "Schedule Recurring Batch" (not Run Now)
                            if google_submitted:  # Schedule Recurring Batch
                                google_search_params.update({
                                    'frequency': google_frequency,
                                    'time': google_time.strftime('%H:%M'),  # Changed from 'scheduled_time' to 'time'
                                    'days': google_days if google_frequency == "Weekly" else None,  # Changed from 'scheduled_days' to 'days'
                                })
                            else:  # Run Now - ignore scheduling
                                google_search_params.update({
                                    'frequency': 'Once',  # Force to one-time execution
                                    'time': None,
                                    'days': None,
                                })

                            try:
                                from async_job_manager import AsyncJobManager
                                google_manager = AsyncJobManager()

                                if google_run_now:
                                    # Run immediately - submit the job for immediate execution
                                    google_search_params['run_immediately'] = True
                                    job = google_manager.submit_google_search(google_search_params, coach.username)

                                    st.success(f"🚀 Google Jobs batch running NOW!")
                                    st.info(f"📋 Job ID: {job.id}")
                                    st.info(f"⏱️ Processing time: ~2-5 minutes for async completion.")
                                    st.info(f"📊 Search: {google_job_limit} jobs | {google_location} | '{final_search_terms}'")
                                    st.info("⚡ One-time execution (ignoring schedule settings)")

                                    # Rerun to show updated table
                                    st.rerun()

                                if google_submitted:
                                    # Schedule recurring batch - create scheduled job entry without immediate execution
                                    google_search_params['run_immediately'] = False
                                    google_search_params['status'] = 'scheduled'
                                    google_search_params['job_type'] = 'google_jobs'

                                    try:
                                        # Create scheduled job
                                        job = google_manager.create_scheduled_job(google_search_params, coach.username)

                                        st.success(f"📅 Google Jobs recurring batch scheduled successfully!")
                                        st.info(f"📋 Schedule ID: {job.id}")
                                        st.info(f"📍 Location: {google_location}")
                                        st.info(f"🔍 Terms: {final_search_terms}")
                                        st.info(f"📅 Schedule: {google_frequency}")
                                        if google_frequency == "Weekly":
                                            st.info(f"🗓️ Days: {', '.join(google_days)}")
                                        st.info(f"⏰ Time: {google_time.strftime('%H:%M')} Central")
                                        st.info("🔮 Job will run at scheduled time - it has NOT been executed yet")

                                    except Exception as e:
                                        # If create_scheduled_job fails, fall back to old method
                                        st.warning(f"⚠️ Google Jobs scheduling failed ({str(e)}), running immediately as fallback")
                                        google_search_params['run_immediately'] = True
                                        job = google_manager.submit_google_search(google_search_params, coach.username)

                                        st.info(f"📋 Job ID: {job.id} (Note: Run immediately due to scheduling error)")
                                        st.info(f"📍 Location: {google_location}")
                                        st.info(f"🎯 Terms: {final_search_terms}")

                                    st.rerun()  # Refresh to show the job in table

                            except Exception as e:
                                st.error(f"❌ Failed to create Google batch: {e}")
                                st.error(f"Error details: {str(e)}")

            # DriverPulse Batch Schedule Section
            with st.expander("➕ Create New DriverPulse Batch Schedule", expanded=False):
                st.caption("Schedule DriverPulse searches to run automatically on selected days. Filters jobs to target markets after scraping.")

                # Check for required DriverPulse credentials
                required_vars = ['DRIVER_PULSE_EMAIL', 'DRIVER_PULSE_FIRST_NAME', 'DRIVER_PULSE_LAST_NAME', 'DRIVER_PULSE_PHONE']
                missing_vars = [var for var in required_vars if not os.getenv(var)]

                if missing_vars:
                    st.error(f"❌ Missing DriverPulse credentials: {', '.join(missing_vars)}")
                    st.info("💡 Set these environment variables to use DriverPulse batch scheduling")
                else:
                    with st.form("driverpulse_batch_scheduler"):
                        st.markdown("**DriverPulse Batch Configuration**")

                        # Row 1: Search Term and Filter Mode
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            dp_batch_search_term = st.text_input(
                                "🔍 Search Term:",
                                value="CDL driver",
                                help="Keywords to search in DriverPulse (e.g., 'CDL driver', 'truck driver', 'no experience')",
                                key="dp_batch_search_term"
                            )

                        with col2:
                            dp_batch_filter_mode = st.selectbox(
                                "📍 Filter Mode:",
                                ["All FreeWorld Markets", "Custom ZIP Codes"],
                                index=0,
                                help="Choose whether to filter to all markets or specific ZIPs",
                                key="dp_batch_filter_mode"
                            )

                        with col3:
                            dp_batch_classifier_type = st.selectbox(
                                "🧠 AI Classifier:",
                                ["CDL Job Classifier", "Pathway Classifier", "Both (CDL + Pathway)", "None (No AI)"],
                                index=0,
                                help="Choose which AI classifier to run",
                                key="dp_batch_classifier_type"
                            )

                        # Row 2: Custom ZIP codes (always show but disable when not selected)
                        dp_batch_custom_zips = st.text_area(
                            "📍 Custom ZIP Codes (comma-separated):",
                            placeholder="e.g., 75060, 77007, 85009, 80218",
                            help="Enter one or more ZIP codes separated by commas (only used if Custom ZIP Codes filter mode is selected)",
                            key="dp_batch_custom_zips",
                            height=100,
                            disabled=(dp_batch_filter_mode != "Custom ZIP Codes")
                        )

                        if dp_batch_filter_mode == "Custom ZIP Codes":
                            if dp_batch_custom_zips:
                                zip_list = [z.strip() for z in dp_batch_custom_zips.split(',') if z.strip()]
                                st.success(f"📍 Will filter to {len(zip_list)} ZIP code(s): {', '.join(zip_list[:5])}{' ...' if len(zip_list) > 5 else ''}")
                            else:
                                st.warning("👆 Please enter ZIP codes above")
                        else:
                            st.info("✅ Will filter to all FreeWorld market locations (6,710 ZIPs)")
                            dp_batch_custom_zips = None

                        # Row 3: Schedule Settings
                        st.markdown("**Schedule Configuration**")
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            dp_batch_frequency = st.selectbox(
                                "Frequency:",
                                ["Once", "Daily", "Weekly"],
                                index=2,  # default to Weekly
                                help="How often to run this search",
                                key="dp_batch_frequency"
                            )

                        with col2:
                            dp_batch_time_str = st.text_input(
                                "Run Time (Central):",
                                value="03:00",
                                help="Time in Central Time Zone (CT/CST) - Format: HH:MM",
                                key="dp_batch_time"
                            )
                            # Convert string to time object for compatibility
                            try:
                                dp_batch_time = pd.Timestamp(dp_batch_time_str).time()
                            except:
                                dp_batch_time = pd.Timestamp("03:00").time()

                        with col3:
                            if dp_batch_frequency == "Weekly":
                                st.write("**Days of Week to Run:**")
                                day_cols = st.columns(7)
                                dp_batch_days = []
                                days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                                default_days = ["Mon", "Thu"]  # Different from Indeed/Google

                                for i, day in enumerate(days):
                                    with day_cols[i]:
                                        if st.checkbox(day, value=day in default_days, key=f"dp_batch_day_{day}"):
                                            dp_batch_days.append(day)
                            else:
                                dp_batch_days = None

                        # Submit buttons
                        col_save, col_run = st.columns(2)
                        with col_save:
                            dp_submitted = st.form_submit_button("📅 Schedule Recurring Batch", width='stretch')
                        with col_run:
                            dp_run_now = st.form_submit_button("⚡ Schedule One-Off Batch", width='stretch', type="secondary")

                        if dp_submitted or dp_run_now:
                            # Validation
                            if not dp_batch_search_term.strip():
                                st.error("❌ Please enter a search term")
                                st.stop()

                            # Validate custom ZIPs if selected
                            if dp_batch_filter_mode == "Custom ZIP Codes":
                                if not dp_batch_custom_zips or not dp_batch_custom_zips.strip():
                                    st.error("❌ Please enter at least one ZIP code for custom mode")
                                    st.stop()
                                target_zips = [z.strip().zfill(5) for z in dp_batch_custom_zips.split(',') if z.strip()]
                                if not target_zips:
                                    st.error("❌ No valid ZIP codes found")
                                    st.stop()
                            else:
                                target_zips = None

                            # Only validate scheduling parameters for "Schedule Recurring Batch"
                            if dp_submitted and dp_batch_frequency == "Weekly" and not dp_batch_days:
                                st.error("❌ Please select at least one day for weekly schedule")
                                st.stop()

                            # Create search parameters for DriverPulse
                            dp_search_params = {
                                # Core search parameters
                                'search_terms': dp_batch_search_term.strip(),

                                # Filter settings (nested object for DriverPulse adapter)
                                'filter_settings': {
                                    'search_term': dp_batch_search_term.strip(),
                                    'classifier_type': dp_batch_classifier_type,
                                    'filter_mode': 'custom_zips' if dp_batch_filter_mode == "Custom ZIP Codes" else 'all_markets',
                                    'custom_zips': target_zips if dp_batch_filter_mode == "Custom ZIP Codes" else None
                                },

                                # Pipeline parameters
                                'coach_username': coach.username,
                                'coach_name': coach.full_name,

                                # Source type
                                'source_type': 'DriverPulse'
                            }

                            # Only add scheduling metadata for "Schedule Recurring Batch" (not Run Now)
                            if dp_submitted:  # Schedule Recurring Batch
                                dp_search_params.update({
                                    'frequency': dp_batch_frequency,
                                    'time': dp_batch_time.strftime('%H:%M'),  # Changed from 'scheduled_time' to 'time'
                                    'days': dp_batch_days if dp_batch_frequency == "Weekly" else None,  # Changed from 'scheduled_days' to 'days'
                                })
                            else:  # Run Now - ignore scheduling
                                dp_search_params.update({
                                    'frequency': 'Once',  # Force to one-time execution
                                    'time': None,
                                    'days': None,
                                })

                            try:
                                from async_job_manager import AsyncJobManager
                                from github_actions_helper import refresh_auth_and_wait, get_auth_age
                                dp_manager = AsyncJobManager()

                                print(f"🔍 DEBUG: dp_run_now = {dp_run_now}, dp_submitted = {dp_submitted}")

                                if dp_run_now:
                                    # Schedule one-off batch via GitHub Actions
                                    # This ensures auth and scraping happen from same IP

                                    # Create job in queue
                                    from datetime import datetime, timezone
                                    job = dp_manager.submit_driver_pulse_search(dp_search_params, coach.username)

                                    # Trigger GitHub Actions workflow
                                    try:
                                        import requests
                                        github_token = st.secrets.get("GITHUB_TOKEN")
                                        repo_owner = st.secrets.get("GITHUB_REPO_OWNER", "hazeltr0n")
                                        repo_name = st.secrets.get("GITHUB_REPO_NAME", "freeworld-success-coach-portal")

                                        if not github_token:
                                            st.error("❌ GITHUB_TOKEN not configured")
                                            st.stop()

                                        # Trigger workflow
                                        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/run_driverpulse_job.yml/dispatches"
                                        headers = {
                                            "Authorization": f"Bearer {github_token}",
                                            "Accept": "application/vnd.github+json",
                                            "X-GitHub-Api-Version": "2022-11-28"
                                        }
                                        payload = {
                                            "ref": "main",
                                            "inputs": {
                                                "job_id": str(job.id)
                                            }
                                        }

                                        response = requests.post(url, headers=headers, json=payload)

                                        if response.status_code == 204:
                                            st.success(f"✅ Batch scheduled to run immediately!")
                                            st.info(f"📋 Job ID: {job.id}")
                                            st.info(f"🔍 Search: '{dp_batch_search_term}' | Filter: {dp_batch_filter_mode}")
                                            if dp_batch_filter_mode == "Custom ZIP Codes":
                                                st.info(f"📍 Target ZIPs: {len(target_zips)} ZIP codes")
                                            else:
                                                st.info(f"📍 Target: All FreeWorld Markets (6,710 ZIPs)")
                                            st.info(f"🧠 Classifier: {dp_batch_classifier_type}")
                                            st.info("⏳ Check the queue below for status updates")
                                        else:
                                            st.error(f"❌ Failed to trigger workflow: {response.status_code}")
                                            st.error(response.text)

                                    except Exception as e:
                                        st.error(f"❌ Error triggering workflow: {e}")
                                        st.stop()

                                    # Rerun to show updated table
                                    st.rerun()

                                if dp_submitted:
                                    # Schedule recurring batch - create scheduled job entry without immediate execution
                                    dp_search_params['run_immediately'] = False
                                    dp_search_params['status'] = 'scheduled'
                                    dp_search_params['job_type'] = 'driver_pulse_jobs'

                                    try:
                                        # Create scheduled job
                                        job = dp_manager.create_scheduled_job(dp_search_params, coach.username)

                                        # Rerun immediately to refresh the table - success message will show after rerun
                                        st.rerun()

                                    except Exception as e:
                                        # If create_scheduled_job fails, show error
                                        st.error(f"❌ DriverPulse scheduling failed: {str(e)}")
                                        st.info("💡 Check the logs for more details")

                            except Exception as e:
                                st.error(f"❌ Failed to create DriverPulse batch: {e}")
                                st.error(f"Error details: {str(e)}")

            # Scheduled batches table
            st.markdown("### 📊 Scheduled Batches Table")
            show_simple_batch_table(coach)

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
                classifier_type = st.selectbox("Classifier Type", ["cdl", "pathway"], index=0,
                                             help="CDL: Traditional CDL driver jobs | Pathway: Career pathway opportunities")
            with colR:
                st.caption("This path classifies CSV jobs and stores them to Supabase memory database with tracking URLs. No PDFs generated. Choose classifier type: CDL for driver jobs, Pathway for career progression analysis.")
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

                    def extract_url_from_json_or_string(value):
                        """Extract first URL from JSON array or return string directly"""
                        if not value or value == '':
                            return ''

                        try:
                            # If it's already a simple URL string, return it
                            if isinstance(value, str) and value.startswith('http'):
                                return value

                            # Try to parse as JSON array
                            import json
                            if isinstance(value, str):
                                url_data = json.loads(value)
                            else:
                                return str(value)

                            if url_data and len(url_data) > 0:
                                # Handle simple string arrays
                                if isinstance(url_data[0], str):
                                    return url_data[0]

                                # Handle URL objects with apply_url: or apply_url
                                if isinstance(url_data[0], dict):
                                    url = url_data[0].get('apply_url:', '') or url_data[0].get('apply_url', '')
                                    return url if url else ''

                            return ''
                        except:
                            return str(value) if value else ''

                    for _, row in df_src.iterrows():
                        title = first(row, ["title", "job_title", "job"], "")
                        company = first(row, ["company", "company_name", "employer"], "")
                        location_raw = first(row, ["formattedLocation", "location", "city", "job_location"], "")
                        # Prefer concrete apply URL - now with JSON support
                        raw_apply_url = first(row, ["viewJobLink", "apply_url", "apply_urls", "applyUrl", "url", "link"], "")
                        apply_url = extract_url_from_json_or_string(raw_apply_url)
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
                    # Use chosen market as search location for foreign language normalization
                    search_location = MARKET_TO_LOCATION.get(chosen_market, chosen_market)
                    # Determine source based on radio button selection
                    csv_source = 'google' if source_type == "Outscraper (Google)" else 'indeed'
                    df_ing = transform_ingest_outscraper(raw_rows, pipe.run_id, search_location, source=csv_source) if raw_rows else ensure_schema(pd.DataFrame())
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
                    classifier_emoji = "🎯" if classifier_type == "pathway" else "🚛"
                    classifier_name = "Pathway Classifier" if classifier_type == "pathway" else "CDL Classifier"
                    st.info(f"🤖 Classifying with AI using {classifier_emoji} {classifier_name}…")
                    df_ai = pipe._stage5_ai_classification(df_dedup, force_fresh_classification=False, classifier_type=classifier_type)
                    try:
                        st.write("🔎 Match breakdown:", df_ai['ai.match'].value_counts().to_dict())
                        if classifier_type == "pathway" and 'ai.career_pathway' in df_ai.columns:
                            pathway_counts = df_ai['ai.career_pathway'].value_counts().to_dict()
                            st.write("🎯 Career pathway breakdown:", pathway_counts)
                    except Exception:
                        pass
                    st.info("🧭 Deriving route types and routing…")
                    
                    # Debug: Check AI classification before routing
                    print(f"🔍 DEBUG: Before routing - AI match counts: {df_ai['ai.match'].value_counts().to_dict() if 'ai.match' in df_ai.columns else 'No ai.match column'}")
                    
                    df_route = pipe._stage5_5_route_rules(df_ai)
                    df_final = pipe._stage6_routing(df_route, 'both')
                    
                    # Apply final schema enforcement to set route.final_status for quality jobs
                    df_final = ensure_schema(df_final)
                    
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
                            # Only generate tracking URLs for included jobs (good/so-so matches that aren't filtered)
                            included_jobs_mask = (
                                (df_final.get('route.filtered', True) == False) &  # Not filtered out
                                (df_final.get('route.final_status', '').astype(str).str.startswith('included'))  # Status starts with 'included'
                            )
                            included_jobs = df_final[included_jobs_mask]
                            st.info(f"🎯 Filtering to {len(included_jobs)} included jobs from {len(df_final)} total classified jobs")

                            jobs_without_tracking = included_jobs[included_jobs.get('meta.tracked_url', '').fillna('') == '']
                            if len(jobs_without_tracking) > 0:
                                st.info(f"🔗 Generating tracking URLs for {len(jobs_without_tracking)} included jobs...")
                                
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

                                        # Generate edge function URL for click tracking (no Short.io)
                                        tracked_url = link_tracker.generate_edge_function_url(
                                            original_url,
                                            candidate_id=None,
                                            tags=tags
                                        )

                                        if tracked_url:
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
                        
                        # Upload ALL classified jobs to Supabase (good/so-so/bad) for complete analytics and memory
                        # This matches the behavior of view_fresh_quality() in canonical_transforms.py
                        if 'ai.match' in df_final.columns:
                            supabase_jobs = df_final[
                                df_final['ai.match'].astype(str).isin(['good', 'so-so', 'bad'])
                            ].copy()
                        else:
                            # Fallback if no AI classification column
                            supabase_jobs = df_final.copy()

                        if len(supabase_jobs) == 0:
                            st.info("ℹ️ No jobs qualified for Supabase storage (must have AI classification: good/so-so/bad)")
                        else:
                            # Run QC validation (non-strict mode for CSV - we want to store data but show warnings)
                            df_validated, qc_report = validate_jobs_for_upload(supabase_jobs, strict_mode=False)
                            
                            st.text(qc_report)
                            
                            # QC is now REPORT-ONLY mode - always proceed to upload all jobs
                            # Store validated jobs to Supabase directly (same as classify_csv.py)
                            st.info(f"💾 Storing {len(df_validated)} QC-validated jobs to Supabase...")
                            from job_memory_db import JobMemoryDB
                            from jobs_schema import prepare_for_supabase

                            # Transform to Supabase format (filters out extra columns like search.*, qa.*)
                            df_supabase = prepare_for_supabase(df_validated)

                            memory_db = JobMemoryDB()
                            success = memory_db.store_classifications(df_supabase)
                            error_count = (df_validated.get('ai.match', '') == 'error').sum() if 'ai.match' in df_validated.columns else 0

                            if success:
                                if error_count > 0:
                                    st.success(f"✅ Stored {len(df_validated)} QC-validated jobs to Supabase ({error_count} had classification errors)")
                                else:
                                    st.success(f"✅ Stored {len(df_validated)} QC-validated jobs to Supabase with tracking URLs")

                                # Show data quality summary
                                rejected_count = len(supabase_jobs) - len(df_validated)
                                unclassified_count = len(df_final) - len(supabase_jobs)
                                if rejected_count > 0:
                                    st.info(f"📊 QC Summary: {rejected_count} jobs had quality issues but were stored with warnings")
                                if unclassified_count > 0:
                                    st.info(f"📊 Classification Summary: {unclassified_count} jobs skipped (no AI classification)")
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

                                render_download_button(
                                    data=csv_buffer,
                                    label="📥 Download Full Classified Data (All Markets)",
                                    filename=filename,
                                    mime_type="text/csv"
                                )
                                st.caption("Download complete classified DataFrame with all jobs from all markets (includes filtered jobs for analysis)")
                                
                                # Show CSV stats
                                total_csv_jobs = len(df_final)
                                included_csv_jobs = int((df_final['route.final_status'].astype(str).str.startswith('included')).sum()) if 'route.final_status' in df_final.columns else 0
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
                                    included_jobs = int(df_final['route.final_status'].astype(str).str.startswith('included').sum())
                                    filtered_jobs = int(df_final['route.final_status'].astype(str).str.startswith('filtered').sum())
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
                        st.dataframe(df_final, height=420)

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
                                            cols_pref = ['source.title', 'source.company', 'ai.match', 'ai.route_type', 'ai.career_pathway', 'ai.training_provided', 'ai.fair_chance', 'ai.summary', 'source.indeed_url']
                                            cols_show = [c for c in cols_pref if c in mdf_inc.columns]
                                            st.dataframe(mdf_inc[cols_show] if cols_show else mdf_inc, height=360)

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
                                                st.dataframe(mdf, height=480)
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
        
        # Debug: Check if AsyncJobManager is properly initialized
        st.write(f"🔍 AsyncJobManager initialized: {async_manager is not None}")
        st.write(f"🔍 Supabase client available: {async_manager.supabase_client is not None}")
        
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
                            render_download_button(
                                data=csv_data,
                                label="📥 CSV",
                                filename=csv_filename,
                                mime_type='text/csv',
                                key=f"csv_{job.id}"
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
                            render_download_button(
                                data=parquet_data,
                                label="📦 PQ",
                                filename=f"batch_{job.id}_results.parquet",
                                mime_type='application/octet-stream',
                                key=f"parquet_{job.id}"
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
    """Scheduled Batches Table with full batch management functionality"""
    try:
        from async_job_manager import AsyncJobManager
        from datetime import datetime, timedelta
        import pandas as pd
        from job_memory_db import JobMemoryDB
        import io

        manager = AsyncJobManager()
        memory_db = JobMemoryDB()

        # Get all jobs for this coach using the available methods
        pending_jobs = manager.get_pending_jobs(None if coach.role == 'admin' else coach.username)
        completed_jobs = manager.get_completed_jobs(None if coach.role == 'admin' else coach.username)
        failed_jobs = manager.get_failed_jobs(None if coach.role == 'admin' else coach.username)
        retrieved_jobs = manager.get_retrieved_jobs(None if coach.role == 'admin' else coach.username)
        scheduled_jobs = manager.get_scheduled_jobs(None if coach.role == 'admin' else coach.username)

        # Combine all job types
        all_jobs = pending_jobs + completed_jobs + failed_jobs + retrieved_jobs + scheduled_jobs

        if not all_jobs:
            st.info("📝 No batches found. Create your first batch above!")
            return

        # Radio button filter for batch type/status
        filter_option = st.radio(
            "Filter batches:",
            ["🔄 Recurring", "1️⃣ One-off", "✅ Completed", "❌ Failed", "📋 All"],
            horizontal=True,
            key="batch_filter_radio"
        )

        st.info("💡 **Batch Types**: One-off batches run once, Recurring batches run on schedule. All times shown in Central Time.")
        
        # Prepare table data with enhanced information
        table_data = []
        for job in all_jobs:
            # Calculate time since creation
            created_time = pd.to_datetime(job.created_at)
            time_since_creation = datetime.now() - created_time.replace(tzinfo=None)
            
            # Map database status to display status
            if job.status == 'submitted':
                if time_since_creation < timedelta(minutes=5):
                    display_status = "⏳ Scheduled"
                else:
                    display_status = "🔄 Processing"
            elif job.status == 'processing':
                display_status = "📥 Running"
            elif job.status == 'completed':
                display_status = "✅ Complete"
            elif job.status == 'failed':
                display_status = "❌ Failed"
            elif job.status == 'cancelled':
                display_status = "🚫 Cancelled"
            else:
                display_status = f"❓ {job.status}"
            
            # Get search parameters safely
            params = job.search_params if isinstance(job.search_params, dict) else {}
            search_terms = params.get('search_terms', 'Unknown')
            limit = params.get('limit', params.get('max_jobs', 'Unknown'))
            frequency = params.get('frequency', 'Once')

            # Determine location/market display
            if job.job_type in ['driver_pulse', 'driver_pulse_jobs']:
                # DriverPulse stores config in filter_settings
                filter_settings = params.get('filter_settings', {})
                filter_mode = filter_settings.get('filter_mode', 'all_markets')

                if filter_mode == 'custom_zips':
                    location = "Custom Location"
                else:
                    location = "All Markets"
            else:
                # Indeed/Google Jobs location handling
                selected_markets = params.get('selected_markets', [])
                if selected_markets:
                    # Multi-market or single market from market selection
                    location = selected_markets[0] if len(selected_markets) == 1 else "Multiple"
                elif params.get('location'):
                    # Custom location or fallback
                    location = params.get('location')
                else:
                    # No location data - show Custom Location instead of Unknown
                    location = "Custom Location"

            # Determine batch type
            batch_type = "🔄 Recurring" if frequency != "Once" else "1️⃣ One-off"
            
            # Apply filter
            should_include = False
            if filter_option == "📋 All":
                should_include = True
            elif filter_option == "🔄 Recurring":
                should_include = frequency != "Once"
            elif filter_option == "1️⃣ One-off":
                should_include = frequency == "Once"
            elif filter_option == "✅ Completed":
                should_include = display_status == "✅ Complete"
            elif filter_option == "❌ Failed":
                should_include = display_status == "❌ Failed"

            if should_include:
                # Determine source display name
                if job.job_type in ['driver_pulse', 'driver_pulse_jobs']:
                    source_display = 'DriverPulse'
                elif job.job_type == 'google_jobs':
                    source_display = 'Google Jobs'
                elif job.job_type == 'indeed_jobs':
                    source_display = 'Indeed'
                else:
                    source_display = job.job_type  # Fallback to raw job_type

                # Get run_id from search_params (stored as 'sys.run_id')
                run_id = params.get('sys.run_id', None)

                table_data.append({
                    'ID': job.id,
                    'Coach': job.coach_username,
                    'Type': batch_type,
                    'Source': source_display,
                    'Location': location,
                    'Terms': search_terms,
                    'Limit': limit,
                    'Status': display_status,
                    'Total Jobs': job.result_count or 0,
                    'Quality Jobs': job.quality_job_count or 0,
                    'Created': created_time.strftime('%m/%d %H:%M'),
                    'Frequency': frequency,
                    'run_id': run_id,  # Get run_id from search_params for downloading results
                    'job_obj': job  # Store full job object for actions
                })

        # Display count of filtered batches
        total_count = len(all_jobs)
        filtered_count = len(table_data)
        if filter_option != "📋 All":
            st.caption(f"Showing {filtered_count} of {total_count} total batches")

        # Group recurring batches by unique configuration
        if filter_option == "🔄 Recurring":
            # Group by recurring_batch_group_id to identify unique recurring batches
            from collections import defaultdict
            recurring_groups = defaultdict(list)

            for data in table_data:
                job_obj = data['job_obj']
                group_id = job_obj.recurring_batch_group_id if hasattr(job_obj, 'recurring_batch_group_id') else None

                # Only group if there's a valid group_id, otherwise use a unique fallback key
                if group_id:
                    key = group_id
                else:
                    # Fallback to old grouping for batches created before recurring_batch_group_id was added
                    key = f"legacy_{data['Location']}_{data['Terms']}_{data['Source']}_{data['Frequency']}"

                recurring_groups[key].append(data)

            st.caption(f"📊 {len(recurring_groups)} unique recurring batch configurations")

            # Display grouped recurring batches
            for group_key, runs in recurring_groups.items():
                # Sort runs by created date (newest first)
                runs = sorted(runs, key=lambda x: x['Created'], reverse=True)
                latest_run = runs[0]

                # Get display info from latest run
                location = latest_run['Location']
                terms = latest_run['Terms']
                source = latest_run['Source']
                frequency = latest_run['Frequency']

                with st.expander(f"🔄 **{source}** - {location} - {terms[:40]}{'...' if len(terms) > 40 else ''}", expanded=False):
                    # Header with edit button
                    header_cols = st.columns([3, 1])
                    with header_cols[0]:
                        st.markdown(f"**Schedule:** {frequency}")
                        if latest_run['Frequency'] == 'Weekly':
                            params = latest_run['job_obj'].search_params
                            days = params.get('scheduled_days', [])
                            time = params.get('scheduled_time', 'N/A')
                            st.caption(f"🗓️ {', '.join(days)} at {time}")

                    with header_cols[1]:
                        if st.button("✏️ Edit", key=f"edit_recurring_{latest_run['ID']}", help="Edit schedule settings"):
                            st.session_state[f'editing_batch_{latest_run["ID"]}'] = True
                            st.rerun()

                    # Show edit form if editing
                    if st.session_state.get(f'editing_batch_{latest_run["ID"]}', False):
                        st.markdown("#### Edit Schedule")
                        params = latest_run['job_obj'].search_params

                        col1, col2 = st.columns(2)
                        with col1:
                            new_frequency = st.selectbox(
                                "Frequency",
                                ["Weekly", "Daily", "Once"],
                                index=["Weekly", "Daily", "Once"].index(params.get('frequency', 'Weekly')),
                                key=f"freq_{latest_run['ID']}"
                            )

                        with col2:
                            new_time = st.time_input(
                                "Time",
                                value=datetime.strptime(params.get('scheduled_time', '09:00'), '%H:%M').time(),
                                key=f"time_{latest_run['ID']}"
                            )

                        if new_frequency == "Weekly":
                            new_days = st.multiselect(
                                "Days",
                                ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                                default=params.get('scheduled_days', []),
                                key=f"days_{latest_run['ID']}"
                            )

                        save_col, cancel_col = st.columns(2)
                        with save_col:
                            if st.button("💾 Save", key=f"save_{latest_run['ID']}"):
                                # Update search_params in database
                                updated_params = params.copy()
                                updated_params['frequency'] = new_frequency
                                updated_params['scheduled_time'] = new_time.strftime('%H:%M')
                                if new_frequency == "Weekly":
                                    updated_params['scheduled_days'] = new_days

                                # Update the job in database
                                manager.supabase_client.table('async_job_queue').update({
                                    'search_params': updated_params
                                }).eq('id', latest_run['ID']).execute()

                                st.success("✅ Schedule updated")
                                st.session_state[f'editing_batch_{latest_run["ID"]}'] = False
                                st.rerun()

                        with cancel_col:
                            if st.button("❌ Cancel", key=f"cancel_edit_{latest_run['ID']}"):
                                st.session_state[f'editing_batch_{latest_run["ID"]}'] = False
                                st.rerun()

                    # Separate upcoming runs from past runs
                    scheduled_runs = [r for r in runs if '⏰' in r['Status'] or '📋' in r['Status']]
                    past_runs = [r for r in runs if '✅' in r['Status'] or '❌' in r['Status'] or '🔄' in r['Status']]

                    # Show next scheduled run
                    if scheduled_runs:
                        st.markdown("**📅 Next Scheduled Run**")
                        next_run = scheduled_runs[0]
                        next_run_obj = next_run['job_obj']
                        scheduled_run_at = next_run_obj.scheduled_run_at

                        if scheduled_run_at:
                            from datetime import datetime, timezone
                            if isinstance(scheduled_run_at, str):
                                scheduled_dt = datetime.fromisoformat(scheduled_run_at.replace('Z', '+00:00'))
                            else:
                                scheduled_dt = scheduled_run_at

                            now = datetime.now(timezone.utc)
                            time_until = scheduled_dt - now
                            hours_until = time_until.total_seconds() / 3600

                            if hours_until > 24:
                                time_str = f"in {int(hours_until / 24)} days"
                            elif hours_until > 1:
                                time_str = f"in {int(hours_until)} hours"
                            elif hours_until > 0:
                                time_str = f"in {int(hours_until * 60)} minutes"
                            else:
                                time_str = "overdue (will run at top of next hour)"

                            st.info(f"⏰ Batch #{next_run['ID']} scheduled for {scheduled_dt.strftime('%m/%d %H:%M UTC')} ({time_str})")
                        else:
                            st.caption(f"Batch #{next_run['ID']} - {next_run['Status']}")

                    # Show past runs
                    if past_runs:
                        st.markdown(f"**📊 Past Runs** ({len(past_runs)} completed)")
                        for run in past_runs[:5]:  # Show last 5 past runs
                            run_cols = st.columns([2, 2, 1])
                            with run_cols[0]:
                                st.caption(f"Run #{run['ID']} - {run['Created']}")
                            with run_cols[1]:
                                st.caption(f"{run['Status']} - {run['Total Jobs']} jobs ({run['Quality Jobs']} quality)")
                            with run_cols[2]:
                                if "Complete" in run['Status'] and run.get('run_id'):
                                    if st.button("📥", key=f"dl_hist_{run['ID']}", help="Download"):
                                        jobs_df = memory_db.query_jobs_by_run_id(run['run_id'])
                                        if not jobs_df.empty:
                                            csv_buffer = io.StringIO()
                                            jobs_df.to_csv(csv_buffer, index=False)
                                            st.download_button(
                                                "💾 CSV",
                                                csv_buffer.getvalue(),
                                                f"batch_{run['ID']}.csv",
                                                "text/csv",
                                                key=f"dl_btn_hist_{run['ID']}"
                                            )

                        if len(past_runs) > 5:
                            st.caption(f"... and {len(past_runs) - 5} more past runs")

                    if not scheduled_runs and not past_runs:
                        st.caption("No runs yet")

        # Display enhanced table with better management - RESPONSIVE DESIGN
        elif table_data:
            # Mobile-friendly responsive table with grouped information
            for data in table_data:
                job_id = data['ID']
                status = data['Status']
                job = data['job_obj']

                # Card-based layout for better mobile experience
                with st.container():
                    # Header row: ID, Status, Actions
                    header_row = st.columns([1.5, 2, 1.5])

                    with header_row[0]:
                        st.markdown(f"**Batch #{job_id}**")
                        st.caption(f"{data['Coach']} • {data['Created']}")

                    with header_row[1]:
                        # Enhanced status display with more details
                        if "Failed" in status and job.error_message:
                            st.error(f"❌ Failed")
                            with st.expander("Error Details", expanded=False):
                                st.text(job.error_message)
                        elif "Complete" in status:
                            if job.result_count and job.result_count > 0:
                                st.success(f"✅ Success ({job.result_count} jobs)")
                            else:
                                st.warning("⚠️ Completed (0 jobs)")
                        elif "Running" in status:
                            st.info("🔄 Running...")
                        else:
                            st.write(status)

                    with header_row[2]:
                        # Enhanced action buttons based on status
                        action_cols = st.columns([1, 1])

                        # Always show delete button (works for any status)
                        with action_cols[0]:
                            if st.button("🗑️", key=f"delete_{job_id}", help="Delete batch"):
                                try:
                                    if manager.delete_job(job_id):
                                        st.success(f"✅ Deleted batch {job_id}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to delete batch {job_id}")
                                except Exception as e:
                                    st.error(f"❌ Delete failed: {e}")

                        # Status-specific secondary action
                        with action_cols[1]:
                            if "Scheduled" in status or "Processing" in status:
                                if st.button("🚫", key=f"cancel_{job_id}", help="Cancel batch"):
                                    try:
                                        # AsyncJobManager doesn't have cancel_job method, so update status to cancelled
                                        if hasattr(manager, 'update_job'):
                                            manager.update_job(job_id, {
                                                'status': 'cancelled',
                                                'error_message': f'Cancelled by {coach.username}',
                                                'completed_at': datetime.now().isoformat()
                                            })
                                            st.success(f"✅ Cancelled batch {job_id}")
                                            st.rerun()
                                        else:
                                            # Fallback: delete if update not available
                                            if manager.delete_job(job_id):
                                                st.success(f"✅ Stopped batch {job_id}")
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to stop batch {job_id}")
                                    except Exception as e:
                                        st.error(f"❌ Cancel failed: {e}")
                            elif "Complete" in status:
                                if st.button("📊", key=f"download_{job_id}", help="Download results"):
                                    try:
                                        run_id = data.get('run_id')
                                        if not run_id:
                                            st.warning(f"⚠️ No run_id found for batch {job_id}")
                                        else:
                                            # Query jobs from Supabase using run_id
                                            jobs_df = memory_db.query_jobs_by_run_id(run_id)

                                            if jobs_df.empty:
                                                st.warning(f"⚠️ No jobs found for batch {job_id} (run_id: {run_id})")
                                            else:
                                                # Generate CSV
                                                csv_buffer = io.StringIO()
                                                jobs_df.to_csv(csv_buffer, index=False)
                                                csv_data = csv_buffer.getvalue()

                                                # Offer download
                                                st.download_button(
                                                    label=f"💾 Download {len(jobs_df)} jobs as CSV",
                                                    data=csv_data,
                                                    file_name=f"batch_{job_id}_{run_id}.csv",
                                                    mime="text/csv",
                                                    key=f"dl_btn_{job_id}"
                                                )
                                                st.success(f"✅ {len(jobs_df)} jobs ready for download")
                                    except Exception as e:
                                        st.error(f"❌ Download failed: {e}")
                                        import traceback
                                        with st.expander("Error details"):
                                            st.code(traceback.format_exc())
                            elif "Failed" in status:
                                if st.button("🔄", key=f"retry_{job_id}", help="Retry batch"):
                                    st.info(f"🔄 Retry functionality for batch {job_id} - coming soon!")

                    # Details row: Search parameters and results
                    details_row = st.columns([2, 2, 1])

                    with details_row[0]:
                        location_terms = f"📍 {data['Location']}"
                        if len(data['Terms']) > 30:
                            search_terms_display = data['Terms'][:30] + "..."
                        else:
                            search_terms_display = data['Terms']
                        st.caption(f"{location_terms}")
                        st.caption(f"🔍 {search_terms_display}")

                    with details_row[1]:
                        st.caption(f"{data['Type']} • {data['Source']}")
                        st.caption(f"📊 {data['Total Jobs']} total, {data['Quality Jobs']} quality")

                    with details_row[2]:
                        if data['Frequency'] != "Once":
                            st.caption(f"🔄 {data['Frequency']}")

                    st.divider()
                    
        else:
            st.info("📝 No scheduled batches found. Create your first batch above!")
            
    except Exception as e:
        st.error(f"❌ Error displaying scheduled batches table: {e}")
        import traceback
        with st.expander("🐛 Error Details", expanded=False):
            st.code(traceback.format_exc())

# Check for Express Interest page (Inside Track partner jobs)
def show_express_interest_page(job_id: str, agent_id: str, prefill_name: str = "", prefill_phone: str = ""):
    """Show Express Interest page for Inside Track jobs - like empty portal notification but for interest."""
    from pdf.html_pdf_generator import _send_email_smtp
    from supabase_utils import get_client
    from datetime import datetime, timezone

    st.set_page_config(page_title="FreeWorld Partner Opportunity", page_icon="🤝", layout="centered")

    # FreeWorld styling
    st.markdown("""
    <style>
    .stApp { background-color: #F4F4F4; }
    .main-card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 24px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }
    .badge { display: inline-block; background: #CDF95C; color: #191931; padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; }
    .job-title { font-size: 22px; color: #004751; margin: 16px 0 8px 0; }
    .company { color: #666; margin-bottom: 16px; }
    </style>
    """, unsafe_allow_html=True)

    client = get_client()
    if not client:
        st.error("Database unavailable. Please try again later.")
        return

    # Look up job
    job_result = client.table('jobs').select('*').eq('job_id', job_id).eq('source', 'inside_track').single().execute()
    if not job_result.data:
        st.error("This job is no longer available.")
        return
    job = job_result.data

    # Look up agent
    agent_result = client.table('agent_profiles').select('agent_name, agent_email, admin_portal_url').eq('agent_uuid', agent_id).single().execute()
    agent = agent_result.data if agent_result.data else {}
    has_full_profile = bool(agent.get('admin_portal_url'))

    # Check if already registered
    existing = client.table('inside_track_interests').select('id').eq('job_id', job_id).eq('agent_uuid', agent_id).single().execute()
    if existing.data:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<div class="badge">FREEWORLD PARTNER OPPORTUNITY</div>', unsafe_allow_html=True)
        st.success("✅ You're Already On The List!")
        st.write("You've already expressed interest in this position. Your Success Coach has been notified and will be in touch soon.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Determine if we can auto-submit (have all required info)
    # Either: has_full_profile OR prefilled name+phone from JS modal
    can_auto_submit = has_full_profile or (prefill_name and prefill_phone)

    # Get final values
    final_name = agent.get('agent_name') or prefill_name
    final_email = agent.get('agent_email')
    final_phone = prefill_phone or None

    if can_auto_submit:
        # Auto-submit - don't show form, just process
        try:
            client.table('inside_track_interests').insert({
                'job_id': job_id,
                'agent_uuid': agent_id,
                'agent_name': final_name,
                'agent_email': final_email,
                'agent_phone': final_phone,
                'coach_username': job.get('success_coach'),
                'status': 'new',
            }).execute()

            # Send email notification
            coach_name = (job.get('success_coach') or 'Unknown').capitalize()
            admin_url = agent.get('admin_portal_url', '')

            html_body = f"""<!DOCTYPE html>
<html><body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px;">
<h2 style="color: #004751;">New Partner Job Interest</h2>
<div style="background: #f4f4f4; padding: 16px; border-radius: 8px; margin: 16px 0;">
<h3 style="margin: 0 0 8px 0; color: #191931;">Free Agent Details</h3>
<p style="margin: 4px 0;"><strong>Name:</strong> {final_name}</p>
{f'<p style="margin: 4px 0;"><strong>Email:</strong> {final_email}</p>' if final_email else ''}
{f'<p style="margin: 4px 0;"><strong>Phone:</strong> {final_phone}</p>' if final_phone else ''}
<p style="margin: 4px 0;"><strong>Coach:</strong> {coach_name}</p>
{f'<p style="margin: 4px 0;"><a href="{admin_url}" style="color: #004751; font-weight: bold;">View Agent Profile</a></p>' if admin_url else ''}
</div>
<div style="background: #e8f5e9; padding: 16px; border-radius: 8px; margin: 16px 0;">
<h3 style="margin: 0 0 8px 0; color: #004751;">Job Details</h3>
<p style="margin: 4px 0;"><strong>Title:</strong> {job['job_title']}</p>
<p style="margin: 4px 0;"><strong>Company:</strong> {job['company']}</p>
<p style="margin: 4px 0;"><strong>Location:</strong> {job['location']}</p>
<p style="margin: 4px 0;"><strong>Market:</strong> {job.get('market', 'N/A')}</p>
</div>
<p style="color: #666; font-size: 14px;">This Free Agent clicked EXPRESS INTEREST on a FreeWorld Partner job.</p>
<hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
<p style="color: #999; font-size: 12px;">Sent automatically by Opptek Portal</p>
</body></html>"""

            text_body = f"""New Partner Job Interest

Free Agent: {final_name}
{f'Email: {final_email}' if final_email else ''}
{f'Phone: {final_phone}' if final_phone else ''}
Coach: {coach_name}
{f'Agent Profile: {admin_url}' if admin_url else ''}

Job: {job['job_title']} at {job['company']}
Location: {job['location']}
Market: {job.get('market', 'N/A')}"""

            _send_email_smtp(
                "james@freeworld.org",  # Testing - change to placement@freeworld.org for prod
                f"New Partner Job Interest: {final_name} - {job['job_title']}",
                html_body,
                text_body
            )

            # Show success page
            st.markdown('<div class="main-card">', unsafe_allow_html=True)
            st.markdown('<div class="badge">FREEWORLD PARTNER OPPORTUNITY</div>', unsafe_allow_html=True)
            st.success("🎉 Interest Registered!")
            st.markdown(f'<h2 class="job-title">{job["job_title"]}</h2>', unsafe_allow_html=True)
            st.markdown(f'<p class="company">{job["company"]} • {job["location"]}</p>', unsafe_allow_html=True)
            st.write("Great news! Your Success Coach has been notified and will reach out soon.")
            st.write("**This is a FreeWorld partner job**, which means we have a direct connection to help you get hired!")
            st.balloons()
            st.markdown('</div>', unsafe_allow_html=True)
            return

        except Exception as e:
            st.error(f"Something went wrong. Please try again. ({e})")
            return

    # Fallback: Show form (shouldn't normally happen if JS modal works correctly)
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge">FREEWORLD PARTNER OPPORTUNITY</div>', unsafe_allow_html=True)
    st.markdown(f'<h2 class="job-title">{job["job_title"]}</h2>', unsafe_allow_html=True)
    st.markdown(f'<p class="company">{job["company"]} • {job["location"]}</p>', unsafe_allow_html=True)

    if job.get('route_type') or job.get('salary'):
        with st.container():
            if job.get('route_type'):
                st.write(f"**Route Type:** {job['route_type']}")
            if job.get('salary'):
                st.write(f"**Pay:** {job['salary']}")
            if job.get('fair_chance') == 'fair_chance_employer':
                st.write("✅ **Fair Chance Employer**")

    if job.get('summary') or job.get('job_description'):
        desc = job.get('summary') or job.get('job_description', '')[:300]
        st.write(desc)

    st.divider()

    # Form for interest (fallback if JS modal didn't provide data)
    with st.form("express_interest_form"):
        st.write("Please provide your contact info so we can reach you about this opportunity:")
        form_name = st.text_input("Your Name *", placeholder="Enter your full name")
        form_phone = st.text_input("Phone Number *", placeholder="(555) 123-4567")

        submitted = st.form_submit_button("✋ I'm Interested - Notify My Coach", use_container_width=True, type="primary")

        if submitted:
            # Validate
            if not form_name or not form_phone:
                st.error("Please enter your name and phone number.")
            else:
                # Save interest
                final_name = form_name
                final_email = agent.get('agent_email')
                final_phone = form_phone

                try:
                    client.table('inside_track_interests').insert({
                        'job_id': job_id,
                        'agent_uuid': agent_id,
                        'agent_name': final_name,
                        'agent_email': final_email,
                        'agent_phone': final_phone,
                        'coach_username': job.get('success_coach'),
                        'status': 'new',
                    }).execute()

                    # Send email notification
                    coach_name = (job.get('success_coach') or 'Unknown').capitalize()
                    admin_url = agent.get('admin_portal_url', '')

                    html_body = f"""<!DOCTYPE html>
<html><body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px;">
<h2 style="color: #004751;">New Partner Job Interest</h2>
<div style="background: #f4f4f4; padding: 16px; border-radius: 8px; margin: 16px 0;">
<h3 style="margin: 0 0 8px 0; color: #191931;">Free Agent Details</h3>
<p style="margin: 4px 0;"><strong>Name:</strong> {final_name}</p>
{f'<p style="margin: 4px 0;"><strong>Email:</strong> {final_email}</p>' if final_email else ''}
{f'<p style="margin: 4px 0;"><strong>Phone:</strong> {final_phone}</p>' if final_phone else ''}
<p style="margin: 4px 0;"><strong>Coach:</strong> {coach_name}</p>
{f'<p style="margin: 4px 0;"><a href="{admin_url}" style="color: #004751; font-weight: bold;">View Agent Profile</a></p>' if admin_url else ''}
</div>
<div style="background: #e8f5e9; padding: 16px; border-radius: 8px; margin: 16px 0;">
<h3 style="margin: 0 0 8px 0; color: #004751;">Job Details</h3>
<p style="margin: 4px 0;"><strong>Title:</strong> {job['job_title']}</p>
<p style="margin: 4px 0;"><strong>Company:</strong> {job['company']}</p>
<p style="margin: 4px 0;"><strong>Location:</strong> {job['location']}</p>
<p style="margin: 4px 0;"><strong>Market:</strong> {job.get('market', 'N/A')}</p>
</div>
<p style="color: #666; font-size: 14px;">This Free Agent clicked EXPRESS INTEREST on a FreeWorld Partner job.</p>
<hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
<p style="color: #999; font-size: 12px;">Sent automatically by Opptek Portal</p>
</body></html>"""

                    text_body = f"""New Partner Job Interest

Free Agent: {final_name}
{f'Email: {final_email}' if final_email else ''}
{f'Phone: {final_phone}' if final_phone else ''}
Coach: {coach_name}
{f'Agent Profile: {admin_url}' if admin_url else ''}

Job: {job['job_title']} at {job['company']}
Location: {job['location']}
Market: {job.get('market', 'N/A')}"""

                    _send_email_smtp(
                        "james@freeworld.org",  # Testing - change to placement@freeworld.org for prod
                        f"New Partner Job Interest: {final_name} - {job['job_title']}",
                        html_body,
                        text_body
                    )

                    st.success("🎉 Interest Registered!")
                    st.write("Great news! Your Success Coach has been notified and will reach out soon.")
                    st.balloons()

                except Exception as e:
                    st.error(f"Something went wrong. Please try again. ({e})")

    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("FreeWorld Partner Jobs give you a direct connection to employers")

# Check for Express Interest query params
try:
    interest_params = st.query_params
    interest_job_id = interest_params.get("interest_job")
    interest_agent_id = interest_params.get("interest_agent")
    interest_name = interest_params.get("name", "")
    interest_phone = interest_params.get("phone", "")
except Exception:
    interest_job_id = None
    interest_agent_id = None
    interest_name = ""
    interest_phone = ""

if interest_job_id and interest_agent_id:
    show_express_interest_page(interest_job_id, interest_agent_id, interest_name, interest_phone)
    st.stop()

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
