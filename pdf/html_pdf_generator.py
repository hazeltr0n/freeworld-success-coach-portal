# pdf/html_pdf_generator.py
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import List, Dict
import datetime as _dt
import base64
import pandas as pd
import re
import html as _html
import os

BASE = Path(__file__).resolve().parents[1]
TEMPLATES = BASE / "templates"
STATIC = BASE / "static"
ASSETS = BASE / "assets"
OUTFIT_FONT_DIR = BASE / "Outfit" / "static"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES)),
    autoescape=select_autoescape()
)

def _encode_asset_base64(path: Path) -> str:
    """Reads an asset file and returns its base64 encoded string."""
    if not path.exists():
        return ""
    try:
        mime_types = {
            ".jpg": "image/jpeg",
            ".png": "image/png",
            ".ttf": "font/truetype",
        }
        mime = mime_types.get(path.suffix, "")
        if not mime:
            return ""
        
        with open(path, "rb") as asset_file:
            encoded_string = base64.b64encode(asset_file.read()).decode("utf-8")
        return f"data:{mime};base64,{encoded_string}"
    except Exception:
        return ""

def jobs_dataframe_to_dicts(df, candidate_id: str = None) -> List[Dict]:
    def _sanitize_html(val: str) -> str:
        try:
            s = _html.unescape(str(val or ''))
            # remove scripts/styles
            s = re.sub(r'(?is)<(script|style)[^>]*>.*?</\\1>', '', s)
            # convert block/line breaks
            s = re.sub(r'(?i)</p\\s*>', '\n\n', s)
            s = re.sub(r'(?i)<br\\s*/?>', '\n', s)
            s = re.sub(r'(?i)<li\\b[^>]*>', '• ', s)
            s = re.sub(r'(?i)</li\\s*>', '\n', s)
            # drop remaining tags
            s = re.sub(r'<[^>]+>', '', s)
            # collapse and convert to HTML
            s = re.sub(r'\n{3,}', '\n\n', s).strip()
            return s.replace('\n', '<br>')
        except Exception:
            return str(val or '')
    def _truncate_text(text: str, max_len: int = 300) -> str:
        try:
            s = (text or '').strip()
            if len(s) <= max_len:
                return s
            return s[: max_len - 1].rstrip() + '…'
        except Exception:
            return text or ''
    def _clean_text(val: any) -> str:
        try:
            if pd.isna(val):
                return ''
        except Exception:
            pass
        s = str(val) if val is not None else ''
        return '' if s.strip().lower() in ('nan', 'none', 'null') else s

    def _format_salary(val: any) -> str:
        # Prefer pre-formatted salary string
        txt = _clean_text(val)
        if not txt:
            return ''
        # If looks like a dict string, try to parse and render terse display
        if txt.startswith('{') and txt.endswith('}'):
            try:
                import ast
                d = ast.literal_eval(txt)
                # Support { 'baseSalary': {'unitOfWork': 'HOUR', 'range': {'min': x, 'max': y}}, 'currencyCode': 'USD' }
                base = d.get('baseSalary', {}) if isinstance(d, dict) else {}
                rng = base.get('range', {}) if isinstance(base, dict) else {}
                unit_raw = base.get('unitOfWork') or ''
                unit = str(unit_raw).lower() if unit_raw else ''
                cur = d.get('currencyCode', 'USD')
                if rng:
                    mn = rng.get('min') or rng.get('minimum')
                    mx = rng.get('max') or rng.get('maximum')
                    parts = []
                    if mn and mx:
                        parts.append(f"{cur} {mn}-{mx}")
                    elif mn:
                        parts.append(f"{cur} {mn}")
                    elif mx:
                        parts.append(f"{cur} {mx}")
                    if unit:
                        parts.append(f"per {unit}")
                    return ' '.join(parts)
            except Exception:
                pass
        return txt

    # Use unified sorting to match FPDF exactly
    try:
        from job_sorting_utils import apply_unified_sorting
        df_sorted = apply_unified_sorting(df)
    except Exception as e:
        # Fallback to original DataFrame if sorting fails
        print(f"⚠️ Unified sorting failed: {e}, using original order")
        df_sorted = df.copy()

    rows = []
    for _, r in df_sorted.iterrows():
        # Use .get() to avoid errors if a column is missing
        # Provide fallbacks for robustness
        title = _clean_text(r.get('source.title') or r.get('norm.title') or 'CDL Driver Position')
        company = _clean_text(r.get('source.company') or r.get('norm.company') or 'Trucking Company')
        city = _clean_text(r.get('norm.city', ''))
        state = _clean_text(r.get('norm.state', ''))
        location_fallback = _clean_text(r.get('norm.location') or r.get('source.location_raw') or '')
        route_type = r.get('ai.route_type', 'Unknown')
        ai_match_raw = r.get('ai.match', 'good')
        ai_match = str(ai_match_raw).lower() if ai_match_raw is not None else 'good'
        fair_raw = r.get('ai.fair_chance', False)
        # Normalize fair chance to a boolean
        fair_chance = False
        if isinstance(fair_raw, bool):
            fair_chance = fair_raw
        else:
            fair_str = str(fair_raw) if fair_raw is not None else ''
            fair_chance = fair_str.lower().find('fair_chance_employer') >= 0 or fair_str.lower() in ('true', 'yes', '1')
        # Build both summary and full description for responsive display
        description_summary = _sanitize_html(r.get('ai.summary') or 'Great opportunity for CDL drivers.')
        description_full = _sanitize_html(r.get('source.description') or r.get('job_description') or r.get('norm.description') or 'Great opportunity for CDL drivers.')
        # Use ai.summary as primary description, fallback to truncated full description if needed
        if not description_summary or description_summary == 'Great opportunity for CDL drivers.':
            description_summary = _truncate_text(description_full, 320)
        # Keep description_full as the complete, untruncated description
        # salary = _format_salary(r.get('norm.salary_display', ''))  # Removed per request

        # Logic for apply URL with proper fallback chain
        # Try tracking URL first, then fall back to source URL (canonical schema)
        tracked = _clean_text(r.get('meta.tracked_url', ''))
        source_url = _clean_text(r.get('source.url', ''))
        clean_url = _clean_text(r.get('clean_apply_url', ''))
        
        # DEBUG: Print URL fields to identify why long URLs still showing
        job_id = r.get('id.job', 'unknown')[:8]
        print(f"🔍 HTML Job {job_id}: tracked='{tracked}', source='{source_url[:60]}...', clean='{clean_url[:60] if clean_url else 'None'}...'")
        
        apply_url = tracked or source_url or clean_url
        display_link = apply_url

        # Generate edge function URL for click tracking in PDFs
        tracking_url = apply_url  # Default to same as apply_url
        if apply_url and candidate_id:
            try:
                from link_tracker import LinkTracker
                tracker = LinkTracker()

                # Extract metadata for tracking
                job_match = r.get('ai.match', 'unknown')
                job_route = r.get('ai.route_type', 'unknown')
                job_fair = 'true' if r.get('ai.fair_chance') else 'false'

                tags = [
                    f"candidate:{candidate_id}",
                    f"job_id:{job_id}",
                    f"match:{job_match}",
                    f"route:{job_route}",
                    f"fair:{job_fair}",
                    "type:job_application"
                ]

                # Generate edge function URL for tracking
                tracking_url = tracker.generate_edge_function_url(
                    target_url=apply_url,
                    candidate_id=candidate_id,
                    tags=tags
                )
                print(f"🔍 PDF Job {job_id}: Generated tracking URL for {apply_url[:50]}...")
            except Exception as e:
                print(f"⚠️ Failed to generate tracking URL for job {job_id}: {e}")
                tracking_url = apply_url

        # Logic for match badge
        if ai_match == 'good':
            match_badge = 'Excellent Match'
        elif ai_match == 'so-so':
            match_badge = 'Possible Fit'
        else:
            match_badge = '' # Don't show a badge for 'bad' or 'unknown'

        rows.append({
            "title": title,
            "company": company,
            "city": city,
            "state": state,
            "location": location_fallback,
            "route_type": route_type,
            "match_badge": match_badge,
            "fair_chance": bool(fair_chance),
            # Backwards compatibility key 'description' holds the summary
            "description": description_summary,
            "description_summary": description_summary,
            "description_full": description_full,
            "apply_url": tracking_url,  # Use tracking URL for actual clicks
            "display_link": display_link,  # Keep Short.io link for display
            # Fields needed for feedback system (job_id for template, candidate_id for fallback)
            "job_id": job_id,
            "candidate_id": candidate_id or 'unknown',
            # "salary": salary,  # Removed per request
        })
    return rows

def render_jobs_html(jobs: List[Dict], agent_params=None, *, fragment: bool = False) -> str:
    """Renders the full report with header + multiple .page job cards."""
    agent_params = agent_params or {}
    location = agent_params.get("location") or "Unknown"
    
    # CRITICAL FIX: Ensure show_prepared_for is always a boolean for template processing
    if 'show_prepared_for' in agent_params:
        show_prepared_for = agent_params['show_prepared_for']
        if isinstance(show_prepared_for, str):
            agent_params['show_prepared_for'] = show_prepared_for.lower() not in ('false', '0', 'f', 'no', '')
        else:
            agent_params['show_prepared_for'] = bool(show_prepared_for)
    
    # Helpers: extract a clean first name from various formats
    def _first_name(raw: str, *, fallback: str) -> str:
        try:
            s = str(raw or "").strip()
            if not s:
                return fallback
            # Strip email domain if present
            s = s.split("@", 1)[0]
            # Normalize common separators (first.last, first_last, first-last)
            import re as _re
            s_norm = _re.sub(r"[._-]+", " ", s)
            words = s_norm.split()
            
            if not words:
                return fallback
            
            # Special handling: if first word is "Coach", take the second word as the name
            if len(words) >= 2 and words[0].lower() == "coach":
                first = words[1]
            else:
                first = words[0]
            
            # Title case but preserve all-caps abbreviations reasonably
            return first.title()
        except Exception:
            return fallback

    # Title page names: prefer explicit names; gracefully handle usernames like first.last
    # Only use fallbacks for _first_name processing, not for template logic
    raw_agent = agent_params.get("agent_name") or agent_params.get("name")
    raw_coach = agent_params.get("coach_name") or agent_params.get("coach_username")
    candidate_id = agent_params.get("agent_uuid") or agent_params.get("candidate_id") or ""
    
    # Only pass names to template if they were actually provided (not fallbacks)
    agent_first = _first_name(raw_agent, fallback="Free Agent") if raw_agent else None
    coach_first = _first_name(raw_coach, fallback="Coach") if raw_coach else None
    generated_on = _dt.datetime.now().strftime("%B %d, %Y")
    total = len(jobs)

    # Encode all assets to be embedded in the HTML
    # Load assets with fallbacks
    # Helper to pick the first available asset from candidates
    def _first_icon(*paths):
        for p in paths:
            enc = _encode_asset_base64(p)
            if enc:
                return enc
        return ""

    wordmark = _encode_asset_base64(ASSETS / "FW-Wordmark-Roots@3x.png")
    # Prefer a small, round/square icon; fall back to wordmark only if none found
    icon = _first_icon(
        ASSETS / "FW-Logo-Roots@2x.png",
        ASSETS / "fw_logo.png",
        BASE / "data" / "FW-Logo-Roots@2x.png",
        BASE / "data" / "fw_logo.png",
    ) or wordmark
    assets = {
        "font_regular": _encode_asset_base64(OUTFIT_FONT_DIR / "Outfit-Regular.ttf"),
        "font_bold": _encode_asset_base64(OUTFIT_FONT_DIR / "Outfit-Bold.ttf"),
        "bg_image": _encode_asset_base64(ASSETS / "highway_background.jpg"),
        "wordmark_logo": wordmark,
        "icon_logo": icon,
    }

    # Optionally hide job cards entirely via env flag (for quick QA/lockdown)
    if os.getenv('FREEWORLD_PORTAL_HIDE_JOBS', '0') == '1':
        jobs = []

    # IMPORTANT: Do not generate or infer links here.
    # The Free Agent portal must only show the canonical tracked link provided by the pipeline.
    # If a job does not have meta.tracked_url, we intentionally leave the link blank.

    tmpl = env.get_template("report.html")
    try:
        html = tmpl.render(
            location=location,
            generated_on=generated_on,
            total_jobs=total,
            jobs=jobs,
            assets=assets,
            agent_name=agent_first,
            coach_name=coach_first,
            candidate_id=candidate_id,
            agent_params=agent_params,
        )
    except Exception as e:
        print(f"Error rendering report.html template: {e}")
        return f"<h1>Error rendering report</h1><p>{e}</p>"

    if not fragment:
        return html

    # Extract CSS from <style> tags
    style_match = re.search(r"<style>(.*?)</style>", html, flags=re.DOTALL|re.IGNORECASE)
    css_content = style_match.group(1).strip() if style_match else ""

    # Return only what's inside <body>...</body> for portal injection
    body_match = re.search(r"<body[^>]*>(.*)</body>", html, flags=re.DOTALL|re.IGNORECASE)
    body_content = body_match.group(1).strip() if body_match else html

    # Add debug comment with jobs data
    debug_jobs_comment = f"<!-- DEBUG_JOBS_DATA: {jobs} -->"
    body_content = f"{debug_jobs_comment}\n{body_content}"

    # Prepend CSS to body content
    return f"<style>{css_content}</style>{body_content}"


def export_pdf_playwright(html: str, output_path: str):
    from playwright.sync_api import sync_playwright
    from pathlib import Path
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "report.html"
        p.write_text(html, encoding="utf-8")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto(p.as_uri(), wait_until="networkidle")
            page.pdf(
                path=output_path,
                format="Letter",
                print_background=True,
                margin={"top":"0","right":"0","bottom":"0","left":"0"}
            )
            browser.close()

def export_pdf_weasyprint(html: str, output_path: str):
    """Export PDF using Playwright (renamed for compatibility)"""
    export_pdf_playwright(html, output_path)
